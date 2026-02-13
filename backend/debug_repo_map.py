"""
调试repo_map工具
"""

import sys
from pathlib import Path
import asyncio
import logging

sys.path.insert(0, str(Path(__file__).parent))

# 设置详细日志
logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(message)s')

async def debug_repo_map():
    """调试repo_map"""
    print("\n" + "="*60)
    print("调试repo_map工具")
    print("="*60)
    
    from daoyoucode.agents.tools.repomap_tools import RepoMapTool
    
    tool = RepoMapTool()
    
    # 测试单个文件解析
    print("\n1. 测试单个文件解析...")
    test_file = Path("daoyoucode/agents/core/agent.py")
    if test_file.exists():
        definitions = tool._parse_file(test_file)
        print(f"   文件: {test_file}")
        print(f"   定义数量: {len(definitions)}")
        if definitions:
            print(f"   前5个定义:")
            for d in definitions[:5]:
                print(f"     - {d}")
        else:
            print("   ⚠ 没有找到定义")
    
    # 测试完整扫描
    print("\n2. 测试完整扫描...")
    result = await tool.execute(
        repo_path='.',
        chat_files=[],
        mentioned_idents=[],
        max_tokens=2000
    )
    
    print(f"   成功: {result.success}")
    if result.success:
        print(f"   元数据: {result.metadata}")
        print(f"\n   内容预览（前1000字符）:")
        print("   " + "-"*56)
        for line in result.content[:1000].split('\n'):
            print(f"   {line}")
        print("   " + "-"*56)
    else:
        print(f"   错误: {result.error}")
    
    print("\n" + "="*60)

if __name__ == '__main__':
    asyncio.run(debug_repo_map())
