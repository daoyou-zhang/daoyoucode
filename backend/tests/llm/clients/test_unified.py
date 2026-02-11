"""
测试统一LLM客户端
"""

import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch
from daoyoucode.llm.clients.unified import UnifiedLLMClient
from daoyoucode.llm.base import LLMRequest, LLMResponse
from daoyoucode.llm.exceptions import LLMConnectionError, LLMTimeoutError


@pytest.fixture
def mock_http_client():
    """模拟HTTP客户端"""
    client = AsyncMock(spec=httpx.AsyncClient)
    return client


@pytest.fixture
def llm_client(mock_http_client):
    """创建LLM客户端"""
    return UnifiedLLMClient(
        http_client=mock_http_client,
        api_key="test-key",
        base_url="https://api.test.com/v1",
        model="qwen-max"
    )


@pytest.mark.asyncio
async def test_chat_success(llm_client, mock_http_client):
    """测试成功的对话"""
    # 模拟响应
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{
            "message": {"content": "Hello!"}
        }],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15
        }
    }
    mock_http_client.post = AsyncMock(return_value=mock_response)
    
    # 执行请求
    request = LLMRequest(
        prompt="Hi",
        model="qwen-max",
        temperature=0.7
    )
    
    response = await llm_client.chat(request)
    
    # 验证
    assert isinstance(response, LLMResponse)
    assert response.content == "Hello!"
    assert response.model == "qwen-max"
    assert response.tokens_used == 15
    assert response.cost > 0
    assert response.latency > 0
    assert response.metadata["prompt_tokens"] == 10
    assert response.metadata["completion_tokens"] == 5


@pytest.mark.asyncio
async def test_chat_timeout(llm_client, mock_http_client):
    """测试超时"""
    mock_http_client.post = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
    
    request = LLMRequest(
        prompt="Hi",
        model="qwen-max"
    )
    
    with pytest.raises(LLMTimeoutError):
        await llm_client.chat(request)


@pytest.mark.asyncio
async def test_chat_connection_error(llm_client, mock_http_client):
    """测试连接错误"""
    mock_http_client.post = AsyncMock(side_effect=httpx.HTTPError("Connection failed"))
    
    request = LLMRequest(
        prompt="Hi",
        model="qwen-max"
    )
    
    with pytest.raises(LLMConnectionError):
        await llm_client.chat(request)


def test_calculate_cost(llm_client):
    """测试成本计算"""
    usage = {
        "prompt_tokens": 1000,
        "completion_tokens": 500
    }
    
    # qwen-max: input=0.02, output=0.06 per 1000 tokens
    cost = llm_client._calculate_cost(usage, "qwen-max")
    expected = (1000 * 0.02 + 500 * 0.06) / 1000
    assert abs(cost - expected) < 0.0001


def test_calculate_cost_unknown_model(llm_client):
    """测试未知模型的成本计算"""
    usage = {
        "prompt_tokens": 1000,
        "completion_tokens": 500
    }
    
    # 使用默认价格
    cost = llm_client._calculate_cost(usage, "unknown-model")
    expected = (1000 * 0.01 + 500 * 0.03) / 1000
    assert abs(cost - expected) < 0.0001


def test_get_headers(llm_client):
    """测试请求头"""
    headers = llm_client._get_headers()
    
    assert headers["Authorization"] == "Bearer test-key"
    assert headers["Content-Type"] == "application/json"


@pytest.mark.asyncio
async def test_stream_chat(llm_client, mock_http_client):
    """测试流式对话"""
    # 模拟流式响应
    async def mock_aiter_lines():
        yield 'data: {"choices":[{"delta":{"content":"Hello"}}]}'
        yield 'data: {"choices":[{"delta":{"content":" world"}}]}'
        yield 'data: [DONE]'
    
    mock_stream_response = MagicMock()
    mock_stream_response.aiter_lines = mock_aiter_lines
    mock_stream_response.__aenter__ = AsyncMock(return_value=mock_stream_response)
    mock_stream_response.__aexit__ = AsyncMock(return_value=None)
    
    mock_http_client.stream = MagicMock(return_value=mock_stream_response)
    
    # 执行流式请求
    request = LLMRequest(
        prompt="Hi",
        model="qwen-max",
        stream=True
    )
    
    chunks = []
    async for chunk in llm_client.stream_chat(request):
        chunks.append(chunk)
    
    # 验证
    assert len(chunks) == 2
    assert chunks[0] == "Hello"
    assert chunks[1] == " world"
