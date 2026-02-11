"""
LLM模块基础接口定义
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class LLMRequest:
    """LLM请求"""
    prompt: str
    model: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    stream: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """LLM响应"""
    content: str
    model: str
    tokens_used: int
    cost: float
    latency: float  # 响应时间（秒）
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class BaseLLMClient(ABC):
    """LLM客户端基类"""
    
    @abstractmethod
    async def chat(self, request: LLMRequest) -> LLMResponse:
        """同步对话"""
        pass
    
    @abstractmethod
    async def stream_chat(self, request: LLMRequest) -> AsyncIterator[str]:
        """流式对话"""
        pass
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            # 发送简单测试请求
            request = LLMRequest(
                prompt="test",
                model=self.model,
                max_tokens=1
            )
            await self.chat(request)
            return True
        except Exception:
            return False
