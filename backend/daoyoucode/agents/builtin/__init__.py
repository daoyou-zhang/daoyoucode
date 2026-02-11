"""
内置Agents

包含所有内置的Agent实现：
- Sisyphus: 主编排器
- ChineseEditor: 中文编辑专家
- Oracle: 架构顾问
- Librarian: 文档专家
- Explore: 代码探索专家
"""

from .sisyphus import SisyphusAgent, create_sisyphus_agent
from .chinese_editor import ChineseEditorAgent, create_chinese_editor_agent
from .oracle import OracleAgent, create_oracle_agent
from .librarian import LibrarianAgent, create_librarian_agent
from .explore import ExploreAgent, create_explore_agent

__all__ = [
    'SisyphusAgent',
    'create_sisyphus_agent',
    'ChineseEditorAgent',
    'create_chinese_editor_agent',
    'OracleAgent',
    'create_oracle_agent',
    'LibrarianAgent',
    'create_librarian_agent',
    'ExploreAgent',
    'create_explore_agent',
]

