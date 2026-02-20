"""
后台任务管理器

采用后台任务执行机制，支持：
- 异步任务提交
- 任务状态查询
- 任务结果获取
- 任务取消
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BackgroundTask:
    """后台任务"""
    task_id: str
    agent_name: str
    prompt: str
    context: Dict[str, Any]
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    task: Optional[asyncio.Task] = None


class BackgroundTaskManager:
    """后台任务管理器"""
    
    def __init__(self):
        self.tasks: Dict[str, BackgroundTask] = {}
        self.logger = logging.getLogger("background_task")
    
    async def submit(
        self,
        agent_name: str,
        prompt: str,
        context: Dict[str, Any],
        task_id: Optional[str] = None
    ) -> str:
        """
        提交后台任务
        
        Args:
            agent_name: Agent名称
            prompt: Prompt内容
            context: 上下文
            task_id: 任务ID（可选，不提供则自动生成）
        
        Returns:
            任务ID
        """
        # 生成任务ID
        if not task_id:
            task_id = str(uuid.uuid4())
        
        # 检查是否已存在
        if task_id in self.tasks:
            existing_task = self.tasks[task_id]
            if existing_task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
                self.logger.info(f"任务 {task_id} 已存在且正在运行，复用")
                return task_id
        
        # 创建任务对象
        bg_task = BackgroundTask(
            task_id=task_id,
            agent_name=agent_name,
            prompt=prompt,
            context=context,
            status=TaskStatus.PENDING,
            created_at=datetime.now()
        )
        
        # 创建异步任务
        task = asyncio.create_task(
            self._execute_background(bg_task)
        )
        bg_task.task = task
        
        # 保存
        self.tasks[task_id] = bg_task
        
        self.logger.info(f"已提交后台任务: {task_id} (Agent: {agent_name})")
        
        return task_id
    
    async def _execute_background(self, bg_task: BackgroundTask):
        """执行后台任务"""
        try:
            # 更新状态
            bg_task.status = TaskStatus.RUNNING
            bg_task.started_at = datetime.now()
            
            self.logger.info(f"开始执行后台任务: {bg_task.task_id}")
            
            # 获取Agent
            from ..registry import get_agent_registry
            agent_registry = get_agent_registry()
            agent = agent_registry.get_agent(bg_task.agent_name)
            
            if not agent:
                raise ValueError(f"Agent不存在: {bg_task.agent_name}")
            
            # 执行Agent
            result = await agent.execute(
                prompt_source={'inline': bg_task.prompt},
                user_input="",
                context=bg_task.context
            )
            
            # 保存结果
            bg_task.result = result
            bg_task.status = TaskStatus.COMPLETED
            bg_task.completed_at = datetime.now()
            
            self.logger.info(f"后台任务完成: {bg_task.task_id}")
        
        except asyncio.CancelledError:
            bg_task.status = TaskStatus.CANCELLED
            bg_task.completed_at = datetime.now()
            self.logger.info(f"后台任务已取消: {bg_task.task_id}")
        
        except Exception as e:
            bg_task.error = str(e)
            bg_task.status = TaskStatus.FAILED
            bg_task.completed_at = datetime.now()
            self.logger.error(
                f"后台任务失败: {bg_task.task_id}, 错误: {e}",
                exc_info=True
            )
    
    async def get_result(
        self,
        task_id: str,
        timeout: Optional[float] = None
    ) -> Any:
        """
        获取任务结果
        
        Args:
            task_id: 任务ID
            timeout: 超时时间（秒），None表示无限等待
        
        Returns:
            任务结果
        
        Raises:
            ValueError: 任务不存在
            asyncio.TimeoutError: 超时
        """
        if task_id not in self.tasks:
            raise ValueError(f"任务不存在: {task_id}")
        
        bg_task = self.tasks[task_id]
        
        # 如果任务还在运行，等待完成
        if bg_task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
            if timeout:
                await asyncio.wait_for(bg_task.task, timeout=timeout)
            else:
                await bg_task.task
        
        # 返回结果
        if bg_task.status == TaskStatus.COMPLETED:
            return bg_task.result
        elif bg_task.status == TaskStatus.FAILED:
            return {'error': bg_task.error}
        elif bg_task.status == TaskStatus.CANCELLED:
            return {'error': '任务已取消'}
        else:
            return {'error': f'未知状态: {bg_task.status}'}
    
    def get_status(self, task_id: str) -> Optional[TaskStatus]:
        """获取任务状态"""
        if task_id not in self.tasks:
            return None
        return self.tasks[task_id].status
    
    def cancel(self, task_id: str) -> bool:
        """
        取消任务
        
        Returns:
            是否成功取消
        """
        if task_id not in self.tasks:
            return False
        
        bg_task = self.tasks[task_id]
        
        if bg_task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
            if bg_task.task:
                bg_task.task.cancel()
            bg_task.status = TaskStatus.CANCELLED
            self.logger.info(f"已取消任务: {task_id}")
            return True
        
        return False
    
    def list_tasks(self) -> Dict[str, Dict[str, Any]]:
        """列出所有任务"""
        return {
            task_id: {
                'agent_name': task.agent_name,
                'status': task.status.value,
                'created_at': task.created_at.isoformat(),
                'started_at': task.started_at.isoformat() if task.started_at else None,
                'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            }
            for task_id, task in self.tasks.items()
        }
    
    def clear_completed(self):
        """清理已完成的任务"""
        completed_ids = [
            task_id
            for task_id, task in self.tasks.items()
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
        ]
        
        for task_id in completed_ids:
            del self.tasks[task_id]
        
        self.logger.info(f"已清理 {len(completed_ids)} 个已完成任务")


# 全局后台任务管理器
_background_manager = BackgroundTaskManager()


def get_background_manager() -> BackgroundTaskManager:
    """获取后台任务管理器"""
    return _background_manager
