"""
记忆存储
负责实际的数据存储和检索
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class MemoryStorage:
    """
    记忆存储
    
    存储结构：
    1. 对话历史：按session_id存储
    2. 用户偏好：按user_id存储
    3. 任务历史：按user_id存储
    4. 共享上下文：按session_id存储（多智能体）
    """
    
    def __init__(
        self,
        max_conversations: int = 10,
        max_tasks: int = 100,
        max_sessions: int = 1000
    ):
        # 对话历史
        self._conversations: Dict[str, List[Dict]] = {}
        
        # 用户偏好
        self._preferences: Dict[str, Dict[str, Any]] = {}
        
        # 任务历史
        self._tasks: Dict[str, List[Dict]] = {}
        
        # 共享上下文（多智能体）
        self._shared_contexts: Dict[str, Dict[str, Any]] = {}
        
        # 配置
        self.max_conversations = max_conversations
        self.max_tasks = max_tasks
        self.max_sessions = max_sessions
        
        logger.info("记忆存储已初始化")
    
    # ========== 对话历史 ==========
    
    def add_conversation(
        self,
        session_id: str,
        user_message: str,
        ai_response: str,
        metadata: Optional[Dict] = None
    ):
        """添加对话"""
        if session_id not in self._conversations:
            self._conversations[session_id] = []
        
        self._conversations[session_id].append({
            'user': user_message,
            'ai': ai_response,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        })
        
        # 保持最近N轮
        if len(self._conversations[session_id]) > self.max_conversations:
            self._conversations[session_id] = \
                self._conversations[session_id][-self.max_conversations:]
    
    def get_conversation_history(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """获取对话历史"""
        history = self._conversations.get(session_id, [])
        
        if limit is None:
            return history
        
        return history[-limit:]
    
    # ========== 用户偏好 ==========
    
    def add_preference(
        self,
        user_id: str,
        key: str,
        value: Any
    ):
        """添加用户偏好"""
        if user_id not in self._preferences:
            self._preferences[user_id] = {}
        
        self._preferences[user_id][key] = {
            'value': value,
            'timestamp': datetime.now().isoformat(),
            'count': self._preferences[user_id].get(key, {}).get('count', 0) + 1
        }
    
    def get_preferences(self, user_id: str) -> Dict[str, Any]:
        """获取用户偏好"""
        prefs = self._preferences.get(user_id, {})
        
        # 只返回value
        return {
            key: data['value']
            for key, data in prefs.items()
        }
    
    # ========== 任务历史 ==========
    
    def add_task(
        self,
        user_id: str,
        task: Dict[str, Any]
    ):
        """添加任务"""
        if user_id not in self._tasks:
            self._tasks[user_id] = []
        
        self._tasks[user_id].append({
            **task,
            'timestamp': datetime.now().isoformat()
        })
        
        # 保持最近N个任务
        if len(self._tasks[user_id]) > self.max_tasks:
            self._tasks[user_id] = self._tasks[user_id][-self.max_tasks:]
    
    def get_task_history(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """获取任务历史"""
        tasks = self._tasks.get(user_id, [])
        return tasks[-limit:]
    
    # ========== 多智能体共享上下文 ==========
    
    def get_shared_context(
        self,
        session_id: str,
        agent_names: List[str]
    ) -> Dict[str, Any]:
        """
        获取多智能体共享上下文
        
        返回格式：
        {
            'agent1': {'key1': 'value1', ...},
            'agent2': {'key2': 'value2', ...},
            'shared': {'shared_key': 'shared_value', ...}
        }
        """
        if session_id not in self._shared_contexts:
            self._shared_contexts[session_id] = {
                'shared': {},  # 所有Agent共享的数据
                'agents': defaultdict(dict)  # 每个Agent的私有数据
            }
        
        ctx = self._shared_contexts[session_id]
        
        # 构建返回结果
        result = {
            'shared': ctx['shared'].copy()
        }
        
        for agent_name in agent_names:
            result[agent_name] = ctx['agents'][agent_name].copy()
        
        return result
    
    def update_shared_context(
        self,
        session_id: str,
        agent_name: str,
        key: str,
        value: Any
    ):
        """更新共享上下文"""
        if session_id not in self._shared_contexts:
            self._shared_contexts[session_id] = {
                'shared': {},
                'agents': defaultdict(dict)
            }
        
        # 如果agent_name是'shared'，更新共享数据
        if agent_name == 'shared':
            self._shared_contexts[session_id]['shared'][key] = value
        else:
            # 否则更新Agent私有数据
            self._shared_contexts[session_id]['agents'][agent_name][key] = value
    
    # ========== 工具方法 ==========
    
    def clear_session(self, session_id: str):
        """清除会话"""
        if session_id in self._conversations:
            del self._conversations[session_id]
        
        if session_id in self._shared_contexts:
            del self._shared_contexts[session_id]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_conversations = sum(
            len(convs) for convs in self._conversations.values()
        )
        
        total_tasks = sum(
            len(tasks) for tasks in self._tasks.values()
        )
        
        return {
            'total_sessions': len(self._conversations),
            'total_conversations': total_conversations,
            'total_users': len(self._preferences),
            'total_tasks': total_tasks,
            'shared_contexts': len(self._shared_contexts)
        }
