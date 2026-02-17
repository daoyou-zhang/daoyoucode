"""
上下文管理中间件
"""

from typing import Dict, Any
from ..core.middleware import BaseMiddleware


class ContextMiddleware(BaseMiddleware):
    """上下文管理中间件（使用记忆系统）"""
    
    async def process(
        self,
        user_input: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """处理上下文管理"""
        try:
            # 使用已有的记忆管理系统
            from ..memory import get_memory_manager
            
            memory = get_memory_manager()
            session_id = context.get('session_id')
            
            if not session_id:
                self.logger.warning("未提供session_id")
                return context
            
            # 获取历史对话（最近5轮）
            history = memory.get_conversation_history(session_id, limit=5)
            if history:
                context['history'] = history
                self.logger.info(f"已加载历史: {len(history)} 轮")
            
            # 如果是追问，可以加载更多上下文
            if context.get('is_followup'):
                # 加载更多历史
                extended_history = memory.get_conversation_history(session_id, limit=10)
                context['extended_history'] = extended_history
                self.logger.info(f"追问模式：已加载扩展历史: {len(extended_history)} 轮")
        
        except Exception as e:
            self.logger.error(f"上下文管理失败: {e}")
            context['history'] = []
        
        return context
