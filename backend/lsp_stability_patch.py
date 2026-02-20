"""
LSP 稳定性增强补丁

解决 LSP 服务不稳定的问题：
1. 增加重试机制
2. 改进超时处理
3. 自动重启死亡的客户端
4. 增强错误恢复
"""

import asyncio
import logging
from functools import wraps
from typing import Callable, Any

logger = logging.getLogger(__name__)


def with_retry(max_retries: int = 3, delay: float = 1.0):
    """
    LSP 请求重试装饰器
    
    Args:
        max_retries: 最大重试次数
        delay: 重试延迟（秒）
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except TimeoutError as e:
                    last_error = e
                    logger.warning(f"LSP 请求超时 (尝试 {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(delay * (attempt + 1))
                except RuntimeError as e:
                    if "not running" in str(e):
                        last_error = e
                        logger.warning(f"LSP 服务器未运行 (尝试 {attempt + 1}/{max_retries})")
                        if attempt < max_retries - 1:
                            # 尝试重启
                            await asyncio.sleep(delay)
                    else:
                        raise
                except Exception as e:
                    logger.error(f"LSP 请求失败: {e}")
                    raise
            
            # 所有重试都失败
            raise last_error or Exception("LSP 请求失败")
        
        return wrapper
    return decorator


class LSPClientWrapper:
    """
    LSP 客户端包装器，提供稳定性增强
    """
    
    def __init__(self, client, manager, root: str, server_config):
        self.client = client
        self.manager = manager
        self.root = root
        self.server_config = server_config
        self._lock = asyncio.Lock()
    
    async def _ensure_alive(self):
        """确保客户端存活"""
        if not self.client.is_alive():
            logger.warning("LSP 客户端已死亡，正在重启...")
            
            # 停止旧客户端
            try:
                await self.client.stop()
            except:
                pass
            
            # 获取新客户端
            self.client = await self.manager.get_client(self.root, self.server_config)
            logger.info("LSP 客户端已重启")
    
    @with_retry(max_retries=3, delay=1.0)
    async def diagnostics(self, file_path: str, wait_time: float = 2.0):
        """获取诊断信息（带重试）"""
        async with self._lock:
            await self._ensure_alive()
            return await self.client.diagnostics(file_path, wait_time)
    
    @with_retry(max_retries=3, delay=1.0)
    async def definition(self, file_path: str, line: int, character: int):
        """跳转到定义（带重试）"""
        async with self._lock:
            await self._ensure_alive()
            return await self.client.definition(file_path, line, character)
    
    @with_retry(max_retries=3, delay=1.0)
    async def references(self, file_path: str, line: int, character: int, include_declaration: bool = True):
        """查找引用（带重试）"""
        async with self._lock:
            await self._ensure_alive()
            return await self.client.references(file_path, line, character, include_declaration)
    
    @with_retry(max_retries=3, delay=1.0)
    async def hover(self, file_path: str, line: int, character: int):
        """获取 hover 信息（带重试）"""
        async with self._lock:
            await self._ensure_alive()
            return await self.client.hover(file_path, line, character)
    
    @with_retry(max_retries=3, delay=1.0)
    async def document_symbols(self, file_path: str):
        """获取文档符号（带重试）"""
        async with self._lock:
            await self._ensure_alive()
            return await self.client.document_symbols(file_path)
    
    @with_retry(max_retries=3, delay=1.0)
    async def workspace_symbols(self, query: str):
        """搜索工作区符号（带重试）"""
        async with self._lock:
            await self._ensure_alive()
            return await self.client.workspace_symbols(query)
    
    @with_retry(max_retries=3, delay=1.0)
    async def rename(self, file_path: str, line: int, character: int, new_name: str):
        """重命名符号（带重试）"""
        async with self._lock:
            await self._ensure_alive()
            return await self.client.rename(file_path, line, character, new_name)
    
    @with_retry(max_retries=3, delay=1.0)
    async def code_actions(self, file_path: str, line: int, character: int):
        """获取代码操作（带重试）"""
        async with self._lock:
            await self._ensure_alive()
            return await self.client.code_actions(file_path, line, character)
    
    def is_alive(self) -> bool:
        """检查客户端是否存活"""
        return self.client.is_alive()
    
    async def stop(self):
        """停止客户端"""
        await self.client.stop()


def wrap_lsp_client(client, manager, root: str, server_config):
    """
    包装 LSP 客户端以提供稳定性增强
    
    使用方法：
        client = await manager.get_client(root, server_config)
        wrapped_client = wrap_lsp_client(client, manager, root, server_config)
        
        # 使用包装后的客户端
        result = await wrapped_client.diagnostics(file_path)
    """
    return LSPClientWrapper(client, manager, root, server_config)


# ========== 配置优化建议 ==========

LSP_STABILITY_CONFIG = {
    # 超时配置
    "request_timeout": 30,  # 增加到 30 秒
    "diagnostics_wait_time": 3.0,  # 诊断等待时间
    "initialization_wait_time": 1.0,  # 初始化等待时间
    
    # 重试配置
    "max_retries": 3,
    "retry_delay": 1.0,
    
    # 清理配置
    "idle_timeout": 600,  # 10 分钟
    "cleanup_interval": 120,  # 2 分钟检查一次
    
    # 缓存配置
    "max_opened_files": 50,  # 最多打开 50 个文件
    "max_diagnostics_cache": 100,  # 最多缓存 100 个文件的诊断
}


def apply_stability_config():
    """
    应用稳定性配置到 LSP 工具
    
    在项目启动时调用此函数
    """
    from daoyoucode.agents.tools import lsp_tools
    
    # 更新超时配置
    if hasattr(lsp_tools, 'LSPClient'):
        # 可以通过猴子补丁的方式修改默认值
        original_send = lsp_tools.LSPClient._send
        
        async def patched_send(self, method: str, params: Any = None):
            """带更长超时的 _send"""
            if not self.process or self.process_exited or self.process.returncode is not None:
                stderr = '\n'.join(self.stderr_buffer[-10:])
                raise RuntimeError(
                    f"LSP server not running (returncode: {self.process.returncode if self.process else 'None'})\n"
                    f"stderr: {stderr}"
                )
            
            self.request_id += 1
            request_id = self.request_id
            
            msg = {
                'jsonrpc': '2.0',
                'id': request_id,
                'method': method,
                'params': params
            }
            
            import json
            content = json.dumps(msg)
            header = f'Content-Length: {len(content.encode())}\r\n\r\n'
            
            self.process.stdin.write((header + content).encode())
            
            # 创建Future
            future = asyncio.Future()
            self.pending_requests[request_id] = future
            
            # 设置更长的超时
            timeout = LSP_STABILITY_CONFIG["request_timeout"]
            
            async def timeout_handler():
                await asyncio.sleep(timeout)
                if request_id in self.pending_requests:
                    del self.pending_requests[request_id]
                    if not future.done():
                        stderr = '\n'.join(self.stderr_buffer[-5:])
                        future.set_exception(
                            TimeoutError(
                                f"LSP request timeout after {timeout}s (method: {method})\n"
                                f"recent stderr: {stderr}"
                            )
                        )
            
            asyncio.create_task(timeout_handler())
            
            return future
        
        lsp_tools.LSPClient._send = patched_send
        logger.info("✅ LSP 稳定性配置已应用")


if __name__ == "__main__":
    print("LSP 稳定性增强补丁")
    print("=" * 60)
    print("\n使用方法：")
    print("\n1. 在项目启动时应用配置：")
    print("   from lsp_stability_patch import apply_stability_config")
    print("   apply_stability_config()")
    print("\n2. 使用包装器：")
    print("   from lsp_stability_patch import wrap_lsp_client")
    print("   client = await manager.get_client(root, server_config)")
    print("   wrapped_client = wrap_lsp_client(client, manager, root, server_config)")
    print("   result = await wrapped_client.diagnostics(file_path)")
    print("\n3. 运行健康检查：")
    print("   python lsp_health_check.py")
    print("   python lsp_health_check.py --fix")
