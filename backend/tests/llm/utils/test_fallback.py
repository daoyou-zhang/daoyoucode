"""
测试降级策略
"""

import pytest
from daoyoucode.llm.utils.fallback import FallbackStrategy, get_fallback_strategy
from daoyoucode.llm.exceptions import FallbackExhaustedError


@pytest.mark.asyncio
async def test_fallback_success_on_first_try():
    """测试首次成功"""
    strategy = FallbackStrategy()
    
    async def success_func(model):
        return f"success with {model}"
    
    result, used_model = await strategy.execute_with_fallback(
        "qwen-max",
        success_func
    )
    
    assert result == "success with qwen-max"
    assert used_model == "qwen-max"


@pytest.mark.asyncio
async def test_fallback_on_failure():
    """测试失败后降级"""
    strategy = FallbackStrategy()
    
    call_count = 0
    
    async def fail_then_success(model):
        nonlocal call_count
        call_count += 1
        
        if call_count == 1:
            raise Exception("First attempt failed")
        return f"success with {model}"
    
    result, used_model = await strategy.execute_with_fallback(
        "qwen-max",
        fail_then_success
    )
    
    assert call_count == 2
    assert used_model == "qwen-plus"  # 降级到第一个备用模型


@pytest.mark.asyncio
async def test_fallback_exhausted():
    """测试降级链耗尽"""
    strategy = FallbackStrategy()
    
    async def always_fail(model):
        raise Exception(f"Failed with {model}")
    
    with pytest.raises(FallbackExhaustedError):
        await strategy.execute_with_fallback(
            "qwen-max",
            always_fail
        )


def test_get_fallback_chain():
    """测试获取降级链"""
    strategy = FallbackStrategy()
    
    chain = strategy.get_fallback_chain("qwen-max")
    
    assert chain[0] == "qwen-max"
    assert len(chain) > 1
    assert "qwen-plus" in chain


def test_configure_fallback_chain():
    """测试配置降级链"""
    strategy = FallbackStrategy()
    
    strategy.configure_fallback_chain(
        "custom-model",
        ["backup-1", "backup-2"]
    )
    
    chain = strategy.get_fallback_chain("custom-model")
    assert chain == ["custom-model", "backup-1", "backup-2"]


def test_fallback_stats():
    """测试降级统计"""
    strategy = FallbackStrategy()
    stats = strategy.get_stats()
    
    assert 'summary' in stats
    assert 'by_model' in stats


def test_get_fallback_info():
    """测试获取降级信息"""
    strategy = FallbackStrategy()
    
    info = strategy.get_fallback_info("qwen-max")
    
    assert info['model'] == "qwen-max"
    assert info['has_fallback'] is True
    assert len(info['fallback_chain']) > 1


def test_get_fallback_strategy_singleton():
    """测试降级策略单例"""
    strategy1 = get_fallback_strategy()
    strategy2 = get_fallback_strategy()
    assert strategy1 is strategy2
