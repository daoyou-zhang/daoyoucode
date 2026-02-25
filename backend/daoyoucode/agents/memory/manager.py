"""
统一的记忆管理器
整合所有记忆功能
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

from .storage import MemoryStorage
from .detector import FollowupDetector
from .shared import SharedMemoryInterface
from ..core.cache import get_profile_cache, get_summary_cache, get_history_cache, get_preference_cache

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
    6. 缓存层（减少文件I/O）
    """
    
    def __init__(self, enable_tree: bool = True, project_path: Optional[Path] = None):
        """
        初始化记忆管理器
        
        Args:
            enable_tree: 是否启用对话树（默认启用）
            project_path: 项目路径（用于项目级存储）
        """
        self.storage = MemoryStorage(project_path=project_path)
        self.detector = FollowupDetector()
        
        # ========== 缓存层 ==========
        self.profile_cache = get_profile_cache()
        self.summary_cache = get_summary_cache()
        self.history_cache = get_history_cache()
        self.preference_cache = get_preference_cache()
        
        # ========== 新增：长期记忆和智能加载 ==========
        from .long_term_memory import LongTermMemory
        from .smart_loader import SmartLoader
        
        self.long_term_memory = LongTermMemory(storage=self.storage)
        self.smart_loader = SmartLoader(enable_tree=enable_tree)
        
        # ========== 对话树（可选）==========
        self.enable_tree = enable_tree
        self._conversation_tree = None
        
        if enable_tree:
            from .conversation_tree import get_conversation_tree
            self._conversation_tree = get_conversation_tree(enabled=True)
            logger.info("记忆管理器已初始化（增强版 + 对话树 + 缓存层）")
        else:
            logger.info("记忆管理器已初始化（增强版 + 缓存层）")
    
    # ========== LLM层记忆（对话历史）==========
    
    def add_conversation(
        self,
        session_id: str,
        user_message: str,
        ai_response: str,
        metadata: Optional[Dict] = None,
        user_id: Optional[str] = None
    ):
        """
        添加对话
        
        Args:
            session_id: 会话ID
            user_message: 用户消息
            ai_response: AI响应
            metadata: 元数据
            user_id: 用户ID（可选，用于维护映射）
        """
        # 如果启用了对话树，先添加到树中
        if self.enable_tree and self._conversation_tree:
            node = self._conversation_tree.add_conversation(
                user_message=user_message,
                ai_response=ai_response,
                detect_topic_switch=True
            )
            
            # 使用树节点的元数据
            if metadata is None:
                metadata = {}
            metadata.update(node.to_dict()['metadata'])
        
        # 添加到存储
        self.storage.add_conversation(
            session_id,
            user_message,
            ai_response,
            metadata,
            user_id=user_id
        )
        
        # 清除历史缓存（因为数据已更新）
        # 清除所有相关的缓存键
        for limit in [None, 1, 2, 3, 5, 10]:
            cache_key = f"{session_id}:{limit or 'all'}"
            self.history_cache.delete(cache_key)
    
    def get_conversation_history(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        获取对话历史（带缓存）
        
        Args:
            session_id: 会话ID
            limit: 限制数量
        
        Returns:
            对话历史列表
        """
        # 构建缓存键
        cache_key = f"{session_id}:{limit or 'all'}"
        
        # 尝试从缓存获取
        cached = self.history_cache.get(cache_key)
        if cached is not None:
            logger.debug(f"历史缓存命中: {session_id}")
            return cached
        
        # 从存储获取
        history = self.storage.get_conversation_history(session_id, limit)
        
        # 缓存结果（TTL: 5分钟）
        self.history_cache.set(cache_key, history, ttl=300)
        
        return history
    
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
        """
        记住用户偏好
        
        Args:
            user_id: 用户ID
            key: 偏好键
            value: 偏好值
        """
        self.storage.add_preference(user_id, key, value)
        
        # 清除偏好缓存（因为数据已更新）
        self.preference_cache.delete(user_id)
    
    def get_preferences(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        获取用户偏好（带缓存）
        
        Args:
            user_id: 用户ID
        
        Returns:
            用户偏好字典
        """
        # 尝试从缓存获取
        cached = self.preference_cache.get(user_id)
        if cached is not None:
            logger.debug(f"偏好缓存命中: {user_id}")
            return cached
        
        # 从存储获取
        prefs = self.storage.get_preferences(user_id)
        
        # 缓存结果（TTL: 1小时）
        self.preference_cache.set(user_id, prefs, ttl=3600)
        
        return prefs
    
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
    
    # ========== 用户会话映射 ==========
    
    def get_user_sessions(self, user_id: str) -> List[str]:
        """
        获取用户的所有会话ID
        
        Args:
            user_id: 用户ID
        
        Returns:
            会话ID列表
        """
        return self.storage.get_user_sessions(user_id)
    
    def get_session_user(self, session_id: str) -> Optional[str]:
        """
        获取会话对应的用户ID
        
        Args:
            session_id: 会话ID
        
        Returns:
            用户ID
        """
        return self.storage.get_session_user(session_id)
    
    # ========== 新增：智能加载接口 ==========
    
    async def load_context_smart(
        self,
        session_id: str,
        user_id: str,
        user_input: str,
        is_followup: bool = False,
        confidence: float = 0.0
    ) -> Dict[str, Any]:
        """
        智能加载上下文（核心方法）
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            user_input: 用户输入
            is_followup: 是否为追问
            confidence: 追问置信度
        
        Returns:
            加载的上下文数据
        """
        # 获取历史数量
        history = self.get_conversation_history(session_id)
        history_count = len(history)
        
        # 检查是否有摘要
        has_summary = self.long_term_memory.get_summary(session_id) is not None
        
        # 决定加载策略
        strategy, config = await self.smart_loader.decide_load_strategy(
            is_followup=is_followup,
            confidence=confidence,
            history_count=history_count,
            has_summary=has_summary,
            current_message=user_input
        )
        
        # 加载上下文
        context = await self.smart_loader.load_context(
            strategy_name=strategy,
            strategy_config=config,
            memory_manager=self,
            session_id=session_id,
            user_id=user_id,
            current_message=user_input
        )
        
        return context
    
    def format_context_for_prompt(
        self,
        context: Dict[str, Any],
        current_message: str
    ) -> str:
        """
        格式化上下文为LLM prompt
        
        Args:
            context: 加载的上下文
            current_message: 当前消息
        
        Returns:
            格式化的prompt文本
        """
        return self.smart_loader.format_context_for_prompt(context, current_message)
    
    # ========== 工具方法 ==========
    
    def clear_session(self, session_id: str):
        """清除会话"""
        self.storage.clear_session(session_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = self.storage.get_stats()
        
        # 添加对话树统计
        if self.enable_tree and self._conversation_tree:
            stats['tree'] = self._conversation_tree.get_tree_stats()
        
        return stats


# 单例模式
_memory_manager_instance = None


def get_memory_manager(project_path: Optional[Path] = None, force_new: bool = False) -> MemoryManager:
    """
    获取记忆管理器单例
    
    Args:
        project_path: 项目路径（用于项目级存储）
        force_new: 是否强制创建新实例
    
    Returns:
        MemoryManager实例
    """
    global _memory_manager_instance
    
    if force_new or _memory_manager_instance is None:
        _memory_manager_instance = MemoryManager(project_path=project_path)
        logger.info("记忆管理器单例已创建")
    
    return _memory_manager_instance
