"""
条件分支编排器

根据条件选择不同的执行路径
"""

from ..core.orchestrator import BaseOrchestrator
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class ConditionalOrchestrator(BaseOrchestrator):
    """
    条件分支编排器
    
    根据条件选择执行if_path或else_path
    """
    
    async def execute(
        self,
        skill,
        user_input: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行条件分支
        
        Skill配置示例:
        condition: ${context.language} == 'python'
        if_path:
          agent: python_expert
        else_path:
          agent: general_programmer
        """
        # 获取条件
        condition = getattr(skill, 'condition', None)
        if not condition:
            return {
                'success': False,
                'content': '',
                'error': 'Skill未定义condition'
            }
        
        # 应用中间件
        if skill.middleware:
            for middleware_name in skill.middleware:
                context = await self._apply_middleware(
                    middleware_name,
                    user_input,
                    context
                )
        
        # 评估条件
        condition_result = await self._evaluate_condition(condition, context)
        
        logger.info(f"条件评估结果: {condition_result}")
        
        # 选择执行路径
        if condition_result:
            path = getattr(skill, 'if_path', None)
            path_name = 'if_path'
        else:
            path = getattr(skill, 'else_path', None)
            path_name = 'else_path'
        
        if not path:
            return {
                'success': False,
                'content': '',
                'error': f'Skill未定义{path_name}'
            }
        
        # 执行选中的路径
        result = await self._execute_path(path, user_input, context)
        
        result['metadata'] = result.get('metadata', {})
        result['metadata'].update({
            'orchestrator': 'conditional',
            'condition': condition,
            'condition_result': condition_result,
            'path_executed': path_name
        })
        
        return result
    
    async def _evaluate_condition(
        self,
        condition: str,
        context: Dict[str, Any]
    ) -> bool:
        """评估条件"""
        try:
            # 替换变量
            condition_str = self._replace_variables(condition, context)
            
            # 安全评估
            return self._safe_eval(condition_str, context)
        
        except Exception as e:
            logger.error(f"条件评估失败: {e}", exc_info=True)
            return False
    
    async def _execute_path(
        self,
        path: Dict[str, Any],
        user_input: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行路径"""
        agent_name = path.get('agent')
        if not agent_name:
            raise ValueError("路径缺少agent配置")
        
        # 获取Agent
        agent = self._get_agent(agent_name)
        
        # 准备prompt
        prompt_config = path.get('prompt', {'use_agent_default': True})
        
        # 执行
        result = await agent.execute(
            prompt_source=prompt_config,
            user_input=user_input,
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
        """获取嵌套值"""
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
            
            # 添加context到命名空间
            safe_dict['context'] = context
            
            # 评估
            return bool(eval(condition, {"__builtins__": {}}, safe_dict))
        
        except Exception as e:
            logger.warning(f"条件评估失败: {e}")
            return False
