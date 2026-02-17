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
        
        # 支持多轮对话：如果request中有messages，使用它；否则构建单轮消息
        if hasattr(request, 'messages') and request.messages:
            messages = request.messages
        else:
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
            
            # 详细请求日志：默认 logger.debug，设置 DEBUG_LLM=1 时用 info 避免生产刷屏（见优化建议 3.5）
            import os
            _log = logger.info if os.getenv('DEBUG_LLM') == '1' else logger.debug
            _log("=" * 60)
            _log("🔍 LLM请求调试信息")
            _log(f"模型: {request.model}")
            _log(f"API Key: {self.api_key[:15]}...{self.api_key[-4:]}")
            _log(f"消息数量: {len(messages)}")
            _log(f"Functions数量: {len(payload.get('functions', []))}")
            for i, msg in enumerate(messages[:3]):
                content = str(msg.get('content', ''))[:200]
                _log(f"消息 {i+1} ({msg.get('role')}): {content}...")
            if len(messages) > 3:
                _log(f"... 还有 {len(messages) - 3} 条消息")
            if payload.get('functions'):
                _log("Functions:")
                for i, func in enumerate(payload['functions'][:3]):
                    _log(f"  {i+1}. {func.get('name')}")
                if len(payload['functions']) > 3:
                    _log(f"  ... 还有 {len(payload['functions']) - 3} 个函数")
            payload_size = len(json.dumps(payload, ensure_ascii=False))
            _log(f"Payload大小: {payload_size} 字节 ({payload_size/1024:.2f} KB)")
            if os.getenv('DEBUG_LLM_REQUEST') == '1':
                debug_file = f"debug_llm_request_{int(time.time())}.json"
                with open(debug_file, 'w', encoding='utf-8') as f:
                    json.dump(payload, f, ensure_ascii=False, indent=2)
                _log(f"💾 完整请求已保存到: {debug_file}")
            _log("=" * 60)
            
            response = await self.http_client.post(
                f"{self.base_url}/chat/completions",
                headers=self._get_headers(),
                json=payload,
                timeout=1800.0  # 🆕 30 分钟（支持大规模文件读写和复杂任务）
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
        except httpx.HTTPStatusError as e:
            # 🔍 DEBUG: 打印错误响应
            logger.error(f"=" * 60)
            logger.error(f"❌ API错误响应")
            logger.error(f"状态码: {e.response.status_code}")
            logger.error(f"URL: {e.request.url}")
            logger.error(f"请求方法: {e.request.method}")
            
            # 尝试打印响应内容
            try:
                error_body = e.response.text
                logger.error(f"响应内容: {error_body[:500]}")
            except:
                logger.error("无法读取响应内容")
            
            logger.error(f"=" * 60)
            
            # 提供更详细的错误信息
            status_code = e.response.status_code
            if status_code == 500:
                error_msg = (
                    f"API服务器错误 (500)。可能原因：\n"
                    f"1. API配额不足（检查阿里云账户余额）\n"
                    f"2. 请求格式错误（特别是Function Calling）\n"
                    f"3. 请求过大（messages历史过长）\n"
                    f"4. 服务端临时故障（稍后重试）\n"
                    f"详情: {e}"
                )
            elif status_code == 429:
                error_msg = f"请求频率超限 (429)。请稍后重试。详情: {e}"
            elif status_code == 401:
                error_msg = f"API Key无效或过期 (401)。请检查DASHSCOPE_API_KEY环境变量。详情: {e}"
            else:
                error_msg = f"HTTP错误 ({status_code}): {e}"
            raise LLMConnectionError(error_msg)
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
                timeout=1800.0  # 🆕 30 分钟（支持大规模文件读写和复杂任务）
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
