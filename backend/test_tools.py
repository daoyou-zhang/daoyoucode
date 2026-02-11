"""
测试工具系统
"""

import asyncio
import sys
import os

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from daoyoucode.tools import get_tool_registry
from daoyoucode.tools.builtin import register_builtin_tools


async def test_tool_registry():
    """测试工具注册"""
    print("\n" + "="*60)
    print("测试1: 工具注册")
    print("="*60)
    
    # 注册内置工具
    register_builtin_tools()
    
    registry = get_tool_registry()
    
    # 列出所有工具
    tools = registry.list_tools()
    print(f"\n已注册工具数量: {len(tools)}")
    print(f"工具列表: {tools}")
    
    # 列出文件工具
    file_tools = registry.list_tools(category="file")
    print(f"\n文件工具: {file_tools}")
    
    assert len(tools) > 0, "应该有工具注册"
    print("\n✅ 工具注册测试通过")


async def test_function_schema():
    """测试Function Schema生成"""
    print("\n" + "="*60)
    print("测试2: Function Schema生成")
    print("="*60)
    
    registry = get_tool_registry()
    
    # 获取read_file工具的schema
    tool = registry.get_tool("read_file")
    assert tool is not None, "read_file工具应该存在"
    
    schema = tool.to_function_schema()
    print(f"\nread_file的Function Schema:")
    import json
    print(json.dumps(schema, indent=2, ensure_ascii=False))
    
    assert schema['name'] == 'read_file'
    assert 'parameters' in schema
    assert 'properties' in schema['parameters']
    
    print("\n✅ Function Schema生成测试通过")


async def test_tool_execution():
    """测试工具执行"""
    print("\n" + "="*60)
    print("测试3: 工具执行")
    print("="*60)
    
    registry = get_tool_registry()
    
    # 创建测试文件
    test_file = "test_tool_file.txt"
    test_content = "Hello, Tool System!"
    
    # 1. 写入文件
    print(f"\n1. 写入文件: {test_file}")
    result = await registry.execute_tool(
        "write_file",
        path=test_file,
        content=test_content
    )
    print(f"   结果: {result}")
    
    # 2. 读取文件
    print(f"\n2. 读取文件: {test_file}")
    content = await registry.execute_tool(
        "read_file",
        path=test_file
    )
    print(f"   内容: {content}")
    assert content == test_content, "内容应该匹配"
    
    # 3. 检查文件存在
    print(f"\n3. 检查文件存在: {test_file}")
    exists = await registry.execute_tool(
        "file_exists",
        path=test_file
    )
    print(f"   存在: {exists}")
    assert exists is True, "文件应该存在"
    
    # 4. 获取文件信息
    print(f"\n4. 获取文件信息: {test_file}")
    info = await registry.execute_tool(
        "get_file_info",
        path=test_file
    )
    print(f"   信息: {info}")
    assert info['name'] == test_file
    
    # 5. 删除文件
    print(f"\n5. 删除文件: {test_file}")
    result = await registry.execute_tool(
        "delete_file",
        path=test_file
    )
    print(f"   结果: {result}")
    
    # 6. 验证文件已删除
    exists = await registry.execute_tool(
        "file_exists",
        path=test_file
    )
    assert exists is False, "文件应该已删除"
    
    print("\n✅ 工具执行测试通过")


async def test_list_files():
    """测试列出文件"""
    print("\n" + "="*60)
    print("测试4: 列出文件")
    print("="*60)
    
    registry = get_tool_registry()
    
    # 列出当前目录的Python文件
    print("\n列出当前目录的Python文件:")
    files = await registry.execute_tool(
        "list_files",
        directory=".",
        pattern="*.py",
        recursive=False
    )
    
    print(f"找到 {len(files)} 个Python文件:")
    for f in files[:5]:  # 只显示前5个
        print(f"  - {f}")
    
    assert len(files) > 0, "应该找到Python文件"
    print("\n✅ 列出文件测试通过")


async def test_get_all_schemas():
    """测试获取所有工具的schemas"""
    print("\n" + "="*60)
    print("测试5: 获取所有Function Schemas")
    print("="*60)
    
    registry = get_tool_registry()
    
    # 获取所有工具的schemas
    schemas = registry.get_function_schemas()
    
    print(f"\n共有 {len(schemas)} 个工具的schemas")
    print("\n工具列表:")
    for schema in schemas:
        print(f"  - {schema['name']}: {schema['description']}")
    
    assert len(schemas) > 0, "应该有schemas"
    print("\n✅ 获取所有schemas测试通过")


async def main():
    """运行所有测试"""
    print("🚀 开始测试工具系统")
    
    try:
        await test_tool_registry()
        await test_function_schema()
        await test_tool_execution()
        await test_list_files()
        await test_get_all_schemas()
        
        print("\n" + "="*60)
        print("🎉 所有测试通过！")
        print("="*60)
    
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
