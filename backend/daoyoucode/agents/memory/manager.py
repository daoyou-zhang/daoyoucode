"""
统一的记忆管理器
整合所有记忆功能
"""

from typing import Dict, List, Optional, Any
import logging

from .storage import MemoryStorage
from .detector import FollowupDetector
from .shared import SharedMemoryInterface

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    统一的记忆管理器
    
    职责：
    1. 管理对话历史（LLM层）
    2. 管理用户偏好（Agent层）
    3. 管理任务历史（Agent层）
    4. 判断追问
    5. 提供多智能体共享接口
    """
    
    def __init__(self):
        self.storage = MemoryStorage()
        self.detector = FollowupDetector()
        
        logger.info("记忆管理器已初始化")
    
    # ========== LLM层记忆（对话历史）==========
    
    def add_conversation(
        self,
        session_id: str,
        user_message: str,
        ai_response: str,
        metadata: Optional[Dict] = None
    ):
        """添加对话"""
        self.storage.add_conversation(
            session_id,
            user_message,
            ai_response,
            metadata
        )
    
    def get_conversation_history(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """获取对话历史"""
        return self.storage.get_conversation_history(session_id, limit)
    
    async def is_followup(
        self,
        session_id: str,
        current_message: str
    ) -> tuple[bool, float, str]:
        """判断是否为追问"""
        history = self.get_conversation_history(session_id)
        return await self.detector.is_followup(current_message, history)
    
    # ========== Agent层记忆（用户偏好）==========
    
    def remember_preference(
        self,
        user_id: str,
        key: str,
        value: Any
    ):
        """记住用户偏好"""
        self.storage.add_preference(user_id, key, value)
    
    def get_preferences(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """获取用户偏好"""
        return self.storage.get_preferences(user_id)
    
    # ========== Agent层记忆（任务历史）==========
    
    def add_task(
        self,
        user_id: str,
        task: Dict[str, Any]
    ):
        """添加任务到历史"""
        self.storage.add_task(user_id, task)
    
    def get_task_history(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """获取任务历史"""
        return self.storage.get_task_history(user_id, limit)
    
    # ========== 多智能体共享接口 ==========
    
    def get_shared_context(
        self,
        session_id: str,
        agent_names: List[str]
    ) -> Dict[str, Any]:
        """
        获取多智能体共享上下文
        
        Args:
            session_id: 会话ID
            agent_names: 参与的Agent名称列表
        
        Returns:
            共享上下文字典
        """
        return self.storage.get_shared_context(session_id, agent_names)
    
    def update_shared_context(
        self,
        session_id: str,
        agent_name: str,
        key: str,
        value: Any
    ):
        """
        更新共享上下文
        
        Args:
            session_id: 会话ID
            agent_name: Agent名称
            key: 键
            value: 值
        """
        self.storage.update_shared_context(
            session_id,
            agent_name,
            key,
            value
        )
    
    def create_shared_memory(
        self,
        session_id: str,
        agent_names: List[str]
    ) -> SharedMemoryInterface:
        """创建共享记忆接口"""
        return SharedMemoryInterface(self, session_id, agent_names)
    
    # ========== 工具方法 ==========
    
    def clear_session(self, session_id: str):
        """清除会话"""
        self.storage.clear_session(session_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.storage.get_stats()


# 单例模式
_memory_manager_instance = None


def get_memory_manager() -> MemoryManager:
    """获取记忆管理器单例"""
    global _memory_manager_instance
    
    if _memory_manager_instance is None:
        _memory_manager_instance = MemoryManager()
        logger.info("记忆管理器单例已创建")
    
    return _memory_manager_instance
