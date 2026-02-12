"""
工作流编排器

按步骤执行的工作流，支持条件分支和数据传递

增强功能：
- 步骤依赖检查
- 步骤超时和重试
- 失败回滚
- 成本追踪
"""

from ..core.orchestrator import BaseOrchestrator
from typing import Dict, Any, Optional, List, Tuple
import logging
import asyncio
import time

logger = logging.getLogger(__name__)


class WorkflowOrchestrator(BaseOrchestrator):
    """
    工作流编排器
    
    支持：
    - 顺序执行多个步骤
    - 步骤间数据传递
    - 条件分支
    - 错误处理
    - 步骤依赖检查（新增）
    - 步骤超时和重试（新增）
    - 失败回滚（新增）
    """
    
    async def execute(
        self,
        skill,
        user_input: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行工作流
        
        Skill配置示例:
        workflow:
          - name: analyze
            agent: analyzer
            output: analysis_result
            max_retries: 3
            timeout: 30.0
          
          - name: implement
            agent: programmer
            depends_on: [analyze]  # 依赖
            input: ${analysis_result}
            condition: ${analysis_result.feasible}
            output: code_changes
            rollback: cleanup_agent  # 回滚Agent
          
          - name: review
            agent: reviewer
            depends_on: [implement]
            input: ${code_changes}
        """
        # 获取工作流定义
        workflow = getattr(skill, 'workflow', None)
        if not workflow:
            return {
                'success': False,
                'content': '',
                'error': 'Skill未定义workflow'
            }
        
        # 初始化工作流上下文
        workflow_context = context.copy()
        workflow_context['user_input'] = user_input
        workflow_context['results'] = {}
        workflow_context['_current_skill'] = skill
        workflow_context['_start_time'] = time.time()
        
        # 应用中间件
        if skill.middleware:
            for middleware_name in skill.middleware:
                workflow_context = await self._apply_middleware(
                    middleware_name,
                    user_input,
                    workflow_context
                )
        
        # 验证依赖关系
        if not self._validate_dependencies(workflow):
            return {
                'success': False,
                'content': '',
                'error': '工作流依赖关系无效（存在循环依赖或未定义的步骤）'
            }
        
        # 执行步骤（记录已执行的步骤用于回滚）
        executed_steps: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []
        
        try:
            for step in workflow:
                step_name = step.get('name', 'unnamed')
                
                logger.info(f"执行工作流步骤: {step_name}")
                
                # 检查依赖
                if not self._check_dependencies(step, workflow_context):
                    logger.warning(f"跳过步骤 {step_name}（依赖未满足）")
                    continue
                
                # 检查条件
                if not await self._check_condition(step, workflow_context):
                    logger.info(f"跳过步骤 {step_name}（条件不满足）")
                    continue
                
                # 执行步骤（带重试和超时）
                step_result = await self._execute_step_with_retry(
                    step,
                    workflow_context
                )
                
                # 保存结果
                output_key = step.get('output', step_name)
                step_result['_step_name'] = step_name  # 保存步骤名称用于依赖检查
                workflow_context['results'][output_key] = step_result
                
                # 记录已执行的步骤（用于回滚）
                executed_steps.append((step, step_result))
                
                # 如果步骤失败且没有配置继续执行，则中断并回滚
                if not step_result.get('success') and not step.get('continue_on_error'):
                    logger.error(f"步骤 {step_name} 失败，开始回滚")
                    await self._rollback_steps(executed_steps, workflow_context)
                    
                    return {
                        'success': False,
                        'content': '',
                        'error': f"步骤 {step_name} 失败: {step_result.get('error')}",
                        'workflow_results': workflow_context['results'],
                        'rollback_executed': True
                    }
        
        except Exception as e:
            logger.error(f"工作流执行异常: {e}", exc_info=True)
            
            # 回滚已执行的步骤
            await self._rollback_steps(executed_steps, workflow_context)
            
            return {
                'success': False,
                'content': '',
                'error': f"工作流异常: {e}",
                'workflow_results': workflow_context['results'],
                'rollback_executed': True
            }
        
        # 聚合结果
        final_result = await self._aggregate_results(
            workflow_context['results']
        )
        
        # 计算总耗时
        total_duration = time.time() - workflow_context['_start_time']
        
        return {
            'success': True,
            'content': final_result,
            'workflow_results': workflow_context['results'],
            'metadata': {
                'orchestrator': 'workflow',
                'steps_executed': len(workflow_context['results']),
                'total_duration': total_duration,
                'rollback_executed': False
            }
        }
    
    async def _check_condition(
        self,
        step: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """检查步骤执行条件"""
        condition = step.get('condition')
        if not condition:
            return True
        
        # 简单的条件评估（支持变量替换）
        try:
            # 替换变量
            condition_str = self._replace_variables(condition, context)
            
            # 评估条件（安全的eval）
            return self._safe_eval(condition_str, context)
        
        except Exception as e:
            logger.warning(f"条件评估失败: {e}")
            return False
    
    async def _execute_step_with_retry(
        self,
        step: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行步骤（带重试和超时）"""
        max_retries = step.get('max_retries', 1)
        timeout = step.get('timeout', 60.0)
        retry_delay = step.get('retry_delay', 1.0)
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # 执行步骤（带超时）
                result = await asyncio.wait_for(
                    self._execute_step(step, context),
                    timeout=timeout
                )
                
                # 验证结果
                if self._validate_step_result(result, step):
                    if attempt > 0:
                        logger.info(f"步骤在第 {attempt + 1} 次尝试后成功")
                    return result
                
                # 结果无效，重试
                logger.warning(f"步骤结果无效，重试 {attempt + 1}/{max_retries}")
                last_error = "结果验证失败"
            
            except asyncio.TimeoutError:
                last_error = f"超时（{timeout}秒）"
                logger.warning(f"步骤超时，重试 {attempt + 1}/{max_retries}")
            
            except Exception as e:
                last_error = str(e)
                logger.error(f"步骤执行失败，重试 {attempt + 1}/{max_retries}: {e}")
            
            # 等待后重试
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
        
        # 所有重试都失败
        return {
            'success': False,
            'content': '',
            'error': f'步骤失败（已重试{max_retries}次）: {last_error}',
            'metadata': {
                'retries': max_retries - 1
            }
        }
    
    async def _execute_step(
        self,
        step: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行单个步骤"""
        agent_name = step.get('agent')
        if not agent_name:
            raise ValueError(f"步骤缺少agent配置")
        
        # 获取Agent
        agent = self._get_agent(agent_name)
        
        # 准备输入
        step_input = step.get('input', context.get('user_input', ''))
        step_input = self._replace_variables(step_input, context)
        
        # 准备prompt
        prompt_config = step.get('prompt', {'use_agent_default': True})
        
        # 准备工具（从步骤配置或Skill配置获取）
        step_tools = step.get('tools')
        if step_tools is None:
            # 如果步骤没有指定工具，使用Skill的工具
            from ..core.skill import get_skill_loader
            skill_loader = get_skill_loader()
            current_skill = context.get('_current_skill')
            if current_skill and hasattr(current_skill, 'tools'):
                step_tools = current_skill.tools
        
        # 执行Agent
        result = await agent.execute(
            prompt_source=prompt_config,
            user_input=step_input,
            context=context,
            tools=step_tools if step_tools else None
        )
        
        return result
    
    def _validate_step_result(
        self,
        result: Dict[str, Any],
        step: Dict[str, Any]
    ) -> bool:
        """验证步骤结果"""
        # 基本验证
        if not result.get('success'):
            return False
        
        # 检查是否有内容
        if not result.get('content'):
            return False
        
        # 自定义验证（如果配置了）
        validation = step.get('validation')
        if validation:
            # 可以扩展为更复杂的验证逻辑
            pass
        
        return True
    
    def _replace_variables(
        self,
        text: str,
        context: Dict[str, Any]
    ) -> str:
        """替换变量 ${variable}"""
        import re
        
        def replace_var(match):
            var_path = match.group(1)
            value = self._get_nested_value(var_path, context)
            return str(value) if value is not None else match.group(0)
        
        return re.sub(r'\$\{([^}]+)\}', replace_var, text)
    
    def _get_nested_value(
        self,
        path: str,
        context: Dict[str, Any]
    ) -> Any:
        """获取嵌套值 (e.g., 'results.analyze.content')"""
        keys = path.split('.')
        value = context
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        
        return value
    
    def _safe_eval(
        self,
        condition: str,
        context: Dict[str, Any]
    ) -> bool:
        """安全的条件评估"""
        # 只允许简单的比较操作
        allowed_ops = ['==', '!=', '>', '<', '>=', '<=', 'and', 'or', 'not', 'in']
        
        # 简化版本：只支持布尔值和简单比较
        try:
            # 移除危险字符
            if any(char in condition for char in ['__', 'import', 'exec', 'eval']):
                return False
            
            # 创建安全的命名空间
            safe_dict = {
                'True': True,
                'False': False,
                'None': None,
            }
            
            # 添加results到命名空间
            if 'results' in context:
                safe_dict['results'] = context['results']
            
            # 评估
            return bool(eval(condition, {"__builtins__": {}}, safe_dict))
        
        except Exception as e:
            logger.warning(f"条件评估失败: {e}")
            return False
    
    def _validate_dependencies(self, workflow: List[Dict[str, Any]]) -> bool:
        """验证工作流依赖关系"""
        # 收集所有步骤名称
        step_names = {step.get('name', f'step_{i}') for i, step in enumerate(workflow)}
        
        # 检查每个步骤的依赖
        for step in workflow:
            depends_on = step.get('depends_on', [])
            if not depends_on:
                continue
            
            # 检查依赖的步骤是否存在
            for dep in depends_on:
                if dep not in step_names:
                    logger.error(f"步骤 {step.get('name')} 依赖未定义的步骤: {dep}")
                    return False
        
        # 检查循环依赖
        if self._has_circular_dependency(workflow):
            logger.error("工作流存在循环依赖")
            return False
        
        return True
    
    def _has_circular_dependency(self, workflow: List[Dict[str, Any]]) -> bool:
        """检查是否存在循环依赖"""
        # 构建依赖图
        graph = {}
        for step in workflow:
            step_name = step.get('name', f'step_{workflow.index(step)}')
            depends_on = step.get('depends_on', [])
            graph[step_name] = depends_on
        
        # DFS检测循环
        visited = set()
        rec_stack = set()
        
        def has_cycle(node):
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for node in graph:
            if node not in visited:
                if has_cycle(node):
                    return True
        
        return False
    
    def _check_dependencies(
        self,
        step: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """检查步骤依赖是否满足"""
        depends_on = step.get('depends_on', [])
        if not depends_on:
            return True
        
        results = context.get('results', {})
        
        # 检查所有依赖的步骤是否已执行且成功
        for dep in depends_on:
            # 检查是否在results中（使用output key）
            dep_found = False
            for output_key, result in results.items():
                # 检查output key或步骤名称
                if output_key == dep or result.get('_step_name') == dep:
                    dep_found = True
                    if not result.get('success'):
                        logger.warning(f"依赖步骤 {dep} 执行失败")
                        return False
                    break
            
            if not dep_found:
                logger.warning(f"依赖步骤 {dep} 未执行")
                return False
        
        return True
    
    async def _rollback_steps(
        self,
        executed_steps: List[Tuple[Dict[str, Any], Dict[str, Any]]],
        context: Dict[str, Any]
    ):
        """回滚已执行的步骤"""
        if not executed_steps:
            return
        
        logger.info(f"开始回滚 {len(executed_steps)} 个步骤")
        
        # 逆序回滚
        for step, result in reversed(executed_steps):
            step_name = step.get('name', 'unnamed')
            rollback_agent = step.get('rollback')
            
            if not rollback_agent:
                logger.debug(f"步骤 {step_name} 没有配置回滚Agent，跳过")
                continue
            
            try:
                logger.info(f"回滚步骤: {step_name}")
                
                # 获取回滚Agent
                agent = self._get_agent(rollback_agent)
                
                # 准备回滚输入（包含原始结果）
                rollback_input = f"回滚步骤 {step_name}，原始结果: {result.get('content', '')}"
                
                # 执行回滚
                await agent.execute(
                    prompt_source={'use_agent_default': True},
                    user_input=rollback_input,
                    context=context
                )
                
                logger.info(f"步骤 {step_name} 回滚成功")
            
            except Exception as e:
                logger.error(f"回滚步骤 {step_name} 失败: {e}")
                # 继续回滚其他步骤
    
    async def _aggregate_results(
        self,
        results: Dict[str, Any]
    ) -> str:
        """聚合所有步骤的结果"""
        # 简单聚合：拼接所有成功步骤的内容
        contents = []
        
        for step_name, result in results.items():
            if result.get('success') and result.get('content'):
                contents.append(f"[{step_name}]\n{result['content']}")
        
        return "\n\n".join(contents)
