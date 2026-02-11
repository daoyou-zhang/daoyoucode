"""
Agents智能体系统

融合oh-my-opencode和daoyouCodePilot的精华：
- 多智能体协作（oh-my-opencode）
- 中文优化（daoyouCodePilot）
- 工具权限控制（oh-my-opencode）
- 任务委托和并行执行（oh-my-opencode）

目录结构：
- core/: 核心基础设施（BaseAgent, Registry等）
- builtin/: 内置Agents（Sisyphus, ChineseEditor等）
- utils/: 工具模块（监控、分析等）
"""

from .core import BaseAgent, AgentConfig, AgentResult, AgentRegistry, get_agent_registry
from .builtin import (
    SisyphusAgent,
    ChineseEditorAgent,
    OracleAgent,
    LibrarianAgent,
    ExploreAgent,
)

__all__ = [
    'BaseAgent',
    'AgentConfig',
    'AgentResult',
    'AgentRegistry',
    'get_agent_registry',
    'SisyphusAgent',
    'ChineseEditorAgent',
    'OracleAgent',
    'LibrarianAgent',
    'ExploreAgent',
]
