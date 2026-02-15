"""
测试工具名称是否正确
"""

import asyncio
from daoyoucode.agents.tools.registry import get_tool_registry


async def test_tool_names():
    """测试所有工具名称"""
    import os
    
    registry = get_tool_registry()
    
    # 设置工作目录为项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    registry.set_working_directory(project_root)
    print(f"工作目录: {project_root}\n")
    
    print("=" * 60)
    print("已注册的工具列表")
    print("=" * 60)
    
    tools = registry.list_tools()
    for i, tool_name in enumerate(tools, 1):
        print(f"{i:2d}. {tool_name}")
    
    print(f"\n总计: {len(tools)} 个工具")
    
    print("\n" + "=" * 60)
    print("验证关键工具")
    print("=" * 60)
    
    # 验证关键工具存在
    critical_tools = [
        "text_search",      # 不是 grep_search
        "list_files",       # 不是 list_directory
        "read_file",
        "write_file",
        "repo_map",
        "get_repo_structure",
        "discover_project_docs",
    ]
    
    for tool_name in critical_tools:
        exists = tool_name in tools
        status = "✅" if exists else "❌"
        print(f"{status} {tool_name}")
    
    print("\n" + "=" * 60)
    print("测试工具调用")
    print("=" * 60)
    
    # 测试 text_search
    print("\n1. 测试 text_search")
    try:
        result = await registry.execute_tool(
            "text_search",
            query="class BaseAgent",
            directory=".",
            file_pattern="**/*.py",
            max_results=5
        )
        if result.success:
            print("   ✅ text_search 调用成功")
            lines = result.content.split('\n')[:3]
            for line in lines:
                print(f"   {line}")
        else:
            print(f"   ❌ text_search 调用失败: {result.error}")
    except Exception as e:
        print(f"   ❌ text_search 异常: {e}")
    
    # 测试 list_files
    print("\n2. 测试 list_files")
    try:
        result = await registry.execute_tool(
            "list_files",
            directory="skills/chat-assistant/prompts",
            pattern="*.md",
            recursive=False
        )
        if result.success:
            print("   ✅ list_files 调用成功")
            print(f"   找到 {len(result.content)} 个文件")
            for file in result.content[:3]:
                print(f"   - {file['name']}")
        else:
            print(f"   ❌ list_files 调用失败: {result.error}")
    except Exception as e:
        print(f"   ❌ list_files 异常: {e}")
    
    # 测试 read_file
    print("\n3. 测试 read_file")
    try:
        result = await registry.execute_tool(
            "read_file",
            file_path="skills/chat-assistant/skill.yaml",
            encoding="utf-8"
        )
        if result.success:
            print("   ✅ read_file 调用成功")
            lines = result.content.split('\n')[:5]
            for line in lines:
                print(f"   {line}")
        else:
            print(f"   ❌ read_file 调用失败: {result.error}")
    except Exception as e:
        print(f"   ❌ read_file 异常: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_tool_names())
