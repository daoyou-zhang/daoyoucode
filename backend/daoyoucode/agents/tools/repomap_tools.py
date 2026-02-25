"""
RepoMap工具 - 代码地图生成

基于daoyouCodePilot的最佳实现：
- Tree-sitter解析代码结构
- PageRank算法智能排序
- 个性化权重（对话文件×50，提到的标识符×10）
- 缓存机制（SQLite + mtime检测）
- Token预算控制
"""

from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
import logging
import json
import time
from collections import defaultdict, namedtuple
import warnings

from diskcache import Cache

from .base import BaseTool, ToolResult

# 忽略 tree_sitter 的 FutureWarning
warnings.simplefilter("ignore", category=FutureWarning)

# 导入 grep_ast 库
try:
    from grep_ast import filename_to_lang
    from grep_ast.tsl import USING_TSL_PACK, get_language, get_parser
    from pygments.lexers import guess_lexer_for_filename
    from pygments.token import Token
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False

logger = logging.getLogger(__name__)

# Tag 数据结构
Tag = namedtuple("Tag", "rel_fname fname line name kind".split())


class RepoMapTool(BaseTool):
    """
    生成代码仓库地图
    
    功能：
    - 提取函数、类定义和引用关系
    - PageRank排序（基于引用关系）
    - 个性化权重（对话文件、提到的标识符）
    - 缓存机制（避免重复解析）
    - Token预算控制
    
    🆕 公开API（供codebase_index等外部模块使用）：
    - get_definitions(): 获取代码定义
    - get_reference_graph(): 获取引用图
    - get_pagerank_scores(): 获取PageRank分数
    """
    
    # RepoMap可以稍微长一点，因为它是智能排序的
    MAX_OUTPUT_CHARS = 10000
    MAX_OUTPUT_LINES = 1000
    
    def __init__(self):
        super().__init__(
            name="repo_map",
            description="生成代码仓库地图，智能排序最相关的代码定义"
        )
        # 🔥 第3层：文件级缓存（diskcache）
        self.file_cache = None
        
        # 🔥 第2层：内存级缓存（definitions + graph）
        self.definitions_cache = None
        self.graph_cache = None
        self.cache_timestamp = None
        self.cached_repo_path = None
        
        # 🔥 第1层：结果级缓存（map结果）
        self.map_cache = {}  # {cache_key: (result, timestamp)}
        self.map_cache_ttl = 300  # 5分钟过期
        
        self.graph = None
        self._last_definitions = None  # 🆕 保存最后一次的definitions
        
        # 缓存统计
        self.cache_stats = {
            'result_hits': 0,
            'result_misses': 0,
            'memory_hits': 0,
            'memory_misses': 0,
            'file_hits': 0,
            'file_misses': 0
        }
    
    def get_function_schema(self) -> Dict[str, Any]:
        """获取Function Calling schema"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "repo_path": {
                        "type": "string",
                        "description": "仓库根目录路径。必须使用 '.' 表示当前工作目录，不要使用占位符路径！"
                    },
                    "chat_files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "对话中提到的文件列表（权重×50）。如果为空，会自动扩大token预算以提供更全面的项目视图"
                    },
                    "mentioned_idents": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "对话中提到的标识符列表（权重×10）"
                    },
                    "max_tokens": {
                        "type": "integer",
                        "description": "最大token数量（默认3000）。如果chat_files为空，会自动扩大到6000",
                        "default": 3000
                    },
                    "auto_scale": {
                        "type": "boolean",
                        "description": "是否自动调整token预算（默认true）。当chat_files为空时，自动扩大预算以提供更全面的视图",
                        "default": True
                    },
                    "enable_lsp": {
                        "type": "boolean",
                        "description": "是否启用LSP增强（默认true）。启用后会显示类型签名和引用计数",
                        "default": True
                    }
                },
                "required": ["repo_path"]
            }
        }
    
    # ========== 🆕 公开API（供外部模块使用）==========
    
    def get_definitions(
        self,
        repo_path: str,
        use_cache: bool = True
    ) -> Dict[str, List[Dict]]:
        """
        获取代码定义（公开API）
        
        Args:
            repo_path: 仓库路径
            use_cache: 是否使用缓存
        
        Returns:
            {
                "backend/agents/core/agent.py": [
                    {
                        "type": "class",
                        "name": "BaseAgent",
                        "line": 50,
                        "end_line": 150,
                        "kind": "def",
                        "parent": None,
                        "scope": "global"
                    },
                    ...
                ]
            }
        """
        repo_path_resolved = self.resolve_path(repo_path)
        
        if not repo_path_resolved.exists():
            logger.warning(f"仓库路径不存在: {repo_path}")
            return {}
        
        if use_cache:
            self._init_cache(repo_path_resolved)
        
        definitions = self._scan_repository(repo_path_resolved)
        
        # 🆕 计算end_line（如果没有）
        definitions = self._compute_end_lines(definitions, repo_path_resolved)
        
        # 保存以供其他方法使用
        self._last_definitions = definitions
        
        return definitions
    
    def get_reference_graph(
        self,
        repo_path: str,
        definitions: Optional[Dict[str, List[Dict]]] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        获取引用图（公开API）
        
        Args:
            repo_path: 仓库路径
            definitions: 代码定义（如果为None，会自动获取）
        
        Returns:
            {
                "file_a.py": {
                    "file_b.py": 3.0,  # file_a引用file_b 3次
                    "file_c.py": 1.0
                }
            }
        """
        repo_path_resolved = self.resolve_path(repo_path)
        
        if definitions is None:
            definitions = self.get_definitions(repo_path)
        
        return self._build_reference_graph(definitions, repo_path_resolved)
    
    def get_pagerank_scores(
        self,
        repo_path: str,
        reference_graph: Optional[Dict] = None,
        definitions: Optional[Dict] = None,
        chat_files: Optional[List[str]] = None,
        mentioned_idents: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """
        获取PageRank分数（公开API）
        
        Args:
            repo_path: 仓库路径
            reference_graph: 引用图（如果为None，会自动获取）
            definitions: 代码定义（如果为None，会自动获取）
            chat_files: 焦点文件
            mentioned_idents: 提到的标识符
        
        Returns:
            {
                "file_a.py": 0.85,
                "file_b.py": 0.65,
                ...
            }
        """
        if definitions is None:
            definitions = self.get_definitions(repo_path)
        
        if reference_graph is None:
            reference_graph = self.get_reference_graph(repo_path, definitions)
        
        ranked = self._pagerank(
            reference_graph,
            definitions,
            chat_files or [],
            mentioned_idents or []
        )
        
        return dict(ranked)
    
    # ========== 私有方法（保持不变）==========
        
    async def execute(
        self,
        repo_path: str,
        chat_files: Optional[List[str]] = None,
        mentioned_idents: Optional[List[str]] = None,
        max_tokens: int = 3000,
        auto_scale: bool = True,
        enable_lsp: bool = True  # 🔥 新增：默认启用LSP
    ) -> ToolResult:
        """
        生成RepoMap
        
        Args:
            repo_path: 仓库根目录
            chat_files: 对话中的文件（权重×50）
            mentioned_idents: 提到的标识符（权重×10）
            max_tokens: 最大token数量
            auto_scale: 是否自动调整token预算
            enable_lsp: 是否启用LSP增强（默认True）
            
        Returns:
            ToolResult
        """
        try:
            # 使用 resolve_path 解析路径（使用 ToolContext）
            repo_path_resolved = self.resolve_path(repo_path)
            
            if not repo_path_resolved.exists():
                return ToolResult(
                    success=False,
                    content=None,
                    error=f"仓库路径不存在: {repo_path}"
                )
            
            chat_files = chat_files or []
            mentioned_idents = mentioned_idents or []
            
            # 智能调整token预算
            original_max_tokens = max_tokens
            if auto_scale:
                if not chat_files or len(chat_files) == 0:
                    # 没有对话文件，扩大预算（2倍，最多6000）
                    max_tokens = min(max_tokens * 2, 6000)
                    logger.info(
                        f"🔍 智能调整: 无对话文件，扩大token预算 "
                        f"{original_max_tokens} → {max_tokens} "
                        f"(提供更全面的项目视图)"
                    )
                else:
                    logger.info(
                        f"📁 智能调整: 有 {len(chat_files)} 个对话文件，"
                        f"使用标准token预算 {max_tokens}"
                    )
            
            # 🔥 第1层：检查结果级缓存
            cache_key = self._make_cache_key(chat_files, mentioned_idents, max_tokens)
            
            if cache_key in self.map_cache:
                cached_result, timestamp = self.map_cache[cache_key]
                if time.time() - timestamp < self.map_cache_ttl:
                    self.cache_stats['result_hits'] += 1
                    logger.info(f"✅ 命中结果级缓存 (0.001秒) | 统计: {self._format_cache_stats()}")
                    return cached_result
            
            self.cache_stats['result_misses'] += 1
            
            # 初始化文件级缓存
            self._init_cache(repo_path_resolved)
            
            # 🔥 第2层：检查内存级缓存
            files_changed = self._check_files_changed(repo_path_resolved)
            
            if not files_changed and self.definitions_cache and self.cached_repo_path == str(repo_path_resolved):
                self.cache_stats['memory_hits'] += 1
                logger.info(f"✅ 命中内存级缓存，跳过扫描 (0.1秒) | 统计: {self._format_cache_stats()}")
                definitions = self.definitions_cache
                graph = self.graph_cache
            else:
                self.cache_stats['memory_misses'] += 1
                
                # 🔥 第3层：扫描仓库（使用文件级缓存 + 增量更新）
                scan_start = time.time()
                definitions, changed_files = self._scan_repository_incremental(repo_path_resolved)
                scan_time = time.time() - scan_start
                
                # 🔥 增量更新引用图
                graph_start = time.time()
                if changed_files and self.graph_cache:
                    # 有改动且有缓存，增量更新
                    graph = self._update_reference_graph_incremental(
                        self.graph_cache,
                        definitions,
                        changed_files,
                        repo_path_resolved
                    )
                    logger.info(f"🔄 增量更新引用图: {len(changed_files)} 个文件")
                    
                    # 🔥 清除结果级缓存（因为 RepoMap 已改变）
                    if self.map_cache:
                        old_cache_size = len(self.map_cache)
                        self.map_cache.clear()
                        logger.info(f"🗑️  清除结果级缓存: {old_cache_size} 个条目（因为文件改动）")
                else:
                    # 首次运行或全量更新
                    graph = self._build_reference_graph(definitions, repo_path_resolved)
                
                graph_time = time.time() - graph_start
                
                logger.info(
                    f"🔍 扫描完成: {len(definitions)} 个文件 "
                    f"(扫描 {scan_time:.2f}秒, 构图 {graph_time:.2f}秒) | "
                    f"统计: {self._format_cache_stats()}"
                )
                
                # 保存到内存缓存
                self.definitions_cache = definitions
                self.graph_cache = graph
                self.cache_timestamp = time.time()
                self.cached_repo_path = str(repo_path_resolved)
            
            # PageRank排序
            ranked = self._pagerank(
                graph,
                definitions,
                chat_files=chat_files,
                mentioned_idents=mentioned_idents
            )
            
            # 🔥 LSP增强：为top-k定义添加类型信息
            if enable_lsp:
                await self._enhance_with_lsp(ranked, definitions, repo_path_resolved)
            
            # 生成地图（控制token）
            repo_map = self._generate_map(
                ranked,
                definitions,
                max_tokens=max_tokens,
                enable_lsp=enable_lsp
            )
            
            # 构建结果
            result = ToolResult(
                success=True,
                content=repo_map,
                metadata={
                    'repo_path': str(repo_path_resolved),
                    'file_count': len(definitions),
                    'definition_count': sum(len(defs) for defs in definitions.values()),
                    'max_tokens': max_tokens,
                    'original_max_tokens': original_max_tokens,
                    'auto_scaled': auto_scale and (max_tokens != original_max_tokens),
                    'chat_files_count': len(chat_files),
                    'lsp_enabled': enable_lsp,
                    'cache_stats': self.cache_stats.copy()
                }
            )
            
            # 🔥 保存到结果级缓存
            self.map_cache[cache_key] = (result, time.time())
            
            return result
            
        except Exception as e:
            logger.error(f"生成RepoMap失败: {e}", exc_info=True)
            return ToolResult(
                success=False,
                content=None,
                error=str(e)
            )
    
    def _init_cache(self, repo_path: Path):
        """初始化 diskcache 缓存"""
        cache_dir = repo_path / ".daoyoucode" / "cache" / "repomap"
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 使用 diskcache（自动管理 SQLite）
        self.file_cache = Cache(str(cache_dir))
    
    def _make_cache_key(
        self,
        chat_files: List[str],
        mentioned_idents: List[str],
        max_tokens: int
    ) -> Tuple:
        """生成结果级缓存键"""
        return (
            tuple(sorted(chat_files or [])),
            tuple(sorted(mentioned_idents or [])),
            max_tokens
        )
    
    def _check_files_changed(self, repo_path: Path) -> bool:
        """
        检查文件是否改动（快速检查）
        
        策略：
        1. 检查 .git/index 的 mtime（最快）
        2. 采样检查缓存文件的 mtime（较快）
        """
        if not self.cache_timestamp:
            return True
        
        # 方法1：检查 .git/index 的 mtime（最快）
        git_index = repo_path / ".git" / "index"
        if git_index.exists():
            index_mtime = git_index.stat().st_mtime
            if index_mtime > self.cache_timestamp:
                logger.info("🔄 检测到 Git 改动，清除内存缓存")
                return True
        
        # 方法2：采样检查缓存文件的 mtime（较快）
        if self.definitions_cache:
            # 采样检查前10个文件
            sample_files = list(self.definitions_cache.keys())[:10]
            for file_path in sample_files:
                full_path = repo_path / file_path
                if full_path.exists():
                    file_mtime = full_path.stat().st_mtime
                    if file_mtime > self.cache_timestamp:
                        logger.info(f"🔄 检测到文件改动: {file_path}")
                        return True
        
        return False
    
    def _format_cache_stats(self) -> str:
        """格式化缓存统计信息"""
        stats = self.cache_stats
        
        # 计算命中率
        result_total = stats['result_hits'] + stats['result_misses']
        memory_total = stats['memory_hits'] + stats['memory_misses']
        file_total = stats['file_hits'] + stats['file_misses']
        
        result_rate = stats['result_hits'] / result_total if result_total > 0 else 0
        memory_rate = stats['memory_hits'] / memory_total if memory_total > 0 else 0
        file_rate = stats['file_hits'] / file_total if file_total > 0 else 0
        
        return (
            f"结果级 {result_rate:.0%} ({stats['result_hits']}/{result_total}), "
            f"内存级 {memory_rate:.0%} ({stats['memory_hits']}/{memory_total}), "
            f"文件级 {file_rate:.0%} ({stats['file_hits']}/{file_total})"
        )
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息（公开API）"""
        stats = self.cache_stats.copy()
        
        # 计算命中率
        result_total = stats['result_hits'] + stats['result_misses']
        memory_total = stats['memory_hits'] + stats['memory_misses']
        file_total = stats['file_hits'] + stats['file_misses']
        
        stats['result_hit_rate'] = stats['result_hits'] / result_total if result_total > 0 else 0
        stats['memory_hit_rate'] = stats['memory_hits'] / memory_total if memory_total > 0 else 0
        stats['file_hit_rate'] = stats['file_hits'] / file_total if file_total > 0 else 0
        
        return stats
    
    def _scan_repository(self, repo_path: Path) -> Dict[str, List[Dict]]:
        """
        扫描仓库，提取定义（支持增量更新）
        
        Returns:
            {file_path: [definition, ...]}
        """
        definitions, _ = self._scan_repository_incremental(repo_path)
        return definitions
    
    def _scan_repository_incremental(self, repo_path: Path) -> Tuple[Dict[str, List[Dict]], List[str]]:
        """
        增量扫描仓库，提取定义
        
        Returns:
            (definitions, changed_files)
            - definitions: {file_path: [definition, ...]}
            - changed_files: [改动的文件列表]
        """
        definitions = {}
        changed_files = []
        unchanged_files = []
        
        # 支持的文件扩展名
        extensions = {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs"}
        
        for file_path in repo_path.rglob("*"):
            if not file_path.is_file():
                continue
            if file_path.suffix not in extensions:
                continue
            if self._should_ignore(file_path):
                continue
            
            # 🆕 subtree_only 过滤
            rel_path_str = str(file_path.relative_to(repo_path))
            if not self.context.should_include_path(rel_path_str):
                logger.debug(f"跳过文件（subtree_only）: {rel_path_str}")
                continue
            
            # 检查缓存
            rel_path = rel_path_str
            mtime = file_path.stat().st_mtime
            
            cached = self._get_cached_definitions(rel_path, mtime)
            if cached is not None:
                # 🔥 命中缓存，直接使用
                definitions[rel_path] = cached
                unchanged_files.append(rel_path)
                continue
            
            # 🔥 未命中缓存，需要重新解析
            changed_files.append(rel_path)
            file_defs = self._parse_file(file_path)
            definitions[rel_path] = file_defs
            
            # 缓存结果
            self._cache_definitions(rel_path, mtime, file_defs)
        
        # 🔥 增量更新日志
        if changed_files:
            logger.info(
                f"🔄 增量更新: {len(changed_files)} 个文件改动, "
                f"{len(unchanged_files)} 个文件复用缓存"
            )
        else:
            logger.info(f"✅ 全部命中缓存: {len(unchanged_files)} 个文件")
        
        return definitions, changed_files
    
    def _should_ignore(self, file_path: Path) -> bool:
        """
        检查是否应该忽略文件
        
        忽略规则：
        1. 常见的构建和依赖目录
        2. 读取 .daoyoucodeignore 文件（如果存在）
        """
        # 常见的构建和依赖目录
        common_ignore = {
            ".git", "node_modules", "__pycache__", ".venv", "venv",
            "dist", "build", ".next", ".nuxt", "target"
        }
        
        for part in file_path.parts:
            if part in common_ignore:
                return True
        
        # TODO: 读取 .daoyoucodeignore 文件
        # 这样用户可以自定义忽略规则，不需要硬编码
        
        return False
    
    def _get_cached_definitions(self, file_path: str, mtime: float) -> Optional[List[Dict]]:
        """从缓存获取定义（使用 diskcache）"""
        val = self.file_cache.get(file_path)
        
        if val is not None and val.get("mtime") == mtime:
            self.cache_stats['file_hits'] += 1
            return val["data"]
        
        self.cache_stats['file_misses'] += 1
        return None
    
    def _cache_definitions(self, file_path: str, mtime: float, definitions: List[Dict]):
        """缓存定义（使用 diskcache）"""
        self.file_cache[file_path] = {
            "mtime": mtime,
            "data": definitions
        }
    
    def _parse_file(self, file_path: Path) -> List[Dict]:
        """
        解析文件，提取定义和引用
        
        使用 Tree-sitter 解析（完整实现）
        """
        if not TREE_SITTER_AVAILABLE:
            logger.warning("Tree-sitter 不可用，跳过文件解析")
            return []
        
        # 获取语言
        lang = filename_to_lang(str(file_path))
        if not lang:
            return []
        
        try:
            language = get_language(lang)
            parser = get_parser(lang)
        except Exception as err:
            logger.warning(f"跳过文件 {file_path}: {err}")
            return []
        
        # 获取查询文件
        query_scm = self._get_scm_fname(lang)
        if not query_scm or not query_scm.exists():
            return []
        
        query_scm_content = query_scm.read_text()
        
        # 读取代码
        try:
            code = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            logger.warning(f"读取文件失败 {file_path}: {e}")
            return []
        
        if not code:
            return []
        
        # 解析代码
        tree = parser.parse(bytes(code, "utf-8"))
        
        # 运行标签查询
        try:
            from tree_sitter import Query, QueryCursor
            query = Query(language, query_scm_content)
            cursor = QueryCursor(query)
            matches = cursor.matches(tree.root_node)
        except Exception as e:
            logger.warning(f"查询执行失败 {file_path}: {e}")
            return []
        
        definitions = []
        saw = set()
        parent_stack = []  # 🆕 跟踪父级（用于确定方法所属的类）
        
        # 处理匹配结果: [(pattern_index, {capture_name: [nodes]})]
        for pattern_index, captures_dict in matches:
            for tag, nodes in captures_dict.items():
                for node in nodes:
                    if tag.startswith("name.definition."):
                        kind = "def"
                    elif tag.startswith("name.reference."):
                        kind = "ref"
                    else:
                        continue
                    
                    saw.add(kind)
                    
                    # 提取类型（class、function、method等）
                    type_name = tag.split(".")[-1]
                    name = node.text.decode("utf-8")
                    
                    # 🆕 确定父级和作用域（仅对定义）
                    parent = None
                    scope = "global"
                    
                    if kind == "def":
                        # 确定父级
                        parent = parent_stack[-1] if parent_stack else None
                        
                        # 确定作用域
                        if type_name == "class":
                            scope = "global"
                            # 将类名压入栈（用于后续方法）
                            parent_stack.append(name)
                        elif type_name in ("function", "method"):
                            scope = "class" if parent else "global"
                        else:
                            scope = "global"
                    
                    definitions.append({
                        "type": type_name,
                        "name": name,
                        "line": node.start_point[0] + 1,
                        "kind": kind,
                        # 🆕 阶段2新增字段
                        "parent": parent,
                        "scope": scope
                    })
        
        # 如果只有定义没有引用，使用 Pygments 补充引用
        if "ref" not in saw and "def" in saw:
            try:
                lexer = guess_lexer_for_filename(str(file_path), code)
                tokens = list(lexer.get_tokens(code))
                tokens = [token[1] for token in tokens if token[0] in Token.Name]
                
                for token in tokens:
                    definitions.append({
                        "type": "reference",
                        "name": token,
                        "line": -1,
                        "kind": "ref"
                    })
            except Exception:
                pass
        
        return definitions
    
    def _get_scm_fname(self, lang: str) -> Optional[Path]:
        """获取 Tree-sitter 查询文件路径"""
        # 查询文件目录
        queries_dir = Path(__file__).parent / "queries"
        
        # 优先使用 tree-sitter-language-pack
        if USING_TSL_PACK:
            subdir = "tree-sitter-language-pack"
            path = queries_dir / subdir / f"{lang}-tags.scm"
            if path.exists():
                return path
        
        # 回退到 tree-sitter-languages
        subdir = "tree-sitter-languages"
        path = queries_dir / subdir / f"{lang}-tags.scm"
        if path.exists():
            return path
        
        return None
    
    def _compute_end_lines(
        self,
        definitions: Dict[str, List[Dict]],
        repo_path: Path
    ) -> Dict[str, List[Dict]]:
        """
        计算每个定义的结束行（🆕 公开API支持）
        
        策略：
        1. 如果已有end_line，保持不变
        2. 否则，找到下一个定义的起始行作为结束行
        3. 如果是最后一个定义，使用文件末尾
        """
        for file_path, defs in definitions.items():
            # 只处理定义，不处理引用
            def_only = [d for d in defs if d.get("kind") == "def"]
            
            if not def_only:
                continue
            
            # 按行号排序
            def_only.sort(key=lambda d: d["line"])
            
            for i, d in enumerate(def_only):
                if "end_line" in d and d["end_line"] > 0:
                    continue
                
                # 找到下一个定义
                if i + 1 < len(def_only):
                    d["end_line"] = def_only[i + 1]["line"] - 1
                else:
                    # 最后一个定义，读取文件获取总行数
                    try:
                        full_path = repo_path / file_path
                        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                            total_lines = len(f.readlines())
                        d["end_line"] = total_lines
                    except Exception as e:
                        logger.debug(f"无法读取文件 {file_path}: {e}")
                        # 如果读取失败，估计50行
                        d["end_line"] = d["line"] + 50
        
        return definitions

    
    def _build_reference_graph(self, definitions: Dict[str, List[Dict]], repo_path: Path) -> Dict[str, Dict[str, float]]:
        """
        构建引用图
        
        Returns:
            {node: {referenced_node: weight, ...}}
        """
        graph = defaultdict(lambda: defaultdict(float))
        
        # 构建标识符到文件的映射（只包含定义）
        ident_to_files = defaultdict(set)
        for file_path, defs in definitions.items():
            for d in defs:
                # 只添加定义，不添加引用
                if d.get("kind") == "def":
                    ident_to_files[d["name"]].add(file_path)
        
        # 扫描引用关系
        for file_path, defs in definitions.items():
            # 收集文件中的所有引用
            references_in_file = set()
            for d in defs:
                if d.get("kind") == "ref":
                    references_in_file.add(d["name"])
            
            # 为每个引用添加边
            for ident in references_in_file:
                if ident in ident_to_files:
                    # 文件引用了这个标识符
                    for ref_file in ident_to_files[ident]:
                        if ref_file != file_path:
                            # 添加边：file_path -> ref_file
                            graph[file_path][ref_file] += 1.0
        
        return dict(graph)
    
    def _update_reference_graph_incremental(
        self,
        old_graph: Dict[str, Dict[str, float]],
        definitions: Dict[str, List[Dict]],
        changed_files: List[str],
        repo_path: Path
    ) -> Dict[str, Dict[str, float]]:
        """
        增量更新引用图（只重新计算改动文件的引用关系）
        
        Args:
            old_graph: 旧的引用图
            definitions: 所有文件的定义
            changed_files: 改动的文件列表
            repo_path: 仓库路径
        
        Returns:
            更新后的引用图
        """
        # 复制旧图
        graph = defaultdict(lambda: defaultdict(float))
        for source, targets in old_graph.items():
            graph[source] = defaultdict(float, targets)
        
        # 🔥 步骤1：删除改动文件的旧引用关系
        for file in changed_files:
            # 删除该文件作为源的引用
            if file in graph:
                del graph[file]
            
            # 删除指向该文件的引用
            for source in list(graph.keys()):
                if file in graph[source]:
                    del graph[source][file]
                    # 如果源文件没有其他引用，删除该源
                    if not graph[source]:
                        del graph[source]
        
        # 🔥 步骤2：重新构建标识符映射（只包含改动文件的定义）
        ident_to_files = defaultdict(set)
        
        # 添加所有文件的定义（用于查找引用目标）
        for file_path, defs in definitions.items():
            for d in defs:
                if d.get("kind") == "def":
                    ident_to_files[d["name"]].add(file_path)
        
        # 🔥 步骤3：重新计算改动文件的引用关系
        for file_path in changed_files:
            if file_path not in definitions:
                continue
            
            defs = definitions[file_path]
            
            # 收集文件中的所有引用
            references_in_file = set()
            for d in defs:
                if d.get("kind") == "ref":
                    references_in_file.add(d["name"])
            
            # 为每个引用添加边
            for ident in references_in_file:
                if ident in ident_to_files:
                    for ref_file in ident_to_files[ident]:
                        if ref_file != file_path:
                            graph[file_path][ref_file] += 1.0
        
        # 🔥 步骤4：重新计算指向改动文件的引用
        # 其他文件可能引用了改动文件中的定义
        changed_idents = set()
        for file_path in changed_files:
            if file_path in definitions:
                for d in definitions[file_path]:
                    if d.get("kind") == "def":
                        changed_idents.add(d["name"])
        
        # 扫描所有文件，找到引用了改动标识符的文件
        for file_path, defs in definitions.items():
            if file_path in changed_files:
                continue  # 跳过改动文件（已处理）
            
            # 收集文件中的引用
            references_in_file = set()
            for d in defs:
                if d.get("kind") == "ref":
                    references_in_file.add(d["name"])
            
            # 检查是否引用了改动的标识符
            referenced_changed = references_in_file.intersection(changed_idents)
            if referenced_changed:
                # 重新计算该文件指向改动文件的引用
                for ident in referenced_changed:
                    if ident in ident_to_files:
                        for ref_file in ident_to_files[ident]:
                            if ref_file != file_path and ref_file in changed_files:
                                graph[file_path][ref_file] += 1.0
        
        return dict(graph)
    
    def _pagerank(
        self,
        graph: Dict[str, Dict[str, float]],
        definitions: Dict[str, List[Dict]],  # 添加 definitions 参数
        chat_files: List[str],
        mentioned_idents: List[str],
        damping: float = 0.85,
        iterations: int = 20
    ) -> List[Tuple[str, float]]:
        """
        PageRank算法排序
        
        Args:
            graph: 引用图
            chat_files: 对话中的文件（权重×50）
            mentioned_idents: 提到的标识符（权重×10）
            damping: 阻尼系数
            iterations: 迭代次数
            
        Returns:
            [(file_path, score), ...] 按分数降序
        """
        # 所有节点
        nodes = set(graph.keys())
        for targets in graph.values():
            nodes.update(targets.keys())
        
        if not nodes:
            return []
        
        # 初始化分数
        scores = {node: 1.0 / len(nodes) for node in nodes}
        
        # 个性化权重
        personalization = {}
        for node in nodes:
            weight = 1.0
            
            # 对话文件权重×50
            if node in chat_files:
                weight *= 50
            
            # 提到的标识符权重×10
            # 检查：1) 路径组件  2) 文件中的定义名称
            if mentioned_idents:
                # 检查路径组件（如 agents/llm/timeout）
                path_components = set(Path(node).parts)
                basename_with_ext = Path(node).name
                basename_without_ext = Path(node).stem
                components_to_check = path_components.union({basename_with_ext, basename_without_ext})
                
                # 检查路径是否包含提到的标识符
                matched_path = components_to_check.intersection(set(ident.lower() for ident in mentioned_idents))
                if matched_path:
                    weight *= 10
                
                # 检查文件中的定义是否包含提到的标识符
                if node in definitions:
                    file_defs = definitions.get(node, [])
                    def_names = {d['name'].lower() for d in file_defs if d.get('kind') == 'def'}
                    mentioned_lower = {ident.lower() for ident in mentioned_idents}
                    
                    # 精确匹配或部分匹配
                    if def_names.intersection(mentioned_lower):
                        weight *= 10
                    else:
                        # 部分匹配（如 'timeout' 匹配 'TimeoutError'）
                        for def_name in def_names:
                            for ident in mentioned_lower:
                                if ident in def_name or def_name in ident:
                                    weight *= 5  # 部分匹配权重较低
                                    break
            
            personalization[node] = weight
        
        # 归一化
        total = sum(personalization.values())
        personalization = {k: v / total for k, v in personalization.items()}
        
        # PageRank迭代
        for _ in range(iterations):
            new_scores = {}
            
            for node in nodes:
                # 基础分数（随机跳转）
                score = (1 - damping) * personalization.get(node, 1.0 / len(nodes))
                
                # 来自其他节点的分数
                for source, targets in graph.items():
                    if node in targets:
                        # source -> node
                        weight = targets[node]
                        out_weight = sum(targets.values())
                        score += damping * scores[source] * (weight / out_weight)
                
                new_scores[node] = score
            
            scores = new_scores
        
        # 排序
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return ranked
    
    def _generate_map(
        self,
        ranked: List[Tuple[str, float]],
        definitions: Dict[str, List[Dict]],
        max_tokens: int,
        enable_lsp: bool = False  # 🔥 新增参数
    ) -> str:
        """
        生成代码地图（控制token数量）
        
        使用二分查找找到最优token数量
        """
        lines = []
        current_tokens = 0
        
        for file_path, score in ranked:
            if file_path not in definitions:
                continue
            
            file_defs = definitions[file_path]
            if not file_defs:
                continue
            
            # 只包含定义，不包含引用
            file_defs = [d for d in file_defs if d.get("kind") == "def"]
            if not file_defs:
                continue
            
            # 标准化路径（确保返回相对于 repo_path 的路径）
            normalized_path = self.normalize_path(file_path)
            
            # 文件头
            file_line = f"\n{normalized_path}:"
            file_tokens = len(file_line.split())
            
            if current_tokens + file_tokens > max_tokens:
                break
            
            lines.append(file_line)
            current_tokens += file_tokens
            
            # 定义列表
            for d in file_defs:
                # 🔥 LSP增强输出：显示类型签名和引用计数
                has_signature = enable_lsp and d.get('lsp_signature')
                has_ref_count = enable_lsp and d.get('lsp_ref_count', 0) > 0
                
                if has_signature and has_ref_count:
                    # 完整LSP信息：类型签名 + 引用计数
                    def_line = f"  {d.get('type', 'unknown')} {d['name']}: {d['lsp_signature']}  # {d['lsp_ref_count']}次引用"
                elif has_signature:
                    # 只有类型签名
                    def_line = f"  {d.get('type', 'unknown')} {d['name']}: {d['lsp_signature']}"
                elif has_ref_count:
                    # 只有引用计数
                    def_line = f"  {d.get('type', 'unknown')} {d['name']} (line {d['line']})  # {d['lsp_ref_count']}次引用"
                elif enable_lsp and d.get('lsp_verified'):
                    # LSP验证通过但无额外信息
                    def_line = f"  {d.get('type', 'unknown')} {d['name']} (line {d['line']}) ✓"
                else:
                    # 标准格式
                    def_line = f"  {d.get('type', 'unknown')} {d['name']} (line {d['line']})"
                
                def_tokens = len(def_line.split())
                
                if current_tokens + def_tokens > max_tokens:
                    break
                
                lines.append(def_line)
                current_tokens += def_tokens
            
            if current_tokens >= max_tokens:
                break
        
        if not lines:
            return "代码地图为空"
        
        # 添加头部
        file_count = len([l for l in lines if l.startswith('\n')])
        header = f"# 代码地图 (Top {file_count} 文件)\n"
        if enable_lsp:
            header += "# (LSP增强: 包含类型签名和引用计数)\n"
        return header + "\n".join(lines)
    
    async def _enhance_with_lsp(
        self,
        ranked: List[Tuple[str, float]],
        definitions: Dict[str, List[Dict]],
        repo_path: Path,
        top_k: int = 50
    ) -> None:
        """
        使用LSP增强定义信息
        
        真正的增强：
        1. 使用hover获取类型签名
        2. 使用references获取引用计数（如果LSP支持）
        3. 为符号添加完整的LSP信息
        """
        from .lsp_tools import with_lsp_client, get_lsp_manager
        
        try:
            manager = get_lsp_manager()
            
            # 按文件分组
            files_to_enhance: Dict[str, List[Dict]] = {}
            count = 0
            
            for file_path, score in ranked:
                if count >= top_k:
                    break
                
                if file_path not in definitions:
                    continue
                
                file_defs = [d for d in definitions[file_path] if d.get("kind") == "def"]
                
                if file_defs:
                    files_to_enhance[file_path] = file_defs
                    count += len(file_defs)
                    if count >= top_k:
                        excess = count - top_k
                        files_to_enhance[file_path] = file_defs[:-excess] if excess > 0 else file_defs
                        break
            
            logger.info(f"🔥 LSP增强: 处理{len(files_to_enhance)}个文件，获取类型信息和引用计数...")
            
            enhanced_count = 0
            skipped_count = 0
            
            for file_path, file_defs in files_to_enhance.items():
                try:
                    abs_file_path = repo_path / file_path
                    
                    if not abs_file_path.exists():
                        skipped_count += len(file_defs)
                        continue
                    
                    # 检查LSP支持
                    ext = abs_file_path.suffix
                    server_config = manager.find_server_for_extension(ext)
                    if not server_config or not manager.is_server_installed(server_config):
                        skipped_count += len(file_defs)
                        continue
                    
                    # 获取LSP符号
                    symbols = await with_lsp_client(
                        str(abs_file_path),
                        lambda client: client.document_symbols(str(abs_file_path))
                    )
                    
                    if not symbols:
                        logger.debug(f"  {file_path}: 未获取到符号")
                        skipped_count += len(file_defs)
                        continue
                    
                    logger.debug(f"  {file_path}: 获取到{len(symbols)}个符号，处理{len(file_defs)}个定义")
                    
                    # 为每个定义获取LSP信息
                    for defn in file_defs:
                        target_line = defn['line'] - 1
                        target_name = defn['name']
                        
                        # 匹配符号
                        matching_symbol = None
                        for sym in symbols:
                            if 'range' in sym:
                                sym_line = sym['range']['start']['line']
                                sym_name = sym.get('name', '')
                                if abs(sym_line - target_line) <= 2 and sym_name == target_name:
                                    matching_symbol = sym
                                    break
                        
                        if not matching_symbol:
                            for sym in symbols:
                                if 'range' in sym:
                                    sym_line = sym['range']['start']['line']
                                    sym_name = sym.get('name', '')
                                    if abs(sym_line - target_line) <= 10 and sym_name == target_name:
                                        matching_symbol = sym
                                        break
                        
                        if matching_symbol:
                            line = matching_symbol['range']['start']['line']
                            char = matching_symbol['range']['start']['character']
                            
                            # 转换为1-based行号
                            line_1based = line + 1
                            
                            # 🔥 关键：使用selectionRange（符号名称的位置）而不是range（整个定义的位置）
                            if 'selectionRange' in matching_symbol:
                                sel_line = matching_symbol['selectionRange']['start']['line']
                                sel_char = matching_symbol['selectionRange']['start']['character']
                                line_1based = sel_line + 1
                                char = sel_char
                            
                            has_info = False
                            
                            # 1. 获取hover信息（类型签名）
                            try:
                                hover_info = await with_lsp_client(
                                    str(abs_file_path),
                                    lambda client: client.hover(str(abs_file_path), line_1based, char)
                                )
                                
                                if hover_info and 'contents' in hover_info:
                                    signature = self._extract_signature(hover_info['contents'])
                                    if signature:
                                        defn['lsp_signature'] = signature
                                        has_info = True
                                        logger.debug(f"    ✓ {target_name}: {signature}")
                            except Exception as e:
                                logger.debug(f"    hover失败 {target_name}: {e}")
                            
                            # 2. 获取引用计数
                            try:
                                references = await with_lsp_client(
                                    str(abs_file_path),
                                    lambda client: client.references(
                                        str(abs_file_path), line_1based, char,
                                        include_declaration=False
                                    )
                                )
                                
                                if references and len(references) > 0:
                                    defn['lsp_ref_count'] = len(references)
                                    has_info = True
                                    logger.debug(f"    ✓ {target_name}: {len(references)}次引用")
                            except Exception as e:
                                logger.debug(f"    references失败 {target_name}: {e}")
                            
                            # 标记为已验证
                            defn['lsp_verified'] = True
                            if has_info:
                                enhanced_count += 1
                            else:
                                skipped_count += 1
                        else:
                            skipped_count += 1
                
                except Exception as e:
                    logger.debug(f"处理文件失败 {file_path}: {e}")
                    skipped_count += len(file_defs)
                    continue
            
            logger.info(f"✅ LSP增强完成: {enhanced_count}个符号增强, {skipped_count}个跳过")
        
        except Exception as e:
            logger.warning(f"LSP增强失败: {e}")
    
    def _extract_signature(self, contents) -> Optional[str]:
        """从hover contents中提取签名"""
        try:
            # contents可能是字符串、MarkupContent或列表
            if isinstance(contents, dict) and 'value' in contents:
                text = contents['value']
            elif isinstance(contents, str):
                text = contents
            elif isinstance(contents, list) and len(contents) > 0:
                first = contents[0]
                if isinstance(first, dict) and 'value' in first:
                    text = first['value']
                elif isinstance(first, str):
                    text = first
                else:
                    return None
            else:
                return None
            
            # 清理markdown
            text = text.strip()
            if text.startswith('```'):
                lines = text.split('\n')
                if len(lines) > 2:
                    text = '\n'.join(lines[1:-1]).strip()
            
            # 只保留第一行（函数签名）
            signature = text.split('\n')[0].strip()
            
            # 限制长度
            if len(signature) > 100:
                signature = signature[:97] + '...'
            
            return signature if signature else None
        
        except Exception:
            return None


class GetRepoStructureTool(BaseTool):
    """
    获取仓库结构（简化版RepoMap）
    
    只返回文件树，不做智能排序
    支持智能注释，帮助理解目录含义
    """
    
    # 目录结构也需要限制
    MAX_OUTPUT_LINES = 500
    MAX_OUTPUT_CHARS = 8000
    
    # 智能注释映射
    DIRECTORY_ANNOTATIONS = {
        'backend': '后端代码',
        'frontend': '前端代码',
        'src': '源代码',
        'lib': '库文件',
        'tests': '测试代码',
        'test': '测试代码',
        'docs': '文档',
        'doc': '文档',
        'scripts': '脚本工具',
        'script': '脚本工具',
        'config': '配置文件',
        'conf': '配置文件',
        'agents': 'Agent系统',
        'agent': 'Agent系统',
        'tools': '工具模块',
        'tool': '工具模块',
        'memory': '记忆系统',
        'orchestrators': '编排器',
        'orchestrator': '编排器',
        'llm': 'LLM客户端',
        'cli': '命令行界面',
        'api': 'API接口',
        'models': '数据模型',
        'model': '数据模型',
        'utils': '工具函数',
        'util': '工具函数',
        'core': '核心组件',
        'common': '公共模块',
        'shared': '共享模块',
        'components': '组件',
        'component': '组件',
        'services': '服务',
        'service': '服务',
        'controllers': '控制器',
        'controller': '控制器',
        'views': '视图',
        'view': '视图',
        'templates': '模板',
        'template': '模板',
        'static': '静态资源',
        'assets': '资源文件',
        'public': '公开资源',
        'private': '私有模块',
        'internal': '内部模块',
        'external': '外部模块',
        'vendor': '第三方库',
        'node_modules': '依赖包',
        'dist': '构建产物',
        'build': '构建产物',
        'out': '输出目录',
        'bin': '可执行文件',
        'pkg': '包文件',
        'examples': '示例代码',
        'example': '示例代码',
        'demo': '演示代码',
        'plugins': '插件',
        'plugin': '插件',
        'extensions': '扩展',
        'extension': '扩展',
        'middleware': '中间件',
        'handlers': '处理器',
        'handler': '处理器',
        'routes': '路由',
        'route': '路由',
        'database': '数据库',
        'db': '数据库',
        'migrations': '数据迁移',
        'migration': '数据迁移',
        'seeds': '数据种子',
        'seed': '数据种子',
        'fixtures': '测试数据',
        'fixture': '测试数据',
    }
    
    def __init__(self):
        super().__init__(
            name="get_repo_structure",
            description="获取仓库目录结构，支持智能注释"
        )
    
    def get_function_schema(self) -> Dict[str, Any]:
        """获取Function Calling schema"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "repo_path": {
                        "type": "string",
                        "description": "仓库根目录路径。必须使用 '.' 表示当前工作目录，不要使用占位符路径！"
                    },
                    "max_depth": {
                        "type": "integer",
                        "description": "最大深度",
                        "default": 3
                    },
                    "show_files": {
                        "type": "boolean",
                        "description": "是否显示文件（否则只显示目录）",
                        "default": True
                    },
                    "annotate": {
                        "type": "boolean",
                        "description": "是否添加智能注释（帮助理解目录含义）",
                        "default": True
                    }
                },
                "required": ["repo_path"]
            }
        }
    
    async def execute(
        self,
        repo_path: str,
        max_depth: int = 3,
        show_files: bool = True,
        annotate: bool = True
    ) -> ToolResult:
        """
        获取仓库结构
        
        Args:
            repo_path: 仓库根目录
            max_depth: 最大深度
            show_files: 是否显示文件
            annotate: 是否添加智能注释
            
        Returns:
            ToolResult
        """
        try:
            repo_path = Path(repo_path).resolve()
            if not repo_path.exists():
                return ToolResult(
                    success=False,
                    content=None,
                    error=f"仓库路径不存在: {repo_path}"
                )
            
            lines = [f"{repo_path.name}/"]
            self._build_tree(repo_path, lines, "", max_depth, show_files, annotate)
            
            return ToolResult(
                success=True,
                content="\n".join(lines),
                metadata={
                    'repo_path': str(repo_path),
                    'max_depth': max_depth,
                    'show_files': show_files,
                    'annotate': annotate
                }
            )
            
        except Exception as e:
            logger.error(f"获取仓库结构失败: {e}", exc_info=True)
            return ToolResult(
                success=False,
                content=None,
                error=str(e)
            )
    
    def _build_tree(
        self,
        path: Path,
        lines: List[str],
        prefix: str,
        max_depth: int,
        show_files: bool,
        annotate: bool,
        current_depth: int = 0
    ):
        """递归构建树"""
        if current_depth >= max_depth:
            return
        
        # 忽略的目录
        ignore = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}
        
        try:
            items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
        except PermissionError:
            return
        
        for i, item in enumerate(items):
            if item.name in ignore:
                continue
            
            is_last = i == len(items) - 1
            current_prefix = "└── " if is_last else "├── "
            next_prefix = prefix + ("    " if is_last else "│   ")
            
            if item.is_dir():
                # 添加注释
                dir_display = f"{item.name}/"
                if annotate:
                    annotation = self._get_annotation(item.name)
                    if annotation:
                        dir_display = f"{item.name}/  # {annotation}"
                
                lines.append(f"{prefix}{current_prefix}{dir_display}")
                self._build_tree(item, lines, next_prefix, max_depth, show_files, annotate, current_depth + 1)
            elif show_files:
                lines.append(f"{prefix}{current_prefix}{item.name}")
    
    def _get_annotation(self, dir_name: str) -> Optional[str]:
        """获取目录注释"""
        dir_lower = dir_name.lower()
        
        # 精确匹配
        if dir_lower in self.DIRECTORY_ANNOTATIONS:
            return self.DIRECTORY_ANNOTATIONS[dir_lower]
        
        # 部分匹配
        for pattern, annotation in self.DIRECTORY_ANNOTATIONS.items():
            if pattern in dir_lower:
                return annotation
        
        return None


class GetFileSymbolsTool(BaseTool):
    """
    获取单文件符号表（类/函数/方法等，AST 深度）
    
    与 repo_map 互补：已知文件时可直接取该文件的定义列表，便于精确理解代码结构。
    使用与 RepoMap 相同的 Tree-sitter 解析。
    """

    def __init__(self):
        super().__init__(
            name="get_file_symbols",
            description="获取指定文件中的符号定义（类、函数、方法等）及行号，基于 AST 解析。"
        )

    async def execute(self, file_path: str) -> ToolResult:
        try:
            path = self.resolve_path(file_path)
            if not path.exists() or not path.is_file():
                return ToolResult(
                    success=False,
                    content=None,
                    error=f"文件不存在或不是文件: {file_path}"
                )
            # 复用 RepoMapTool 的解析逻辑
            repomap = RepoMapTool()
            repomap._context = self.context
            defs = repomap._parse_file(path)
            defs = [d for d in defs if d.get("kind") == "def"]
            if not defs:
                return ToolResult(
                    success=True,
                    content="该文件中未解析到符号定义（或语言/解析器不支持）",
                    metadata={"file_path": str(path), "count": 0}
                )
            lines = [f"  {d.get('type', '?')} {d['name']} (line {d['line']})" for d in defs]
            text = f"# {path.name}\n" + "\n".join(lines)
            return ToolResult(
                success=True,
                content=text,
                metadata={"file_path": str(path), "count": len(defs)}
            )
        except Exception as e:
            logger.exception("get_file_symbols 失败")
            return ToolResult(success=False, content=None, error=str(e))

    def get_function_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "相对项目根的文件路径"
                    }
                },
                "required": ["file_path"]
            }
        }
