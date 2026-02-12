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
    """
    
    def __init__(self):
        super().__init__(
            name="repo_map",
            description="生成代码仓库地图，智能排序最相关的代码定义"
        )
        self.cache_db = None
        self.graph = None
    
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
                        "description": "仓库根目录路径"
                    },
                    "chat_files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "对话中提到的文件列表（权重×50）"
                    },
                    "mentioned_idents": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "对话中提到的标识符列表（权重×10）"
                    },
                    "max_tokens": {
                        "type": "integer",
                        "description": "最大token数量",
                        "default": 2000
                    }
                },
                "required": ["repo_path"]
            }
        }
        
    async def execute(
        self,
        repo_path: str,
        chat_files: Optional[List[str]] = None,
        mentioned_idents: Optional[List[str]] = None,
        max_tokens: int = 2000
    ) -> ToolResult:
        """
        生成RepoMap
        
        Args:
            repo_path: 仓库根目录
            chat_files: 对话中的文件（权重×50）
            mentioned_idents: 提到的标识符（权重×10）
            max_tokens: 最大token数量
            
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
            
            chat_files = chat_files or []
            mentioned_idents = mentioned_idents or []
            
            # 初始化缓存
            self._init_cache(repo_path)
            
            # 扫描仓库
            definitions = self._scan_repository(repo_path)
            
            # 构建引用图
            graph = self._build_reference_graph(definitions, repo_path)
            
            # PageRank排序
            ranked = self._pagerank(
                graph,
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
                    'repo_path': str(repo_path),
                    'file_count': len(definitions),
                    'definition_count': sum(len(defs) for defs in definitions.values())
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
            
            # 检查缓存
            rel_path = str(file_path.relative_to(repo_path))
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
        """检查是否应该忽略文件"""
        ignore_patterns = {
            ".git", "node_modules", "__pycache__", ".venv", "venv",
            "dist", "build", ".next", ".nuxt", "target"
        }
        
        for part in file_path.parts:
            if part in ignore_patterns:
                return True
        
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
                    
                    definitions.append({
                        "type": type_name,
                        "name": node.text.decode("utf-8"),
                        "line": node.start_point[0] + 1,
                        "kind": kind
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
            # （简化：检查文件名是否包含标识符）
            for ident in mentioned_idents:
                if ident.lower() in node.lower():
                    weight *= 10
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
            
            # 文件头
            file_line = f"\n{file_path}:"
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
    """
    
    def __init__(self):
        super().__init__(
            name="get_repo_structure",
            description="获取仓库目录结构"
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
                        "description": "仓库根目录路径"
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
                    }
                },
                "required": ["repo_path"]
            }
        }
    
    async def execute(
        self,
        repo_path: str,
        max_depth: int = 3,
        show_files: bool = True
    ) -> ToolResult:
        """
        获取仓库结构
        
        Args:
            repo_path: 仓库根目录
            max_depth: 最大深度
            show_files: 是否显示文件
            
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
            self._build_tree(repo_path, lines, "", max_depth, show_files)
            
            return ToolResult(
                success=True,
                content="\n".join(lines),
                metadata={
                    'repo_path': str(repo_path),
                    'max_depth': max_depth,
                    'show_files': show_files
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
                lines.append(f"{prefix}{current_prefix}{item.name}/")
                self._build_tree(item, lines, next_prefix, max_depth, show_files, current_depth + 1)
            elif show_files:
                lines.append(f"{prefix}{current_prefix}{item.name}")
