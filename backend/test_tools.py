"""
测试工具注册
"""

import sys
from pathlib import Path

# 添加backend到路径
sys.path.insert(0, str(Path(__file__).parent))

from daoyoucode.agents.tools import get_tool_registry

def test_tools():
    print("="*60)
    print("测试工具注册")
    print("="*60)
    
    # 获取工具注册表
    tool_registry = get_tool_registry()
    
    # 列出所有工具
    tools = tool_registry.list_tools()
    print(f"\n✓ 已注册 {len(tools)} 个工具:")
    for tool in sorted(tools):
        print(f"  • {tool}")
    
    # 检查关键工具
    key_tools = [
        "repo_map",
        "get_repo_structure", 
        "read_file",
        "write_file",
        "list_files",
        "text_search",
        "regex_search"
    ]
    
    print(f"\n检查关键工具:")
    for tool_name in key_tools:
        if tool_name in tools:
            print(f"  ✓ {tool_name}")
        else:
            print(f"  ✗ {tool_name} - 未找到")
    
    # 获取repo_map的schema
    print(f"\nrepo_map工具的schema:")
    tool = tool_registry.get_tool("repo_map")
    if tool:
        schema = tool.get_function_schema()
        print(f"  • 名称: {schema['name']}")
        print(f"  • 描述: {schema['description']}")
        print(f"  • 参数: {list(schema['parameters']['properties'].keys())}")
    else:
        print("  ✗ repo_map工具未找到")
    
    return len(tools) > 0

if __name__ == "__main__":
    success = test_tools()
    print("\n" + "="*60)
    if success:
        print("✅ 工具注册测试通过")
    else:
        print("❌ 工具注册测试失败")
    print("="*60)
