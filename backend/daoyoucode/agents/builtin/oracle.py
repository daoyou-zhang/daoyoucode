"""
Oracle - 高IQ咨询Agent

只读分析，提供架构建议和技术咨询
采用高IQ分析设计

Prompt配置在 skills/oracle/prompts/oracle.md
"""

from ..core.agent import BaseAgent, AgentConfig


class OracleAgent(BaseAgent):
    """
    Oracle - 高IQ咨询Agent
    
    职责：
    - 架构分析和决策
    - 代码审查和建议
    - 性能分析
    - 安全审查
    - 技术咨询
    
    特点：
    - 只读权限（不修改代码）
    - 使用最强模型
    - 专注于高质量分析
    - 适合复杂决策
    
    使用场景：
    - 架构决策
    - 完成重要工作后的自我审查
    - 2次以上修复失败后
    - 不熟悉的代码模式
    - 安全/性能问题
    
    避免使用：
    - 简单文件操作
    - 第一次尝试修复
    - 从已读代码可以回答的问题
    - 琐碎决策（变量命名、格式化）
    
    Prompt由Skill配置文件管理
    """
    
    def __init__(self):
        config = AgentConfig(
            name="oracle",
            description="高IQ咨询Agent，提供架构分析和技术建议（只读）",
            model="qwen-max",  # 使用最强模型
            temperature=0.1,   # 低温度，更准确
            system_prompt=""   # Prompt由Skill配置文件管理
        )
        super().__init__(config)
