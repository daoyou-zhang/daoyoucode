"""
并行探索编排器

使用后台任务并行执行多个探索任务，提升响应速度

增强功能：
- 动态任务生成（LLM驱动，可选）
- 进度通知
- 任务优先级
- 智能结果聚合
"""

from ..core.orchestrator import BaseOrchestrator
from ..core.background import get_background_manager
from typing import Dict, Any, List, Optional
import logging
import asyncio
import json

logger = logging.getLogger(__name__)


class ParallelExploreOrchestrator(BaseOrchestrator):
    """
    并行探索编排器
    
    特点：
    - 启动多个后台探索任务
    - 主任务立即执行，不等待后台任务
    - 收集后台结果（如果完成）
    - 聚合所有结果
    - 动态任务生成（LLM驱动，可选）
    - 进度通知
    """
    
    def __init__(self):
        super().__init__()
        self.bg_manager = get_background_manager()
    
    async def execute(
        self,
        skill,
        user_input: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行并行探索
        
        Skill配置示例:
        orchestrator: parallel_explore
        agent: main_agent
        
        # 模式1: 静态配置（现有）
        background_tasks:
          - agent: explore
            prompt: "在代码库中查找: {{user_input}}"
            timeout: 5.0
            priority: 8
          
          - agent: librarian
            prompt: "查找官方文档: {{user_input}}"
            timeout: 5.0
            priority: 5
        
        # 模式2: 动态生成（新增）
        use_dynamic_tasks: true
        llm:
          model: qwen-turbo
        available_agents:
          - explore: 代码探索
          - librarian: 文档查找
          - web_search: 网络搜索
        """
        # 应用中间件
        if skill.middleware:
            for middleware_name in skill.middleware:
                context = await self._apply_middleware(
                    middleware_name,
                    user_input,
                    context
                )
        
        # 决定使用静态还是动态任务
        use_dynamic = getattr(skill, 'use_dynamic_tasks', False)
        
        if use_dynamic:
            # 动态生成后台任务
            background_tasks = await self._generate_dynamic_tasks(
                skill,
                user_input,
                context
            )
        else:
            # 使用静态配置
            background_tasks = getattr(skill, 'background_tasks', [])
        
        # 1. 启动后台任务
        task_ids = []
        
        for bg_task_config in background_tasks:
            agent_name = bg_task_config.get('agent')
            prompt_template = bg_task_config.get('prompt', '')
            
            if not agent_name:
                logger.warning("后台任务缺少agent配置，跳过")
                continue
            
            # 渲染prompt
            prompt = self._render_template(prompt_template, {
                'user_input': user_input,
                **context
            })
            
            # 提交后台任务
            task_id = await self.bg_manager.submit(
                agent_name=agent_name,
                prompt=prompt,
                context=context
            )
            
            task_info = {
                'task_id': task_id,
                'agent_name': agent_name,
                'timeout': bg_task_config.get('timeout', 5.0),
                'priority': bg_task_config.get('priority', 5)
            }
            task_ids.append(task_info)
            
            # 注册进度回调
            self._register_progress_callback(task_id, agent_name)
        
        logger.info(f"已启动 {len(task_ids)} 个后台任务")
        
        # 2. 执行主任务（不等待后台任务）
        main_agent = self._get_agent(skill.agent)
        
        main_result = await main_agent.execute(
            prompt_source=skill.prompt,
            user_input=user_input,
            context=context,
            tools=skill.tools if skill.tools else None
        )
        
        logger.info("主任务执行完成")
        
        # 3. 收集后台结果（按优先级排序）
        task_ids.sort(key=lambda t: t.get('priority', 5), reverse=True)
        background_results = []
        
        for task_info in task_ids:
            task_id = task_info['task_id']
            timeout = task_info['timeout']
            agent_name = task_info['agent_name']
            
            try:
                result = await self.bg_manager.get_result(
                    task_id,
                    timeout=timeout
                )
                background_results.append({
                    'agent': agent_name,
                    'result': result,
                    'priority': task_info['priority']
                })
                logger.info(f"后台任务完成: {agent_name}")
            
            except asyncio.TimeoutError:
                logger.warning(f"后台任务超时: {agent_name}")
                background_results.append({
                    'agent': agent_name,
                    'result': {'error': '超时'},
                    'priority': task_info['priority']
                })
            
            except Exception as e:
                logger.error(f"获取后台结果失败: {e}")
                background_results.append({
                    'agent': agent_name,
                    'result': {'error': str(e)},
                    'priority': task_info['priority']
                })
        
        # 4. 智能聚合结果
        use_llm_aggregate = getattr(skill, 'use_llm_aggregate', False)
        
        if use_llm_aggregate:
            aggregated_content = await self._smart_aggregate_with_llm(
                main_result,
                background_results,
                skill
            )
        else:
            aggregated_content = await self._aggregate_results(
                main_result,
                background_results
            )
        
        return {
            'success': True,
            'content': aggregated_content,
            'main_result': main_result,
            'background_results': background_results,
            'metadata': {
                'orchestrator': 'parallel_explore',
                'background_tasks_count': len(task_ids),
                'dynamic_tasks': use_dynamic,
                'llm_aggregate': use_llm_aggregate
            }
        }
    
    def _render_template(
        self,
        template: str,
        context: Dict[str, Any]
    ) -> str:
        """渲染模板"""
        from jinja2 import Template
        return Template(template).render(**context)
    
    async def _generate_dynamic_tasks(
        self,
        skill,
        user_input: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """使用LLM动态生成后台探索任务"""
        available_agents = getattr(skill, 'available_agents', {})
        
        if not available_agents:
            logger.warning("未配置available_agents，无法动态生成任务")
            return []
        
        # 构建LLM提示词
        agents_desc = "\n".join([
            f"- {name}: {desc}"
            for name, desc in available_agents.items()
        ])
        
        analysis_prompt = f"""分析以下任务，决定需要哪些后台探索来辅助主任务：

任务: {user_input}

可用的探索Agent:
{agents_desc}

请返回JSON数组，每个探索任务包含：
- agent: Agent名称
- prompt: 探索提示词
- priority: 优先级（1-10，10最高）
- timeout: 超时时间（秒）

示例:
[
  {{"agent": "explore", "prompt": "搜索相关代码实现", "priority": 8, "timeout": 5.0}},
  {{"agent": "librarian", "prompt": "查找API文档", "priority": 6, "timeout": 5.0}}
]

注意：
- 只选择真正有帮助的探索任务（1-3个）
- 优先级高的任务会优先收集结果
- 超时时间不要太长（建议3-10秒）
"""
        
        try:
            # 调用LLM
            llm_config = getattr(skill, 'llm', {})
            model = llm_config.get('model', 'qwen-turbo')
            
            # 使用相对导入
            import sys
            import os
            parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)
            from llm.client_manager import get_client_manager
            
            client_manager = get_client_manager()
            client = await client_manager.get_client(model)
            
            response = await client.chat(
                messages=[{'role': 'user', 'content': analysis_prompt}],
                temperature=0.3
            )
            
            # 解析响应
            content = response.get('content', '[]')
            
            # 提取JSON（可能包含在markdown代码块中）
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            tasks = json.loads(content)
            
            logger.info(f"LLM生成了 {len(tasks)} 个后台任务")
            
            return tasks
        
        except Exception as e:
            logger.error(f"动态生成任务失败: {e}")
            # 降级：返回空列表
            return []
    
    def _register_progress_callback(self, task_id: str, agent_name: str):
        """注册进度回调"""
        def on_progress(progress: float):
            logger.info(f"后台任务 [{agent_name}] 进度: {progress:.0f}%")
        
        # 如果BackgroundManager支持进度回调，注册它
        if hasattr(self.bg_manager, 'on_progress'):
            self.bg_manager.on_progress(task_id, on_progress)
    
    async def _smart_aggregate_with_llm(
        self,
        main_result: Dict[str, Any],
        background_results: List[Dict[str, Any]],
        skill
    ) -> str:
        """使用LLM智能聚合结果"""
        # 提取所有成功的结果
        main_content = main_result.get('content', '')
        bg_contents = []
        
        for bg_result in background_results:
            agent_name = bg_result['agent']
            result = bg_result['result']
            priority = bg_result.get('priority', 5)
            
            if isinstance(result, dict) and result.get('content'):
                bg_contents.append({
                    'agent': agent_name,
                    'content': result['content'],
                    'priority': priority
                })
        
        if not bg_contents:
            # 没有后台结果，直接返回主结果
            return main_content
        
        # 构建聚合提示词
        bg_sections = "\n\n".join([
            f"[{item['agent']} - 优先级{item['priority']}]\n{item['content']}"
            for item in bg_contents
        ])
        
        aggregation_prompt = f"""请智能聚合以下主任务结果和后台探索结果：

【主要结果】
{main_content}

【后台探索结果】
{bg_sections}

要求：
1. 以主要结果为核心
2. 将后台探索的有价值信息融入其中
3. 去除重复信息
4. 保持连贯性和可读性
5. 突出重点信息

请直接返回聚合后的内容，不要添加额外说明。
"""
        
        try:
            # 调用LLM
            llm_config = getattr(skill, 'llm', {})
            model = llm_config.get('model', 'qwen-turbo')
            
            # 使用相对导入
            import sys
            import os
            parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)
            from llm.client_manager import get_client_manager
            
            client_manager = get_client_manager()
            client = await client_manager.get_client(model)
            
            response = await client.chat(
                messages=[{'role': 'user', 'content': aggregation_prompt}],
                temperature=0.5
            )
            
            aggregated = response.get('content', main_content)
            
            logger.info("LLM智能聚合完成")
            
            return aggregated
        
        except Exception as e:
            logger.error(f"LLM聚合失败: {e}")
            # 降级：使用简单聚合
            return await self._aggregate_results(main_result, background_results)
    
    async def _aggregate_results(
        self,
        main_result: Dict[str, Any],
        background_results: List[Dict[str, Any]]
    ) -> str:
        """聚合结果"""
        parts = []
        
        # 主结果
        if main_result.get('content'):
            parts.append(f"[主要结果]\n{main_result['content']}")
        
        # 后台结果
        for bg_result in background_results:
            agent_name = bg_result['agent']
            result = bg_result['result']
            
            if isinstance(result, dict) and result.get('content'):
                parts.append(f"[{agent_name}]\n{result['content']}")
            elif isinstance(result, dict) and result.get('error'):
                # 跳过错误结果
                pass
        
        return "\n\n".join(parts)
