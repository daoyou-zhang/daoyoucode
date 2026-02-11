"""
简单编排器

直接执行单个Agent
"""

from typing import Dict, Any, Optional
from ..core.orchestrator import BaseOrchestrator


class SimpleOrchestrator(BaseOrchestrator):
    """简单编排器"""
    
    async def execute(
        self,
        skill: 'SkillConfig',
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行Skill"""
        if context is None:
            context = {}
        
        self.logger.info(f"执行Skill: {skill.name}, Agent: {skill.agent}")
        
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
            llm_config=skill.llm
        )
        
        # 5. 返回结果
        return {
            'success': result.success,
            'content': result.content,
            'metadata': {
                **result.metadata,
                'skill': skill.name,
                'agent': skill.agent,
                'orchestrator': 'simple'
            },
            'error': result.error
        }
    
    def _prepare_prompt_source(self, skill: 'SkillConfig') -> Dict[str, Any]:
        """准备prompt来源配置"""
        if skill.prompt:
            if isinstance(skill.prompt, dict):
                return skill.prompt
            if isinstance(skill.prompt, str):
                return {'file': skill.prompt}
        
        return {'use_agent_default': True}
