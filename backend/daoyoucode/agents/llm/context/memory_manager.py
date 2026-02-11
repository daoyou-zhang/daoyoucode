"""
记忆管理器
管理短期记忆（最近对话）和长期记忆（摘要、关键信息）
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    记忆管理器
    
    功能：
    1. 短期记忆：最近N轮对话（内存）
    2. 长期记忆：对话摘要（可选，需要LLM）
    3. 会话管理：按session_id隔离
    """
    
    def __init__(self, max_history: int = 10, max_sessions: int = 1000):
        """
        初始化记忆管理器
        
        Args:
            max_history: 每个session最多保存多少轮对话
            max_sessions: 最多保存多少个session
        """
        self.max_history = max_history
        self.max_sessions = max_sessions
        
        # 内存存储
        # 格式: {session_id: {'history': [...], 'metadata': {...}, 'last_access': datetime}}
        self._sessions: Dict[str, Dict[str, Any]] = {}
        
        logger.info(f"记忆管理器已初始化: max_history={max_history}, max_sessions={max_sessions}")
    
    def add_message(
        self,
        session_id: str,
        user_message: str,
        ai_response: str,
        metadata: Optional[Dict] = None
    ):
        """
        添加一轮对话
        
        Args:
            session_id: 会话ID
            user_message: 用户消息
            ai_response: AI响应
            metadata: 元数据（skill、model等）
        """
        # 初始化session
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                'history': [],
                'metadata': {},
                'last_access': datetime.now()
            }
        
        # 添加对话
        self._sessions[session_id]['history'].append({
            'user': user_message,
            'ai': ai_response,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        })
        
        # 保持最近N轮
        if len(self._sessions[session_id]['history']) > self.max_history:
            self._sessions[session_id]['history'] = \
                self._sessions[session_id]['history'][-self.max_history:]
        
        # 更新最后访问时间
        self._sessions[session_id]['last_access'] = datetime.now()
        
        # 清理过期session
        self._cleanup_old_sessions()
    
    def get_history(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        获取对话历史
        
        Args:
            session_id: 会话ID
            limit: 最多返回多少轮（None表示全部）
        
        Returns:
            对话历史列表
        """
        if session_id not in self._sessions:
            return []
        
        history = self._sessions[session_id]['history']
        
        if limit is None:
            return history
        
        return history[-limit:]
    
    def get_recent_context(
        self,
        session_id: str,
        rounds: int = 3
    ) -> str:
        """
        获取最近N轮对话的文本摘要
        
        Args:
            session_id: 会话ID
            rounds: 最近多少轮
        
        Returns:
            格式化的对话文本
        """
        history = self.get_history(session_id, limit=rounds)
        
        if not history:
            return ""
        
        lines = []
        for idx, item in enumerate(history, 1):
            lines.append(f"[第{idx}轮]")
            lines.append(f"用户: {item['user']}")
            lines.append(f"AI: {item['ai'][:200]}...")  # 限制长度
            lines.append("")
        
        return "\n".join(lines)
    
    def clear_session(self, session_id: str):
        """清除会话"""
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info(f"已清除会话: {session_id}")
    
    def get_session_count(self) -> int:
        """获取当前session数量"""
        return len(self._sessions)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_messages = sum(
            len(session['history'])
            for session in self._sessions.values()
        )
        
        return {
            'total_sessions': len(self._sessions),
            'total_messages': total_messages,
            'max_history': self.max_history,
            'max_sessions': self.max_sessions
        }
    
    def _cleanup_old_sessions(self):
        """清理旧session（超过最大数量时）"""
        if len(self._sessions) <= self.max_sessions:
            return
        
        # 按最后访问时间排序
        sorted_sessions = sorted(
            self._sessions.items(),
            key=lambda x: x[1]['last_access']
        )
        
        # 删除最旧的session
        to_delete = len(self._sessions) - self.max_sessions
        for session_id, _ in sorted_sessions[:to_delete]:
            del self._sessions[session_id]
            logger.debug(f"清理旧session: {session_id}")


def get_memory_manager() -> MemoryManager:
    """获取记忆管理器单例"""
    if not hasattr(get_memory_manager, '_instance'):
        get_memory_manager._instance = MemoryManager()
    return get_memory_manager._instance
