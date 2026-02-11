"""
统一LLM客户端（OpenAI兼容）
"""

import httpx
import json
import time
from typing import AsyncIterator, Optional
import logging

from ..base import BaseLLMClient, LLMRequest, LLMResponse
from ..exceptions import LLMConnectionError, LLMTimeoutError

logger = logging.getLogger(__name__)


class UnifiedLLMClient(BaseLLMClient):
    """统一LLM客户端（OpenAI兼容格式）"""
    
    # 模型定价（每1000 tokens，单位：元）
    PRICING = {
        # 通义千问
        "qwen-max": {"input": 0.02, "output": 0.06},
        "qwen-plus": {"input": 0.004, "output": 0.012},
        "qwen-turbo": {"input": 0.002, "output": 0.006},
        "qwen-coder-plus": {"input": 0.004, "output": 0.012},
        # DeepSeek
        "deepseek-chat": {"input": 0.001, "output": 0.002},
        "deepseek-coder": {"input": 0.001, "output": 0.002},
        # 默认价格
        "default": {"input": 0.01, "output": 0.03},
    }
    
    def __init__(
        self,
        http_client: httpx.AsyncClient,
        api_key: str,
        base_url: str,
        model: str
    ):
        """
        初始化客户端
        
        Args:
            http_client: 共享的HTTP客户端（带连接池）
            api_key: API密钥
            base_url: API端点
            model: 模型名称
        """
        self.http_client = http_client
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.model = model
    
    async def chat(self, request: LLMRequest) -> LLMResponse:
        """同步对话"""
        start_time = time.time()
        
        messages = [{"role": "user", "content": request.prompt}]
        
        try:
            payload = {
                "model": request.model,
                "messages": messages,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
            }
            
            # 添加Function Calling支持
            if hasattr(request, 'functions') and request.functions:
                payload["functions"] = request.functions
                if hasattr(request, 'function_call'):
                    payload["function_call"] = request.function_call
            
            response = await self.http_client.post(
                f"{self.base_url}/chat/completions",
                headers=self._get_headers(),
                json=payload,
                timeout=60.0
            )
            response.raise_for_status()
            data = response.json()
            
            latency = time.time() - start_time
            
            # 检查是否有function_call
            message = data["choices"][0]["message"]
            function_call = message.get("function_call")
            
            return LLMResponse(
                content=message.get("content", ""),
                model=request.model,
                tokens_used=data["usage"]["total_tokens"],
                cost=self._calculate_cost(data["usage"], request.model),
                latency=latency,
                metadata={
                    "prompt_tokens": data["usage"]["prompt_tokens"],
                    "completion_tokens": data["usage"]["completion_tokens"],
                    "function_call": function_call
                }
            )
        
        except httpx.TimeoutException as e:
            raise LLMTimeoutError(f"请求超时: {e}")
        except httpx.HTTPError as e:
            raise LLMConnectionError(f"连接错误: {e}")
    
    async def stream_chat(self, request: LLMRequest) -> AsyncIterator[str]:
        """流式对话"""
        messages = [{"role": "user", "content": request.prompt}]
        
        try:
            async with self.http_client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=self._get_headers(),
                json={
                    "model": request.model,
                    "messages": messages,
                    "temperature": request.temperature,
                    "max_tokens": request.max_tokens,
                    "stream": True,
                },
                timeout=60.0
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        data_str = line[5:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue
        
        except httpx.TimeoutException as e:
            raise LLMTimeoutError(f"流式请求超时: {e}")
        except httpx.HTTPError as e:
            raise LLMConnectionError(f"流式连接错误: {e}")
    
    def _get_headers(self) -> dict:
        """获取请求头"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
    
    def _calculate_cost(self, usage: dict, model: str) -> float:
        """计算成本"""
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        
        # 获取定价
        pricing = self.PRICING.get(model, self.PRICING["default"])
        
        # 计算成本（元）
        cost = (
            input_tokens * pricing["input"] +
            output_tokens * pricing["output"]
        ) / 1000
        
        return cost
