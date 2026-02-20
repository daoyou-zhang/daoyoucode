"""
Hook生命周期系统

提供灵活的扩展点，允许用户在执行流程的关键节点注入自定义逻辑。
采用生命周期Hook设计
"""

from typing import Callable, Dict, List, Any, Optional
from enum import Enum
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class HookEvent(Enum):
    """Hook事件类型"""
    # Executor级别
    PRE_EXECUTE = "pre_execute"           # 执行前
    POST_EXECUTE = "post_execute"         # 执行后
    ON_ERROR = "on_error"                 # 错误时
    
    # Orchestrator级别
    PRE_ORCHESTRATE = "pre_orchestrate"   # 编排前
    POST_ORCHESTRATE = "post_orchestrate" # 编排后
    
    # Agent级别
    PRE_AGENT = "pre_agent"               # Agent执行前
    POST_AGENT = "post_agent"             # Agent执行后
    
    # Tool级别
    PRE_TOOL = "pre_tool"                 # 工具调用前
    POST_TOOL = "post_tool"               # 工具调用后
    
    # Task级别
    TASK_CREATED = "task_created"         # 任务创建
    TASK_STARTED = "task_started"         # 任务开始
    TASK_COMPLETED = "task_completed"     # 任务完成
    TASK_FAILED = "task_failed"           # 任务失败
    
    # Context级别
    CONTEXT_CREATED = "context_created"   # 上下文创建
    CONTEXT_UPDATED = "context_updated"   # 上下文更新
    
    # Memory级别
    MEMORY_SAVED = "memory_saved"         # 记忆保存
    MEMORY_LOADED = "memory_loaded"       # 记忆加载


@dataclass
class HookContext:
    """Hook上下文"""
    event: HookEvent
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取数据"""
        return self.data.get(key, default)
    
    def set(self, key: str, value: Any):
        """设置数据"""
        self.data[key] = value


class Hook:
    """Hook基类"""
    
    def __init__(self, name: str, priority: int = 100):
        """
        初始化Hook
        
        Args:
            name: Hook名称
            priority: 优先级（数字越小越先执行）
        """
        self.name = name
        self.priority = priority
    
    async def execute(self, context: HookContext) -> Optional[HookContext]:
        """
        执行Hook
        
        Args:
            context: Hook上下文
            
        Returns:
            修改后的上下文，或None表示中断执行
        """
        raise NotImplementedError
    
    def __repr__(self):
        return f"Hook(name={self.name}, priority={self.priority})"


class FunctionHook(Hook):
    """函数Hook"""
    
    def __init__(self, name: str, func: Callable, priority: int = 100):
        super().__init__(name, priority)
        self.func = func
    
    async def execute(self, context: HookContext) -> Optional[HookContext]:
        """执行函数Hook"""
        try:
            result = self.func(context)
            # 支持异步函数
            if hasattr(result, '__await__'):
                result = await result
            return result  # 直接返回结果，包括None
        except Exception as e:
            logger.error(f"Hook {self.name} 执行失败: {e}", exc_info=True)
            return context


class HookManager:
    """Hook管理器（单例）"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.hooks: Dict[HookEvent, List[Hook]] = {event: [] for event in HookEvent}
        self._initialized = True
        logger.info("HookManager 初始化完成")
    
    def register(self, event: HookEvent, hook: Hook):
        """
        注册Hook
        
        Args:
            event: Hook事件
            hook: Hook实例
        """
        self.hooks[event].append(hook)
        # 按优先级排序
        self.hooks[event].sort(key=lambda h: h.priority)
        logger.info(f"注册Hook: {hook.name} -> {event.value}")
    
    def register_function(
        self, 
        event: HookEvent, 
        func: Callable, 
        name: Optional[str] = None,
        priority: int = 100
    ):
        """
        注册函数Hook
        
        Args:
            event: Hook事件
            func: Hook函数
            name: Hook名称（默认使用函数名）
            priority: 优先级
        """
        hook_name = name or func.__name__
        hook = FunctionHook(hook_name, func, priority)
        self.register(event, hook)
    
    def unregister(self, event: HookEvent, name: str):
        """
        注销Hook
        
        Args:
            event: Hook事件
            name: Hook名称
        """
        self.hooks[event] = [h for h in self.hooks[event] if h.name != name]
        logger.info(f"注销Hook: {name} <- {event.value}")
    
    async def trigger(
        self, 
        event: HookEvent, 
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> HookContext:
        """
        触发Hook
        
        Args:
            event: Hook事件
            data: Hook数据
            metadata: Hook元数据
            
        Returns:
            最终的Hook上下文
        """
        context = HookContext(
            event=event,
            data=data or {},
            metadata=metadata or {}
        )
        
        hooks = self.hooks.get(event, [])
        if not hooks:
            return context
        
        logger.debug(f"触发Hook: {event.value}, 共 {len(hooks)} 个")
        
        for hook in hooks:
            try:
                result = await hook.execute(context)
                if result is None:
                    # Hook返回None表示中断执行
                    logger.warning(f"Hook {hook.name} 中断了执行流程")
                    context.set('_interrupted', True)
                    context.set('_interrupted_by', hook.name)
                    break
                context = result
            except Exception as e:
                logger.error(f"Hook {hook.name} 执行失败: {e}", exc_info=True)
                # 继续执行其他Hook
        
        return context
    
    def list_hooks(self, event: Optional[HookEvent] = None) -> Dict[str, List[str]]:
        """
        列出所有Hook
        
        Args:
            event: 可选的事件过滤
            
        Returns:
            事件到Hook名称列表的映射
        """
        if event:
            return {event.value: [h.name for h in self.hooks[event]]}
        
        return {
            e.value: [h.name for h in hooks]
            for e, hooks in self.hooks.items()
            if hooks
        }
    
    def clear(self, event: Optional[HookEvent] = None):
        """
        清空Hook
        
        Args:
            event: 可选的事件过滤，None表示清空所有
        """
        if event:
            self.hooks[event] = []
            logger.info(f"清空Hook: {event.value}")
        else:
            for e in HookEvent:
                self.hooks[e] = []
            logger.info("清空所有Hook")


# 全局Hook管理器实例
_hook_manager = HookManager()


def get_hook_manager() -> HookManager:
    """获取Hook管理器实例"""
    return _hook_manager


# 便捷装饰器
def hook(event: HookEvent, priority: int = 100):
    """
    Hook装饰器
    
    使用示例:
        @hook(HookEvent.PRE_EXECUTE, priority=50)
        def my_hook(context: HookContext) -> HookContext:
            print(f"执行前: {context.data}")
            return context
    """
    def decorator(func: Callable):
        manager = get_hook_manager()
        manager.register_function(event, func, priority=priority)
        return func
    return decorator


# 内置Hook示例
class LoggingHook(Hook):
    """日志Hook"""
    
    def __init__(self, priority: int = 1000):
        super().__init__("logging", priority)
    
    async def execute(self, context: HookContext) -> HookContext:
        """记录日志"""
        logger.info(f"[Hook] {context.event.value}: {context.data.get('name', 'unknown')}")
        return context


class TimingHook(Hook):
    """计时Hook"""
    
    def __init__(self, priority: int = 10):
        super().__init__("timing", priority)
    
    async def execute(self, context: HookContext) -> HookContext:
        """记录时间"""
        import time
        
        if context.event.value.startswith('pre_'):
            # 开始计时
            context.metadata['start_time'] = time.time()
        elif context.event.value.startswith('post_'):
            # 结束计时
            start_time = context.metadata.get('start_time')
            if start_time:
                elapsed = time.time() - start_time
                context.metadata['elapsed_time'] = elapsed
                logger.info(f"[Timing] {context.data.get('name', 'unknown')}: {elapsed:.2f}s")
        
        return context


class ValidationHook(Hook):
    """验证Hook"""
    
    def __init__(self, priority: int = 5):
        super().__init__("validation", priority)
    
    async def execute(self, context: HookContext) -> Optional[HookContext]:
        """验证数据"""
        # 示例：验证必需字段
        required_fields = context.metadata.get('required_fields', [])
        for field in required_fields:
            if field not in context.data:
                logger.error(f"验证失败: 缺少必需字段 {field}")
                return None  # 中断执行
        
        return context
