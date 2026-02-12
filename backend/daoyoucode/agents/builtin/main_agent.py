"""
MainAgent - 主对话Agent

通用的对话Agent，支持代码理解、编写和项目分析
Prompt配置在 skills/chat-assistant/prompts/chat_assistant.md
"""

from ..core.agent import BaseAgent, AgentConfig


class MainAgent(BaseAgent):
    """
    主对话Agent
    
    这是一个通用的对话Agent，可以：
    - 理解项目代码
    - 回答编程问题
    - 编写和修改代码
    - 分析项目结构
    - 调用各种工具
    
    Prompt由Skill配置文件管理
    """
    
    def __init__(self):
        config = AgentConfig(
            name="MainAgent",
            description="主对话Agent，支持代码理解、编写和项目分析",
            model="qwen-max",
            temperature=0.7,
            system_prompt=""  # Prompt由Skill配置文件管理
        )
        super().__init__(config)
