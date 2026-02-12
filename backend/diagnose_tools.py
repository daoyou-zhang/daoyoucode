"""诊断工具注册问题"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

print("="*60)
print("诊断工具注册")
print("="*60)

# 第1次导入
print("\n1. 第一次导入工具注册表...")
from daoyoucode.agents.tools import get_tool_registry
registry1 = get_tool_registry()
tools1 = registry1.list_tools()
print(f"   工具数量: {len(tools1)}")
print(f"   repo_map存在: {'repo_map' in tools1}")
print(f"   注册表ID: {id(registry1)}")

# 第2次导入
print("\n2. 第二次导入工具注册表...")
from daoyoucode.agents.tools import get_tool_registry as get_tool_registry2
registry2 = get_tool_registry2()
tools2 = registry2.list_tools()
print(f"   工具数量: {len(tools2)}")
print(f"   repo_map存在: {'repo_map' in tools2}")
print(f"   注册表ID: {id(registry2)}")
print(f"   是同一个实例: {registry1 is registry2}")

# 通过不同路径导入
print("\n3. 通过agents模块导入...")
import daoyoucode.agents
# agents模块在__init__.py中已经初始化了工具注册表
from daoyoucode.agents.tools import get_tool_registry as get_tool_registry3
registry3 = get_tool_registry3()
tools3 = registry3.list_tools()
print(f"   工具数量: {len(tools3)}")
print(f"   repo_map存在: {'repo_map' in tools3}")
print(f"   注册表ID: {id(registry3)}")
print(f"   是同一个实例: {registry1 is registry3}")

# 检查repo_map工具
print("\n4. 检查repo_map工具...")
tool = registry1.get_tool("repo_map")
if tool:
    print(f"   ✓ 找到repo_map工具")
    print(f"   名称: {tool.name}")
    print(f"   描述: {tool.description}")
else:
    print(f"   ✗ 未找到repo_map工具")

print("\n" + "="*60)
print("诊断完成")
print("="*60)
