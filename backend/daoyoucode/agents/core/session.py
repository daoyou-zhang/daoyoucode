"""
Agent会话管理

支持会话恢复和上下文保持。
采用智能会话管理设计
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import uuid
import logging

logger = logging.getLogger(__name__)


class AgentSession:
    """Agent会话"""
    
    def __init__(self, session_id: str, agent: Any):
        self.session_id = session_id
        self.agent = agent
        self.history: List[Dict] = []
        self.context: Dict = {}
        self.created_at = datetime.now()
        self.last_used_at = datetime.now()
    
    async def execute(self, instruction: str, **kwargs) -> Dict:
        """在会话中执行指令"""
        self.last_used_at = datetime.now()
        
        # 使用历史上下文
        result = await self.agent.execute(
            instruction,
            history=self.history,
            context=self.context,
            **kwargs
        )
        
        # 更新历史
        self.history.append({
            'instruction': instruction,
            'result': result,
            'timestamp': datetime.now()
        })
        
        return result
    
    def get_age_hours(self) -> float:
        """获取会话年龄（小时）"""
        return (datetime.now() - self.last_used_at).total_seconds() / 3600


class SessionManager:
    """会话管理器（单例）"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.sessions: Dict[str, AgentSession] = {}
        self._initialized = True
        logger.info("SessionManager 初始化完成")
    
    def create_session(
        self,
        agent: Any,
        session_id: Optional[str] = None
    ) -> str:
        """
        创建新会话
        
        Args:
            agent: Agent实例
            session_id: 会话ID（可选）
        
        Returns:
            session_id
        """
        if session_id is None:
            session_id = f"ses_{uuid.uuid4().hex[:8]}"
        
        session = AgentSession(session_id, agent)
        self.sessions[session_id] = session
        
        logger.info(f"创建会话: {session_id}")
        return session_id
    
    async def execute(
        self,
        session_id: str,
        instruction: str,
        **kwargs
    ) -> Dict:
        """
        在会话中执行
        
        Args:
            session_id: 会话ID
            instruction: 指令
            **kwargs: 其他参数
        
        Returns:
            执行结果
        """
        session = self.sessions.get(session_id)
        if not session:
            return {
                'status': 'error',
                'error': f'Session {session_id} not found'
            }
        
        return await session.execute(instruction, **kwargs)
    
    def get_session(self, session_id: str) -> Optional[AgentSession]:
        """获取会话"""
        return self.sessions.get(session_id)
    
    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"删除会话: {session_id}")
            return True
        return False
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """
        清理旧会话
        
        Args:
            max_age_hours: 最大年龄（小时）
        """
        to_remove = []
        
        for session_id, session in self.sessions.items():
            if session.get_age_hours() > max_age_hours:
                to_remove.append(session_id)
        
        for session_id in to_remove:
            del self.sessions[session_id]
        
        if to_remove:
            logger.info(f"清理了 {len(to_remove)} 个旧会话")
    
    def list_sessions(self) -> Dict[str, Dict]:
        """列出所有会话"""
        return {
            session_id: {
                'created_at': session.created_at,
                'last_used_at': session.last_used_at,
                'age_hours': session.get_age_hours(),
                'history_length': len(session.history),
            }
            for session_id, session in self.sessions.items()
        }


def get_session_manager() -> SessionManager:
    """获取会话管理器实例"""
    return SessionManager()
