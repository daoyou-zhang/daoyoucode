"""
多Agent编排器

协调多个Agent协作
"""

from typing import Dict, Any, Optional, List
import asyncio
from ..core.orchestrator import BaseOrchestrator


class MultiAgentOrchestrator(BaseOrchestrator):
    """多Agent编排器"""
    
    async def execute(
        self,
        skill: 'SkillConfig',
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行Skill"""
        if context is None:
            context = {}
        
        self.logger.info(f"多Agent执行Skill: {skill.name}")
        
        # 1. 应用中间件
        if skill.middleware:
            for middleware_name in skill.middleware:
                context = await self._apply_middleware(
                    middleware_name,
                    user_input,
                    context
                )
        
        # 2. 获取Agent列表
        agents = self._get_agents_from_skill(skill)
        
        if not agents:
            return {
                'success': False,
                'content': '',
                'error': 'No agents configured'
            }
        
        # 3. 简化版：使用第一个Agent执行
        # 未来可以实现任务分解和并行执行
        main_agent = agents[0]
        prompt_source = {'use_agent_default': True}
        
        result = await main_agent.execute(
            prompt_source=prompt_source,
            user_input=user_input,
            context=context,
            llm_config=skill.llm
        )
        
        return {
            'success': result.success,
            'content': result.content,
            'metadata': {
                **result.metadata,
                'skill': skill.name,
                'orchestrator': 'multi_agent',
                'agents_used': [agent.name for agent in agents]
            },
            'error': result.error
        }
    
    def _get_agents_from_skill(self, skill: 'SkillConfig') -> List:
        """从Skill配置获取Agent列表"""
        agents = []
        
        if skill.agents:
            for agent_name in skill.agents:
                agent = self._get_agent(agent_name)
                agents.append(agent)
        elif skill.agent:
            agent = self._get_agent(skill.agent)
            agents.append(agent)
        
        return agents
