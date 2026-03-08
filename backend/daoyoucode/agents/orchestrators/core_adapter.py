"""
CoreOrchestrator 适配器

将 CoreOrchestrator 适配到现有的编排器系统中
"""

from typing import Dict, Any, Optional
import logging

from ..core.orchestrator import BaseOrchestrator
from ..core.core_orchestrator import CoreOrchestrator

logger = logging.getLogger(__name__)


class CoreOrchestratorAdapter(BaseOrchestrator):
    """
    CoreOrchestrator 适配器
    
    将 CoreOrchestrator 适配到 BaseOrchestrator 接口
    """
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("orchestrator.CoreAdapter")
    
    async def execute(
        self,
        skill: 'SkillConfig',
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行 Skill
        
        Args:
            skill: Skill 配置
            user_input: 用户输入
            context: 执行上下文
        
        Returns:
            执行结果
        """
        if context is None:
            context = {}
        
        self.logger.info(f"使用 CoreOrchestrator 执行: {skill.name}")
        
        # 创建 CoreOrchestrator 实例
        orchestrator = CoreOrchestrator(skill)
        
        # 执行
        result = await orchestrator.execute(user_input, context)
        
        # 检查是否返回生成器（流式输出）
        import inspect
        if inspect.isasyncgen(result):
            # 流式输出，直接返回生成器
            return result
        
        # 确保返回格式符合 BaseOrchestrator 的要求
        if not isinstance(result, dict):
            self.logger.error(f"CoreOrchestrator 返回了非字典类型: {type(result)}")
            return {
                'success': False,
                'content': '',
                'error': 'Invalid result type from CoreOrchestrator'
            }
        
        return result
