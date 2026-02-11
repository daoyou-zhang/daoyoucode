"""
测试限流器
"""

import pytest
import asyncio
from daoyoucode.llm.utils.rate_limiter import (
    TokenBucket,
    SlidingWindowCounter,
    RateLimiter,
    get_rate_limiter
)
from daoyoucode.llm.exceptions import LLMRateLimitError


@pytest.mark.asyncio
async def test_token_bucket_acquire():
    """测试令牌桶获取"""
    bucket = TokenBucket(capacity=10, refill_rate=1.0)
    
    # 获取令牌
    result = await bucket.acquire(tokens=5)
    assert result is True
    assert bucket.tokens == 5


@pytest.mark.asyncio
async def test_token_bucket_refill():
    """测试令牌桶填充"""
    bucket = TokenBucket(capacity=10, refill_rate=10.0)  # 每秒10个
    
    # 消耗所有令牌
    await bucket.acquire(tokens=10)
    assert bucket.tokens == 0
    
    # 等待填充
    await asyncio.sleep(0.5)  # 等待0.5秒，应该填充5个
    
    # 再次获取
    result = await bucket.acquire(tokens=4)
    assert result is True


@pytest.mark.asyncio
async def test_token_bucket_timeout():
    """测试令牌桶超时"""
    bucket = TokenBucket(capacity=1, refill_rate=0.1)  # 很慢的填充速率
    
    # 消耗令牌
    await bucket.acquire(tokens=1)
    
    # 尝试获取更多令牌，应该超时
    with pytest.raises(LLMRateLimitError):
        await bucket.acquire(tokens=1, timeout=0.1)


@pytest.mark.asyncio
async def test_sliding_window_acquire():
    """测试滑动窗口获取"""
    window = SlidingWindowCounter(window_size=60, max_requests=5)
    
    # 获取5次许可
    for _ in range(5):
        result = await window.acquire()
        assert result is True
    
    assert window.get_current_count() == 5


@pytest.mark.asyncio
async def test_sliding_window_limit():
    """测试滑动窗口限制"""
    window = SlidingWindowCounter(window_size=60, max_requests=2)
    
    # 获取2次许可
    await window.acquire()
    await window.acquire()
    
    # 第3次应该超时
    with pytest.raises(LLMRateLimitError):
        await window.acquire(timeout=0.1)


@pytest.mark.asyncio
async def test_rate_limiter_user_limit():
    """测试用户限流"""
    limiter = RateLimiter()
    limiter.configure_user_limit(capacity=5, refill_rate=1.0)
    
    # 用户1获取许可
    await limiter.acquire(user_id=1)
    await limiter.acquire(user_id=1)
    
    # 用户2独立限流
    await limiter.acquire(user_id=2)


@pytest.mark.asyncio
async def test_rate_limiter_model_limit():
    """测试模型限流"""
    limiter = RateLimiter()
    limiter.configure_model_limit(
        model="qwen-max",
        window_size=60,
        max_requests=3
    )
    
    # 获取3次许可
    for _ in range(3):
        await limiter.acquire(model="qwen-max")
    
    # 第4次应该失败
    with pytest.raises(LLMRateLimitError):
        await limiter.acquire(model="qwen-max", timeout=0.1)


@pytest.mark.asyncio
async def test_rate_limiter_global_limit():
    """测试全局限流"""
    limiter = RateLimiter()
    limiter.configure_global_limit(capacity=5, refill_rate=1.0)
    
    # 获取5次许可
    for _ in range(5):
        await limiter.acquire()
    
    # 第6次应该失败
    with pytest.raises(LLMRateLimitError):
        await limiter.acquire(timeout=0.1)


def test_rate_limiter_stats():
    """测试限流统计"""
    limiter = RateLimiter()
    limiter.configure_user_limit(capacity=10, refill_rate=1.0)
    
    stats = limiter.get_stats()
    
    assert 'user_count' in stats
    assert 'model_count' in stats
    assert 'users' in stats
    assert 'models' in stats


def test_get_rate_limiter_singleton():
    """测试限流器单例"""
    limiter1 = get_rate_limiter()
    limiter2 = get_rate_limiter()
    assert limiter1 is limiter2
