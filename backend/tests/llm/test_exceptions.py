"""
测试异常定义
"""

import pytest
from daoyoucode.llm.exceptions import (
    LLMError,
    LLMConnectionError,
    LLMTimeoutError,
    LLMRateLimitError,
    CircuitBreakerOpenError,
    FallbackExhaustedError,
    SkillNotFoundError,
    SkillExecutionError
)


def test_llm_error():
    """测试基础异常"""
    error = LLMError("Test error")
    assert str(error) == "Test error"
    assert isinstance(error, Exception)


def test_llm_connection_error():
    """测试连接错误"""
    error = LLMConnectionError("Connection failed")
    assert isinstance(error, LLMError)
    assert str(error) == "Connection failed"


def test_llm_timeout_error():
    """测试超时错误"""
    error = LLMTimeoutError("Request timeout")
    assert isinstance(error, LLMError)


def test_llm_rate_limit_error():
    """测试限流错误"""
    error = LLMRateLimitError("Rate limit exceeded")
    assert isinstance(error, LLMError)


def test_circuit_breaker_open_error():
    """测试熔断器错误"""
    error = CircuitBreakerOpenError("Circuit breaker is open")
    assert isinstance(error, LLMError)


def test_fallback_exhausted_error():
    """测试降级链耗尽错误"""
    error = FallbackExhaustedError("All fallbacks failed")
    assert isinstance(error, LLMError)


def test_skill_not_found_error():
    """测试Skill未找到错误"""
    error = SkillNotFoundError("Skill not found")
    assert isinstance(error, LLMError)


def test_skill_execution_error():
    """测试Skill执行错误"""
    error = SkillExecutionError("Skill execution failed")
    assert isinstance(error, LLMError)
