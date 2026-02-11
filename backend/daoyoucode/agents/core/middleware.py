"""
中间件基类和注册表

中间件提供可选的能力增强
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class BaseMiddleware(ABC):
    """中间件基类"""
    
    def __init__(self):
        self.name = self.__class__.__name__
        self.logger = logging.getLogger(f"middleware.{self.name}")
    
    @abstractmethod
    async def process(
        self,
        user_input: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """处理请求，增强上下文"""
        pass


class MiddlewareRegistry:
    """中间件注册表"""
    
    def __init__(self):
        self._middleware: Dict[str, type] = {}
        self._instances: Dict[str, BaseMiddleware] = {}
    
    def register(self, name: str, middleware_class: type):
        """注册中间件"""
        if not issubclass(middleware_class, BaseMiddleware):
            raise TypeError(f"{middleware_class} must inherit from BaseMiddleware")
        
        self._middleware[name] = middleware_class
        logger.info(f"已注册中间件: {name}")
    
    def get(self, name: str) -> BaseMiddleware:
        """获取中间件实例（单例）"""
        if name not in self._middleware:
            logger.warning(f"中间件 '{name}' 未注册")
            return None
        
        if name not in self._instances:
            self._instances[name] = self._middleware[name]()
        
        return self._instances[name]
    
    def list_middleware(self) -> list:
        """列出所有中间件"""
        return list(self._middleware.keys())


# 全局注册表
_middleware_registry = MiddlewareRegistry()


def get_middleware_registry() -> MiddlewareRegistry:
    """获取中间件注册表"""
    return _middleware_registry


def get_middleware(name: str) -> BaseMiddleware:
    """获取中间件"""
    return _middleware_registry.get(name)


def register_middleware(name: str, middleware_class: type):
    """注册中间件"""
    _middleware_registry.register(name, middleware_class)
