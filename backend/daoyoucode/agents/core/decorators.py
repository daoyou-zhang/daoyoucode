"""
装饰器

提供常用的装饰器功能
"""

from functools import wraps
from typing import Callable
import logging

logger = logging.getLogger(__name__)


def require_permission(action: str, path_param: str = 'path'):
    """
    权限检查装饰器
    
    Args:
        action: 权限动作 (read/write/execute/delete)
        path_param: 路径参数名
    
    Example:
        @require_permission('write', 'file_path')
        async def write_file(file_path: str, content: str):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            from .permission import get_permission_manager
            
            # 获取路径参数
            path = kwargs.get(path_param)
            if not path:
                # 尝试从位置参数获取
                import inspect
                sig = inspect.signature(func)
                params = list(sig.parameters.keys())
                if path_param in params:
                    idx = params.index(path_param)
                    if idx < len(args):
                        path = args[idx]
            
            if not path:
                raise ValueError(f"无法获取路径参数: {path_param}")
            
            # 检查权限
            manager = get_permission_manager()
            agent_name = kwargs.get('agent_name')
            
            allowed = await manager.check_permission(action, path, agent_name)
            
            if not allowed:
                raise PermissionError(
                    f"权限被拒绝: {action} {path}"
                )
            
            # 执行函数
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def log_execution(level: str = 'INFO'):
    """
    日志装饰器
    
    Args:
        level: 日志级别
    
    Example:
        @log_execution('DEBUG')
        async def my_function():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            func_name = func.__name__
            
            # 记录开始
            logger.log(
                getattr(logging, level),
                f"开始执行: {func_name}"
            )
            
            try:
                result = await func(*args, **kwargs)
                
                # 记录成功
                logger.log(
                    getattr(logging, level),
                    f"执行成功: {func_name}"
                )
                
                return result
            
            except Exception as e:
                # 记录失败
                logger.error(
                    f"执行失败: {func_name}, 错误: {e}",
                    exc_info=True
                )
                raise
        
        return wrapper
    return decorator


def retry_on_error(max_retries: int = 3, delay: float = 1.0):
    """
    重试装饰器
    
    Args:
        max_retries: 最大重试次数
        delay: 重试延迟（秒）
    
    Example:
        @retry_on_error(max_retries=3, delay=1.0)
        async def unstable_function():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            import asyncio
            
            last_error = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                
                except Exception as e:
                    last_error = e
                    
                    if attempt < max_retries:
                        logger.warning(
                            f"执行失败（第{attempt + 1}次），"
                            f"{delay}秒后重试: {e}"
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"达到最大重试次数({max_retries})，放弃: {e}"
                        )
            
            raise last_error
        
        return wrapper
    return decorator


def cache_result(ttl: int = 60):
    """
    缓存装饰器
    
    Args:
        ttl: 缓存时间（秒）
    
    Example:
        @cache_result(ttl=60)
        async def expensive_function(arg):
            ...
    """
    def decorator(func: Callable):
        cache = {}
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            import time
            import hashlib
            import json
            
            # 生成缓存键
            key_data = {
                'args': args,
                'kwargs': kwargs
            }
            key = hashlib.md5(
                json.dumps(key_data, sort_keys=True).encode()
            ).hexdigest()
            
            # 检查缓存
            if key in cache:
                cached_value, cached_time = cache[key]
                if time.time() - cached_time < ttl:
                    logger.debug(f"使用缓存结果: {func.__name__}")
                    return cached_value
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 缓存结果
            cache[key] = (result, time.time())
            
            return result
        
        return wrapper
    return decorator
