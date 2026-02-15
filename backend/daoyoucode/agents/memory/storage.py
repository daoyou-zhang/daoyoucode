"""
记忆存储
负责实际的数据存储和检索

支持持久化：
- 对话历史：内存存储（临时）
- 用户偏好：持久化存储（JSON）
- 任务历史：持久化存储（JSON）
- 摘要：持久化存储（JSON）
- 用户画像：持久化存储（JSON）
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import defaultdict
from pathlib import Path
import json
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
        max_sessions: int = 1000,
        storage_dir: Optional[str] = None
    ):
        # 对话历史（内存存储，临时）
        self._conversations: Dict[str, List[Dict]] = {}
        
        # 用户偏好（持久化）
        self._preferences: Dict[str, Dict[str, Any]] = {}
        
        # 任务历史（持久化）
        self._tasks: Dict[str, List[Dict]] = {}
        
        # 共享上下文（内存存储，临时）
        self._shared_contexts: Dict[str, Dict[str, Any]] = {}
        
        # ========== 新增：长期记忆存储（持久化）==========
        # 对话摘要
        self._summaries: Dict[str, str] = {}
        
        # 关键信息
        self._key_info: Dict[str, Dict[str, Any]] = {}
        
        # 用户画像
        self._user_profiles: Dict[str, Dict[str, Any]] = {}
        
        # ========== 新增：用户会话映射（持久化）==========
        # user_id -> [session_id1, session_id2, ...]
        self._user_sessions: Dict[str, List[str]] = defaultdict(list)
        
        # session_id -> user_id
        self._session_users: Dict[str, str] = {}
        
        # 配置
        self.max_conversations = max_conversations
        self.max_tasks = max_tasks
        self.max_sessions = max_sessions
        
        # ========== 持久化配置 ==========
        if storage_dir is None:
            # 默认存储在用户目录下
            storage_dir = str(Path.home() / '.daoyoucode' / 'memory')
        
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # 持久化文件路径
        self._preferences_file = self.storage_dir / 'preferences.json'
        self._tasks_file = self.storage_dir / 'tasks.json'
        self._summaries_file = self.storage_dir / 'summaries.json'
        self._key_info_file = self.storage_dir / 'key_info.json'
        self._profiles_file = self.storage_dir / 'profiles.json'
        self._user_sessions_file = self.storage_dir / 'user_sessions.json'
        
        # 加载持久化数据
        self._load_persistent_data()
        
        logger.info(f"记忆存储已初始化（持久化目录: {self.storage_dir}）")
    
    # ========== 对话历史 ==========
    
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
            user_id: 用户ID（可选，用于维护user_id到session_id的映射）
        """
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
        
        # 维护user_id到session_id的映射
        if user_id:
            self._register_session(user_id, session_id)
    
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
        
        # 持久化
        self._save_preferences()
    
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
        
        # 持久化
        self._save_tasks()
    
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
    
    # ========== 摘要管理 ==========
    
    def save_summary(self, session_id: str, summary: str):
        """保存对话摘要"""
        self._summaries[session_id] = summary
        # 持久化
        self._save_summaries()
    
    def get_summary(self, session_id: str) -> Optional[str]:
        """获取对话摘要"""
        return self._summaries.get(session_id)
    
    # ========== 关键信息管理 ==========
    
    def save_key_info(self, session_id: str, key_info: Dict[str, Any]):
        """保存关键信息"""
        self._key_info[session_id] = key_info
        # 持久化
        self._save_key_info()
    
    def get_key_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取关键信息"""
        return self._key_info.get(session_id)
    
    # ========== 用户画像管理 ==========
    
    def save_user_profile(self, user_id: str, profile: Dict[str, Any]):
        """保存用户画像"""
        self._user_profiles[user_id] = profile
        # 持久化
        self._save_profiles()
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户画像"""
        return self._user_profiles.get(user_id)
    
    # ========== 用户会话映射 ==========
    
    def _register_session(self, user_id: str, session_id: str):
        """
        注册用户会话映射
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
        """
        # 添加到user_id -> sessions映射
        if session_id not in self._user_sessions[user_id]:
            self._user_sessions[user_id].append(session_id)
        
        # 添加到session_id -> user_id映射
        self._session_users[session_id] = user_id
        
        # 持久化
        self._save_user_sessions()
    
    def get_user_sessions(self, user_id: str) -> List[str]:
        """
        获取用户的所有会话ID
        
        Args:
            user_id: 用户ID
        
        Returns:
            会话ID列表
        """
        return self._user_sessions.get(user_id, [])
    
    def get_session_user(self, session_id: str) -> Optional[str]:
        """
        获取会话对应的用户ID
        
        Args:
            session_id: 会话ID
        
        Returns:
            用户ID，如果不存在返回None
        """
        return self._session_users.get(session_id)
    
    # ========== 工具方法 ==========
    
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
            'shared_contexts': len(self._shared_contexts),
            'summaries': len(self._summaries),
            'key_info': len(self._key_info),
            'user_profiles': len(self._user_profiles)
        }
    
    # ========== 持久化方法 ==========
    
    def _load_persistent_data(self):
        """加载持久化数据"""
        try:
            # 加载用户偏好
            if self._preferences_file.exists():
                with open(self._preferences_file, 'r', encoding='utf-8') as f:
                    self._preferences = json.load(f)
                logger.info(f"加载了 {len(self._preferences)} 个用户的偏好")
            
            # 加载任务历史
            if self._tasks_file.exists():
                with open(self._tasks_file, 'r', encoding='utf-8') as f:
                    self._tasks = json.load(f)
                total_tasks = sum(len(tasks) for tasks in self._tasks.values())
                logger.info(f"加载了 {total_tasks} 个任务")
            
            # 加载摘要
            if self._summaries_file.exists():
                with open(self._summaries_file, 'r', encoding='utf-8') as f:
                    self._summaries = json.load(f)
                logger.info(f"加载了 {len(self._summaries)} 个摘要")
            
            # 加载关键信息
            if self._key_info_file.exists():
                with open(self._key_info_file, 'r', encoding='utf-8') as f:
                    self._key_info = json.load(f)
                logger.info(f"加载了 {len(self._key_info)} 个关键信息")
            
            # 加载用户画像
            if self._profiles_file.exists():
                with open(self._profiles_file, 'r', encoding='utf-8') as f:
                    self._user_profiles = json.load(f)
                logger.info(f"加载了 {len(self._user_profiles)} 个用户画像")
            
            # 加载用户会话映射
            if self._user_sessions_file.exists():
                with open(self._user_sessions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._user_sessions = defaultdict(list, data.get('user_sessions', {}))
                    self._session_users = data.get('session_users', {})
                logger.info(f"加载了 {len(self._user_sessions)} 个用户的会话映射")
        
        except Exception as e:
            logger.warning(f"加载持久化数据失败: {e}")
    
    def _save_preferences(self):
        """保存用户偏好"""
        try:
            with open(self._preferences_file, 'w', encoding='utf-8') as f:
                json.dump(self._preferences, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存用户偏好失败: {e}")
    
    def _save_tasks(self):
        """保存任务历史"""
        try:
            with open(self._tasks_file, 'w', encoding='utf-8') as f:
                json.dump(self._tasks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存任务历史失败: {e}")
    
    def _save_summaries(self):
        """保存摘要"""
        try:
            with open(self._summaries_file, 'w', encoding='utf-8') as f:
                json.dump(self._summaries, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存摘要失败: {e}")
    
    def _save_key_info(self):
        """保存关键信息"""
        try:
            with open(self._key_info_file, 'w', encoding='utf-8') as f:
                json.dump(self._key_info, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存关键信息失败: {e}")
    
    def _save_profiles(self):
        """保存用户画像"""
        try:
            with open(self._profiles_file, 'w', encoding='utf-8') as f:
                json.dump(self._user_profiles, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存用户画像失败: {e}")
    
    def _save_user_sessions(self):
        """保存用户会话映射"""
        try:
            data = {
                'user_sessions': dict(self._user_sessions),
                'session_users': self._session_users
            }
            with open(self._user_sessions_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存用户会话映射失败: {e}")
