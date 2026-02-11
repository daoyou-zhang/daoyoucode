"""
测试基础接口
"""

import pytest
from datetime import datetime
from daoyoucode.llm.base import LLMRequest, LLMResponse


def test_llm_request_creation():
    """测试LLMRequest创建"""
    request = LLMRequest(
        prompt="Hello",
        model="qwen-max",
        temperature=0.7,
        max_tokens=100
    )
    
    assert request.prompt == "Hello"
    assert request.model == "qwen-max"
    assert request.temperature == 0.7
    assert request.max_tokens == 100
    assert request.stream is False
    assert isinstance(request.metadata, dict)


def test_llm_request_defaults():
    """测试LLMRequest默认值"""
    request = LLMRequest(
        prompt="Hello",
        model="qwen-max"
    )
    
    assert request.temperature == 0.7
    assert request.max_tokens is None
    assert request.stream is False


def test_llm_response_creation():
    """测试LLMResponse创建"""
    response = LLMResponse(
        content="Hi there",
        model="qwen-max",
        tokens_used=50,
        cost=0.001,
        latency=1.5
    )
    
    assert response.content == "Hi there"
    assert response.model == "qwen-max"
    assert response.tokens_used == 50
    assert response.cost == 0.001
    assert response.latency == 1.5
    assert isinstance(response.timestamp, datetime)
    assert isinstance(response.metadata, dict)


def test_llm_response_with_metadata():
    """测试LLMResponse带元数据"""
    metadata = {
        "prompt_tokens": 30,
        "completion_tokens": 20
    }
    
    response = LLMResponse(
        content="Hi",
        model="qwen-max",
        tokens_used=50,
        cost=0.001,
        latency=1.5,
        metadata=metadata
    )
    
    assert response.metadata["prompt_tokens"] == 30
    assert response.metadata["completion_tokens"] == 20
