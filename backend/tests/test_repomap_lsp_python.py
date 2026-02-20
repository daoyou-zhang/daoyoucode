"""
测试RepoMap LSP集成（Python文件）
"""

import asyncio
import sys
from pathlib import Path

backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))


async def test_repomap_lsp_python():
    """测试RepoMap LSP集成（Python文件）"""
    print("=" * 60)
    print("测试RepoMap LSP集成（Python文件）")
    print("=" * 60)
    
    from daoyoucode.agents.tools.repomap_tools import RepoMapTool
    from daoyoucode.agents.tools.base import ToolContext
    
    # 创建工具
    tool = RepoMapTool()
    
    # 设置上下文
    context = ToolContext(
        repo_path=backend_dir.parent,
        subtree_only=False,
        cwd=backend_dir.parent
    )
    tool.set_context(context)
    
    # 测试：只看Python文件
    print("\n测试: 启用LSP，只看Python文件...")
    result = await tool.execute(
        repo_path=".",
        chat_files=["backend/daoyoucode/agents/executor.py"],
        max_tokens=1000,
        enable_lsp=True
    )
    
    if result.success:
        print("[OK] 成功")
        print(f"LSP启用: {result.metadata.get('lsp_enabled')}")
        print("\n输出:")
        print("-" * 60)
        print(result.content)
        print("-" * 60)
        
        # 检查是否有LSP信息
        has_signature = ": " in result.content and "->" in result.content
        has_ref_count = "被引用" in result.content
        
        print(f"\n类型签名: {'[YES]' if has_signature else '[NO]'}")
        print(f"引用计数: {'[YES]' if has_ref_count else '[NO]'}")
        
        if has_signature or has_ref_count:
            print("\n✓ LSP信息已显示")
        else:
            print("\n✗ LSP信息未显示")
    else:
        print(f"[FAIL] {result.error}")


async def main():
    await test_repomap_lsp_python()


if __name__ == "__main__":
    asyncio.run(main())
