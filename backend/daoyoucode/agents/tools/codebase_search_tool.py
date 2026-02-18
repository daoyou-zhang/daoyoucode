"""
语义代码检索工具（Cursor 同级按问检索）

根据自然语言 query 检索最相关的代码块，使用代码库向量索引或关键词回退。
"""

from pathlib import Path
from typing import Dict, Any, Optional

from .base import BaseTool, ToolResult


class SemanticCodeSearchTool(BaseTool):
    """按问题语义检索相关代码块（类似 Cursor @codebase）"""

    MAX_OUTPUT_CHARS = 8000

    def __init__(self):
        super().__init__(
            name="semantic_code_search",
            description="根据自然语言描述检索最相关的代码片段（语义/关键词）。适合「和当前问题最相关的代码在哪」类问题。"
        )

    def get_function_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "用自然语言描述要找的代码（如：超时重试逻辑、LLM 调用的入口、repo_map 的 PageRank）"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "返回最多几条结果（默认 8）",
                        "default": 8
                    },
                    "repo_path": {
                        "type": "string",
                        "description": "仓库路径，使用 '.' 表示当前项目根",
                        "default": "."
                    }
                },
                "required": ["query"]
            }
        }

    async def execute(
        self,
        query: str,
        top_k: int = 8,
        repo_path: str = "."
    ) -> ToolResult:
        try:
            path = self.resolve_path(repo_path)
            if not path.exists() or not path.is_dir():
                return ToolResult(success=False, content=None, error=f"目录不存在: {repo_path}")

            from ..memory.codebase_index import search_codebase
            # 默认 hybrid：语义 + BM25 + PageRank + 多层扩展，充分利用 repomap/chunk 元数据
            results = search_codebase(path, query, top_k=top_k, strategy="hybrid")

            if not results:
                return ToolResult(
                    success=True,
                    content="未找到相关代码块。可尝试更具体的关键词或先运行 repo_map 了解项目。",
                    metadata={"count": 0}
                )

            lines = []
            for i, r in enumerate(results, 1):
                path_rel = r.get("path", "")
                start = r.get("start", 0)
                end = r.get("end", 0)
                text = (r.get("text") or "")[:1200]
                # hybrid 策略返回 hybrid_score，否则为 score
                score = r.get("hybrid_score", r.get("score", 0))
                lines.append(f"[{i}] {path_rel} (L{start}-{end}) score={score:.3f}\n```\n{text}\n```")
            content = "\n\n".join(lines)
            if len(content) > self.MAX_OUTPUT_CHARS:
                content = content[: self.MAX_OUTPUT_CHARS] + "\n…(已截断)"
            return ToolResult(
                success=True,
                content=content,
                metadata={"count": len(results)}
            )
        except Exception as e:
            return ToolResult(success=False, content=None, error=str(e))
