"""
熔断器（Circuit Breaker）
防止级联故障，自动故障恢复
"""

import asyncio
import time
from typing import Dict, Callable, Any, Optional
from enum import Enum
import logging

from ..exceptions import CircuitBreakerOpenError

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """熔断器状态"""
    CLOSED = "closed"        # 关闭（正常）
    OPEN = "open"            # 打开（熔断）
    HALF_OPEN = "half_open"  # 半开（尝试恢复）


class CircuitBreaker:
    """
    熔断器
    
    工作原理：
    1. CLOSED: 正常状态，请求正常通过
    2. 失败次数达到阈值 -> OPEN
    3. OPEN: 熔断状态，直接拒绝请求
    4. 超过恢复时间 -> HALF_OPEN
    5. HALF_OPEN: 尝试恢复，允许少量请求
    6. 成功 -> CLOSED，失败 -> OPEN
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,      # 失败阈值
        success_threshold: int = 2,      # 成功阈值（半开状态）
        timeout: int = 60,               # 恢复超时（秒）
        half_open_max_calls: int = 3     # 半开状态最大调用数
    ):
        """
        初始化熔断器
        
        Args:
            failure_threshold: 失败阈值（连续失败多少次后打开熔断器）
            success_threshold: 成功阈值（半开状态成功多少次后关闭熔断器）
            timeout: 恢复超时（熔断后多久尝试恢复）
            half_open_max_calls: 半开状态最大调用数
        """
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout
        self.half_open_max_calls = half_open_max_calls
        
        # 状态
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.half_open_calls = 0
        
        # 统计
        self.stats = {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'rejected_calls': 0,
            'state_changes': []
        }
        
        self._lock = asyncio.Lock()
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        通过熔断器调用函数
        
        Args:
            func: 要调用的函数
            *args, **kwargs: 函数参数
        
        Returns:
            函数返回值
        
        Raises:
            CircuitBreakerOpenError: 熔断器打开
            Exception: 函数执行异常
        """
        async with self._lock:
            self.stats['total_calls'] += 1
            
            # 检查状态
            if self.state == CircuitState.OPEN:
                # 检查是否可以尝试恢复
                if self._should_attempt_reset():
                    self._transition_to_half_open()
                else:
                    self.stats['rejected_calls'] += 1
                    raise CircuitBreakerOpenError(
                        f"熔断器打开: 失败{self.failure_count}次，"
                        f"将在{self._get_remaining_timeout():.1f}秒后尝试恢复"
                    )
            
            # 半开状态检查调用次数
            if self.state == CircuitState.HALF_OPEN:
                if self.half_open_calls >= self.half_open_max_calls:
                    self.stats['rejected_calls'] += 1
                    raise CircuitBreakerOpenError(
                        "熔断器半开状态: 已达到最大调用次数"
                    )
                self.half_open_calls += 1
        
        # 执行函数
        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            await self._on_success()
            return result
        
        except Exception as e:
            await self._on_failure(e)
            raise
    
    async def _on_success(self):
        """处理成功"""
        async with self._lock:
            self.stats['successful_calls'] += 1
            
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                
                # 达到成功阈值，关闭熔断器
                if self.success_count >= self.success_threshold:
                    self._transition_to_closed()
            
            elif self.state == CircuitState.CLOSED:
                # 重置失败计数
                self.failure_count = 0
    
    async def _on_failure(self, error: Exception):
        """处理失败"""
        async with self._lock:
            self.stats['failed_calls'] += 1
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            logger.warning(f"熔断器检测到失败: {error}")
            
            if self.state == CircuitState.HALF_OPEN:
                # 半开状态失败，立即打开熔断器
                self._transition_to_open()
            
            elif self.state == CircuitState.CLOSED:
                # 达到失败阈值，打开熔断器
                if self.failure_count >= self.failure_threshold:
                    self._transition_to_open()
    
    def _should_attempt_reset(self) -> bool:
        """是否应该尝试恢复"""
        if self.last_failure_time is None:
            return False
        
        elapsed = time.time() - self.last_failure_time
        return elapsed >= self.timeout
    
    def _get_remaining_timeout(self) -> float:
        """获取剩余恢复时间"""
        if self.last_failure_time is None:
            return 0
        
        elapsed = time.time() - self.last_failure_time
        return max(0, self.timeout - elapsed)
    
    def _transition_to_open(self):
        """转换到打开状态"""
        old_state = self.state
        self.state = CircuitState.OPEN
        self.success_count = 0
        self.half_open_calls = 0
        
        self.stats['state_changes'].append({
            'from': old_state.value,
            'to': CircuitState.OPEN.value,
            'time': time.time(),
            'failure_count': self.failure_count
        })
        
        logger.error(
            f"熔断器打开: 失败{self.failure_count}次，"
            f"将在{self.timeout}秒后尝试恢复"
        )
    
    def _transition_to_half_open(self):
        """转换到半开状态"""
        old_state = self.state
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
        self.half_open_calls = 0
        
        self.stats['state_changes'].append({
            'from': old_state.value,
            'to': CircuitState.HALF_OPEN.value,
            'time': time.time()
        })
        
        logger.info("熔断器进入半开状态，尝试恢复")
    
    def _transition_to_closed(self):
        """转换到关闭状态"""
        old_state = self.state
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.half_open_calls = 0
        
        self.stats['state_changes'].append({
            'from': old_state.value,
            'to': CircuitState.CLOSED.value,
            'time': time.time()
        })
        
        logger.info("熔断器关闭，恢复正常")
    
    def get_state(self) -> CircuitState:
        """获取当前状态"""
        return self.state
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            **self.stats,
            'current_state': self.state.value,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'remaining_timeout': self._get_remaining_timeout() if self.state == CircuitState.OPEN else 0
        }
    
    def reset(self):
        """手动重置熔断器"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.half_open_calls = 0
        logger.info("熔断器已手动重置")


class CircuitBreakerManager:
    """熔断器管理器"""
    
    def __init__(self):
        # 按模型管理熔断器
        self.breakers: Dict[str, CircuitBreaker] = {}
        
        # 默认配置
        self.default_config = {
            'failure_threshold': 5,
            'success_threshold': 2,
            'timeout': 60,
            'half_open_max_calls': 3
        }
        
        logger.info("熔断器管理器已初始化")
    
    def get_breaker(self, model: str) -> CircuitBreaker:
        """获取模型的熔断器"""
        if model not in self.breakers:
            self.breakers[model] = CircuitBreaker(**self.default_config)
            logger.info(f"为模型 {model} 创建熔断器")
        
        return self.breakers[model]
    
    def configure(
        self,
        model: str,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: int = 60,
        half_open_max_calls: int = 3
    ):
        """配置模型的熔断器"""
        self.breakers[model] = CircuitBreaker(
            failure_threshold=failure_threshold,
            success_threshold=success_threshold,
            timeout=timeout,
            half_open_max_calls=half_open_max_calls
        )
        logger.info(f"模型 {model} 熔断器配置完成")
    
    async def call(self, model: str, func: Callable, *args, **kwargs) -> Any:
        """通过熔断器调用函数"""
        breaker = self.get_breaker(model)
        return await breaker.call(func, *args, **kwargs)
    
    def get_stats(self, model: Optional[str] = None) -> Dict:
        """获取统计信息"""
        if model:
            breaker = self.breakers.get(model)
            return breaker.get_stats() if breaker else {}
        
        return {
            model: breaker.get_stats()
            for model, breaker in self.breakers.items()
        }
    
    def reset(self, model: Optional[str] = None):
        """重置熔断器"""
        if model:
            if model in self.breakers:
                self.breakers[model].reset()
        else:
            for breaker in self.breakers.values():
                breaker.reset()


def get_circuit_breaker_manager() -> CircuitBreakerManager:
    """获取熔断器管理器单例"""
    if not hasattr(get_circuit_breaker_manager, '_instance'):
        get_circuit_breaker_manager._instance = CircuitBreakerManager()
    return get_circuit_breaker_manager._instance
