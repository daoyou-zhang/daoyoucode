"""
测试熔断器
"""

import pytest
import asyncio
from daoyoucode.llm.utils.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitBreakerManager,
    get_circuit_breaker_manager
)
from daoyoucode.llm.exceptions import CircuitBreakerOpenError


@pytest.mark.asyncio
async def test_circuit_breaker_closed_state():
    """测试关闭状态"""
    breaker = CircuitBreaker(failure_threshold=3)
    
    async def success_func():
        return "success"
    
    result = await breaker.call(success_func)
    assert result == "success"
    assert breaker.get_state() == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_circuit_breaker_open_on_failures():
    """测试失败后打开"""
    breaker = CircuitBreaker(failure_threshold=3)
    
    async def fail_func():
        raise Exception("Test error")
    
    # 失败3次
    for _ in range(3):
        with pytest.raises(Exception):
            await breaker.call(fail_func)
    
    # 熔断器应该打开
    assert breaker.get_state() == CircuitState.OPEN


@pytest.mark.asyncio
async def test_circuit_breaker_rejects_when_open():
    """测试打开时拒绝请求"""
    breaker = CircuitBreaker(failure_threshold=2, timeout=10)
    
    async def fail_func():
        raise Exception("Test error")
    
    # 失败2次打开熔断器
    for _ in range(2):
        with pytest.raises(Exception):
            await breaker.call(fail_func)
    
    # 应该拒绝新请求
    with pytest.raises(CircuitBreakerOpenError):
        await breaker.call(fail_func)


@pytest.mark.asyncio
async def test_circuit_breaker_half_open():
    """测试半开状态"""
    breaker = CircuitBreaker(failure_threshold=2, timeout=0.1)
    
    async def fail_func():
        raise Exception("Test error")
    
    # 打开熔断器
    for _ in range(2):
        with pytest.raises(Exception):
            await breaker.call(fail_func)
    
    # 等待恢复时间
    await asyncio.sleep(0.2)
    
    # 下次调用应该进入半开状态
    async def success_func():
        return "success"
    
    result = await breaker.call(success_func)
    assert result == "success"


def test_circuit_breaker_stats():
    """测试统计信息"""
    breaker = CircuitBreaker()
    stats = breaker.get_stats()
    
    assert 'total_calls' in stats
    assert 'successful_calls' in stats
    assert 'failed_calls' in stats
    assert 'current_state' in stats


def test_circuit_breaker_manager():
    """测试熔断器管理器"""
    manager = CircuitBreakerManager()
    
    breaker1 = manager.get_breaker("qwen-max")
    breaker2 = manager.get_breaker("qwen-max")
    
    assert breaker1 is breaker2


def test_get_circuit_breaker_manager_singleton():
    """测试管理器单例"""
    manager1 = get_circuit_breaker_manager()
    manager2 = get_circuit_breaker_manager()
    assert manager1 is manager2
