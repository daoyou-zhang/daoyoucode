"""
测试RepoMap LSP集成（详细日志）
"""

import asyncio
import sys
import logging
from pathlib import Path

# 设置详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))


async def test_repomap_lsp_verbose():
    """测试RepoMap LSP集成（详细日志）"""
    print("=" * 60)
    print("测试RepoMap LSP集成（详细日志）")
    print("=" * 60)
    
    from daoyoucode.agents.tools.repomap_tools import RepoMapTool
    from daoyoucode.agents.tools.base import ToolContext
    
    # 创建工具
    tool = RepoMapTool()
    
    # 设置上下文：只扫描backend目录
    context = ToolContext(
        repo_path=backend_dir.parent,
        subtree_only=True,
        cwd=backend_dir
    )
    tool.set_context(context)
    
    # 测试：启用LSP，只看一个文件
    print("\n测试: 启用LSP，只看executor.py...")
    result = await tool.execute(
        repo_path=".",
        chat_files=["backend/daoyoucode/agents/executor.py"],
        max_tokens=500,
        enable_lsp=True
    )
    
    if result.success:
        print("\n[OK] 成功")
        print(f"LSP启用: {result.metadata.get('lsp_enabled')}")
        print("\n输出:")
        print("-" * 60)
        print(result.content)
        print("-" * 60)
    else:
        print(f"\n[FAIL] {result.error}")


async def main():
    await test_repomap_lsp_verbose()


if __name__ == "__main__":
    asyncio.run(main())
