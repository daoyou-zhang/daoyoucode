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
            from .vector_retriever import get_vector_retriever
            r = get_vector_retriever()
            r.enable()
            self._retriever = r
        return self._retriever

    def build_index(
        self,
        max_file_size: int = 200_000,
        extensions: Optional[Tuple[str, ...]] = None,
        force: bool = False
    ) -> int:
        """扫描仓库、分块、编码并持久化。返回 chunk 数量。"""
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
