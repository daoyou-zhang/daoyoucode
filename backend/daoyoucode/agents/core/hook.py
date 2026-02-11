"""
Hook系统

提供统一的扩展点，类似oh-my-opencode的31个Hook
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class HookContext:
    """Hook上下文"""
    skill_name: str
    user_input: str
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseHook(ABC):
    """Hook基类"""
    
    def __init__(self, name: str):
        self.name = name
        self.enabled = True
        self.logger = logging.getLogger(f"hook.{name}")
    
    @abstractmethod
    async def on_before_execute(
        self,
        context: HookContext
    ) -> HookContext:
        """
        执行前Hook
        
        Args:
            context: Hook上下文
        
        Returns:
            修改后的上下文
        """
        pass
    
    @abstractmethod
    async def on_after_execute(
        self,
        context: HookContext,
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行后Hook
        
        Args:
            context: Hook上下文
            result: 执行结果
        
        Returns:
            修改后的结果
        """
        pass
    
    @abstractmethod
    async def on_error(
        self,
        context: HookContext,
        error: Exception
    ) -> Optional[Dict[str, Any]]:
        """
        错误Hook
        
        Args:
            context: Hook上下文
            error: 异常对象
        
        Returns:
            错误处理结果（None表示继续抛出异常）
        """
        pass
    
    def enable(self):
        """启用Hook"""
        self.enabled = True
        self.logger.info(f"Hook '{self.name}' 已启用")
    
    def disable(self):
        """禁用Hook"""
        self.enabled = False
        self.logger.info(f"Hook '{self.name}' 已禁用")


class HookManager:
    """Hook管理器"""
    
    def __init__(self):
        self.hooks: List[BaseHook] = []
        self.logger = logging.getLogger("hook.manager")
    
    def register(self, hook: BaseHook):
        """注册Hook"""
        self.hooks.append(hook)
        self.logger.info(f"已注册Hook: {hook.name}")
    
    def unregister(self, hook_name: str):
        """注销Hook"""
        self.hooks = [h for h in self.hooks if h.name != hook_name]
        self.logger.info(f"已注销Hook: {hook_name}")
    
    def get_hook(self, hook_name: str) -> Optional[BaseHook]:
        """获取Hook"""
        for hook in self.hooks:
            if hook.name == hook_name:
                return hook
        return None
    
    def list_hooks(self) -> List[str]:
        """列出所有Hook"""
        return [h.name for h in self.hooks]
    
    async def run_before_hooks(
        self,
        context: HookContext
    ) -> HookContext:
        """运行所有before hooks"""
        for hook in self.hooks:
            if not hook.enabled:
                continue
            
            try:
                context = await hook.on_before_execute(context)
            except Exception as e:
                self.logger.error(
                    f"Hook '{hook.name}' before执行失败: {e}",
                    exc_info=True
                )
        
        return context
    
    async def run_after_hooks(
        self,
        context: HookContext,
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """运行所有after hooks"""
        for hook in self.hooks:
            if not hook.enabled:
                continue
            
            try:
                result = await hook.on_after_execute(context, result)
            except Exception as e:
                self.logger.error(
                    f"Hook '{hook.name}' after执行失败: {e}",
                    exc_info=True
                )
        
        return result
    
    async def run_error_hooks(
        self,
        context: HookContext,
        error: Exception
    ) -> Optional[Dict[str, Any]]:
        """运行所有error hooks"""
        for hook in self.hooks:
            if not hook.enabled:
                continue
            
            try:
                result = await hook.on_error(context, error)
                if result is not None:
                    # Hook处理了错误，返回结果
                    return result
            except Exception as e:
                self.logger.error(
                    f"Hook '{hook.name}' error执行失败: {e}",
                    exc_info=True
                )
        
        return None


# 全局Hook管理器
_hook_manager = HookManager()


def get_hook_manager() -> HookManager:
    """获取Hook管理器"""
    return _hook_manager


def register_hook(hook: BaseHook):
    """注册Hook"""
    _hook_manager.register(hook)


def unregister_hook(hook_name: str):
    """注销Hook"""
    _hook_manager.unregister(hook_name)
