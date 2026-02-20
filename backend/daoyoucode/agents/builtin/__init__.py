"""
内置Agent注册

所有内置Agent在这里注册到全局注册表
"""

from ..core.agent import register_agent
from .main_agent import MainAgent
from .translator import TranslatorAgent
from .programmer import ProgrammerAgent
from .code_analyzer import CodeAnalyzerAgent
from .code_explorer import CodeExplorerAgent
from .refactor_master import RefactorMasterAgent
from .test_expert import TestExpertAgent

# 新增：高级Agent
from .sisyphus import SisyphusAgent
from .oracle import OracleAgent
from .librarian import LibrarianAgent


def register_builtin_agents():
    """注册所有内置Agent"""
    
    # 主Agent
    register_agent(MainAgent())
    
    # 编排Agent
    register_agent(SisyphusAgent())          # 主编排Agent
    
    # 咨询Agent
    register_agent(OracleAgent())            # 高IQ咨询Agent（只读）
    register_agent(LibrarianAgent())         # 文档搜索Agent（只读）
    
    # 基础Agent
    register_agent(TranslatorAgent())
    register_agent(ProgrammerAgent())
    
    # 编程辅助Agent
    register_agent(CodeAnalyzerAgent())      # 架构分析
    register_agent(CodeExplorerAgent())      # 代码探索
    register_agent(RefactorMasterAgent())    # 重构专家
    register_agent(TestExpertAgent())        # 测试专家


__all__ = [
    'register_builtin_agents',
    'MainAgent',
    'SisyphusAgent',
    'OracleAgent',
    'LibrarianAgent',
    'TranslatorAgent',
    'ProgrammerAgent',
    'CodeAnalyzerAgent',
    'CodeExplorerAgent',
    'RefactorMasterAgent',
    'TestExpertAgent',
]
