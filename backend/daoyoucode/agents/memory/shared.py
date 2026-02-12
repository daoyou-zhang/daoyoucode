"""
多智能体共享接口
提供便捷的多智能体记忆访问方法
"""

from typing import Dict, List, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .manager import MemoryManager


class SharedMemoryInterface:
    """
    多智能体共享记忆接口
    
    用于多智能体协作时的记忆共享
    """
    
    def __init__(self, memory: 'MemoryManager', session_id: str, agent_names: List[str]):
        self.memory = memory
        self.session_id = session_id
        self.agent_names = agent_names
    
    def get_context(self) -> Dict[str, Any]:
        """获取共享上下文"""
        return self.memory.get_shared_context(
            self.session_id,
            self.agent_names
        )
    
    def set_shared(self, key: str, value: Any):
        """设置共享数据（所有Agent可见）"""
        self.memory.update_shared_context(
            self.session_id,
            'shared',
            key,
            value
        )
    
    def set_agent_data(self, agent_name: str, key: str, value: Any):
        """设置Agent私有数据"""
        if agent_name not in self.agent_names:
            raise ValueError(f"Agent {agent_name} not in session")
        
        self.memory.update_shared_context(
            self.session_id,
            agent_name,
            key,
            value
        )
    
    def get_shared(self, key: str, default=None) -> Any:
        """获取共享数据"""
        ctx = self.get_context()
        return ctx.get('shared', {}).get(key, default)
    
    def get_agent_data(self, agent_name: str, key: str, default=None) -> Any:
        """获取Agent私有数据"""
        ctx = self.get_context()
        return ctx.get(agent_name, {}).get(key, default)
