"""
输入验证Hook

验证用户输入的合法性
"""

from ..core.hook import BaseHook, HookContext
from typing import Dict, Any, Optional


class ValidationHook(BaseHook):
    """输入验证Hook"""
    
    def __init__(
        self,
        min_length: int = 1,
        max_length: int = 10000,
        forbidden_words: Optional[list] = None
    ):
        super().__init__("validation")
        self.min_length = min_length
        self.max_length = max_length
        self.forbidden_words = forbidden_words or []
    
    async def on_before_execute(
        self,
        context: HookContext
    ) -> HookContext:
        """验证输入"""
        user_input = context.user_input
        
        # 检查长度
        if len(user_input) < self.min_length:
            raise ValueError(
                f"输入太短，最少需要{self.min_length}个字符"
            )
        
        if len(user_input) > self.max_length:
            raise ValueError(
                f"输入太长，最多允许{self.max_length}个字符"
            )
        
        # 检查空白
        if not user_input.strip():
            raise ValueError("输入不能为空")
        
        # 检查禁用词
        for word in self.forbidden_words:
            if word.lower() in user_input.lower():
                raise ValueError(f"输入包含禁用词: {word}")
        
        self.logger.debug(f"输入验证通过: {user_input[:50]}...")
        
        return context
    
    async def on_after_execute(
        self,
        context: HookContext,
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """验证输出"""
        # 检查结果格式
        if not isinstance(result, dict):
            self.logger.warning("结果不是字典格式")
        
        if 'success' not in result:
            self.logger.warning("结果缺少success字段")
        
        if 'content' not in result:
            self.logger.warning("结果缺少content字段")
        
        return result
    
    async def on_error(
        self,
        context: HookContext,
        error: Exception
    ) -> Optional[Dict[str, Any]]:
        """错误处理"""
        # 如果是验证错误，返回友好的错误信息
        if isinstance(error, ValueError):
            return {
                'success': False,
                'content': '',
                'error': str(error),
                'error_type': 'validation_error'
            }
        
        return None
