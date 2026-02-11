"""
限流器（Rate Limiter）
防止请求过载，保护LLM服务
"""

import asyncio
import time
from typing import Dict, Optional
from collections import deque
import logging

from ..exceptions import LLMRateLimitError

logger = logging.getLogger(__name__)


class TokenBucket:
    """令牌桶算法实现"""
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        初始化令牌桶
        
        Args:
            capacity: 桶容量（最大令牌数）
            refill_rate: 填充速率（令牌/秒）
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
        self._lock = asyncio.Lock()
    
    async def acquire(self, tokens: int = 1, timeout: Optional[float] = None) -> bool:
        """
        获取令牌
        
        Args:
            tokens: 需要的令牌数
            timeout: 超时时间（秒），None表示无限等待
        
        Returns:
            是否成功获取令牌
        
        Raises:
            LLMRateLimitError: 超时未获取到令牌
        """
        start_time = time.time()
        
        while True:
            async with self._lock:
                # 填充令牌
                self._refill()
                
                # 检查是否有足够的令牌
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return True
            
            # 检查超时
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    raise LLMRateLimitError(
                        f"获取令牌超时: 需要{tokens}个令牌，当前{self.tokens:.2f}个"
                    )
            
            # 等待一小段时间再重试
            await asyncio.sleep(0.1)
    
    def _refill(self):
        """填充令牌"""
        now = time.time()
        elapsed = now - self.last_refill
        
        # 计算应该填充的令牌数
        tokens_to_add = elapsed * self.refill_rate
        
        if tokens_to_add > 0:
            self.tokens = min(self.capacity, self.tokens + tokens_to_add)
            self.last_refill = now
    
    def get_available_tokens(self) -> float:
        """获取当前可用令牌数"""
        return self.tokens


class SlidingWindowCounter:
    """滑动窗口计数器"""
    
    def __init__(self, window_size: int, max_requests: int):
        """
        初始化滑动窗口
        
        Args:
            window_size: 窗口大小（秒）
            max_requests: 窗口内最大请求数
        """
        self.window_size = window_size
        self.max_requests = max_requests
        self.requests = deque()
        self._lock = asyncio.Lock()
    
    async def acquire(self, timeout: Optional[float] = None) -> bool:
        """
        尝试获取许可
        
        Args:
            timeout: 超时时间（秒）
        
        Returns:
            是否成功获取许可
        
        Raises:
            LLMRateLimitError: 超时未获取到许可
        """
        start_time = time.time()
        
        while True:
            async with self._lock:
                # 清理过期请求
                self._cleanup()
                
                # 检查是否可以通过
                if len(self.requests) < self.max_requests:
                    self.requests.append(time.time())
                    return True
            
            # 检查超时
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    raise LLMRateLimitError(
                        f"限流超时: 窗口内已有{len(self.requests)}个请求，"
                        f"最大{self.max_requests}个"
                    )
            
            # 等待一小段时间再重试
            await asyncio.sleep(0.1)
    
    def _cleanup(self):
        """清理过期的请求记录"""
        now = time.time()
        cutoff = now - self.window_size
        
        while self.requests and self.requests[0] < cutoff:
            self.requests.popleft()
    
    def get_current_count(self) -> int:
        """获取当前窗口内的请求数"""
        return len(self.requests)


class RateLimiter:
    """
    限流器
    
    支持多种限流策略：
    1. 按用户限流
    2. 按模型限流
    3. 全局限流
    """
    
    def __init__(self):
        # 用户限流器（每个用户独立的令牌桶）
        self.user_limiters: Dict[int, TokenBucket] = {}
        
        # 模型限流器（每个模型独立的滑动窗口）
        self.model_limiters: Dict[str, SlidingWindowCounter] = {}
        
        # 全局限流器
        self.global_limiter: Optional[TokenBucket] = None
        
        # 默认配置
        self.default_user_config = {
            'capacity': 10,      # 10个令牌
            'refill_rate': 1.0   # 每秒1个令牌
        }
        
        self.default_model_config = {
            'window_size': 60,    # 60秒窗口
            'max_requests': 100   # 最多100个请求
        }
        
        logger.info("限流器已初始化")
    
    def configure_user_limit(self, capacity: int, refill_rate: float):
        """配置用户限流"""
        self.default_user_config = {
            'capacity': capacity,
            'refill_rate': refill_rate
        }
        logger.info(f"用户限流配置: 容量={capacity}, 速率={refill_rate}/s")
    
    def configure_model_limit(self, model: str, window_size: int, max_requests: int):
        """配置模型限流"""
        self.model_limiters[model] = SlidingWindowCounter(
            window_size=window_size,
            max_requests=max_requests
        )
        logger.info(f"模型 {model} 限流配置: {max_requests}次/{window_size}秒")
    
    def configure_global_limit(self, capacity: int, refill_rate: float):
        """配置全局限流"""
        self.global_limiter = TokenBucket(
            capacity=capacity,
            refill_rate=refill_rate
        )
        logger.info(f"全局限流配置: 容量={capacity}, 速率={refill_rate}/s")
    
    async def acquire(
        self,
        user_id: Optional[int] = None,
        model: Optional[str] = None,
        timeout: float = 30.0
    ):
        """
        获取许可（通过所有限流检查）
        
        Args:
            user_id: 用户ID
            model: 模型名称
            timeout: 超时时间
        
        Raises:
            LLMRateLimitError: 限流失败
        """
        # 1. 全局限流
        if self.global_limiter:
            await self.global_limiter.acquire(tokens=1, timeout=timeout)
        
        # 2. 用户限流
        if user_id is not None:
            if user_id not in self.user_limiters:
                self.user_limiters[user_id] = TokenBucket(
                    capacity=self.default_user_config['capacity'],
                    refill_rate=self.default_user_config['refill_rate']
                )
            
            await self.user_limiters[user_id].acquire(tokens=1, timeout=timeout)
        
        # 3. 模型限流
        if model is not None and model in self.model_limiters:
            await self.model_limiters[model].acquire(timeout=timeout)
    
    def get_stats(self) -> Dict:
        """获取限流统计"""
        stats = {
            'user_count': len(self.user_limiters),
            'model_count': len(self.model_limiters),
            'users': {},
            'models': {}
        }
        
        # 用户统计
        for user_id, limiter in self.user_limiters.items():
            stats['users'][user_id] = {
                'available_tokens': limiter.get_available_tokens(),
                'capacity': limiter.capacity
            }
        
        # 模型统计
        for model, limiter in self.model_limiters.items():
            stats['models'][model] = {
                'current_count': limiter.get_current_count(),
                'max_requests': limiter.max_requests
            }
        
        # 全局统计
        if self.global_limiter:
            stats['global'] = {
                'available_tokens': self.global_limiter.get_available_tokens(),
                'capacity': self.global_limiter.capacity
            }
        
        return stats


def get_rate_limiter() -> RateLimiter:
    """获取限流器单例"""
    if not hasattr(get_rate_limiter, '_instance'):
        get_rate_limiter._instance = RateLimiter()
    return get_rate_limiter._instance
