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
from .parallel_explore import ParallelExploreOrchestrator


def register_builtin_orchestrators():
    """注册所有内置编排器"""
    register_orchestrator('simple', SimpleOrchestrator)
    register_orchestrator('multi_agent', MultiAgentOrchestrator)
    register_orchestrator('workflow', WorkflowOrchestrator)
    register_orchestrator('conditional', ConditionalOrchestrator)
    register_orchestrator('parallel', ParallelOrchestrator)
    register_orchestrator('parallel_explore', ParallelExploreOrchestrator)
    
    # 向后兼容：react 指向 simple
    # 说明：ReAct循环已在Agent层通过Function Calling实现
    #      SimpleOrchestrator 包含了原 ReActOrchestrator 的所有功能（预取、重试等）
    register_orchestrator('react', SimpleOrchestrator)


# 自动注册
register_builtin_orchestrators()


__all__ = [
    'SimpleOrchestrator',
    'MultiAgentOrchestrator',
    'WorkflowOrchestrator',
    'ConditionalOrchestrator',
    'ParallelOrchestrator',
    'ParallelExploreOrchestrator',
    'register_builtin_orchestrators',
]
