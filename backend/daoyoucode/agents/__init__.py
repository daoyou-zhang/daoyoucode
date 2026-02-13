"""
Agents系统 - 统一的Agent执行框架

架构:
    Skill (配置) → Orchestrator (编排) → Agent (执行) → LLM (基础设施)

核心组件:
    - core: 核心基类和注册表
    - orchestrators: 编排器实现
    - middleware: 中间件实现
    - builtin: 内置Agent
    - llm: LLM基础设施
    - hooks: Hook系统
"""

# 导入并注册内置编排器
from . import orchestrators

# 初始化工具注册表（确保工具在系统启动时就可用）
from .tools import get_tool_registry
_tool_registry = get_tool_registry()  # 触发工具注册

from .init import initialize_agent_system
from .executor import execute_skill, list_skills, get_skill_info
from .core.agent import BaseAgent, AgentConfig, register_agent, get_agent_registry
from .core.orchestrator import BaseOrchestrator, register_orchestrator, get_orchestrator
from .core.middleware import BaseMiddleware, register_middleware, get_middleware
from .core.skill import SkillConfig, SkillLoader
from .core.hook import BaseHook, HookContext, register_hook, unregister_hook, get_hook_manager

__all__ = [
    # 初始化
    'initialize_agent_system',
    
    # 执行器
    'execute_skill',
    'list_skills',
    'get_skill_info',
    
    # Agent
    'BaseAgent',
    'AgentConfig',
    'register_agent',
    'get_agent_registry',
    
    # Orchestrator
    'BaseOrchestrator',
    'register_orchestrator',
    'get_orchestrator',
    
    # Middleware
    'BaseMiddleware',
    'register_middleware',
    'get_middleware',
    
    # Skill
    'SkillConfig',
    'SkillLoader',
    
    # Hook
    'BaseHook',
    'HookContext',
    'register_hook',
    'unregister_hook',
    'get_hook_manager',
]
