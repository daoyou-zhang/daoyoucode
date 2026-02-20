"""
并行执行器

支持真正的后台任务并行执行。
采用高效并行执行设计
"""

import asyncio
from typing import Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ParallelExecutor:
    """并行执行器（单例）"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.tasks: Dict[str, asyncio.Task] = {}
        self.results: Dict[str, Any] = {}
        self.metadata: Dict[str, Dict] = {}
        self._initialized = True
        logger.info("ParallelExecutor 初始化完成")
    
    async def submit(
        self,
        task_id: str,
        coro,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        提交后台任务
        
        Args:
            task_id: 任务ID
            coro: 协程
            metadata: 元数据
        
        Returns:
            task_id
        """
        # 创建异步任务
        task = asyncio.create_task(coro)
        self.tasks[task_id] = task
        self.metadata[task_id] = {
            'submitted_at': datetime.now(),
            'status': 'running',
            **(metadata or {})
        }
        
        logger.info(f"提交后台任务: {task_id}")
        return task_id
    
    async def get_result(
        self,
        task_id: str,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        获取任务结果
        
        Args:
            task_id: 任务ID
            timeout: 超时时间（秒）
        
        Returns:
            任务结果
        """
        # 检查缓存
        if task_id in self.results:
            return self.results[task_id]
        
        # 获取任务
        task = self.tasks.get(task_id)
        if not task:
            return {
                'status': 'error',
                'error': f'Task {task_id} not found'
            }
        
        try:
            # 等待结果
            result = await asyncio.wait_for(task, timeout=timeout)
            
            # 缓存结果
            self.results[task_id] = result
            self.metadata[task_id]['status'] = 'completed'
            self.metadata[task_id]['completed_at'] = datetime.now()
            
            logger.info(f"任务完成: {task_id}")
            return result
        
        except asyncio.TimeoutError:
            logger.warning(f"任务超时: {task_id}")
            return {
                'status': 'timeout',
                'task_id': task_id
            }
        
        except Exception as e:
            logger.error(f"任务失败: {task_id}, {e}")
            self.metadata[task_id]['status'] = 'failed'
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def cancel(self, task_id: str) -> bool:
        """取消任务"""
        task = self.tasks.get(task_id)
        if task:
            task.cancel()
            self.metadata[task_id]['status'] = 'cancelled'
            logger.info(f"取消任务: {task_id}")
            return True
        return False
    
    def cancel_all(self):
        """取消所有任务"""
        for task_id, task in self.tasks.items():
            if not task.done():
                task.cancel()
                self.metadata[task_id]['status'] = 'cancelled'
        
        logger.info(f"取消所有任务: {len(self.tasks)} 个")
        self.tasks.clear()
    
    def get_status(self, task_id: str) -> Optional[str]:
        """获取任务状态"""
        return self.metadata.get(task_id, {}).get('status')
    
    def list_tasks(self) -> Dict[str, Dict]:
        """列出所有任务"""
        return self.metadata.copy()


def get_parallel_executor() -> ParallelExecutor:
    """获取并行执行器实例"""
    return ParallelExecutor()
