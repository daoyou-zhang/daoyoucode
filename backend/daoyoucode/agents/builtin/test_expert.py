"""
测试专家Agent

专注于测试编写、测试修复和测试策略
Prompt配置在 skills/testing/prompts/test.md
"""

from ..core.agent import BaseAgent, AgentConfig


class TestExpertAgent(BaseAgent):
    """测试专家Agent"""
    
    def __init__(self):
        config = AgentConfig(
            name="test_expert",
            description="测试编写和修复专家，TDD工作流支持",
            model="qwen-coder-plus",  # 改用qwen-coder-plus（已配置）
            temperature=0.3,
            system_prompt=""  # Prompt由Skill配置文件管理
        )
        super().__init__(config)
