"""
上下文管理中间件
"""

from typing import Dict, Any
from ..core.middleware import BaseMiddleware


class ContextMiddleware(BaseMiddleware):
    """上下文管理中间件"""
    
    async def process(
        self,
        user_input: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """处理上下文管理"""
        try:
            from ..core.context import ContextManager
            
            manager = ContextManager()
            session_id = context.get('session_id')
            
            if not session_id:
                self.logger.warning("未提供session_id")
                return context
            
            # 获取历史对话
            history = manager.get_history(session_id)
            context['history'] = history
            
            # 如果是追问，获取摘要
            if context.get('is_followup'):
                summary = manager.get_context_summary(session_id, rounds=3)
                context['history_summary'] = summary
                self.logger.info(f"已加载历史摘要")
            else:
                self.logger.info(f"已加载历史: {len(history)} 条")
        
        except Exception as e:
            self.logger.error(f"上下文管理失败: {e}")
            context['history'] = []
        
        return context
