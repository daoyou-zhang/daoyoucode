"""
并行编排器（增强版）

支持LLM智能任务拆分和结果聚合
"""

from ..core.orchestrator import BaseOrchestrator
from typing import Dict, Any, List
import asyncio
import json
import logging

logger = logging.getLogger(__name__)


class ParallelOrchestrator(BaseOrchestrator):
    """
    并行编排器（增强版）
    
    新增功能：
    - LLM智能任务拆分
    - 优先级调度
    - LLM智能结果聚合
    - 批量执行控制
    """
    
    def __init__(self, timeout: float = 60.0, batch_size: int = 3):
        super().__init__()
        self.timeout = timeout
        self.batch_size = batch_size
    
    async def execute(
        self,
        skill,
        user_input: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        并行执行
        
        支持两种模式：
        1. 配置模式：使用Skill配置的agents
        2. 智能模式：使用LLM自动拆分任务
        """
        # 应用中间件
        if skill.middleware:
            for middleware_name in skill.middleware:
                context = await self._apply_middleware(
                    middleware_name,
                    user_input,
                    context
                )
        
        # 保存Skill引用
        context['_current_skill'] = skill
        
        # 获取任务列表
        agents_config = getattr(skill, 'agents', None)
        use_llm_split = getattr(skill, 'use_llm_split', False)
        
        if agents_config:
            # 配置模式
            logger.info("使用配置的agents")
            tasks = self._prepare_tasks(agents_config, user_input, context)
        elif use_llm_split:
            # 智能模式：使用LLM拆分
            logger.info("使用LLM智能拆分任务")
            tasks = await self._llm_analyze_and_split(user_input, context, skill)
        else:
            # 简单模式：基于关键词拆分
            logger.info("使用关键词拆分任务")
            tasks = await self._analyze_and_split(user_input, context)
        
        if not tasks:
            return {
                'success': False,
                'content': '',
                'error': '无法生成任务'
            }
        
        # 按优先级排序
        tasks.sort(key=lambda t: t.get('priority', 5), reverse=True)
        
        logger.info(f"并行执行 {len(tasks)} 个任务（批量大小: {self.batch_size}）")
        
        # 分批执行
        all_results = await self._execute_in_batches(tasks, context)
        
        # 智能聚合结果
        use_llm_aggregate = getattr(skill, 'use_llm_aggregate', False)
        
        if use_llm_aggregate:
            logger.info("使用LLM智能聚合结果")
            aggregated = await self._llm_smart_aggregate(all_results, user_input)
        else:
            logger.info("使用简单聚合")
            aggregated = await self._smart_aggregate(all_results)
        
        # 统计
        successful_results = [r for r in all_results if not isinstance(r, Exception) and r.get('success')]
        failed_results = [r for r in all_results if isinstance(r, Exception) or not r.get('success')]
        
        return {
            'success': len(successful_results) > 0,
            'content': aggregated,
            'parallel_results': all_results,
            'metadata': {
                'orchestrator': 'parallel',
                'total_tasks': len(tasks),
                'successful_tasks': len(successful_results),
                'failed_tasks': len(failed_results),
                'batch_size': self.batch_size,
                'use_llm_split': use_llm_split,
                'use_llm_aggregate': use_llm_aggregate
            }
        }
    
    async def _llm_analyze_and_split(
        self,
        user_input: str,
        context: Dict[str, Any],
        skill
    ) -> List[Dict[str, Any]]:
        """
        使用LLM智能拆分任务
        
        LLM会分析任务并决定：
        - 需要哪些子任务
        - 每个子任务使用哪个Agent
        - 子任务的优先级
        """
        # 获取可用的Agent列表
        from ..core.agent import get_agent_registry
        registry = get_agent_registry()
        available_agents = registry.list_agents()
        
        # 构建分析Prompt
        analysis_prompt = f"""
分析以下任务，拆分成可以并行执行的子任务。

任务: {user_input}

可用的Agent:
{chr(10).join([f"- {agent}: 专门处理相关任务" for agent in available_agents[:10]])}

请返回JSON数组，每个子任务包含：
- name: 子任务名称（简短）
- description: 子任务描述
- agent: 建议使用的Agent（从上面列表选择）
- priority: 优先级（1-10，10最高）

要求：
1. 子任务应该可以并行执行（互不依赖）
2. 每个子任务应该聚焦一个方面
3. 优先级高的任务更重要
4. 最多拆分5个子任务

示例输出：
[
  {{"name": "search_code", "description": "搜索相关代码", "agent": "code_explorer", "priority": 8}},
  {{"name": "search_docs", "description": "查找文档", "agent": "translator", "priority": 5}}
]

只返回JSON数组，不要其他内容。
"""
        
        try:
            # 调用LLM
            from ..llm import get_client_manager
            from ..llm.base import LLMRequest
            
            client_manager = get_client_manager()
            model = getattr(skill, 'llm', {}).get('model', 'qwen-turbo')
            client = client_manager.get_client(model=model)
            
            request = LLMRequest(
                prompt=analysis_prompt,
                model=model,
                temperature=0.3
            )
            
            response = await client.chat(request)
            
            # 解析JSON
            content = response.content.strip()
            
            # 提取JSON（可能被包裹在```json```中）
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            tasks = json.loads(content)
            
            logger.info(f"LLM拆分出 {len(tasks)} 个子任务")
            
            # 转换为标准格式
            formatted_tasks = []
            for task in tasks:
                formatted_tasks.append({
                    'name': task.get('name', 'unnamed'),
                    'agent': task.get('agent', 'translator'),
                    'task': task.get('description', user_input),
                    'prompt': {'use_agent_default': True},
                    'priority': task.get('priority', 5)
                })
            
            return formatted_tasks
        
        except Exception as e:
            logger.error(f"LLM任务拆分失败: {e}")
            # 降级到简单拆分
            return await self._analyze_and_split(user_input, context)
    
    async def _execute_in_batches(
        self,
        tasks: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """分批执行任务"""
        all_results = []
        
        for i in range(0, len(tasks), self.batch_size):
            batch = tasks[i:i+self.batch_size]
            batch_num = i // self.batch_size + 1
            total_batches = (len(tasks) + self.batch_size - 1) // self.batch_size
            
            logger.info(f"执行批次 {batch_num}/{total_batches}: {len(batch)} 个任务")
            
            try:
                batch_results = await asyncio.wait_for(
                    asyncio.gather(*[
                        self._execute_task(task, context)
                        for task in batch
                    ], return_exceptions=True),
                    timeout=self.timeout
                )
                
                all_results.extend(batch_results)
            
            except asyncio.TimeoutError:
                logger.error(f"批次 {batch_num} 超时")
                all_results.extend([
                    {'success': False, 'error': '超时'}
                    for _ in batch
                ])
        
        return all_results
    
    async def _llm_smart_aggregate(
        self,
        results: List[Dict[str, Any]],
        user_input: str
    ) -> str:
        """
        使用LLM智能聚合结果
        
        LLM会：
        - 去除重复信息
        - 保留关键信息
        - 组织成连贯的结构
        - 突出重点
        """
        # 提取成功的结果
        successful_results = []
        for r in results:
            if not isinstance(r, Exception) and r.get('success') and r.get('content'):
                successful_results.append({
                    'task': r.get('task_name', 'unknown'),
                    'agent': r.get('agent_name', 'unknown'),
                    'content': r['content']
                })
        
        if not successful_results:
            return "所有并行任务都失败了"
        
        # 构建聚合Prompt
        results_text = []
        for i, r in enumerate(successful_results):
            results_text.append(f"[任务{i+1}: {r['task']}]")
            results_text.append(f"Agent: {r['agent']}")
            results_text.append(r['content'])
            results_text.append("")
        
        aggregation_prompt = f"""
以下是多个并行任务的结果，请智能聚合成一个连贯的回答。

原始问题: {user_input}

并行任务结果:
{chr(10).join(results_text)}

要求：
1. 去除重复信息
2. 保留所有关键信息
3. 组织成连贯的结构
4. 突出重点
5. 如果结果之间有冲突，指出并说明

请直接给出聚合后的答案，不要添加"根据以上结果"等前缀。
"""
        
        try:
            # 调用LLM
            from ..llm import get_client_manager
            from ..llm.base import LLMRequest
            
            client_manager = get_client_manager()
            client = client_manager.get_client(model='qwen-max')
            
            request = LLMRequest(
                prompt=aggregation_prompt,
                model='qwen-max',
                temperature=0.3
            )
            
            response = await client.chat(request)
            
            return response.content
        
        except Exception as e:
            logger.error(f"LLM聚合失败: {e}")
            # 降级到简单聚合
            return await self._smart_aggregate(results)
    
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
        
        # 准备工具（从任务配置或Skill配置获取）
        task_tools = task.get('tools')
        if task_tools is None and '_current_skill' in context:
            # 如果任务没有指定工具，使用Skill的工具
            current_skill = context['_current_skill']
            if hasattr(current_skill, 'tools'):
                task_tools = current_skill.tools
        
        # 执行
        result = await agent.execute(
            prompt_source=prompt_config,
            user_input=task_input,
            context=context,
            tools=task_tools if task_tools else None
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
                'prompt': config.get('prompt', {'use_agent_default': True}),
                'priority': config.get('priority', 5)
            }
            tasks.append(task)
        
        return tasks
    
    async def _analyze_and_split(
        self,
        user_input: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        简单的任务拆分（基于关键词）
        
        作为LLM拆分失败时的降级方案
        """
        tasks = []
        
        # 检测是否需要代码搜索
        if any(kw in user_input.lower() for kw in ['查找', '搜索', '代码', 'find', 'search']):
            tasks.append({
                'name': 'code_search',
                'agent': 'code_explorer',
                'task': f"在代码库中查找: {user_input}",
                'prompt': {'use_agent_default': True},
                'priority': 8
            })
        
        # 检测是否需要文档查询
        if any(kw in user_input.lower() for kw in ['文档', '官方', 'docs', 'documentation']):
            tasks.append({
                'name': 'doc_search',
                'agent': 'translator',
                'task': f"查找官方文档: {user_input}",
                'prompt': {'use_agent_default': True},
                'priority': 5
            })
        
        # 如果没有特定任务，使用默认Agent
        if not tasks:
            tasks.append({
                'name': 'default',
                'agent': 'translator',
                'task': user_input,
                'prompt': {'use_agent_default': True},
                'priority': 5
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
        
        # 准备工具
        task_tools = task.get('tools')
        if task_tools is None and '_current_skill' in context:
            current_skill = context['_current_skill']
            if hasattr(current_skill, 'tools'):
                task_tools = current_skill.tools
        
        # 执行
        result = await agent.execute(
            prompt_source=prompt_config,
            user_input=task_input,
            context=context,
            tools=task_tools if task_tools else None
        )
        
        # 转换为字典
        return {
            'success': result.success,
            'content': result.content,
            'error': result.error,
            'task_name': task['name'],
            'agent_name': agent_name,
            'tokens_used': result.tokens_used
        }
    
    async def _smart_aggregate(
        self,
        results: List[Dict[str, Any]]
    ) -> str:
        """
        简单聚合结果
        
        根据结果类型和内容智能组合
        """
        if not results:
            return ""
        
        # 按任务类型分组
        grouped = {}
        for result in results:
            if isinstance(result, Exception):
                continue
            
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
