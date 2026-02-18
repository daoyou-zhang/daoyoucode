"""
代码库向量索引（Cursor 同级按问检索）

对仓库做 chunk → embed → 存储，支持按 query 检索 top-k 相关代码块。
依赖：sentence-transformers 可选；未安装时退化为关键词匹配。
"""

from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import logging
import json
import hashlib
import re

logger = logging.getLogger(__name__)

# 单例：按 repo 路径缓存索引
_index_cache: Dict[str, "CodebaseIndex"] = {}
# 默认 chunk 最大行数
DEFAULT_CHUNK_LINES = 55
# 索引目录名
INDEX_DIR = ".daoyoucode/codebase_index"


def _repo_key(repo_path: Path) -> str:
    try:
        abs_path = repo_path.resolve()
        return hashlib.sha256(str(abs_path).encode()).hexdigest()[:16]
    except Exception:
        return "default"


def _get_index_dir(repo_path: Path) -> Path:
    key = _repo_key(repo_path)
    base = repo_path if repo_path.is_dir() else repo_path.parent
    return base / INDEX_DIR / key


def _load_ignore_patterns(repo_path: Path) -> set:
    """读取 .cursorignore 与 .gitignore，返回用于排除的 pattern 集合（Cursor 同级）"""
    out = set()
    for name in (".cursorignore", ".gitignore"):
        f = repo_path / name
        if not f.is_file():
            continue
        try:
            for line in f.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                # 去掉尾随 /，保留为字面匹配用
                out.add(line.rstrip("/"))
        except Exception:
            pass
    return out


def _should_ignore(path: Path, repo_path: Path, extra_patterns: Optional[set] = None) -> bool:
    rel = path.relative_to(repo_path) if repo_path in path.parents or path == repo_path else path
    rel_str = str(rel).replace("\\", "/")
    parts = rel_str.split("/")
    ignore = {
        ".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build",
        ".daoyoucode", ".cursor", ".idea", ".pytest_cache", "vendor"
    }
    for p in parts:
        if p in ignore or (p.startswith(".") and len(p) > 1):
            return True
        if p.endswith(".pyc"):
            return True
    for pat in extra_patterns or set():
        if "/" in pat:
            if pat in rel_str or rel_str.startswith(pat + "/"):
                return True
        elif pat in parts:
            return True
    return False


def _chunk_file(content: str, path: Path, max_lines: int = DEFAULT_CHUNK_LINES) -> List[Dict[str, Any]]:
    """按行或 def/class 边界切分为块（Python 按 def/class，其它按行）"""
    lines = content.splitlines()
    if not lines:
        return []
    ext = path.suffix.lower()
    chunks = []
    if ext == ".py":
        # Python: 按 def/class 边界
        current_start = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if (stripped.startswith("def ") or stripped.startswith("class ")) and i > current_start:
                block = "\n".join(lines[current_start:i])
                if block.strip():
                    chunks.append({"start": current_start + 1, "end": i, "text": block})
                current_start = i
        if current_start < len(lines):
            block = "\n".join(lines[current_start:])
            if block.strip():
                chunks.append({"start": current_start + 1, "end": len(lines), "text": block})
    else:
        for start in range(0, len(lines), max_lines):
            end = min(start + max_lines, len(lines))
            block = "\n".join(lines[start:end])
            if block.strip():
                chunks.append({"start": start + 1, "end": end, "text": block})
    return chunks


class CodebaseIndex:
    """代码库向量索引：chunk + embed + 检索"""

    def __init__(self, repo_path: Path):
        self.repo_path = Path(repo_path).resolve()
        if not self.repo_path.is_dir():
            self.repo_path = self.repo_path.parent
        self.index_dir = _get_index_dir(self.repo_path)
        self.chunks: List[Dict[str, Any]] = []  # [{path, start, end, text}, ...]
        self.embeddings: Optional[Any] = None   # np.ndarray (n, dim) or None
        self._retriever = None

    def _get_retriever(self):
        if self._retriever is None:
            from .vector_retriever_factory import get_retriever_singleton
            r = get_retriever_singleton()
            if hasattr(r, 'enable'):
                r.enable()
            self._retriever = r
        return self._retriever

    def build_index(
        self,
        max_file_size: int = 200_000,
        extensions: Optional[Tuple[str, ...]] = None,
        force: bool = False
    ) -> int:
        """
        扫描仓库、分块、编码并持久化。返回 chunk 数量。
        
        🆕 优化：复用RepoMap的tree-sitter解析结果，避免重复解析
        """
        if extensions is None:
            extensions = (".py", ".js", ".ts", ".tsx", ".jsx", ".md", ".yaml", ".yml", ".json")
        self.index_dir.mkdir(parents=True, exist_ok=True)
        meta_file = self.index_dir / "meta.json"
        npy_file = self.index_dir / "embeddings.npy"

        if not force and meta_file.exists():
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.chunks = data.get("chunks", [])
                if npy_file.exists():
                    import numpy as np
                    self.embeddings = np.load(npy_file)
                logger.info(f"已加载代码库索引: {len(self.chunks)} 块")
                return len(self.chunks)
            except Exception as e:
                logger.warning(f"加载索引失败，重建: {e}")

        # 🆕 使用RepoMap的tree-sitter解析结果
        try:
            from ..tools.repomap_tools import RepoMapTool
            repomap_tool = RepoMapTool()
            
            # 获取代码定义（已包含end_line）
            logger.info("🔍 使用RepoMap解析代码结构...")
            definitions = repomap_tool.get_definitions(str(self.repo_path))
            
            # 获取引用图（用于PageRank）
            reference_graph = repomap_tool.get_reference_graph(str(self.repo_path), definitions)
            
            # 获取PageRank分数
            pagerank_scores = repomap_tool.get_pagerank_scores(
                str(self.repo_path),
                reference_graph=reference_graph,
                definitions=definitions
            )
            
            logger.info(f"✅ RepoMap解析完成: {len(definitions)} 文件, {sum(len(defs) for defs in definitions.values())} 定义")
            
            # 🆕 阶段2：预先提取所有文件的导入关系
            logger.info("📦 提取导入关系...")
            file_imports = {}
            for file_path in definitions.keys():
                full_path = self.repo_path / file_path
                if full_path.exists():
                    file_imports[file_path] = self._extract_imports(full_path)
            
            # 基于definitions构建高质量的chunks
            self.chunks = []
            for file_path, defs in definitions.items():
                # 只处理定义，不处理引用
                def_only = [d for d in defs if d.get("kind") == "def"]
                
                for d in def_only:
                    # 提取代码文本
                    code_text = self._extract_code_chunk(
                        self.repo_path / file_path,
                        d["line"],
                        d.get("end_line", d["line"] + 50)
                    )
                    
                    if not code_text.strip():
                        continue
                    
                    # 🆕 阶段2：提取函数调用
                    calls = self._extract_calls(code_text)
                    
                    # 🆕 阶段2：找到调用者
                    called_by = self._find_callers(d["name"], file_path, definitions)
                    
                    # 🆕 阶段2：获取相关文件
                    related_files = self._get_related_files(file_path, reference_graph)
                    
                    # 构建增强的chunk
                    chunk = {
                        "path": file_path,
                        "start": d["line"],
                        "end": d.get("end_line", d["line"] + len(code_text.splitlines())),
                        "text": code_text[:4000],  # 限制长度
                        
                        # 基础元数据（阶段1）
                        "type": d.get("type", "unknown"),
                        "name": d.get("name", ""),
                        "pagerank_score": pagerank_scores.get(file_path, 0.0),
                        
                        # 🆕 阶段2新增字段
                        "parent_class": d.get("parent"),
                        "scope": d.get("scope", "global"),
                        "calls": calls,
                        "called_by": called_by,
                        "imports": file_imports.get(file_path, []),
                        "related_files": related_files
                    }
                    
                    self.chunks.append(chunk)
            
            logger.info(f"✅ 构建了 {len(self.chunks)} 个高质量代码块（基于AST + 引用关系）")
            
        except Exception as e:
            logger.warning(f"RepoMap解析失败，回退到传统方法: {e}")
            # 回退到原有的扫描逻辑
            self.chunks = []
            extra_ignore = _load_ignore_patterns(self.repo_path)
            for path in self.repo_path.rglob("*"):
                if not path.is_file():
                    continue
                if _should_ignore(path, self.repo_path, extra_ignore):
                    continue
                if path.suffix.lower() not in extensions:
                    continue
                try:
                    content = path.read_text(encoding="utf-8", errors="ignore")
                except Exception as e:
                    logger.debug(f"跳过 {path}: {e}")
                    continue
                if len(content) > max_file_size:
                    continue
                rel_path = path.relative_to(self.repo_path)
                rel_str = str(rel_path).replace("\\", "/")
                for c in _chunk_file(content, path):
                    self.chunks.append({
                        "path": rel_str,
                        "start": c["start"],
                        "end": c["end"],
                        "text": c["text"][:4000]
                    })

        if not self.chunks:
            logger.warning("代码库索引无 chunk")
            self._save_meta()
            return 0

        retriever = self._get_retriever()
        if not getattr(retriever, "enabled", False) or not retriever.model:
            logger.warning("embedding 未启用，仅保存 chunk 元数据，检索将使用关键词回退")
            self._save_meta()
            return len(self.chunks)

        import numpy as np
        dim = getattr(retriever.model, "get_sentence_embedding_dimension", lambda: 384)()
        vecs = []
        for c in self.chunks:
            text = c.get("text", "")[:2000]
            emb = retriever.encode(text)
            if emb is not None:
                vecs.append(emb)
            else:
                vecs.append(np.zeros(dim, dtype=np.float32))
        self.embeddings = np.array(vecs, dtype=np.float32)
        self._save_meta()
        np.save(npy_file, self.embeddings)
        logger.info(f"代码库索引已构建: {len(self.chunks)} 块, 向量维度 {self.embeddings.shape[1]}")
        return len(self.chunks)

    def _save_meta(self):
        self.index_dir.mkdir(parents=True, exist_ok=True)
        meta_file = self.index_dir / "meta.json"
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump({"chunks": self.chunks, "repo": str(self.repo_path)}, f, ensure_ascii=False, indent=0)
    
    def _extract_code_chunk(
        self,
        file_path: Path,
        start_line: int,
        end_line: int
    ) -> str:
        """
        提取代码块（精确边界）
        
        策略：
        1. 使用start_line和end_line提取代码
        2. 向上扩展：包含装饰器和注释
        3. 保持缩进一致性
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            if not lines:
                return ""
            
            # 转为0-based索引
            start_idx = max(0, start_line - 1)
            end_idx = min(len(lines), end_line)
            
            # 🔑 向上扩展：包含装饰器和注释
            while start_idx > 0:
                prev_line = lines[start_idx - 1].strip()
                if prev_line.startswith('@') or prev_line.startswith('#'):
                    start_idx -= 1
                else:
                    break
            
            # 提取代码
            code_lines = lines[start_idx:end_idx]
            code_text = ''.join(code_lines)
            
            return code_text
        
        except Exception as e:
            logger.debug(f"提取代码块失败 {file_path}:{start_line}-{end_line}: {e}")
            return ""
    
    def _extract_calls(self, code_text: str, language: str = "python") -> List[str]:
        """
        从代码中提取函数调用（🆕 阶段2）
        
        策略：
        1. Python: 正则匹配 identifier(
        2. 过滤常见关键字（if, for, while等）
        3. 去重
        """
        if language == "python":
            # 匹配函数调用：identifier(
            pattern = r'(\w+)\s*\('
            calls = re.findall(pattern, code_text)
            
            # 过滤Python关键字和内置函数
            keywords = {
                'if', 'for', 'while', 'def', 'class', 'return',
                'import', 'from', 'try', 'except', 'with', 'as',
                'print', 'len', 'str', 'int', 'float', 'list', 'dict',
                'set', 'tuple', 'bool', 'range', 'enumerate', 'zip',
                'open', 'super', 'isinstance', 'hasattr', 'getattr'
            }
            calls = [c for c in calls if c not in keywords]
            
            # 去重并排序
            return sorted(set(calls))[:20]  # 限制数量
        
        return []
    
    def _extract_imports(self, file_path: Path) -> List[str]:
        """
        提取文件的导入语句（🆕 阶段2）
        
        返回：
        [
            "from ..llm import get_client_manager",
            "from ..tools import get_tool_registry",
            "import json"
        ]
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            imports = []
            
            # 匹配 import xxx
            pattern1 = r'^import\s+[\w\.]+(?:\s+as\s+\w+)?'
            imports.extend(re.findall(pattern1, content, re.MULTILINE))
            
            # 匹配 from xxx import yyy
            pattern2 = r'^from\s+[\w\.]+\s+import\s+[\w\s,]+(?:\s+as\s+\w+)?'
            imports.extend(re.findall(pattern2, content, re.MULTILINE))
            
            return imports[:20]  # 限制数量
        
        except Exception as e:
            logger.debug(f"提取导入失败 {file_path}: {e}")
            return []
    
    def _get_related_files(
        self,
        file_path: str,
        reference_graph: Dict[str, Dict[str, float]],
        top_k: int = 5
    ) -> List[str]:
        """
        获取相关文件（基于引用图）（🆕 阶段2）
        
        策略：
        1. 从引用图中获取直接引用的文件
        2. 按引用次数排序
        3. 返回top_k个
        """
        if file_path not in reference_graph:
            return []
        
        # 获取引用关系 {file: count}
        refs = reference_graph[file_path]
        
        # 按引用次数排序
        sorted_refs = sorted(
            refs.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # 返回文件路径
        return [file for file, _ in sorted_refs[:top_k]]
    
    def _find_callers(
        self,
        function_name: str,
        file_path: str,
        all_definitions: Dict[str, List[Dict]]
    ) -> List[str]:
        """
        找到调用这个函数的文件（🆕 阶段2）
        
        策略：
        1. 遍历所有definitions
        2. 找到kind="ref"且name匹配的引用
        3. 返回引用所在的文件
        """
        callers = []
        
        for other_file, defs in all_definitions.items():
            if other_file == file_path:
                continue  # 跳过自己
            
            for d in defs:
                if d.get("kind") == "ref" and d.get("name") == function_name:
                    if other_file not in callers:
                        callers.append(other_file)
                        break  # 每个文件只记录一次
        
        return callers[:10]  # 限制数量

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """按 query 检索最相关的代码块。无向量时退化为关键词匹配。"""
        if not self.chunks:
            self.build_index()
        if not self.chunks:
            return []

        retriever = self._get_retriever()
        if retriever.enabled and self.embeddings is not None:
            import numpy as np
            q = retriever.encode(query)
            if q is not None:
                q_norm = q / np.linalg.norm(q)
                emb_norm = self.embeddings / np.linalg.norm(self.embeddings, axis=1, keepdims=True)
                scores = np.dot(emb_norm, q_norm)
                top_idx = np.argsort(scores)[::-1][:top_k]
                return [
                    {**self.chunks[i], "score": float(scores[i])}
                    for i in top_idx if scores[i] > 1e-6
                ]

        # 关键词回退
        words = re.findall(r"\w+", query.lower())
        if not words:
            return self.chunks[:top_k]
        scored = []
        for c in self.chunks:
            text = (c.get("text") or "").lower()
            score = sum(1 for w in words if w in text)
            if score > 0:
                scored.append((score, c))
        scored.sort(key=lambda x: -x[0])
        return [{**c, "score": float(s)} for s, c in scored[:top_k]]
    
    # ========== 阶段3：多层次检索 ==========
    
    def search_multilayer(
        self,
        query: str,
        top_k: int = 10,
        enable_file_expansion: bool = True,
        enable_reference_expansion: bool = True,
        max_expansion: int = 50
    ) -> List[Dict[str, Any]]:
        """
        多层次检索（🆕 阶段3）
        
        Args:
            query: 查询字符串
            top_k: 返回结果数量
            enable_file_expansion: 是否启用文件关联扩展
            enable_reference_expansion: 是否启用引用关系扩展
            max_expansion: 最大扩展数量
        
        Returns:
            增强的检索结果列表
        """
        if not self.chunks:
            self.build_index()
        if not self.chunks:
            return []
        
        logger.info(f"🔍 多层次检索: {query}")
        
        # 第1层：语义检索
        results = self.search(query, top_k * 2)
        logger.info(f"   第1层（语义）: {len(results)} 个结果")
        
        if not results:
            return []
        
        # 第2层：文件关联扩展
        if enable_file_expansion:
            results = self._expand_by_files(results)
            results = results[:max_expansion]  # 限制规模
            logger.info(f"   第2层（文件关联）: {len(results)} 个结果")
        
        # 第3层：引用关系扩展
        if enable_reference_expansion:
            results = self._expand_by_references(results)
            results = results[:max_expansion]  # 限制规模
            logger.info(f"   第3层（引用关系）: {len(results)} 个结果")
        
        # 第4层：去重和重排序
        results = self._deduplicate_and_rerank(results, query)
        logger.info(f"   第4层（去重排序）: {len(results)} 个结果")
        
        # 返回top-k
        final_results = results[:top_k]
        logger.info(f"   ✅ 最终返回: {len(final_results)} 个结果")
        
        return final_results
    
    def _expand_by_files(
        self,
        results: List[Dict],
        max_per_file: int = 2
    ) -> List[Dict]:
        """
        文件关联扩展（🆕 阶段3）
        
        策略：
        1. 对每个结果，获取其related_files
        2. 从每个相关文件中选择top-2 chunks
        3. 添加到结果集
        """
        expanded = list(results)  # 保留原始结果
        seen_ids = {self._chunk_id(c) for c in results}
        
        for result in results[:5]:  # 只扩展前5个
            related_files = result.get('related_files', [])
            
            for related_file in related_files[:3]:  # 每个结果最多3个相关文件
                # 获取该文件的chunks
                file_chunks = [
                    c for c in self.chunks 
                    if c['path'] == related_file
                ]
                
                # 按PageRank排序，选择top-2
                file_chunks.sort(
                    key=lambda c: c.get('pagerank_score', 0),
                    reverse=True
                )
                
                for chunk in file_chunks[:max_per_file]:
                    chunk_id = self._chunk_id(chunk)
                    if chunk_id not in seen_ids:
                        expanded.append(chunk)
                        seen_ids.add(chunk_id)
        
        return expanded
    
    def _expand_by_references(
        self,
        results: List[Dict],
        max_callers: int = 1,
        max_callees: int = 1
    ) -> List[Dict]:
        """
        引用关系扩展（🆕 阶段3）
        
        策略：
        1. 对每个结果，获取其called_by（调用者）
        2. 对每个结果，获取其calls（被调用者）
        3. 添加到结果集
        """
        expanded = list(results)
        seen_ids = {self._chunk_id(c) for c in results}
        
        for result in results[:3]:  # 只扩展前3个
            # 扩展到调用者
            called_by = result.get('called_by', [])
            for caller_file in called_by[:max_callers]:
                caller_chunks = [
                    c for c in self.chunks
                    if c['path'] == caller_file
                ]
                
                # 选择PageRank最高的
                if caller_chunks:
                    caller_chunks.sort(
                        key=lambda c: c.get('pagerank_score', 0),
                        reverse=True
                    )
                    chunk = caller_chunks[0]
                    chunk_id = self._chunk_id(chunk)
                    if chunk_id not in seen_ids:
                        expanded.append(chunk)
                        seen_ids.add(chunk_id)
            
            # 扩展到被调用者
            calls = result.get('calls', [])
            for callee_name in calls[:max_callees]:
                # 查找该函数的定义
                callee_chunks = [
                    c for c in self.chunks
                    if c['name'] == callee_name and c['type'] in ('function', 'method')
                ]
                
                if callee_chunks:
                    # 选择PageRank最高的
                    callee_chunks.sort(
                        key=lambda c: c.get('pagerank_score', 0),
                        reverse=True
                    )
                    chunk = callee_chunks[0]
                    chunk_id = self._chunk_id(chunk)
                    if chunk_id not in seen_ids:
                        expanded.append(chunk)
                        seen_ids.add(chunk_id)
        
        return expanded
    
    def _deduplicate_and_rerank(
        self,
        results: List[Dict],
        query: str
    ) -> List[Dict]:
        """
        去重和重排序（🆕 阶段3）
        
        策略：
        1. 去重（基于path+start）
        2. 计算综合分数：
           - 语义相似度（如果有）
           - PageRank分数
           - 在结果中的位置（越早越重要）
        3. 排序并返回
        """
        # 去重
        seen_ids = set()
        unique_results = []
        
        for result in results:
            chunk_id = self._chunk_id(result)
            if chunk_id not in seen_ids:
                unique_results.append(result)
                seen_ids.add(chunk_id)
        
        # 重排序
        retriever = self._get_retriever()
        if retriever.enabled and self.embeddings is not None:
            # 重新计算语义相似度
            q = retriever.encode(query)
            if q is not None:
                import numpy as np
                for i, result in enumerate(unique_results):
                    # 找到原始embedding
                    chunk_idx = self._find_chunk_index(result)
                    if chunk_idx >= 0:
                        emb = self.embeddings[chunk_idx]
                        similarity = np.dot(emb, q) / (np.linalg.norm(emb) * np.linalg.norm(q))
                    else:
                        similarity = 0.0
                    
                    # 综合分数
                    position_score = 1.0 / (i + 1)  # 位置越早分数越高
                    pagerank_score = result.get('pagerank_score', 0.0)
                    
                    result['final_score'] = (
                        0.5 * similarity +           # 语义相似度 50%
                        0.3 * pagerank_score +       # PageRank 30%
                        0.2 * position_score         # 位置 20%
                    )
        else:
            # 没有向量，只用PageRank和位置
            for i, result in enumerate(unique_results):
                position_score = 1.0 / (i + 1)
                pagerank_score = result.get('pagerank_score', 0.0)
                
                result['final_score'] = (
                    0.7 * pagerank_score +
                    0.3 * position_score
                )
        
        # 排序
        unique_results.sort(key=lambda r: r.get('final_score', 0), reverse=True)
        
        return unique_results
    
    def _chunk_id(self, chunk: Dict) -> str:
        """生成chunk的唯一ID（🆕 阶段3）"""
        return f"{chunk['path']}:{chunk['start']}"
    
    def _find_chunk_index(self, chunk: Dict) -> int:
        """找到chunk在self.chunks中的索引（🆕 阶段3）"""
        chunk_id = self._chunk_id(chunk)
        for i, c in enumerate(self.chunks):
            if self._chunk_id(c) == chunk_id:
                return i
        return -1

    @classmethod
    def get_index(cls, repo_path: Path) -> "CodebaseIndex":
        key = _repo_key(Path(repo_path).resolve())
        if key not in _index_cache:
            _index_cache[key] = cls(repo_path)
        return _index_cache[key]


def search_codebase(repo_path: Path, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
    """便捷函数：获取或构建索引并检索。"""
    idx = CodebaseIndex.get_index(repo_path)
    return idx.search(query, top_k=top_k)
