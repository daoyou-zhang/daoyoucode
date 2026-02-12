"""
上下文管理器

提供结构化的上下文管理，支持：
1. 上下文生命周期管理
2. 上下文版本控制（快照和回滚）
3. 上下文变量追踪
4. 上下文历史记录
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from copy import deepcopy
import uuid
import logging

logger = logging.getLogger(__name__)


@dataclass
class ContextSnapshot:
    """上下文快照"""
    id: str
    variables: Dict[str, Any]
    timestamp: datetime
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'variables': self.variables,
            'timestamp': self.timestamp.isoformat(),
            'description': self.description
        }


@dataclass
class ContextChange:
    """上下文变更记录"""
    key: str
    old_value: Any
    new_value: Any
    timestamp: datetime
    operation: str  # set, delete, update
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'key': self.key,
            'old_value': str(self.old_value)[:100] if self.old_value else None,
            'new_value': str(self.new_value)[:100] if self.new_value else None,
            'timestamp': self.timestamp.isoformat(),
            'operation': self.operation
        }


class Context:
    """
    结构化上下文
    
    功能：
    1. 变量管理
    2. 快照和回滚
    3. 变更历史
    4. 嵌套上下文
    """
    
    def __init__(
        self,
        session_id: str,
        parent: Optional['Context'] = None,
        max_history: int = 100,
        max_snapshots: int = 10
    ):
        """
        初始化上下文
        
        Args:
            session_id: 会话ID
            parent: 父上下文（支持嵌套）
            max_history: 最大历史记录数
            max_snapshots: 最大快照数
        """
        self.session_id = session_id
        self.parent = parent
        self.max_history = max_history
        self.max_snapshots = max_snapshots
        
        # 变量存储
        self.variables: Dict[str, Any] = {}
        
        # 变更历史
        self.history: List[ContextChange] = []
        
        # 快照列表
        self.snapshots: List[ContextSnapshot] = []
        
        # 元数据
        self.metadata: Dict[str, Any] = {
            'created_at': datetime.now(),
            'last_modified': datetime.now()
        }
        
        logger.debug(f"创建上下文: session={session_id}")
    
    def set(self, key: str, value: Any, track_change: bool = True):
        """
        设置变量
        
        Args:
            key: 变量名
            value: 变量值
            track_change: 是否追踪变更
        """
        old_value = self.variables.get(key)
        operation = 'update' if key in self.variables else 'set'
        
        self.variables[key] = value
        self.metadata['last_modified'] = datetime.now()
        
        # 记录变更
        if track_change:
            self._record_change(key, old_value, value, operation)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取变量
        
        Args:
            key: 变量名
            default: 默认值
        
        Returns:
            变量值，如果不存在则返回default
        """
        # 先查找当前上下文
        if key in self.variables:
            return self.variables[key]
        
        # 如果有父上下文，查找父上下文
        if self.parent:
            return self.parent.get(key, default)
        
        return default
    
    def delete(self, key: str, track_change: bool = True):
        """
        删除变量
        
        Args:
            key: 变量名
            track_change: 是否追踪变更
        """
        if key in self.variables:
            old_value = self.variables[key]
            del self.variables[key]
            self.metadata['last_modified'] = datetime.now()
            
            # 记录变更
            if track_change:
                self._record_change(key, old_value, None, 'delete')
    
    def has(self, key: str) -> bool:
        """
        检查变量是否存在
        
        Args:
            key: 变量名
        
        Returns:
            是否存在
        """
        if key in self.variables:
            return True
        
        if self.parent:
            return self.parent.has(key)
        
        return False
    
    def update(self, variables: Dict[str, Any], track_change: bool = True):
        """
        批量更新变量
        
        Args:
            variables: 变量字典
            track_change: 是否追踪变更
        """
        for key, value in variables.items():
            self.set(key, value, track_change)
    
    def clear(self, track_change: bool = True):
        """
        清空所有变量
        
        Args:
            track_change: 是否追踪变更
        """
        if track_change:
            for key in list(self.variables.keys()):
                self.delete(key, track_change=True)
        else:
            self.variables.clear()
            self.metadata['last_modified'] = datetime.now()
    
    def keys(self) -> List[str]:
        """获取所有变量名"""
        keys = list(self.variables.keys())
        
        # 包含父上下文的key
        if self.parent:
            parent_keys = self.parent.keys()
            keys.extend([k for k in parent_keys if k not in keys])
        
        return keys
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = self.variables.copy()
        
        # 包含父上下文的变量
        if self.parent:
            parent_dict = self.parent.to_dict()
            for key, value in parent_dict.items():
                if key not in result:
                    result[key] = value
        
        return result
    
    # ========== 快照和回滚 ==========
    
    def create_snapshot(self, description: str = "") -> str:
        """
        创建快照
        
        Args:
            description: 快照描述
        
        Returns:
            快照ID
        """
        snapshot = ContextSnapshot(
            id=str(uuid.uuid4()),
            variables=deepcopy(self.variables),
            timestamp=datetime.now(),
            description=description
        )
        
        self.snapshots.append(snapshot)
        
        # 保持最大快照数
        if len(self.snapshots) > self.max_snapshots:
            self.snapshots = self.snapshots[-self.max_snapshots:]
        
        logger.info(f"创建快照: {snapshot.id[:8]}... - {description}")
        
        return snapshot.id
    
    def rollback_to_snapshot(self, snapshot_id: str) -> bool:
        """
        回滚到快照
        
        Args:
            snapshot_id: 快照ID
        
        Returns:
            是否成功
        """
        snapshot = next(
            (s for s in self.snapshots if s.id == snapshot_id),
            None
        )
        
        if not snapshot:
            logger.warning(f"快照不存在: {snapshot_id}")
            return False
        
        # 回滚变量
        self.variables = deepcopy(snapshot.variables)
        self.metadata['last_modified'] = datetime.now()
        
        # 记录回滚操作
        self._record_change(
            '__rollback__',
            None,
            snapshot_id,
            'rollback'
        )
        
        logger.info(f"回滚到快照: {snapshot_id[:8]}...")
        
        return True
    
    def list_snapshots(self) -> List[Dict[str, Any]]:
        """列出所有快照"""
        return [s.to_dict() for s in self.snapshots]
    
    def get_snapshot(self, snapshot_id: str) -> Optional[ContextSnapshot]:
        """获取快照"""
        return next(
            (s for s in self.snapshots if s.id == snapshot_id),
            None
        )
    
    # ========== 变更历史 ==========
    
    def _record_change(
        self,
        key: str,
        old_value: Any,
        new_value: Any,
        operation: str
    ):
        """记录变更"""
        change = ContextChange(
            key=key,
            old_value=old_value,
            new_value=new_value,
            timestamp=datetime.now(),
            operation=operation
        )
        
        self.history.append(change)
        
        # 保持最大历史数
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
    
    def get_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取变更历史
        
        Args:
            limit: 最多返回多少条
        
        Returns:
            变更历史列表
        """
        history = self.history
        
        if limit:
            history = history[-limit:]
        
        return [c.to_dict() for c in history]
    
    def get_changes_for_key(self, key: str) -> List[Dict[str, Any]]:
        """
        获取指定变量的变更历史
        
        Args:
            key: 变量名
        
        Returns:
            变更历史列表
        """
        changes = [c for c in self.history if c.key == key]
        return [c.to_dict() for c in changes]
    
    # ========== 嵌套上下文 ==========
    
    def create_child(self) -> 'Context':
        """
        创建子上下文
        
        Returns:
            子上下文
        """
        child = Context(
            session_id=f"{self.session_id}_child",
            parent=self,
            max_history=self.max_history,
            max_snapshots=self.max_snapshots
        )
        
        logger.debug(f"创建子上下文: parent={self.session_id}")
        
        return child


class ContextManager:
    """
    上下文管理器
    
    职责：
    1. 管理多个会话的上下文
    2. 提供上下文创建和销毁
    3. 提供上下文查询和统计
    """
    
    def __init__(self, max_contexts: int = 1000):
        """
        初始化上下文管理器
        
        Args:
            max_contexts: 最大上下文数
        """
        self.max_contexts = max_contexts
        self.contexts: Dict[str, Context] = {}
        
        logger.info("上下文管理器已初始化")
    
    def create_context(
        self,
        session_id: str,
        parent_session_id: Optional[str] = None
    ) -> Context:
        """
        创建上下文
        
        Args:
            session_id: 会话ID
            parent_session_id: 父会话ID（可选）
        
        Returns:
            上下文
        """
        # 获取父上下文
        parent = None
        if parent_session_id and parent_session_id in self.contexts:
            parent = self.contexts[parent_session_id]
        
        # 创建上下文
        context = Context(session_id, parent)
        self.contexts[session_id] = context
        
        # 清理旧上下文
        self._cleanup_old_contexts()
        
        logger.info(f"创建上下文: {session_id}")
        
        return context
    
    def get_context(self, session_id: str) -> Optional[Context]:
        """
        获取上下文
        
        Args:
            session_id: 会话ID
        
        Returns:
            上下文，如果不存在返回None
        """
        return self.contexts.get(session_id)
    
    def get_or_create_context(self, session_id: str) -> Context:
        """
        获取或创建上下文
        
        Args:
            session_id: 会话ID
        
        Returns:
            上下文
        """
        if session_id not in self.contexts:
            return self.create_context(session_id)
        
        return self.contexts[session_id]
    
    def delete_context(self, session_id: str):
        """
        删除上下文
        
        Args:
            session_id: 会话ID
        """
        if session_id in self.contexts:
            del self.contexts[session_id]
            logger.info(f"删除上下文: {session_id}")
    
    def list_contexts(self) -> List[str]:
        """列出所有上下文的session_id"""
        return list(self.contexts.keys())
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计信息
        """
        total_variables = sum(
            len(ctx.variables) for ctx in self.contexts.values()
        )
        
        total_snapshots = sum(
            len(ctx.snapshots) for ctx in self.contexts.values()
        )
        
        total_history = sum(
            len(ctx.history) for ctx in self.contexts.values()
        )
        
        return {
            'total_contexts': len(self.contexts),
            'total_variables': total_variables,
            'total_snapshots': total_snapshots,
            'total_history': total_history,
            'max_contexts': self.max_contexts
        }
    
    def _cleanup_old_contexts(self):
        """清理旧上下文"""
        if len(self.contexts) <= self.max_contexts:
            return
        
        # 按最后修改时间排序
        sorted_contexts = sorted(
            self.contexts.items(),
            key=lambda x: x[1].metadata['last_modified']
        )
        
        # 删除最旧的上下文
        to_delete = len(self.contexts) - self.max_contexts
        for session_id, _ in sorted_contexts[:to_delete]:
            del self.contexts[session_id]
            logger.debug(f"清理旧上下文: {session_id}")


# 单例模式
_context_manager_instance = None


def get_context_manager() -> ContextManager:
    """获取上下文管理器单例"""
    global _context_manager_instance
    
    if _context_manager_instance is None:
        _context_manager_instance = ContextManager()
        logger.info("上下文管理器单例已创建")
    
    return _context_manager_instance
