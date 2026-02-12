"""测试工具注册"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from daoyoucode.agents.tools import get_tool_registry

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

# 检查repo_map
print(f"\n检查repo_map工具:")
tool = tool_registry.get_tool("repo_map")
if tool:
    print(f"  ✓ repo_map已注册")
    schema = tool.get_function_schema()
    print(f"  • 描述: {schema['description']}")
else:
    print(f"  ✗ repo_map未找到")

print("\n" + "="*60)
