"""
任务抽象和任务管理器

提供统一的任务建模和管理
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import logging

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """
    任务抽象
    
    表示一个可执行的任务单元
    """
    id: str
    description: str
    status: TaskStatus
    orchestrator: str
    agent: Optional[str] = None
    parent_id: Optional[str] = None
    subtasks: List['Task'] = field(default_factory=list)
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'description': self.description,
            'status': self.status.value,
            'orchestrator': self.orchestrator,
            'agent': self.agent,
            'parent_id': self.parent_id,
            'subtasks': [st.to_dict() for st in self.subtasks],
            'result': self.result,
            'error': self.error,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


class TaskManager:
    """
    全局任务管理器
    
    职责：
    1. 创建和追踪任务
    2. 管理任务层次结构（父子关系）
    3. 更新任务状态
    4. 提供任务查询和统计
    """
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.task_history: List[Task] = []
        self.max_history = 1000
        
        logger.info("任务管理器已初始化")
    
    def create_task(
        self,
        description: str,
        orchestrator: str,
        agent: Optional[str] = None,
        parent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Task:
        """
        创建任务
        
        Args:
            description: 任务描述
            orchestrator: 使用的编排器
            agent: 使用的Agent（可选）
            parent_id: 父任务ID（可选）
            metadata: 元数据（可选）
        
        Returns:
            创建的任务
        """
        task = Task(
            id=str(uuid.uuid4()),
            description=description,
            status=TaskStatus.PENDING,
            orchestrator=orchestrator,
            agent=agent,
            parent_id=parent_id,
            metadata=metadata or {}
        )
        
        self.tasks[task.id] = task
        
        # 如果有父任务，添加到父任务的subtasks
        if parent_id and parent_id in self.tasks:
            parent = self.tasks[parent_id]
            parent.subtasks.append(task)
        
        logger.info(f"创建任务: {task.id[:8]}... - {description[:50]}")
        
        return task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        return self.tasks.get(task_id)
    
    def update_status(
        self,
        task_id: str,
        status: TaskStatus,
        result: Optional[Any] = None,
        error: Optional[str] = None
    ):
        """
        更新任务状态
        
        Args:
            task_id: 任务ID
            status: 新状态
            result: 执行结果（可选）
            error: 错误信息（可选）
        """
        if task_id not in self.tasks:
            logger.warning(f"任务不存在: {task_id}")
            return
        
        task = self.tasks[task_id]
        old_status = task.status
        task.status = status
        
        # 更新时间戳
        if status == TaskStatus.RUNNING and not task.started_at:
            task.started_at = datetime.now()
        elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            task.completed_at = datetime.now()
        
        # 更新结果和错误
        if result is not None:
            task.result = result
        if error is not None:
            task.error = error
        
        logger.info(f"任务状态更新: {task_id[:8]}... {old_status.value} -> {status.value}")
        
        # 如果任务完成或失败，移到历史
        if status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            self._archive_task(task)
    
    def _archive_task(self, task: Task):
        """归档任务到历史"""
        self.task_history.append(task)
        
        # 保持历史大小
        if len(self.task_history) > self.max_history:
            self.task_history = self.task_history[-self.max_history:]
    
    def get_task_tree(self, task_id: str) -> Dict[str, Any]:
        """
        获取任务树（包含所有子任务）
        
        Args:
            task_id: 根任务ID
        
        Returns:
            任务树字典
        """
        task = self.get_task(task_id)
        if not task:
            return {}
        
        return self._build_task_tree(task)
    
    def _build_task_tree(self, task: Task) -> Dict[str, Any]:
        """递归构建任务树"""
        tree = task.to_dict()
        
        if task.subtasks:
            tree['subtasks'] = [
                self._build_task_tree(st) for st in task.subtasks
            ]
        
        return tree
    
    def get_active_tasks(self) -> List[Task]:
        """获取所有活跃任务（pending或running）"""
        return [
            task for task in self.tasks.values()
            if task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]
        ]
    
    def get_tasks_by_orchestrator(self, orchestrator: str) -> List[Task]:
        """获取指定编排器的所有任务"""
        return [
            task for task in self.tasks.values()
            if task.orchestrator == orchestrator
        ]
    
    def get_tasks_by_agent(self, agent: str) -> List[Task]:
        """获取指定Agent的所有任务"""
        return [
            task for task in self.tasks.values()
            if task.agent == agent
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        total = len(self.tasks)
        
        status_counts = {}
        for status in TaskStatus:
            status_counts[status.value] = sum(
                1 for task in self.tasks.values()
                if task.status == status
            )
        
        orchestrator_counts = {}
        for task in self.tasks.values():
            orchestrator_counts[task.orchestrator] = \
                orchestrator_counts.get(task.orchestrator, 0) + 1
        
        return {
            'total_tasks': total,
            'active_tasks': len(self.get_active_tasks()),
            'history_size': len(self.task_history),
            'status_counts': status_counts,
            'orchestrator_counts': orchestrator_counts
        }
    
    def clear_completed(self):
        """清除已完成的任务"""
        completed_ids = [
            task_id for task_id, task in self.tasks.items()
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
        ]
        
        for task_id in completed_ids:
            del self.tasks[task_id]
        
        logger.info(f"清除了 {len(completed_ids)} 个已完成任务")
    
    def get_task_duration(self, task_id: str) -> Optional[float]:
        """
        获取任务执行时长（秒）
        
        Args:
            task_id: 任务ID
        
        Returns:
            执行时长（秒），如果任务未完成返回None
        """
        task = self.get_task(task_id)
        if not task or not task.started_at or not task.completed_at:
            return None
        
        duration = (task.completed_at - task.started_at).total_seconds()
        return duration


# 单例模式
_task_manager_instance = None


def get_task_manager() -> TaskManager:
    """获取任务管理器单例"""
    global _task_manager_instance
    
    if _task_manager_instance is None:
        _task_manager_instance = TaskManager()
        logger.info("任务管理器单例已创建")
    
    return _task_manager_instance
