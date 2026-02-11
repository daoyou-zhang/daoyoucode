"""
Agent注册表

管理所有Agent的注册和获取
"""

from typing import Dict, Optional, List
import logging

from .base import BaseAgent, AgentConfig

logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    Agent注册表（单例）
    
    参考oh-my-opencode的builtinAgents设计
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._agents: Dict[str, BaseAgent] = {}
        self._configs: Dict[str, AgentConfig] = {}
        self._initialized = True
        
        logger.info("Agent注册表已初始化")
    
    def register(self, agent: BaseAgent):
        """
        注册Agent
        
        Args:
            agent: Agent实例
        """
        name = agent.name
        
        if name in self._agents:
            logger.warning(f"Agent '{name}' 已存在，将被覆盖")
        
        self._agents[name] = agent
        self._configs[name] = agent.config
        
        logger.info(f"已注册Agent: {name} ({agent.config.description})")
    
    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """
        获取Agent
        
        Args:
            name: Agent名称
        
        Returns:
            Agent实例，如果不存在返回None
        """
        return self._agents.get(name)
    
    def get_config(self, name: str) -> Optional[AgentConfig]:
        """获取Agent配置"""
        return self._configs.get(name)
    
    def list_agents(self) -> List[str]:
        """列出所有已注册的Agent"""
        return list(self._agents.keys())
    
    def get_agents_info(self) -> Dict[str, Dict]:
        """
        获取所有Agent的信息
        
        Returns:
            {
                "agent_name": {
                    "description": "...",
                    "model": "...",
                    "read_only": bool,
                    ...
                }
            }
        """
        return {
            name: {
                'description': config.description,
                'model': config.model,
                'temperature': config.temperature,
                'read_only': config.read_only,
                'chinese_optimized': config.chinese_optimized,
                'thinking_budget': config.thinking_budget,
            }
            for name, config in self._configs.items()
        }
    
    def unregister(self, name: str):
        """注销Agent"""
        if name in self._agents:
            del self._agents[name]
            del self._configs[name]
            logger.info(f"已注销Agent: {name}")


def get_agent_registry() -> AgentRegistry:
    """获取Agent注册表单例"""
    return AgentRegistry()
