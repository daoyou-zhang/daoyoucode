"""
追踪工具加载过程
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import logging

# 设置详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(name)s - %(levelname)s - %(message)s'
)

print("\n" + "="*60)
print("追踪工具加载过程")
print("="*60)

# 1. 初始化Agent系统
print("\n1. 初始化Agent系统...")
from daoyoucode.agents.init import initialize_agent_system
tool_registry = initialize_agent_system()

print(f"\n工具注册表ID: {id(tool_registry)}")
print(f"工具数量: {len(tool_registry.list_tools())}")

# 2. 加载Skill
print("\n2. 加载Skill...")
from daoyoucode.agents.core.skill import get_skill_loader
skill_loader = get_skill_loader()
skill = skill_loader.get_skill("chat_assistant")

print(f"Skill名称: {skill.name}")
print(f"Skill工具: {skill.tools}")

# 3. 获取编排器
print("\n3. 获取编排器...")
from daoyoucode.agents.core.orchestrator import get_orchestrator
orchestrator = get_orchestrator(skill.orchestrator)

print(f"编排器: {orchestrator.get_name()}")

# 4. 获取Agent
print("\n4. 获取Agent...")
from daoyoucode.agents.core.agent import get_agent_registry
agent_registry = get_agent_registry()
agent = agent_registry.get_agent(skill.agent)

print(f"Agent: {agent.name}")
print(f"Agent工具注册表ID: {id(agent._tool_registry)}")
print(f"与主注册表相同: {id(agent._tool_registry) == id(tool_registry)}")

# 5. 检查Agent能否找到工具
print("\n5. 检查Agent能否找到工具...")
for tool_name in ['repo_map', 'get_repo_structure', 'read_file']:
    tool = agent._tool_registry.get_tool(tool_name)
    print(f"   {tool_name}: {'✓ 找到' if tool else '✗ 未找到'}")

print("\n" + "="*60)
print("追踪完成")
print("="*60)
