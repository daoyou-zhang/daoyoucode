"""
简单编排器（增强版）

直接执行单个Agent，支持重试和结果验证
"""

from typing import Dict, Any, Optional
import time
import asyncio
from ..core.orchestrator import BaseOrchestrator


class SimpleOrchestrator(BaseOrchestrator):
    """
    简单编排器（增强版）
    
    新增功能：
    - 自动重试机制
    - 结果验证
    - 成本追踪
    - 执行时间统计
    """
    
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        super().__init__()
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    async def execute(
        self,
        skill: 'SkillConfig',
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行Skill（带重试）"""
        if context is None:
            context = {}
        
        # 获取配置的重试次数（优先使用Skill配置）
        max_retries = getattr(skill, 'max_retries', self.max_retries)
        retry_delay = getattr(skill, 'retry_delay', self.retry_delay)
        
        self.logger.info(f"执行Skill: {skill.name}, Agent: {skill.agent}, 最大重试: {max_retries}")
        
        start_time = time.time()
        last_error = None
        
        # 重试循环
        for attempt in range(max_retries):
            try:
                # 执行一次
                result = await self._execute_once(skill, user_input, context)
                
                # 验证结果
                if self._validate_result(result):
                    # 成功，添加元数据
                    duration = time.time() - start_time
                    result['metadata']['duration'] = duration
                    result['metadata']['retries'] = attempt
                    
                    self.logger.info(f"执行成功，耗时: {duration:.2f}s, 重试次数: {attempt}")
                    return result
                
                # 结果无效，记录并重试
                self.logger.warning(f"结果验证失败，重试 {attempt + 1}/{max_retries}")
                last_error = "结果验证失败"
                
                # 等待后重试
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
            
            except Exception as e:
                last_error = e
                self.logger.error(f"执行失败 {attempt + 1}/{max_retries}: {e}")
                
                # 等待后重试
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
        
        # 所有重试都失败
        duration = time.time() - start_time
        
        return {
            'success': False,
            'content': '',
            'error': f'执行失败（已重试{max_retries}次）: {last_error}',
            'metadata': {
                'skill': skill.name,
                'agent': skill.agent,
                'orchestrator': 'simple',
                'duration': duration,
                'retries': max_retries,
                'failed': True
            },
            'tools_used': [],
            'tokens_used': 0,
            'cost': 0.0
        }
    
    async def _execute_once(
        self,
        skill: 'SkillConfig',
        user_input: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行一次（不重试）"""
        
        # 1. 应用中间件
        if skill.middleware:
            for middleware_name in skill.middleware:
                self.logger.debug(f"应用中间件: {middleware_name}")
                context = await self._apply_middleware(
                    middleware_name,
                    user_input,
                    context
                )
        
        # 2. 获取Agent
        agent = self._get_agent(skill.agent)
        
        # 3. 准备prompt来源
        prompt_source = self._prepare_prompt_source(skill)
        
        # 4. 执行Agent
        result = await agent.execute(
            prompt_source=prompt_source,
            user_input=user_input,
            context=context,
            llm_config=skill.llm,
            tools=skill.tools if skill.tools else None
        )
        
        # 5. 返回结果
        return {
            'success': result.success,
            'content': result.content,
            'metadata': {
                **result.metadata,
                'skill': skill.name,
                'agent': skill.agent,
                'orchestrator': 'simple',
                'tools_used': result.tools_used,
                'tokens_used': result.tokens_used,
                'cost': result.cost
            },
            'error': result.error,
            'tools_used': result.tools_used,
            'tokens_used': result.tokens_used,
            'cost': result.cost
        }
    
    def _validate_result(self, result: Dict[str, Any]) -> bool:
        """
        验证结果是否有效
        
        验证规则：
        1. success标志为True
        2. content不为空
        3. 没有error
        """
        if not result.get('success'):
            self.logger.debug("验证失败: success=False")
            return False
        
        if not result.get('content'):
            self.logger.debug("验证失败: content为空")
            return False
        
        if result.get('error'):
            self.logger.debug(f"验证失败: 有错误 - {result['error']}")
            return False
        
        return True
    
    def _prepare_prompt_source(self, skill: 'SkillConfig') -> Dict[str, Any]:
        """准备prompt来源配置"""
        if skill.prompt:
            if isinstance(skill.prompt, dict):
                return skill.prompt
            if isinstance(skill.prompt, str):
                return {'file': skill.prompt}
        
        return {'use_agent_default': True}
