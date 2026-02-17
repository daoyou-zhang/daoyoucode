"""
Librarian - 文档和代码搜索Agent

专注于信息检索和知识搜索
借鉴oh-my-opencode的设计

Prompt配置在 skills/librarian/prompts/librarian.md
"""

from ..core.agent import BaseAgent, AgentConfig


class LibrarianAgent(BaseAgent):
    """
    Librarian - 文档和代码搜索Agent
    
    职责：
    - 搜索项目文档
    - 搜索代码实现
    - 查找相关示例
    - 提供参考资料
    
    特点：
    - 只读权限
    - 专注于搜索和检索
    - 快速定位信息
    - 可以集成外部搜索（websearch MCP）
    
    使用场景：
    - 查找文档
    - 搜索代码示例
    - 了解最佳实践
    - 学习新技术
    
    Prompt由Skill配置文件管理
    """
    
    def __init__(self):
        config = AgentConfig(
            name="librarian",
            description="文档和代码搜索Agent，专注于信息检索",
            model="qwen-max",
            temperature=0.1,
            system_prompt=""  # Prompt由Skill配置文件管理
        )
        super().__init__(config)
