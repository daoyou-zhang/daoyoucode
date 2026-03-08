"""
编排器基类和注册表

编排器负责协调Skill的执行流程
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class BaseOrchestrator(ABC):
    """编排器基类"""
    
    def __init__(self):
        self.name = self.__class__.__name__
        self.logger = logging.getLogger(f"orchestrator.{self.name}")
    
    @abstractmethod
    async def execute(
        self,
        skill: 'SkillConfig',
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行Skill"""
        pass
    
    def _init_workflow_manager(
        self,
        skill: 'SkillConfig',
        context: Dict[str, Any]
    ) -> None:
        """
        初始化工作流管理器（Skill 级别）
        
        在编排器的 execute 方法开始时调用，确保工作流管理器被正确初始化。
        工作流管理器会根据 Skill 的 workflows 配置（包括 source 和 preferred_intents）
        加载可用的工作流集合。
        
        Args:
            skill: Skill 配置
            context: 执行上下文（工作流管理器会被添加到 context 中）
        """
        if skill.skill_path:
            from .workflow_manager import WorkflowManager
            
            skill_config = {
                'skill_dir': str(skill.skill_path),
                'workflows': getattr(skill, 'workflows', {})
            }
            
            workflow_manager = WorkflowManager(skill_config)
            
            self.logger.info(
                f"✅ 工作流管理器已初始化: {len(workflow_manager.workflows)} 个可用工作流"
            )
            
            if workflow_manager.workflows:
                self.logger.debug(f"可用工作流: {list(workflow_manager.workflows.keys())}")
            
            # 将工作流管理器添加到 context，供 Agent 使用
            context['workflow_manager'] = workflow_manager
    
    def _get_agent(self, agent_name: str):
        """获取Agent实例"""
        from .agent import get_agent_registry
        
        registry = get_agent_registry()
        agent = registry.get_agent(agent_name)
        
        if not agent:
            raise ValueError(f"Agent '{agent_name}' not found")
        
        return agent
    
    async def _apply_middleware(
        self,
        middleware_name: str,
        user_input: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """应用中间件"""
        from .middleware import get_middleware
        
        middleware = get_middleware(middleware_name)
        if middleware:
            context = await middleware.process(user_input, context)
        
        return context


class OrchestratorRegistry:
    """编排器注册表"""
    
    def __init__(self):
        self._orchestrators: Dict[str, type] = {}
        self._instances: Dict[str, BaseOrchestrator] = {}
    
    def register(self, name: str, orchestrator_class: type):
        """注册编排器"""
        if not issubclass(orchestrator_class, BaseOrchestrator):
            raise TypeError(f"{orchestrator_class} must inherit from BaseOrchestrator")
        
        self._orchestrators[name] = orchestrator_class
        logger.info(f"已注册编排器: {name}")
    
    def get(self, name: str) -> Optional[BaseOrchestrator]:
        """获取编排器实例（单例）"""
        if name not in self._orchestrators:
            logger.error(f"编排器 '{name}' 未注册")
            return None
        
        if name not in self._instances:
            self._instances[name] = self._orchestrators[name]()
        
        return self._instances[name]
    
    def list_orchestrators(self) -> list:
        """列出所有编排器"""
        return list(self._orchestrators.keys())


# 全局注册表
_orchestrator_registry = OrchestratorRegistry()


def get_orchestrator_registry() -> OrchestratorRegistry:
    """获取编排器注册表"""
    return _orchestrator_registry


def get_orchestrator(name: str) -> Optional[BaseOrchestrator]:
    """获取编排器"""
    return _orchestrator_registry.get(name)


def register_orchestrator(name: str, orchestrator_class: type):
    """注册编排器"""
    _orchestrator_registry.register(name, orchestrator_class)
