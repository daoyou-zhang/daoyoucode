"""
代码分析Agent - 架构顾问

借鉴oh-my-opencode的Oracle智能体
Prompt配置在 skills/code-analysis/prompts/oracle.md
"""

from ..core.agent import BaseAgent, AgentConfig


class CodeAnalyzerAgent(BaseAgent):
    """代码分析Agent（架构顾问）"""
    
    def __init__(self):
        config = AgentConfig(
            name="code_analyzer",
            description="代码架构分析专家，提供高IQ分析和建议（借鉴oh-my-opencode Oracle）",
            model="qwen-max",
            temperature=0.1,
            system_prompt=""  # Prompt由Skill配置文件管理
        )
        super().__init__(config)
