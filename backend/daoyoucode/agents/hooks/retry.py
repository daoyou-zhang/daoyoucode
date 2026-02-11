"""
重试Hook

自动重试失败的执行
"""

from ..core.hook import BaseHook, HookContext
from typing import Dict, Any, Optional
import asyncio


class RetryHook(BaseHook):
    """重试Hook"""
    
    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        exponential_backoff: bool = True
    ):
        super().__init__("retry")
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.exponential_backoff = exponential_backoff
        self._retry_counts: Dict[str, int] = {}
    
    async def on_before_execute(
        self,
        context: HookContext
    ) -> HookContext:
        """记录重试次数"""
        session_key = f"{context.session_id}_{context.skill_name}"
        
        if session_key not in self._retry_counts:
            self._retry_counts[session_key] = 0
        
        retry_count = self._retry_counts[session_key]
        context.metadata['retry_count'] = retry_count
        
        if retry_count > 0:
            self.logger.info(
                f"重试执行 (第{retry_count}次): {context.skill_name}"
            )
        
        return context
    
    async def on_after_execute(
        self,
        context: HookContext,
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """成功后清除重试计数"""
        session_key = f"{context.session_id}_{context.skill_name}"
        
        if result.get('success'):
            # 成功，清除重试计数
            self._retry_counts.pop(session_key, None)
        
        # 添加重试信息到结果
        if 'retry_count' in context.metadata:
            result['retry_count'] = context.metadata['retry_count']
        
        return result
    
    async def on_error(
        self,
        context: HookContext,
        error: Exception
    ) -> Optional[Dict[str, Any]]:
        """错误时尝试重试"""
        session_key = f"{context.session_id}_{context.skill_name}"
        retry_count = self._retry_counts.get(session_key, 0)
        
        if retry_count < self.max_retries:
            # 增加重试计数
            self._retry_counts[session_key] = retry_count + 1
            
            # 计算延迟时间
            if self.exponential_backoff:
                delay = self.retry_delay * (2 ** retry_count)
            else:
                delay = self.retry_delay
            
            self.logger.warning(
                f"执行失败，将在{delay}秒后重试 "
                f"(第{retry_count + 1}/{self.max_retries}次): {error}"
            )
            
            # 等待后重试
            await asyncio.sleep(delay)
            
            # 返回None表示需要重试（由executor处理）
            return None
        
        else:
            # 达到最大重试次数
            self.logger.error(
                f"达到最大重试次数({self.max_retries})，放弃重试: {error}"
            )
            
            # 清除重试计数
            self._retry_counts.pop(session_key, None)
            
            # 返回错误结果
            return {
                'success': False,
                'content': '',
                'error': f"执行失败（已重试{self.max_retries}次）: {error}",
                'retry_count': self.max_retries,
            }
