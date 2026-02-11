"""
重构专家Agent

专注于代码重构，提供安全、渐进式的重构方案
Prompt配置在 skills/refactoring/prompts/refactor.md
"""

from ..core.agent import BaseAgent, AgentConfig


class RefactorMasterAgent(BaseAgent):
    """重构专家Agent"""
    
    def __init__(self):
        config = AgentConfig(
            name="refactor_master",
            description="代码重构专家，提供安全渐进式重构方案",
            model="qwen-coder-plus",
            temperature=0.2,
            system_prompt=""  # Prompt由Skill配置文件管理
        )
        super().__init__(config)
