"""
编程Agent

Prompt配置在 skills/programming/prompts/programmer.md
"""

from ..core.agent import BaseAgent, AgentConfig


class ProgrammerAgent(BaseAgent):
    """编程Agent"""
    
    def __init__(self):
        config = AgentConfig(
            name="programmer",
            description="编程专家",
            model="qwen-coder-plus",
            temperature=0.1,
            system_prompt=""  # Prompt由Skill配置文件管理
        )
        super().__init__(config)
