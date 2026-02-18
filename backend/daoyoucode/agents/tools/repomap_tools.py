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
import sqlite3
import json
from collections import defaultdict, namedtuple
import warnings

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
        self.cache_db = None
        self.graph = None
        self._last_definitions = None  # 🆕 保存最后一次的definitions
    
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
        auto_scale: bool = True
    ) -> ToolResult:
        """
        生成RepoMap
        
        Args:
            repo_path: 仓库根目录
            chat_files: 对话中的文件（权重×50）
            mentioned_idents: 提到的标识符（权重×10）
            max_tokens: 最大token数量
            auto_scale: 是否自动调整token预算
            
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
            
            # 智能调整token预算（借鉴aider）
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
            
            # 初始化缓存
            self._init_cache(repo_path_resolved)
            
            # 扫描仓库
            definitions = self._scan_repository(repo_path_resolved)
            
            # 构建引用图
            graph = self._build_reference_graph(definitions, repo_path_resolved)
            
            # PageRank排序
            ranked = self._pagerank(
                graph,
                definitions,  # 传递 definitions
                chat_files=chat_files,
                mentioned_idents=mentioned_idents
            )
            
            # 生成地图（控制token）
            repo_map = self._generate_map(
                ranked,
                definitions,
                max_tokens=max_tokens
            )
            
            # 关闭数据库
            if self.cache_db:
                self.cache_db.close()
                self.cache_db = None
            
            return ToolResult(
                success=True,
                content=repo_map,
                metadata={
                    'repo_path': str(repo_path_resolved),
                    'file_count': len(definitions),
                    'definition_count': sum(len(defs) for defs in definitions.values()),
                    'max_tokens': max_tokens,
                    'original_max_tokens': original_max_tokens,
                    'auto_scaled': auto_scale and (max_tokens != original_max_tokens),
                    'chat_files_count': len(chat_files)
                }
            )
            
        except Exception as e:
            logger.error(f"生成RepoMap失败: {e}", exc_info=True)
            # 关闭数据库
            if self.cache_db:
                self.cache_db.close()
                self.cache_db = None
            return ToolResult(
                success=False,
                content=None,
                error=str(e)
            )
    
    def _init_cache(self, repo_path: Path):
        """初始化SQLite缓存"""
        cache_dir = repo_path / ".daoyoucode" / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        cache_file = cache_dir / "repomap.db"
        self.cache_db = sqlite3.connect(str(cache_file))
        
        # 创建表
        self.cache_db.execute("""
            CREATE TABLE IF NOT EXISTS definitions (
                file_path TEXT,
                mtime REAL,
                definitions TEXT,
                PRIMARY KEY (file_path)
            )
        """)
        self.cache_db.commit()
    
    def _scan_repository(self, repo_path: Path) -> Dict[str, List[Dict]]:
        """
        扫描仓库，提取定义
        
        Returns:
            {file_path: [definition, ...]}
        """
        definitions = {}
        
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
                definitions[rel_path] = cached
                continue
            
            # 解析文件
            file_defs = self._parse_file(file_path)
            definitions[rel_path] = file_defs
            
            # 缓存结果
            self._cache_definitions(rel_path, mtime, file_defs)
        
        return definitions
    
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
        """从缓存获取定义"""
        cursor = self.cache_db.execute(
            "SELECT mtime, definitions FROM definitions WHERE file_path = ?",
            (file_path,)
        )
        row = cursor.fetchone()
        
        if row is None:
            return None
        
        cached_mtime, cached_defs = row
        if cached_mtime != mtime:
            return None
        
        return json.loads(cached_defs)
    
    def _cache_definitions(self, file_path: str, mtime: float, definitions: List[Dict]):
        """缓存定义"""
        self.cache_db.execute(
            "INSERT OR REPLACE INTO definitions (file_path, mtime, definitions) VALUES (?, ?, ?)",
            (file_path, mtime, json.dumps(definitions))
        )
        self.cache_db.commit()
    
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
        max_tokens: int
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
        return header + "\n".join(lines)


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
