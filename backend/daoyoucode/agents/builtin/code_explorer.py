"""
代码探索Agent

借鉴oh-my-opencode的Explore智能体
Prompt配置在 skills/code-exploration/prompts/explore.md
"""

from ..core.agent import BaseAgent, AgentConfig


class CodeExplorerAgent(BaseAgent):
    """代码探索Agent"""
    
    def __init__(self):
        config = AgentConfig(
            name="code_explorer",
            description="代码库搜索专家，快速查找代码位置",
            model="qwen-coder-plus",
            temperature=0.1,
            system_prompt=""  # Prompt由Skill配置文件管理
        )
        super().__init__(config)
