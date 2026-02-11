"""
内置编排器

自动注册所有内置编排器
"""

from ..core.orchestrator import register_orchestrator
from .simple import SimpleOrchestrator
from .multi_agent import MultiAgentOrchestrator
from .workflow import WorkflowOrchestrator
from .conditional import ConditionalOrchestrator
from .parallel import ParallelOrchestrator


def register_builtin_orchestrators():
    """注册所有内置编排器"""
    register_orchestrator('simple', SimpleOrchestrator)
    register_orchestrator('multi_agent', MultiAgentOrchestrator)
    register_orchestrator('workflow', WorkflowOrchestrator)
    register_orchestrator('conditional', ConditionalOrchestrator)
    register_orchestrator('parallel', ParallelOrchestrator)


# 自动注册
register_builtin_orchestrators()


__all__ = [
    'SimpleOrchestrator',
    'MultiAgentOrchestrator',
    'WorkflowOrchestrator',
    'ConditionalOrchestrator',
    'ParallelOrchestrator',
    'register_builtin_orchestrators',
]
