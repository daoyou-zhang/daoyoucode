"""
记忆模块
独立的记忆管理系统

提供完整的记忆管理功能：
1. LLM层记忆：对话历史
2. Agent层记忆：用户偏好、任务历史
3. 长期记忆：摘要、关键信息、用户画像
4. 智能加载：按需加载，节省token
5. 多智能体共享：跨Agent的记忆共享
6. 用户管理：用户ID生成和管理
7. 对话树：分支管理、话题切换
"""

from .manager import MemoryManager, get_memory_manager
from .storage import MemoryStorage
from .detector import FollowupDetector
from .shared import SharedMemoryInterface
from .long_term_memory import LongTermMemory, get_long_term_memory
from .smart_loader import SmartLoader, get_smart_loader
from .vector_retriever import VectorRetriever, get_vector_retriever
from .user_manager import UserManager, get_user_manager, get_current_user_id
from .conversation_tree import ConversationTree, get_conversation_tree
from .bm25_matcher import BM25Matcher, get_bm25_matcher

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
    
    # 长期记忆
    'LongTermMemory',
    'get_long_term_memory',
    
    # 智能加载
    'SmartLoader',
    'get_smart_loader',
    
    # 向量检索（可选）
    'VectorRetriever',
    'get_vector_retriever',
    
    # 用户管理
    'UserManager',
    'get_user_manager',
    'get_current_user_id',
    
    # 对话树
    'ConversationTree',
    'get_conversation_tree',
    
    # BM25匹配
    'BM25Matcher',
    'get_bm25_matcher',
]
