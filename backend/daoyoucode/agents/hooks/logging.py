"""
日志Hook

记录Skill执行的详细日志
"""

from ..core.hook import BaseHook, HookContext
from typing import Dict, Any, Optional
import logging
import time

logger = logging.getLogger(__name__)


class LoggingHook(BaseHook):
    """日志Hook"""
    
    def __init__(self):
        super().__init__("logging")
        self._start_times: Dict[str, float] = {}
    
    async def on_before_execute(
        self,
        context: HookContext
    ) -> HookContext:
        """执行前记录日志"""
        session_key = f"{context.session_id}_{context.skill_name}"
        self._start_times[session_key] = time.time()
        
        self.logger.info(
            f"开始执行Skill: {context.skill_name}, "
            f"session: {context.session_id}, "
            f"input: {context.user_input[:50]}..."
        )
        
        return context
    
    async def on_after_execute(
        self,
        context: HookContext,
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行后记录日志"""
        session_key = f"{context.session_id}_{context.skill_name}"
        start_time = self._start_times.pop(session_key, None)
        
        if start_time:
            duration = time.time() - start_time
            self.logger.info(
                f"Skill执行完成: {context.skill_name}, "
                f"耗时: {duration:.2f}s, "
                f"成功: {result.get('success', False)}"
            )
        
        return result
    
    async def on_error(
        self,
        context: HookContext,
        error: Exception
    ) -> Optional[Dict[str, Any]]:
        """错误时记录日志"""
        self.logger.error(
            f"Skill执行失败: {context.skill_name}, "
            f"错误: {error}",
            exc_info=True
        )
        
        # 不处理错误，继续抛出
        return None
