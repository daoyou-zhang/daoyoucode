"""
测试RepoMap LSP集成（只扫描backend目录）
"""

import asyncio
import sys
from pathlib import Path

backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))


async def test_repomap_lsp_backend():
    """测试RepoMap LSP集成（只扫描backend目录）"""
    print("=" * 60)
    print("测试RepoMap LSP集成（只扫描backend目录）")
    print("=" * 60)
    
    from daoyoucode.agents.tools.repomap_tools import RepoMapTool
    from daoyoucode.agents.tools.base import ToolContext
    
    # 创建工具
    tool = RepoMapTool()
    
    # 设置上下文：只扫描backend目录
    context = ToolContext(
        repo_path=backend_dir.parent,
        subtree_only=True,  # 🔥 只扫描backend及其子目录
        cwd=backend_dir  # 当前目录是backend
    )
    tool.set_context(context)
    
    # 测试：启用LSP
    print("\n测试: 启用LSP，扫描backend目录...")
    result = await tool.execute(
        repo_path=".",
        chat_files=["backend/daoyoucode/agents/executor.py"],
        max_tokens=2000,
        enable_lsp=True
    )
    
    if result.success:
        print("[OK] 成功")
        print(f"LSP启用: {result.metadata.get('lsp_enabled')}")
        print(f"文件数: {result.metadata.get('file_count')}")
        print(f"定义数: {result.metadata.get('definition_count')}")
        print("\n输出:")
        print("-" * 60)
        print(result.content[:3000])  # 只显示前3000字符
        print("-" * 60)
        
        # 检查是否有LSP信息
        has_signature = ":" in result.content and ("(class)" in result.content or "(function)" in result.content)
        has_ref_count = "次引用" in result.content
        
        print(f"\n类型签名: {'[YES]' if has_signature else '[NO]'}")
        print(f"引用计数: {'[YES]' if has_ref_count else '[NO]'}")
        
        if has_signature or has_ref_count:
            print("\n✓ LSP信息已显示")
            # 统计
            if has_signature:
                signature_count = result.content.count("(class)") + result.content.count("(function)")
                print(f"  类型签名数: {signature_count}")
            if has_ref_count:
                ref_count = result.content.count("次引用")
                print(f"  引用计数数: {ref_count}")
        else:
            print("\n✗ LSP信息未显示")
    else:
        print(f"[FAIL] {result.error}")


async def main():
    await test_repomap_lsp_backend()


if __name__ == "__main__":
    asyncio.run(main())
