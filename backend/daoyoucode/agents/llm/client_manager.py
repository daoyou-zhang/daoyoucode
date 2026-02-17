"""
LLM客户端管理器（简化版）
使用 httpx 内置连接池，不需要额外的连接池层
支持多API Key轮询
"""

import httpx
import logging
from typing import Dict, Optional, List
from .clients.unified import UnifiedLLMClient
from .exceptions import LLMError

logger = logging.getLogger(__name__)


class LLMClientManager:
    """
    LLM客户端管理器
    
    核心设计：
    1. 全局共享 httpx.AsyncClient（内置连接池）
    2. 按提供商缓存配置
    3. 轻量级客户端对象创建
    4. 支持多API Key轮询（Round-robin）
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # 全局共享的 HTTP 客户端（内置连接池）
        self.http_client = httpx.AsyncClient(
            limits=httpx.Limits(
                max_connections=100,           # 最大连接数
                max_keepalive_connections=20   # 保持活跃的连接数
            ),
            timeout=httpx.Timeout(1800.0)  # 🆕 30 分钟（支持大规模文件读写和复杂任务）
        )
        
        # 提供商配置缓存
        self.provider_configs: Dict[str, Dict] = {}
        
        # API Key轮询计数器（每个提供商独立计数）
        self.key_counters: Dict[str, int] = {}
        
        # 统计信息
        self.stats = {
            'total_requests': 0,
            'total_tokens': 0,
            'total_cost': 0.0,
        }
        
        self._initialized = True
        logger.info("LLM客户端管理器已初始化（支持API Key轮询）")
    
    def configure_provider(
        self,
        provider: str,
        api_key: Optional[str] = None,
        api_keys: Optional[List[str]] = None,
        base_url: str = "",
        models: Optional[list] = None
    ):
        """
        配置提供商
        
        Args:
            provider: 提供商名称（qwen, deepseek, openai等）
            api_key: 单个API密钥（与api_keys二选一）
            api_keys: 多个API密钥列表（轮询使用）
            base_url: API端点
            models: 支持的模型列表
        """
        # 处理API Key（支持单个或多个）
        if api_keys:
            keys = api_keys
        elif api_key:
            keys = [api_key]
        else:
            raise LLMError(f"提供商 {provider} 必须配置 api_key 或 api_keys")
        
        self.provider_configs[provider] = {
            'api_keys': keys,  # 统一存储为列表
            'base_url': base_url,
            'models': models or []
        }
        
        # 初始化轮询计数器
        self.key_counters[provider] = 0
        
        logger.info(f"已配置提供商: {provider}, API Key数量: {len(keys)}")
    
    def _get_next_api_key(self, provider: str) -> str:
        """
        获取下一个API Key（Round-robin轮询）
        
        Args:
            provider: 提供商名称
        
        Returns:
            API Key
        """
        config = self.provider_configs[provider]
        keys = config['api_keys']
        
        # 如果只有一个key，直接返回
        if len(keys) == 1:
            return keys[0]
        
        # 轮询：获取当前计数器对应的key，然后递增计数器
        current_index = self.key_counters[provider] % len(keys)
        self.key_counters[provider] += 1
        
        selected_key = keys[current_index]
        
        # 日志显示使用的是第几个key（避免泄露完整key）
        logger.debug(f"提供商 {provider}: 使用API Key #{current_index + 1}/{len(keys)} ({selected_key[:10]}...)")
        
        return selected_key
    
    def get_client(self, model: str, provider: Optional[str] = None) -> UnifiedLLMClient:
        """
        获取客户端（轻量级对象）
        
        Args:
            model: 模型名称
            provider: 提供商名称（可选，自动推断）
        
        Returns:
            UnifiedLLMClient实例
        """
        # 自动推断提供商
        if provider is None:
            provider = self._infer_provider(model)
        
        # 获取配置
        if provider not in self.provider_configs:
            raise LLMError(f"未配置提供商: {provider}")
        
        config = self.provider_configs[provider]
        
        # 获取下一个API Key（轮询）
        api_key = self._get_next_api_key(provider)
        
        # 创建轻量级客户端（共享HTTP客户端）
        return UnifiedLLMClient(
            http_client=self.http_client,  # 共享连接池
            api_key=api_key,
            base_url=config['base_url'],
            model=model
        )
    
    def _infer_provider(self, model: str) -> str:
        """根据模型名称推断提供商"""
        if model.startswith('qwen'):
            return 'qwen'
        elif model.startswith('deepseek'):
            return 'deepseek'
        elif model.startswith('gpt'):
            return 'openai'
        elif model.startswith('claude'):
            return 'anthropic'
        elif model.startswith('gemini'):
            return 'google'
        else:
            raise LLMError(f"无法推断模型 {model} 的提供商")
    
    def record_usage(self, tokens: int, cost: float):
        """记录使用统计"""
        self.stats['total_requests'] += 1
        self.stats['total_tokens'] += tokens
        self.stats['total_cost'] += cost
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        stats = {**self.stats}
        
        # 尝试获取HTTP连接池统计（可选）
        try:
            if hasattr(self.http_client, '_limits'):
                stats['http_pool_stats'] = {
                    'max_connections': self.http_client._limits.max_connections,
                    'max_keepalive': self.http_client._limits.max_keepalive_connections,
                }
        except Exception:
            pass
        
        return stats
    
    async def close(self):
        """关闭管理器"""
        await self.http_client.aclose()
        logger.info(f"LLM客户端管理器已关闭。统计: {self.stats}")


def get_client_manager() -> LLMClientManager:
    """获取客户端管理器单例"""
    return LLMClientManager()
