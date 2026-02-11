"""
LLM模块异常定义
"""


class LLMError(Exception):
    """LLM基础异常"""
    pass


class LLMConnectionError(LLMError):
    """连接错误"""
    pass


class LLMTimeoutError(LLMError):
    """超时错误"""
    pass


class LLMRateLimitError(LLMError):
    """限流错误"""
    pass


class LLMAuthenticationError(LLMError):
    """认证错误"""
    pass


class LLMInvalidRequestError(LLMError):
    """无效请求错误"""
    pass


class LLMModelNotFoundError(LLMError):
    """模型不存在错误"""
    pass


class CircuitBreakerOpenError(LLMError):
    """熔断器打开错误"""
    pass


class FallbackExhaustedError(LLMError):
    """降级链耗尽错误"""
    pass


class SkillNotFoundError(LLMError):
    """Skill未找到"""
    pass


class SkillExecutionError(LLMError):
    """Skill执行错误"""
    pass
