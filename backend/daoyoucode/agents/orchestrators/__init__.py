"""
编排器注册

架构重构后只保留 CoreOrchestrator（通过 CoreOrchestratorAdapter 适配）
所有 Skills 现在都使用统一的 core 编排器
"""

from ..core.orchestrator import register_orchestrator
from .core_adapter import CoreOrchestratorAdapter


def register_builtin_orchestrators():
    """注册编排器 - 只注册 core"""
    register_orchestrator('core', CoreOrchestratorAdapter)


# 自动注册
register_builtin_orchestrators()


__all__ = [
    'CoreOrchestratorAdapter',
    'register_builtin_orchestrators',
]
