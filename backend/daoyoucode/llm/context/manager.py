"""
上下文管理器
整合追问判断和记忆管理
"""

from typing import Dict, List, Tuple, Optional, Any
import logging

from .followup_detector import get_followup_detector
from .memory_manager import get_memory_manager

logger = logging.getLogger(__name__)


class ContextManager:
    """
    上下文管理器
    
    职责：
    1. 管理对话历史（短期记忆）
    2. 判断追问（智能判断）
    3. 提供上下文（格式化）
    """
    
    def __init__(self):
        self.followup_detector = get_followup_detector()
        self.memory_manager = get_memory_manager()
        
        logger.info("上下文管理器已初始化")
    
    async def add_conversation(
        self,
        session_id: str,
        user_message: str,
        ai_response: str,
        skill_name: Optional[str] = None,
        model: Optional[str] = None
    ):
        """
        添加一轮对话
        
        Args:
            session_id: 会话ID
            user_message: 用户消息
            ai_response: AI响应
            skill_name: 使用的Skill
            model: 使用的模型
        """
        metadata = {}
        if skill_name:
            metadata['skill'] = skill_name
        if model:
            metadata['model'] = model
        
        self.memory_manager.add_message(
            session_id,
            user_message,
            ai_response,
            metadata
        )
        
        logger.debug(f"已添加对话: session={session_id}, skill={skill_name}")
    
    async def is_followup(
        self,
        session_id: str,
        current_message: str,
        skill_name: Optional[str] = None
    ) -> Tuple[bool, float, str]:
        """
        判断是否为追问
        
        Args:
            session_id: 会话ID
            current_message: 当前消息
            skill_name: 当前Skill名称
        
        Returns:
            (is_followup, confidence, reason)
        """
        # 获取历史
        history = self.memory_manager.get_history(session_id)
        
        # 判断追问
        return await self.followup_detector.is_followup(
            current_message,
            history,
            skill_name
        )
    
    def get_history(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        获取对话历史
        
        Args:
            session_id: 会话ID
            limit: 最多返回多少轮
        
        Returns:
            对话历史列表
        """
        return self.memory_manager.get_history(session_id, limit)
    
    def get_context_summary(
        self,
        session_id: str,
        rounds: int = 3
    ) -> str:
        """
        获取上下文摘要（用于追问时的prompt）
        
        Args:
            session_id: 会话ID
            rounds: 最近多少轮
        
        Returns:
            格式化的上下文文本
        """
        return self.memory_manager.get_recent_context(session_id, rounds)
    
    def format_context_for_prompt(
        self,
        session_id: str,
        current_message: str,
        include_history: bool = True,
        history_limit: int = 3
    ) -> str:
        """
        格式化上下文为LLM prompt
        
        Args:
            session_id: 会话ID
            current_message: 当前消息
            include_history: 是否包含历史
            history_limit: 历史轮数限制
        
        Returns:
            格式化的prompt文本
        """
        parts = []
        
        # 1. 历史对话
        if include_history:
            history = self.memory_manager.get_history(session_id, limit=history_limit)
            
            if history:
                history_lines = []
                for idx, item in enumerate(history, 1):
                    history_lines.append(f"[第{idx}轮]")
                    history_lines.append(f"用户: {item['user']}")
                    history_lines.append(f"AI: {item['ai'][:300]}...")
                    history_lines.append("")
                
                parts.append(f"【历史对话】\n" + "\n".join(history_lines))
        
        # 2. 当前问题
        parts.append(f"【当前问题】\n{current_message}")
        
        return "\n\n".join(parts)
    
    def clear_session(self, session_id: str):
        """清除会话"""
        self.memory_manager.clear_session(session_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.memory_manager.get_stats()


def get_context_manager() -> ContextManager:
    """获取上下文管理器单例"""
    if not hasattr(get_context_manager, '_instance'):
        get_context_manager._instance = ContextManager()
    return get_context_manager._instance
