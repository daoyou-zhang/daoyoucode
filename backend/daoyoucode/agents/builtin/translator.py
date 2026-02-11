"""
翻译Agent

Prompt配置在 skills/translation/prompts/translator.md
"""

from ..core.agent import BaseAgent, AgentConfig


class TranslatorAgent(BaseAgent):
    """翻译Agent"""
    
    def __init__(self):
        config = AgentConfig(
            name="translator",
            description="专业翻译专家",
            model="qwen-max",
            temperature=0.3,
            system_prompt=""  # Prompt由Skill配置文件管理
        )
        super().__init__(config)
