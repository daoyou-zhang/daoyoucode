"""
工作流编排器

按步骤执行的工作流，支持条件分支和数据传递
"""

from ..core.orchestrator import BaseOrchestrator
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class WorkflowOrchestrator(BaseOrchestrator):
    """
    工作流编排器
    
    支持：
    - 顺序执行多个步骤
    - 步骤间数据传递
    - 条件分支
    - 错误处理
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
          
          - name: implement
            agent: programmer
            input: ${analysis_result}
            condition: ${analysis_result.feasible}
            output: code_changes
          
          - name: review
            agent: reviewer
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
        
        # 应用中间件
        if skill.middleware:
            for middleware_name in skill.middleware:
                workflow_context = await self._apply_middleware(
                    middleware_name,
                    user_input,
                    workflow_context
                )
        
        # 执行每个步骤
        for step in workflow:
            step_name = step.get('name', 'unnamed')
            
            logger.info(f"执行工作流步骤: {step_name}")
            
            # 检查条件
            if not await self._check_condition(step, workflow_context):
                logger.info(f"跳过步骤 {step_name}（条件不满足）")
                continue
            
            # 执行步骤
            try:
                step_result = await self._execute_step(
                    step,
                    workflow_context
                )
                
                # 保存结果
                output_key = step.get('output', step_name)
                workflow_context['results'][output_key] = step_result
                
                # 如果步骤失败且没有配置继续执行，则中断
                if not step_result.get('success') and not step.get('continue_on_error'):
                    return {
                        'success': False,
                        'content': '',
                        'error': f"步骤 {step_name} 失败: {step_result.get('error')}",
                        'workflow_results': workflow_context['results']
                    }
            
            except Exception as e:
                logger.error(f"步骤 {step_name} 执行失败: {e}", exc_info=True)
                
                if not step.get('continue_on_error'):
                    return {
                        'success': False,
                        'content': '',
                        'error': f"步骤 {step_name} 异常: {e}",
                        'workflow_results': workflow_context['results']
                    }
        
        # 聚合结果
        final_result = await self._aggregate_results(
            workflow_context['results']
        )
        
        return {
            'success': True,
            'content': final_result,
            'workflow_results': workflow_context['results'],
            'metadata': {
                'orchestrator': 'workflow',
                'steps_executed': len(workflow_context['results'])
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
        
        # 执行Agent
        result = await agent.execute(
            prompt_source=prompt_config,
            user_input=step_input,
            context=context
        )
        
        return result
    
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
