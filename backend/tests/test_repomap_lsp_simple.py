"""
简单测试RepoMap LSP集成
"""

import asyncio
import sys
import logging
from pathlib import Path

backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(message)s')


async def test_simple():
    """简单测试"""
    print("=" * 60)
    print("简单测试RepoMap LSP集成")
    print("=" * 60)
    
    from daoyoucode.agents.tools.repomap_tools import RepoMapTool
    
    tool = RepoMapTool()
    
    # 只测试一个文件
    print("\n测试: 启用LSP，只看executor.py...")
    result = await tool.execute(
        repo_path=".",
        chat_files=["daoyoucode/agents/executor.py"],  # 指定文件
        max_tokens=500,
        enable_lsp=True
    )
    
    if result.success:
        print("\n[OK] 成功")
        print(f"LSP启用: {result.metadata.get('lsp_enabled', False)}")
        
        print("\n输出:")
        print("-" * 60)
        print(result.content)
        print("-" * 60)
        
        # 检查LSP标记
        has_signature = ': async' in result.content or '-> ' in result.content
        has_ref_count = '被引用' in result.content
        
        print(f"\n类型签名: {'[OK]' if has_signature else '[NO]'}")
        print(f"引用计数: {'[OK]' if has_ref_count else '[NO]'}")
        
        if has_signature or has_ref_count:
            print("\n✓ RepoMap LSP集成成功！")
        else:
            print("\n✗ LSP信息未显示")
    else:
        print(f"\n[NO] 失败: {result.error}")


async def main():
    await test_simple()


if __name__ == "__main__":
    asyncio.run(main())
