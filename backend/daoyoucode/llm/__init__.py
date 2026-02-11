"""
LLM模块 - 统一的大语言模型调用接口
"""

from .base import LLMRequest, LLMResponse, BaseLLMClient
from .exceptions import (
    LLMError,
    LLMConnectionError,
    LLMTimeoutError,
    LLMRateLimitError,
    LLMAuthenticationError,
    LLMInvalidRequestError,
    LLMModelNotFoundError,
    SkillNotFoundError,
    SkillExecutionError
)
from .client_manager import LLMClientManager, get_client_manager
from .clients.unified import UnifiedLLMClient
from .orchestrator import LLMOrchestrator, get_orchestrator

__all__ = [
    # 基础类
    'LLMRequest',
    'LLMResponse',
    'BaseLLMClient',
    
    # 异常
    'LLMError',
    'LLMConnectionError',
    'LLMTimeoutError',
    'LLMRateLimitError',
    'LLMAuthenticationError',
    'LLMInvalidRequestError',
    'LLMModelNotFoundError',
    'SkillNotFoundError',
    'SkillExecutionError',
    
    # 客户端管理
    'LLMClientManager',
    'get_client_manager',
    
    # 客户端
    'UnifiedLLMClient',
    
    # 编排器（主要接口）
    'LLMOrchestrator',
    'get_orchestrator',
]

__version__ = "0.1.0"
