"""
测试新增工具（搜索工具和Git工具）
"""

import asyncio
import sys
from pathlib import Path

# 添加backend到路径
sys.path.insert(0, str(Path(__file__).parent))

from daoyoucode.tools import get_tool_registry


async def test_search_tools():
    """测试搜索工具"""
    print("\n" + "="*60)
    print("测试搜索工具")
    print("="*60)
    
    registry = get_tool_registry()
    
    # 1. 测试grep_search
    print("\n1. 测试 grep_search")
    print("-" * 40)
    
    result = await registry.execute_tool(
        'grep_search',
        pattern='class.*Agent',
        directory='daoyoucode/agents',
        file_pattern='*.py',
        recursive=True,
        max_results=5
    )
    print(result)
    
    # 2. 测试find_function
    print("\n2. 测试 find_function")
    print("-" * 40)
    
    result = await registry.execute_tool(
        'find_function',
        function_name='execute',
        directory='daoyoucode/agents',
        language='python'
    )
    print(result[:500] + "..." if len(result) > 500 else result)
    
    # 3. 测试find_class
    print("\n3. 测试 find_class")
    print("-" * 40)
    
    result = await registry.execute_tool(
        'find_class',
        class_name='BaseAgent',
        directory='daoyoucode/agents',
        language='python'
    )
    print(result)


async def test_git_tools():
    """测试Git工具"""
    print("\n" + "="*60)
    print("测试Git工具")
    print("="*60)
    
    registry = get_tool_registry()
    
    # 1. 测试git_status
    print("\n1. 测试 git_status")
    print("-" * 40)
    
    try:
        result = await registry.execute_tool('git_status', directory='.')
        print(result)
    except Exception as e:
        print(f"Error: {e}")
    
    # 2. 测试git_branch
    print("\n2. 测试 git_branch")
    print("-" * 40)
    
    try:
        result = await registry.execute_tool('git_branch', directory='.')
        print(result)
    except Exception as e:
        print(f"Error: {e}")
    
    # 3. 测试git_log
    print("\n3. 测试 git_log")
    print("-" * 40)
    
    try:
        result = await registry.execute_tool(
            'git_log',
            max_count=5,
            directory='.'
        )
        print(result)
    except Exception as e:
        print(f"Error: {e}")
    
    # 4. 测试git_diff
    print("\n4. 测试 git_diff")
    print("-" * 40)
    
    try:
        result = await registry.execute_tool('git_diff', directory='.')
        print(result[:500] + "..." if len(result) > 500 else result)
    except Exception as e:
        print(f"Error: {e}")


async def test_tool_registry():
    """测试工具注册表"""
    print("\n" + "="*60)
    print("测试工具注册表")
    print("="*60)
    
    registry = get_tool_registry()
    
    # 1. 列出所有工具
    print("\n1. 所有工具")
    print("-" * 40)
    all_tools = registry.list_tools()
    print(f"总共 {len(all_tools)} 个工具:")
    for tool_name in sorted(all_tools):
        print(f"  - {tool_name}")
    
    # 2. 按分类列出
    print("\n2. 按分类列出")
    print("-" * 40)
    
    categories = ['file', 'search', 'git']
    for category in categories:
        tools = registry.list_tools(category=category)
        print(f"\n{category.upper()} 工具 ({len(tools)}个):")
        for tool_name in tools:
            tool = registry.get_tool(tool_name)
            print(f"  - {tool_name}: {tool.description}")
    
    # 3. 获取Function Schemas
    print("\n3. Function Schemas (前3个)")
    print("-" * 40)
    
    schemas = registry.get_function_schemas()
    for schema in schemas[:3]:
        print(f"\n{schema['name']}:")
        print(f"  描述: {schema['description']}")
        print(f"  参数: {list(schema['parameters']['properties'].keys())}")


async def main():
    """主函数"""
    print("\n" + "="*60)
    print("新增工具测试")
    print("="*60)
    
    # 测试工具注册表
    await test_tool_registry()
    
    # 测试搜索工具
    await test_search_tools()
    
    # 测试Git工具
    await test_git_tools()
    
    print("\n" + "="*60)
    print("所有测试完成！")
    print("="*60)


if __name__ == '__main__':
    asyncio.run(main())
