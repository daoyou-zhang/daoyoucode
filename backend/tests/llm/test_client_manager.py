"""
测试客户端管理器
"""

import pytest
from unittest.mock import MagicMock, patch
from daoyoucode.llm.client_manager import LLMClientManager, get_client_manager
from daoyoucode.llm.clients.unified import UnifiedLLMClient
from daoyoucode.llm.exceptions import LLMError


@pytest.fixture
def manager():
    """创建管理器实例"""
    # 重置单例
    LLMClientManager._instance = None
    LLMClientManager._initialized = False
    return LLMClientManager()


def test_singleton(manager):
    """测试单例模式"""
    manager2 = LLMClientManager()
    assert manager is manager2


def test_get_client_manager():
    """测试获取管理器"""
    LLMClientManager._instance = None
    manager1 = get_client_manager()
    manager2 = get_client_manager()
    assert manager1 is manager2


def test_configure_provider(manager):
    """测试配置提供商"""
    manager.configure_provider(
        provider="qwen",
        api_key="test-key",
        base_url="https://api.qwen.com/v1",
        models=["qwen-max", "qwen-plus"]
    )
    
    assert "qwen" in manager.provider_configs
    assert manager.provider_configs["qwen"]["api_key"] == "test-key"
    assert manager.provider_configs["qwen"]["base_url"] == "https://api.qwen.com/v1"
    assert "qwen-max" in manager.provider_configs["qwen"]["models"]


def test_infer_provider(manager):
    """测试提供商推断"""
    assert manager._infer_provider("qwen-max") == "qwen"
    assert manager._infer_provider("deepseek-chat") == "deepseek"
    assert manager._infer_provider("gpt-4") == "openai"
    assert manager._infer_provider("claude-3") == "anthropic"
    assert manager._infer_provider("gemini-pro") == "google"


def test_infer_provider_unknown(manager):
    """测试未知提供商"""
    with pytest.raises(LLMError, match="无法推断模型"):
        manager._infer_provider("unknown-model")


def test_get_client(manager):
    """测试获取客户端"""
    # 配置提供商
    manager.configure_provider(
        provider="qwen",
        api_key="test-key",
        base_url="https://api.qwen.com/v1"
    )
    
    # 获取客户端
    client = manager.get_client("qwen-max")
    
    assert isinstance(client, UnifiedLLMClient)
    assert client.model == "qwen-max"
    assert client.api_key == "test-key"
    assert client.base_url == "https://api.qwen.com/v1"


def test_get_client_explicit_provider(manager):
    """测试显式指定提供商"""
    manager.configure_provider(
        provider="qwen",
        api_key="test-key",
        base_url="https://api.qwen.com/v1"
    )
    
    client = manager.get_client("qwen-max", provider="qwen")
    assert isinstance(client, UnifiedLLMClient)


def test_get_client_unconfigured_provider(manager):
    """测试未配置的提供商"""
    with pytest.raises(LLMError, match="未配置提供商"):
        manager.get_client("qwen-max")


def test_record_usage(manager):
    """测试记录使用统计"""
    initial_requests = manager.stats['total_requests']
    initial_tokens = manager.stats['total_tokens']
    initial_cost = manager.stats['total_cost']
    
    manager.record_usage(tokens=100, cost=0.05)
    
    assert manager.stats['total_requests'] == initial_requests + 1
    assert manager.stats['total_tokens'] == initial_tokens + 100
    assert manager.stats['total_cost'] == initial_cost + 0.05


def test_get_stats(manager):
    """测试获取统计信息"""
    manager.record_usage(tokens=100, cost=0.05)
    
    stats = manager.get_stats()
    
    assert 'total_requests' in stats
    assert 'total_tokens' in stats
    assert 'total_cost' in stats
    assert 'http_pool_stats' in stats
    assert stats['total_requests'] >= 1
    assert stats['total_tokens'] >= 100


@pytest.mark.asyncio
async def test_close(manager):
    """测试关闭管理器"""
    # 模拟关闭
    manager.http_client.aclose = MagicMock()
    
    await manager.close()
    
    # 验证HTTP客户端被关闭
    manager.http_client.aclose.assert_called_once()


def test_shared_http_client(manager):
    """测试共享HTTP客户端"""
    manager.configure_provider(
        provider="qwen",
        api_key="test-key",
        base_url="https://api.qwen.com/v1"
    )
    
    client1 = manager.get_client("qwen-max")
    client2 = manager.get_client("qwen-plus")
    
    # 两个客户端应该共享同一个HTTP客户端
    assert client1.http_client is client2.http_client
    assert client1.http_client is manager.http_client
