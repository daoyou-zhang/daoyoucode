"""daoyoucode - 新一代AI编程助手"""

__version__ = "0.1.0"

# 导出Agents系统
from .agents import (
    execute_skill,
    list_skills,
    get_skill_info,
    register_agent,
    register_orchestrator,
    register_middleware,
)

__all__ = [
    'execute_skill',
    'list_skills',
    'get_skill_info',
    'register_agent',
    'register_orchestrator',
    'register_middleware',
]
