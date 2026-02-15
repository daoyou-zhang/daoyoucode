"""
测试 working_directory 设置
"""

import asyncio
import os
import sys

# 添加backend到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def test_working_directory():
    """测试工作目录设置"""
    print("=" * 60)
    print("测试 Working Directory 设置")
    print("=" * 60)
    
    # 1. 初始化系统
    from daoyoucode.agents.init import initialize_agent_system
    initialize_agent_system()
    
    # 2. 获取项目根目录
    project_root = os.path.dirname(os.path.abspath(__file__))
    print(f"\n当前脚本目录: {project_root}")
    print(f"项目根目录应该是: {os.path.dirname(project_root)}")
    
    # 3. 设置工作目录
    from daoyoucode.agents.tools.registry import get_tool_registry
    registry = get_tool_registry()
    
    # 使用项目根目录（backend的上一级）
    actual_root = os.path.dirname(project_root)
    registry.set_working_directory(actual_root)
    print(f"\n设置工作目录为: {actual_root}")
    
    # 4. 测试工具
    print("\n" + "=" * 60)
    print("测试工具调用")
    print("=" * 60)
    
    # 测试 list_files
    print("\n1. 测试 list_files")
    try:
        result = await registry.execute_tool(
            "list_files",
            directory="skills/chat-assistant/prompts",
            pattern="chat_assistant*.md"
        )
        if result.success:
            print("   ✅ list_files 调用成功")
            print(f"   找到 {len(result.content)} 个文件:")
            for file in result.content:
                print(f"   - {file['name']} ({file['size']} bytes)")
                print(f"     path: {file['path']}")
        else:
            print(f"   ❌ list_files 调用失败: {result.error}")
    except Exception as e:
        print(f"   ❌ list_files 异常: {e}")
    
    # 测试 read_file
    print("\n2. 测试 read_file")
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
    
    # 5. 测试 execute_skill
    print("\n" + "=" * 60)
    print("测试 execute_skill")
    print("=" * 60)
    
    from daoyoucode.agents.executor import execute_skill
    
    context = {
        "session_id": "test-session",
        "repo": actual_root,
        "working_directory": actual_root,
        "model": "qwen-plus"
    }
    
    print(f"\nContext:")
    print(f"  repo: {context['repo']}")
    print(f"  working_directory: {context['working_directory']}")
    
    # 注意：这里不实际执行skill，只是测试context传递
    print("\n✅ Context 准备完成")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_working_directory())
