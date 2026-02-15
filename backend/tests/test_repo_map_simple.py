"""
简单测试repo_map工具
"""

import sys
from pathlib import Path
import asyncio

sys.path.insert(0, str(Path(__file__).parent))

async def test_repo_map():
    """测试repo_map工具"""
    print("\n" + "="*60)
    print("测试repo_map工具")
    print("="*60)
    
    from daoyoucode.agents.tools import get_tool_registry
    
    registry = get_tool_registry()
    
    # 测试repo_map
    print("\n1. 测试repo_map...")
    result = await registry.execute_tool(
        'repo_map',
        repo_path='.',  # 当前目录就是backend
        chat_files=[],
        mentioned_idents=[],
        max_tokens=1000
    )
    
    if result.success:
        print("   ✓ 执行成功")
        print(f"\n   结果预览（前500字符）:")
        print("   " + "-"*56)
        content = result.content[:500]
        for line in content.split('\n'):
            print(f"   {line}")
        print("   " + "-"*56)
        print(f"\n   元数据: {result.metadata}")
    else:
        print(f"   ✗ 执行失败: {result.error}")
        return False
    
    # 测试get_repo_structure
    print("\n2. 测试get_repo_structure...")
    result = await registry.execute_tool(
        'get_repo_structure',
        repo_path='.',  # 当前目录就是backend
        max_depth=2,
        show_files=True
    )
    
    if result.success:
        print("   ✓ 执行成功")
        print(f"\n   结果预览（前500字符）:")
        print("   " + "-"*56)
        content = result.content[:500]
        for line in content.split('\n'):
            print(f"   {line}")
        print("   " + "-"*56)
    else:
        print(f"   ✗ 执行失败: {result.error}")
        return False
    
    print("\n" + "="*60)
    print("✓ 测试通过")
    print("="*60)
    return True

if __name__ == '__main__':
    success = asyncio.run(test_repo_map())
    sys.exit(0 if success else 1)
