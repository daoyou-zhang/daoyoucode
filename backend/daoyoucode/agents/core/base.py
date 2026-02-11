"""
Agent基类

设计思想：
1. 每个Agent都是独立的专家
2. 有明确的职责和工具权限
3. 支持并行执行和任务委托
4. 统一的接口和配置
"""

from typing import Dict, Any, Optional, Set, List
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """
    Agent配置
    
    参考oh-my-opencode的AgentConfig设计
    """
    name: str
    description: str
    model: str
    temperature: float = 0.1
    
    # 工具权限（参考oh-my-opencode）
    allowed_tools: Optional[Set[str]] = None  # None表示允许所有
    denied_tools: Set[str] = field(default_factory=set)
    
    # 思考预算（参考oh-my-opencode的extended thinking）
    thinking_budget: int = 0  # 0表示不使用extended thinking
    
    # 系统提示词
    system_prompt: str = ""
    
    # 是否只读（参考oh-my-opencode的oracle）
    read_only: bool = False
    
    # 中文优化（参考daoyouCodePilot）
    chinese_optimized: bool = False


@dataclass
class AgentResult:
    """Agent执行结果"""
    success: bool
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    
    # 使用的工具
    tools_used: List[str] = field(default_factory=list)
    
    # tokens使用情况
    tokens_used: int = 0
    cost: float = 0.0


class BaseAgent(ABC):
    """
    Agent基类
    
    所有Agent都继承这个基类
    """
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.name = config.name
        self.logger = logging.getLogger(f"agent.{self.name}")
    
    @abstractmethod
    async def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AgentResult:
        """
        执行任务
        
        Args:
            task: 任务描述
            context: 上下文信息
            **kwargs: 其他参数
        
        Returns:
            AgentResult
        """
        pass
    
    def can_use_tool(self, tool_name: str) -> bool:
        """
        检查是否可以使用某个工具
        
        参考oh-my-opencode的工具权限控制
        """
        # 如果在拒绝列表中，不能使用
        if tool_name in self.config.denied_tools:
            return False
        
        # 如果有允许列表，只能使用列表中的工具
        if self.config.allowed_tools is not None:
            return tool_name in self.config.allowed_tools
        
        # 默认允许
        return True
    
    async def delegate_task(
        self,
        agent_name: str,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        background: bool = False
    ) -> AgentResult:
        """
        委托任务给其他Agent
        
        参考oh-my-opencode的delegate_task
        
        Args:
            agent_name: 目标Agent名称
            task: 任务描述
            context: 上下文
            background: 是否后台执行
        """
        from ..core import get_agent_registry
        
        registry = get_agent_registry()
        target_agent = registry.get_agent(agent_name)
        
        if not target_agent:
            return AgentResult(
                success=False,
                content="",
                error=f"Agent '{agent_name}' not found"
            )
        
        self.logger.info(
            f"Delegating task to {agent_name}"
            f"{' (background)' if background else ''}"
        )
        
        if background:
            # TODO: 实现后台执行
            # 参考oh-my-opencode的background task
            pass
        
        return await target_agent.execute(task, context)
    
    def _build_prompt(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        构建完整的prompt
        
        结合系统提示词和任务描述
        """
        parts = []
        
        # 系统提示词
        if self.config.system_prompt:
            parts.append(self.config.system_prompt)
        
        # 上下文信息
        if context:
            context_str = self._format_context(context)
            if context_str:
                parts.append(f"\n## 上下文\n{context_str}")
        
        # 任务描述
        parts.append(f"\n## 任务\n{task}")
        
        return "\n".join(parts)
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """格式化上下文信息"""
        lines = []
        
        # 文件列表
        if 'files' in context:
            lines.append("相关文件：")
            for file in context['files']:
                lines.append(f"- {file}")
        
        # 代码片段
        if 'code' in context:
            lines.append("\n代码：")
            lines.append(f"```\n{context['code']}\n```")
        
        # 历史对话
        if 'history' in context:
            lines.append("\n历史对话：")
            for item in context['history'][-3:]:  # 最近3轮
                lines.append(f"- 用户: {item.get('user', '')}")
                lines.append(f"  AI: {item.get('ai', '')}")
        
        return "\n".join(lines)
    
    async def _call_llm(
        self,
        prompt: str,
        **kwargs
    ) -> str:
        """
        调用LLM
        
        使用已有的LLM模块
        """
        from ...llm import get_client_manager
        
        client_manager = get_client_manager()
        
        # 获取客户端
        client = await client_manager.get_client(
            model=self.config.model
        )
        
        # 调用
        response = await client.chat(
            prompt=prompt,
            temperature=self.config.temperature
        )
        
        return response
