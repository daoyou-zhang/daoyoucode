"""
追问判断中间件
"""

from typing import Dict, Any
from ..core.middleware import BaseMiddleware


class FollowupMiddleware(BaseMiddleware):
    """追问判断中间件"""
    
    async def process(
        self,
        user_input: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """处理追问判断"""
        try:
            from ...llm.context import get_followup_detector
            
            detector = get_followup_detector()
            history = context.get('history', [])
            
            is_followup, confidence, reason = await detector.is_followup(
                user_input,
                history
            )
            
            context['is_followup'] = is_followup
            context['followup_confidence'] = confidence
            context['followup_reason'] = reason
            
            self.logger.info(
                f"追问判断: is_followup={is_followup}, "
                f"confidence={confidence:.2f}"
            )
        
        except Exception as e:
            self.logger.error(f"追问判断失败: {e}")
            context['is_followup'] = False
            context['followup_confidence'] = 0.0
        
        return context
