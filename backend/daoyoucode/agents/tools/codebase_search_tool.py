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
                    },
                    "enable_lsp": {
                        "type": "boolean",
                        "description": "是否启用LSP增强（默认 True，提供类型信息、引用计数、代码质量评估）",
                        "default": True
                    }
                },
                "required": ["query"]
            }
        }

    async def execute(
        self,
        query: str,
        top_k: int = 8,
        repo_path: str = ".",
        enable_lsp: bool = True  # 🔥 默认启用LSP增强
    ) -> ToolResult:
        try:
            path = self.resolve_path(repo_path)
            if not path.exists() or not path.is_dir():
                return ToolResult(success=False, content=None, error=f"目录不存在: {repo_path}")

            # 🔥 默认使用LSP增强检索
            if enable_lsp:
                try:
                    from ..memory.codebase_index_lsp_enhanced import search_codebase_with_lsp
                    results = await search_codebase_with_lsp(
                        path,
                        query,
                        top_k=top_k,
                        enable_lsp=True
                    )
                    
                    # 检查LSP是否真正工作
                    has_lsp_info = any(r.get('has_lsp_info') for r in results)
                    
                    if not has_lsp_info:
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.warning("⚠️  LSP信息未获取，可能需要安装LSP服务器")
                        logger.warning("   Python: pip install pyright")
                    
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"❌ LSP增强失败: {e}")
                    # 只在异常时降级
                    from ..memory.codebase_index import search_codebase
                    results = search_codebase(path, query, top_k=top_k, strategy="hybrid")
            else:
                # 明确禁用时才使用普通检索
                from ..memory.codebase_index import search_codebase
                results = search_codebase(path, query, top_k=top_k, strategy="hybrid")

            if not results:
                return ToolResult(
                    success=True,
                    content="未找到相关代码块。可尝试更具体的关键词或先运行 repo_map 了解项目。",
                    metadata={"count": 0}
                )

            # 🔥 增强输出格式（包含LSP信息）
            lines = []
            for i, r in enumerate(results, 1):
                path_rel = r.get("path", "")
                start = r.get("start", 0)
                end = r.get("end", 0)
                text = (r.get("text") or "")[:1200]
                
                # 基础信息
                lines.append(f"[{i}] {path_rel} (L{start}-{end})")
                
                # 🔥 LSP增强信息
                if r.get('has_lsp_info'):
                    # 质量指标
                    symbol_count = r.get('symbol_count', 0)
                    if symbol_count > 0:
                        stars = "⭐" * min(5, symbol_count)
                        lines.append(f"质量: {stars}")
                    
                    # 类型注解
                    if r.get('has_type_annotations'):
                        lines.append("✅ 有类型注解")
                    
                    # 引用计数
                    ref_count = r.get('reference_count', 0)
                    if ref_count > 10:
                        lines.append(f"🔥 热点代码 (被引用{ref_count}次)")
                    
                    # LSP符号信息
                    symbols = r.get('lsp_symbols', [])
                    if symbols:
                        lines.append("\n📝 符号信息:")
                        for sym in symbols[:3]:  # 最多显示3个
                            name = sym.get('name', 'N/A')
                            detail = sym.get('detail', '')
                            if detail:
                                lines.append(f"  - {name}: {detail}")
                            else:
                                lines.append(f"  - {name}")
                else:
                    # 🔥 调试：显示为什么没有LSP信息
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.debug(f"结果{i}没有LSP信息: has_lsp_info={r.get('has_lsp_info')}")
                
                # 分数
                score = r.get('lsp_enhanced_score', r.get('hybrid_score', r.get('score', 0)))
                lines.append(f"分数: {score:.3f}")
                
                # 代码
                lines.append(f"\n```\n{text}\n```")
            
            content = "\n\n".join(lines)
            if len(content) > self.MAX_OUTPUT_CHARS:
                content = content[: self.MAX_OUTPUT_CHARS] + "\n…(已截断)"
            
            return ToolResult(
                success=True,
                content=content,
                metadata={
                    "count": len(results),
                    "lsp_enabled": enable_lsp,
                    "has_lsp_info": any(r.get('has_lsp_info') for r in results)
                }
            )
        except Exception as e:
            return ToolResult(success=False, content=None, error=str(e))
