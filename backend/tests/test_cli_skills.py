"""
测试CLI skills和agent命令的输出
"""

import sys
from pathlib import Path

# 添加backend到路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from cli.commands.skills import list_all_skills, show_orchestrators
from cli.commands.agent import list_all_agents

print("=" * 80)
print("测试1: 列出所有Agent")
print("=" * 80)
list_all_agents()

print("\n" + "=" * 80)
print("测试2: 列出所有Skill")
print("=" * 80)
list_all_skills()

print("\n" + "=" * 80)
print("测试3: 显示编排器")
print("=" * 80)
show_orchestrators()
