"""
并行编排器（增强版）

并行执行多个Agent，智能聚合结果
"""

from ..core.orchestrator import BaseOrchestrator
from typing import Dict, Any, List
import asyncio
import logging

logger = logging.getLogger(__name__)


class ParallelOrchestrator(BaseOrchestrator):
    """
    并行编排器
    
    特性：
    - 并行执行多个Agent
    - 智能任务拆分
    - 结果聚合
    - 超时控制
    """
    
    def __init__(self, timeout: float = 60.0):
        super().__init__()
        self.timeout = timeout
    
    async def execute(
        self,
        skill,
        user_input: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        并行执行
        
        Skill配置示例:
        agents:
          - name: explorer
            agent: explore
            task: "查找相关代码"
          - name: researcher
            agent: librarian
            task: "查找文档"
        """
        # 应用中间件
        if skill.middleware:
            for middleware_name in skill.middleware:
                context = await self._apply_middleware(
                    middleware_name,
                    user_input,
                    context
                )
        
        # 获取并行任务配置
        agents_config = getattr(skill, 'agents', None)
        
        if not agents_config:
            # 如果没有配置，尝试自动拆分任务
            tasks = await self._analyze_and_split(user_input, context)
        else:
            # 使用配置的任务
            tasks = self._prepare_tasks(agents_config, user_input, context)
        
        logger.info(f"并行执行 {len(tasks)} 个任务")
        
        # 并行执行所有任务
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*[
                    self._execute_task(task, context)
                    for task in tasks
                ], return_exceptions=True),
                timeout=self.timeout
            )
        except asyncio.TimeoutError:
            logger.error(f"并行执行超时（{self.timeout}秒）")
            return {
                'success': False,
                'content': '',
                'error': f'执行超时（{self.timeout}秒）'
            }
        
        # 处理异常
        successful_results = []
        failed_tasks = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"任务 {i} 失败: {result}")
                failed_tasks.append({'index': i, 'error': str(result)})
            else:
                successful_results.append(result)
        
        # 智能聚合结果
        aggregated = await self._smart_aggregate(successful_results)
        
        return {
            'success': len(successful_results) > 0,
            'content': aggregated,
            'parallel_results': successful_results,
            'failed_tasks': failed_tasks,
            'metadata': {
                'orchestrator': 'parallel',
                'total_tasks': len(tasks),
                'successful_tasks': len(successful_results),
                'failed_tasks': len(failed_tasks)
            }
        }
    
    def _prepare_tasks(
        self,
        agents_config: List[Dict[str, Any]],
        user_input: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """准备任务列表"""
        tasks = []
        
        for config in agents_config:
            task = {
                'name': config.get('name', 'unnamed'),
                'agent': config.get('agent'),
                'task': config.get('task', user_input),
                'prompt': config.get('prompt', {'use_agent_default': True})
            }
            tasks.append(task)
        
        return tasks
    
    async def _analyze_and_split(
        self,
        user_input: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        分析任务并自动拆分
        
        简化版本：基于关键词拆分
        """
        tasks = []
        
        # 检测是否需要代码搜索
        if any(kw in user_input.lower() for kw in ['查找', '搜索', '代码', 'find', 'search']):
            tasks.append({
                'name': 'code_search',
                'agent': 'explore',
                'task': f"在代码库中查找: {user_input}",
                'prompt': {'use_agent_default': True}
            })
        
        # 检测是否需要文档查询
        if any(kw in user_input.lower() for kw in ['文档', '官方', 'docs', 'documentation']):
            tasks.append({
                'name': 'doc_search',
                'agent': 'librarian',
                'task': f"查找官方文档: {user_input}",
                'prompt': {'use_agent_default': True}
            })
        
        # 如果没有特定任务，使用默认Agent
        if not tasks:
            tasks.append({
                'name': 'default',
                'agent': 'translator',  # 默认Agent
                'task': user_input,
                'prompt': {'use_agent_default': True}
            })
        
        return tasks
    
    async def _execute_task(
        self,
        task: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行单个任务"""
        agent_name = task['agent']
        task_input = task['task']
        prompt_config = task['prompt']
        
        # 获取Agent
        agent = self._get_agent(agent_name)
        
        # 执行
        result = await agent.execute(
            prompt_source=prompt_config,
            user_input=task_input,
            context=context
        )
        
        # 添加任务信息
        result['task_name'] = task['name']
        result['agent_name'] = agent_name
        
        return result
    
    async def _smart_aggregate(
        self,
        results: List[Dict[str, Any]]
    ) -> str:
        """
        智能聚合结果
        
        根据结果类型和内容智能组合
        """
        if not results:
            return ""
        
        # 按任务类型分组
        grouped = {}
        for result in results:
            task_name = result.get('task_name', 'unknown')
            if task_name not in grouped:
                grouped[task_name] = []
            grouped[task_name].append(result)
        
        # 组合结果
        sections = []
        
        for task_name, task_results in grouped.items():
            # 提取内容
            contents = [
                r.get('content', '')
                for r in task_results
                if r.get('success') and r.get('content')
            ]
            
            if contents:
                section = f"## {task_name}\n\n" + "\n\n".join(contents)
                sections.append(section)
        
        return "\n\n---\n\n".join(sections)
