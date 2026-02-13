"""
诊断两个工具注册表的问题
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

print("\n" + "="*60)
print("诊断两个工具注册表")
print("="*60)

# 1. 检查新的工具系统
print("\n1. 新的工具系统 (daoyoucode.agents.tools)")
from daoyoucode.agents.tools import get_tool_registry as get_new_registry
new_registry = get_new_registry()
new_tools = new_registry.list_tools()
print(f"   工具数量: {len(new_tools)}")
print(f"   工具列表: {', '.join(sorted(new_tools)[:10])}...")
print(f"   注册表ID: {id(new_registry)}")
print(f"   repo_map存在: {'repo_map' in new_tools}")
print(f"   get_repo_structure存在: {'get_repo_structure' in new_tools}")

# 2. 检查旧的工具系统
print("\n2. 旧的工具系统 (daoyoucode.tools)")
try:
    from daoyoucode.tools import get_tool_registry as get_old_registry
    old_registry = get_old_registry()
    old_tools = old_registry.list_tools()
    print(f"   工具数量: {len(old_tools)}")
    print(f"   工具列表: {', '.join(sorted(old_tools)[:10])}...")
    print(f"   注册表ID: {id(old_registry)}")
    print(f"   repo_map存在: {'repo_map' in old_tools}")
    print(f"   get_repo_structure存在: {'get_repo_structure' in old_tools}")
except Exception as e:
    print(f"   错误: {e}")

# 3. 检查是否是同一个注册表
print("\n3. 检查是否是同一个注册表")
print(f"   相同: {id(new_registry) == id(old_registry)}")

# 4. 检查Agent使用哪个
print("\n4. 检查Agent使用哪个工具注册表")
from daoyoucode.agents.core.agent import BaseAgent, AgentConfig
config = AgentConfig(
    name="TestAgent",
    description="测试",
    model="qwen-plus"
)
agent = BaseAgent(config)
print(f"   Agent工具注册表ID: {id(agent._tool_registry)}")
print(f"   与新系统相同: {id(agent._tool_registry) == id(new_registry)}")
try:
    print(f"   与旧系统相同: {id(agent._tool_registry) == id(old_registry)}")
except:
    print(f"   与旧系统相同: N/A")

print("\n" + "="*60)
print("诊断完成")
print("="*60)
