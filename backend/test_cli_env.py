"""测试CLI环境下的工具注册"""
import sys
from pathlib import Path

# 模拟CLI的路径设置
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

print("="*60)
print("测试CLI环境下的工具注册")
print("="*60)

print(f"\n当前工作目录: {Path.cwd()}")
print(f"backend路径: {backend_path}")
print(f"sys.path[0]: {sys.path[0]}")

# 导入工具注册表
print("\n导入工具注册表...")
from daoyoucode.agents.tools import get_tool_registry

tool_registry = get_tool_registry()
tools = tool_registry.list_tools()

print(f"\n✓ 工具数量: {len(tools)}")
print(f"✓ repo_map存在: {'repo_map' in tools}")

if 'repo_map' not in tools:
    print("\n❌ repo_map未找到！")
    print(f"可用工具: {', '.join(sorted(tools))}")
else:
    print("\n✓ repo_map已注册")
    tool = tool_registry.get_tool("repo_map")
    print(f"  名称: {tool.name}")
    print(f"  描述: {tool.description}")

print("\n" + "="*60)
