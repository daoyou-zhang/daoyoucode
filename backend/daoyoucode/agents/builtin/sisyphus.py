"""
Sisyphus - 主编排Agent

负责智能任务分解和Agent调度
借鉴oh-my-opencode的设计，实现todo驱动的工作流

Prompt配置在 skills/sisyphus/prompts/sisyphus.md
"""

from ..core.agent import BaseAgent, AgentConfig


class SisyphusAgent(BaseAgent):
    """
    Sisyphus - 主编排Agent
    
    职责：
    - 分析用户请求
    - 分解复杂任务
    - 选择合适的专业Agent
    - 验证执行结果
    - 聚合最终答案
    
    特点：
    - Todo驱动工作流
    - 智能Agent选择
    - 结果验证
    - 只使用4个基础工具（快速探索）
    
    Prompt由Skill配置文件管理
    """
    
    def __init__(self):
        config = AgentConfig(
            name="sisyphus",
            description="主编排Agent，负责任务分解和Agent调度",
            model="qwen-max",  # 使用最强模型
            temperature=0.1,   # 低温度，更准确
            system_prompt=""   # Prompt由Skill配置文件管理
        )
        super().__init__(config)
