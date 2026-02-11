"""
Agents核心模块

包含Agent的基础设施：
- BaseAgent: Agent基类
- AgentConfig: Agent配置
- AgentResult: 执行结果
- AgentRegistry: Agent注册表
- AgentLoader: Agent加载器（支持插件式加载）
"""

from .base import BaseAgent, AgentConfig, AgentResult
from .registry import AgentRegistry, get_agent_registry
from .loader import AgentLoader, get_agent_loader

__all__ = [
    'BaseAgent',
    'AgentConfig',
    'AgentResult',
    'AgentRegistry',
    'get_agent_registry',
    'AgentLoader',
    'get_agent_loader',
]
