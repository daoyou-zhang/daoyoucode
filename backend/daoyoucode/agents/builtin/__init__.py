"""
内置Agent注册

所有内置Agent在这里注册到全局注册表
"""

from ..core.agent import register_agent
from .translator import TranslatorAgent
from .programmer import ProgrammerAgent
from .code_analyzer import CodeAnalyzerAgent
from .code_explorer import CodeExplorerAgent
from .refactor_master import RefactorMasterAgent
from .test_expert import TestExpertAgent


def register_builtin_agents():
    """注册所有内置Agent"""
    
    # 基础Agent
    register_agent(TranslatorAgent())
    register_agent(ProgrammerAgent())
    
    # 编程辅助Agent（借鉴oh-my-opencode）
    register_agent(CodeAnalyzerAgent())      # Oracle - 架构顾问
    register_agent(CodeExplorerAgent())      # Explore - 代码搜索
    register_agent(RefactorMasterAgent())    # 重构专家
    register_agent(TestExpertAgent())        # 测试专家


__all__ = [
    'register_builtin_agents',
    'TranslatorAgent',
    'ProgrammerAgent',
    'CodeAnalyzerAgent',
    'CodeExplorerAgent',
    'RefactorMasterAgent',
    'TestExpertAgent',
]
