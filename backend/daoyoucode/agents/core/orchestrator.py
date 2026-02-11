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
