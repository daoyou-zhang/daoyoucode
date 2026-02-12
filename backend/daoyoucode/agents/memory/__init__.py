"""
记忆模块
独立的记忆管理系统
"""

from .manager import MemoryManager, get_memory_manager
from .storage import MemoryStorage
from .detector import FollowupDetector
from .shared import SharedMemoryInterface

__all__ = [
    # 主要接口
    'MemoryManager',
    'get_memory_manager',
    
    # 存储
    'MemoryStorage',
    
    # 追问判断
    'FollowupDetector',
    
    # 多智能体共享
    'SharedMemoryInterface',
]
