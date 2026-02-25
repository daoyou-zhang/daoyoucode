"""
记忆存储（统一版本）

支持分层存储：
- 用户级（~/.daoyoucode/）：用户画像、全局偏好（跨项目）
- 项目级（[project]/.daoyoucode/）：项目上下文、对话历史（项目独立）
- 会话级（内存）：对话历史、临时数据（临时）

向后兼容：
- 自动从旧位置（~/.daoyoucode/memory/）迁移数据
- 保持原有 API 不变
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path
import json
import logging
import yaml

logger = logging.getLogger(__name__)


class MemoryStorage:
    """
    记忆存储（统一版本）
    
    三层架构：
    1. 用户级（~/.daoyoucode/）- 跨项目
    2. 项目级（[project]/.daoyoucode/）- 项目独立
    3. 会话级（内存）- 临时
    """
    
    def __init__(
        self,
        max_conversations: int = 10,
        max_tasks: int = 100,
        max_sessions: int = 1000,
        storage_dir: Optional[str] = None,
        project_path: Optional[Path] = None
    ):
        # 会话级存储（内存，临时）
        self._conversations: Dict[str, List[Dict]] = {}
        self._shared_contexts: Dict[str, Dict[str, Any]] = {}
        
        # 配置
        self.max_conversations = max_conversations
        self.max_tasks = max_tasks
        self.max_sessions = max_sessions
        
        # ========== 用户级存储目录 ==========
        if storage_dir is None:
            storage_dir = str(Path.home() / '.daoyoucode')
        
        self.user_dir = Path(storage_dir)
        self.user_dir.mkdir(parents=True, exist_ok=True)
        
        # ========== 项目级存储目录 ==========
        self.project_dir = None
        if project_path:
            self.project_dir = project_path / '.daoyoucode'
            self.project_dir.mkdir(parents=True, exist_ok=True)
        
        # 用户级文件路径
        self._preferences_file = self.user_dir / 'preferences.json'
        self._profiles_file = self.user_dir / 'user_profile.json'
        self._user_sessions_file = self.user_dir / 'user_sessions.json'
        self._tasks_file = self.user_dir / 'tasks.json'  # 🆕 任务历史（用户级）
        
        # 项目级文件路径（如果有项目）
        if self.project_dir:
            self._summaries_file = self.project_dir / 'summaries.json'
            self._key_info_file = self.project_dir / 'key_info.json'
            self._project_context_file = self.project_dir / 'project_context.json'
            self._chat_history_file = self.project_dir / 'chat.history.md'
        else:
            # 回退到用户目录（向后兼容）
            self._summaries_file = self.user_dir / 'summaries.json'
            self._key_info_file = self.user_dir / 'key_info.json'
            self._project_context_file = None
            self._chat_history_file = None
        
        # 数据缓存
        self._preferences: Dict[str, Dict[str, Any]] = {}
        self._user_profiles: Dict[str, Dict[str, Any]] = {}
        self._user_sessions: Dict[str, List[str]] = defaultdict(list)
        self._session_users: Dict[str, str] = {}
        self._summaries: Dict[str, str] = {}
        self._key_info: Dict[str, Dict[str, Any]] = {}
        self._tasks: Dict[str, List[Dict]] = {}  # 已废弃，仅用于迁移
        
        # 加载持久化数据
        self._load_persistent_data()
        
        # 自动迁移旧数据
        self._migrate_old_data()
        
        logger.info(
            f"记忆存储已初始化 | "
            f"用户级: {self.user_dir} | "
            f"项目级: {self.project_dir or '未设置'}"
        )
    
    # ========== 对话历史（会话级，内存）==========
    
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
        
        # 🆕 同时保存到项目级对话历史（Markdown格式）
        if self._chat_history_file:
            self._append_chat_history(user_message, ai_response, metadata)
    
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
    
    def _append_chat_history(self, user_message: str, ai_response: str, metadata: Optional[Dict] = None):
        """追加对话历史到 Markdown 文件"""
        if not self._chat_history_file:
            return
        
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            content = f"\n## {timestamp}\n\n"
            content += f"**User**: {user_message}\n\n"
            content += f"**AI**: {ai_response}\n\n"
            
            if metadata:
                content += f"*Metadata*: {json.dumps(metadata, ensure_ascii=False)}\n\n"
            
            content += "---\n"
            
            with open(self._chat_history_file, 'a', encoding='utf-8') as f:
                f.write(content)
            
            # 检查文件大小
            self._check_chat_history_size()
        except Exception as e:
            logger.error(f"追加对话历史失败: {e}")
    
    def _check_chat_history_size(self):
        """检查对话历史文件大小"""
        if not self._chat_history_file or not self._chat_history_file.exists():
            return
        
        try:
            size_mb = self._chat_history_file.stat().st_size / (1024 * 1024)
            if size_mb > 10:  # 超过10MB
                logger.warning(f"对话历史文件过大 ({size_mb:.2f} MB)，执行清理")
                self._cleanup_chat_history()
        except Exception as e:
            logger.error(f"检查对话历史大小失败: {e}")
    
    def _cleanup_chat_history(self):
        """清理对话历史（归档旧数据）"""
        if not self._chat_history_file:
            return
        
        try:
            with open(self._chat_history_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            sections = content.split('## ')
            cutoff_date = datetime.now() - timedelta(days=30)
            
            recent_sections = []
            archived_sections = []
            
            for section in sections:
                if not section.strip():
                    continue
                
                try:
                    date_str = section.split('\n')[0].strip()
                    date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                    
                    if date >= cutoff_date:
                        recent_sections.append('## ' + section)
                    else:
                        archived_sections.append('## ' + section)
                except:
                    recent_sections.append('## ' + section)
            
            # 归档
            if archived_sections and self.project_dir:
                archive_dir = self.project_dir / 'archive'
                archive_dir.mkdir(exist_ok=True)
                
                archive_file = archive_dir / f'chat.history.{datetime.now().strftime("%Y%m%d")}.md'
                with open(archive_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(archived_sections))
                
                logger.info(f"归档了 {len(archived_sections)} 条旧对话")
            
            # 保存最近的
            with open(self._chat_history_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(recent_sections))
        
        except Exception as e:
            logger.error(f"清理对话历史失败: {e}")
    
    # ========== 用户偏好（用户级）==========
    
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
    
    # ========== 任务历史（用户级）==========
    
    def add_task(
        self,
        user_id: str,
        task: Dict[str, Any]
    ):
        """
        添加任务到历史
        
        Args:
            user_id: 用户ID
            task: 任务信息
        """
        if user_id not in self._tasks:
            self._tasks[user_id] = []
        
        self._tasks[user_id].append({
            **task,
            'timestamp': datetime.now().isoformat()
        })
        
        # 保持最近N个任务
        if len(self._tasks[user_id]) > self.max_tasks:
            self._tasks[user_id] = self._tasks[user_id][-self.max_tasks:]
        
        # 🆕 持久化到用户级（任务历史是跨项目的）
        self._save_tasks()
    
    def get_task_history(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        获取任务历史
        
        Args:
            user_id: 用户ID
            limit: 限制数量
        
        Returns:
            任务历史列表
        """
        tasks = self._tasks.get(user_id, [])
        return tasks[-limit:]
    
    # ========== 项目上下文（项目级）==========
    
    def save_project_context(self, context: Dict[str, Any]):
        """保存项目上下文"""
        if not self._project_context_file:
            logger.warning("项目目录未设置，无法保存项目上下文")
            return
        
        try:
            with open(self._project_context_file, 'w', encoding='utf-8') as f:
                json.dump(context, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存项目上下文失败: {e}")
    
    def get_project_context(self) -> Optional[Dict[str, Any]]:
        """获取项目上下文"""
        if not self._project_context_file or not self._project_context_file.exists():
            return None
        
        try:
            with open(self._project_context_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"获取项目上下文失败: {e}")
            return None
    
    # ========== 多智能体共享上下文（会话级，内存）==========
    
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
    
    # ========== 摘要管理（项目级）==========
    
    def save_summary(self, session_id: str, summary: str):
        """保存对话摘要"""
        self._summaries[session_id] = summary
        # 持久化
        self._save_summaries()
    
    def get_summary(self, session_id: str) -> Optional[str]:
        """获取对话摘要"""
        return self._summaries.get(session_id)
    
    # ========== 关键信息管理（项目级）==========
    
    def save_key_info(self, session_id: str, key_info: Dict[str, Any]):
        """保存关键信息"""
        self._key_info[session_id] = key_info
        # 持久化
        self._save_key_info()
    
    def get_key_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取关键信息"""
        return self._key_info.get(session_id)
    
    # ========== 用户画像管理（用户级）==========
    
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
        
        return {
            'total_sessions': len(self._conversations),
            'total_conversations': total_conversations,
            'total_users': len(self._preferences),
            'total_tasks': sum(len(tasks) for tasks in self._tasks.values()),
            'shared_contexts': len(self._shared_contexts),
            'summaries': len(self._summaries),
            'key_info': len(self._key_info),
            'user_profiles': len(self._user_profiles),
            'storage': {
                'user_dir': str(self.user_dir),
                'project_dir': str(self.project_dir) if self.project_dir else None
            }
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
            
            # 🆕 加载任务历史
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
        
        except Exception as e:
            logger.warning(f"加载持久化数据失败: {e}")
    
    def _migrate_old_data(self):
        """从旧位置迁移数据"""
        old_memory_dir = Path.home() / '.daoyoucode' / 'memory'
        
        if not old_memory_dir.exists():
            return
        
        logger.info(f"检测到旧数据目录: {old_memory_dir}，开始迁移...")
        
        try:
            # 迁移用户画像
            old_profiles = old_memory_dir / 'profiles.json'
            if old_profiles.exists() and not self._profiles_file.exists():
                import shutil
                shutil.copy(str(old_profiles), str(self._profiles_file))
                logger.info(f"✓ 迁移用户画像")
            
            # 迁移用户偏好
            old_prefs = old_memory_dir / 'preferences.json'
            if old_prefs.exists() and not self._preferences_file.exists():
                import shutil
                shutil.copy(str(old_prefs), str(self._preferences_file))
                logger.info(f"✓ 迁移用户偏好")
            
            # 迁移用户会话映射
            old_sessions = old_memory_dir / 'user_sessions.json'
            if old_sessions.exists() and not self._user_sessions_file.exists():
                import shutil
                shutil.copy(str(old_sessions), str(self._user_sessions_file))
                logger.info(f"✓ 迁移用户会话映射")
            
            # 归档旧目录
            archive_dir = Path.home() / '.daoyoucode' / 'archive'
            archive_dir.mkdir(exist_ok=True)
            
            import shutil
            archive_path = archive_dir / f'memory_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
            shutil.move(str(old_memory_dir), str(archive_path))
            
            logger.info(f"✓ 旧数据已归档到: {archive_path}")
        
        except Exception as e:
            logger.error(f"数据迁移失败: {e}")
    
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
