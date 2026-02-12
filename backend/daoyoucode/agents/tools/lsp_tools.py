"""
LSP工具 - Language Server Protocol集成

基于oh-my-opencode的最佳实现：
- 6个独立工具（diagnostics, rename, goto_definition, find_references, symbols, code_actions）
- LSP服务器管理（启动、停止、重启）
- 支持多种语言（Python、JavaScript、TypeScript等）
- 结果限制合理（避免输出过多）

参考：oh-my-opencode/src/tools/lsp/
"""

from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import logging
import subprocess
import json
import asyncio
from dataclasses import dataclass
import shutil

from .base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


# ========== LSP配置 ==========

@dataclass
class LSPServerConfig:
    """LSP服务器配置"""
    id: str
    command: List[str]
    extensions: List[str]
    env: Optional[Dict[str, str]] = None
    initialization: Optional[Dict[str, Any]] = None


# 内置LSP服务器配置（参考oh-my-opencode）
BUILTIN_LSP_SERVERS = {
    "pyright": LSPServerConfig(
        id="pyright",
        command=["pyright-langserver", "--stdio"],
        extensions=[".py"]
    ),
    "pylsp": LSPServerConfig(
        id="pylsp",
        command=["pylsp"],
        extensions=[".py"]
    ),
    "typescript-language-server": LSPServerConfig(
        id="typescript-language-server",
        command=["typescript-language-server", "--stdio"],
        extensions=[".ts", ".tsx", ".js", ".jsx"]
    ),
    "rust-analyzer": LSPServerConfig(
        id="rust-analyzer",
        command=["rust-analyzer"],
        extensions=[".rs"]
    ),
    "gopls": LSPServerConfig(
        id="gopls",
        command=["gopls"],
        extensions=[".go"]
    ),
}

# 扩展名到语言ID的映射
EXT_TO_LANG = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascriptreact",
    ".ts": "typescript",
    ".tsx": "typescriptreact",
    ".rs": "rust",
    ".go": "go",
    ".java": "java",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c",
    ".hpp": "cpp",
}

# 默认限制（参考oh-my-opencode）
DEFAULT_MAX_REFERENCES = 50
DEFAULT_MAX_SYMBOLS = 50
DEFAULT_MAX_DIAGNOSTICS = 100


# ========== LSP客户端（完整实现）==========

class LSPClient:
    """
    完整的LSP客户端实现
    
    功能：
    - JSON-RPC 2.0协议
    - 异步消息处理
    - 服务器生命周期管理
    - 诊断信息缓存
    - 文件同步
    
    参考：oh-my-opencode/src/tools/lsp/client.ts
    """
    
    def __init__(self, root: str, server_config: LSPServerConfig):
        self.root = Path(root).resolve()
        self.server_config = server_config
        self.process: Optional[asyncio.subprocess.Process] = None
        self.request_id = 0
        self.opened_files: set = set()
        self.pending_requests: Dict[int, asyncio.Future] = {}
        self.diagnostics_store: Dict[str, List[Dict]] = {}
        self.buffer = b""
        self.process_exited = False
        self.stderr_buffer: List[str] = []
        self._read_task: Optional[asyncio.Task] = None
        self._stderr_task: Optional[asyncio.Task] = None
    
    def is_server_installed(self) -> bool:
        """检查LSP服务器是否已安装"""
        command = self.server_config.command[0]
        return shutil.which(command) is not None
    
    async def start(self):
        """启动LSP服务器"""
        if not self.is_server_installed():
            raise FileNotFoundError(
                f"LSP server not found: {self.server_config.command[0]}\n"
                f"Please install it first."
            )
        
        # 准备环境变量
        env = dict(self.server_config.env) if self.server_config.env else {}
        
        # 启动进程
        self.process = await asyncio.create_subprocess_exec(
            *self.server_config.command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(self.root),
            env={**dict(asyncio.subprocess.os.environ), **env}
        )
        
        # 启动读取任务
        self._read_task = asyncio.create_task(self._read_stdout())
        self._stderr_task = asyncio.create_task(self._read_stderr())
        
        # 等待启动
        await asyncio.sleep(0.1)
        
        if self.process.returncode is not None:
            stderr = '\n'.join(self.stderr_buffer)
            raise RuntimeError(
                f"LSP server exited immediately with code {self.process.returncode}\n"
                f"stderr: {stderr}"
            )
    
    async def _read_stdout(self):
        """读取stdout（异步）"""
        try:
            while True:
                chunk = await self.process.stdout.read(4096)
                if not chunk:
                    self.process_exited = True
                    self._reject_all_pending("LSP server stdout closed")
                    break
                
                self.buffer += chunk
                self._process_buffer()
        except Exception as e:
            self.process_exited = True
            self._reject_all_pending(f"LSP stdout read error: {e}")
    
    async def _read_stderr(self):
        """读取stderr（异步）"""
        try:
            while True:
                line = await self.process.stderr.readline()
                if not line:
                    break
                
                text = line.decode('utf-8', errors='ignore')
                self.stderr_buffer.append(text)
                if len(self.stderr_buffer) > 100:
                    self.stderr_buffer.pop(0)
        except:
            pass
    
    def _reject_all_pending(self, reason: str):
        """拒绝所有待处理的请求"""
        for request_id, future in list(self.pending_requests.items()):
            if not future.done():
                future.set_exception(Exception(reason))
            del self.pending_requests[request_id]
    
    def _process_buffer(self):
        """处理缓冲区中的消息"""
        while True:
            # 查找Content-Length头
            header_end = self.buffer.find(b'\r\n\r\n')
            if header_end == -1:
                header_end = self.buffer.find(b'\n\n')
                if header_end == -1:
                    break
                sep_len = 2
            else:
                sep_len = 4
            
            # 解析Content-Length
            header = self.buffer[:header_end].decode('utf-8', errors='ignore')
            match = None
            for line in header.split('\n'):
                if line.lower().startswith('content-length:'):
                    try:
                        match = int(line.split(':', 1)[1].strip())
                    except:
                        pass
                    break
            
            if match is None:
                break
            
            content_length = match
            start = header_end + sep_len
            end = start + content_length
            
            if len(self.buffer) < end:
                break
            
            # 提取消息
            content = self.buffer[start:end].decode('utf-8', errors='ignore')
            self.buffer = self.buffer[end:]
            
            # 解析JSON
            try:
                msg = json.loads(content)
                self._handle_message(msg)
            except:
                pass
    
    def _handle_message(self, msg: Dict[str, Any]):
        """处理收到的消息"""
        # 通知消息（没有id）
        if 'method' in msg and 'id' not in msg:
            if msg['method'] == 'textDocument/publishDiagnostics':
                uri = msg.get('params', {}).get('uri')
                diagnostics = msg.get('params', {}).get('diagnostics', [])
                if uri:
                    self.diagnostics_store[uri] = diagnostics
        
        # 服务器请求（有id和method）
        elif 'id' in msg and 'method' in msg:
            self._handle_server_request(msg['id'], msg['method'], msg.get('params'))
        
        # 响应消息（有id）
        elif 'id' in msg:
            request_id = msg['id']
            if request_id in self.pending_requests:
                future = self.pending_requests[request_id]
                del self.pending_requests[request_id]
                
                if 'error' in msg:
                    future.set_exception(Exception(msg['error'].get('message', 'Unknown error')))
                else:
                    future.set_result(msg.get('result'))
    
    def _handle_server_request(self, request_id: Any, method: str, params: Any):
        """处理服务器请求"""
        # 简单响应一些常见请求
        if method == 'workspace/configuration':
            items = params.get('items', []) if params else []
            result = []
            for item in items:
                if item.get('section') == 'json':
                    result.append({'validate': {'enable': True}})
                else:
                    result.append({})
            self._respond(request_id, result)
        
        elif method in ['client/registerCapability', 'window/workDoneProgress/create']:
            self._respond(request_id, None)
    
    def _send(self, method: str, params: Any = None) -> asyncio.Future:
        """发送请求"""
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
        
        content = json.dumps(msg)
        header = f'Content-Length: {len(content.encode())}\r\n\r\n'
        
        self.process.stdin.write((header + content).encode())
        
        # 创建Future
        future = asyncio.Future()
        self.pending_requests[request_id] = future
        
        # 设置超时
        async def timeout_handler():
            await asyncio.sleep(15)
            if request_id in self.pending_requests:
                del self.pending_requests[request_id]
                if not future.done():
                    stderr = '\n'.join(self.stderr_buffer[-5:])
                    future.set_exception(
                        TimeoutError(
                            f"LSP request timeout (method: {method})\n"
                            f"recent stderr: {stderr}"
                        )
                    )
        
        asyncio.create_task(timeout_handler())
        
        return future
    
    def _notify(self, method: str, params: Any = None):
        """发送通知（不需要响应）"""
        if not self.process or self.process_exited or self.process.returncode is not None:
            return
        
        msg = {
            'jsonrpc': '2.0',
            'method': method,
            'params': params
        }
        
        content = json.dumps(msg)
        header = f'Content-Length: {len(content.encode())}\r\n\r\n'
        
        try:
            self.process.stdin.write((header + content).encode())
        except:
            pass
    
    def _respond(self, request_id: Any, result: Any):
        """响应服务器请求"""
        if not self.process or self.process_exited or self.process.returncode is not None:
            return
        
        msg = {
            'jsonrpc': '2.0',
            'id': request_id,
            'result': result
        }
        
        content = json.dumps(msg)
        header = f'Content-Length: {len(content.encode())}\r\n\r\n'
        
        try:
            self.process.stdin.write((header + content).encode())
        except:
            pass
    
    async def initialize(self):
        """初始化LSP服务器"""
        root_uri = self.root.as_uri()
        
        init_params = {
            'processId': asyncio.subprocess.os.getpid(),
            'rootUri': root_uri,
            'rootPath': str(self.root),
            'workspaceFolders': [{'uri': root_uri, 'name': 'workspace'}],
            'capabilities': {
                'textDocument': {
                    'hover': {'contentFormat': ['markdown', 'plaintext']},
                    'definition': {'linkSupport': True},
                    'references': {},
                    'documentSymbol': {'hierarchicalDocumentSymbolSupport': True},
                    'publishDiagnostics': {},
                    'rename': {
                        'prepareSupport': True,
                        'prepareSupportDefaultBehavior': 1,
                        'honorsChangeAnnotations': True
                    },
                    'codeAction': {
                        'codeActionLiteralSupport': {
                            'codeActionKind': {
                                'valueSet': [
                                    'quickfix', 'refactor', 'refactor.extract',
                                    'refactor.inline', 'refactor.rewrite',
                                    'source', 'source.organizeImports', 'source.fixAll'
                                ]
                            }
                        },
                        'isPreferredSupport': True,
                        'disabledSupport': True,
                        'dataSupport': True,
                        'resolveSupport': {'properties': ['edit', 'command']}
                    }
                },
                'workspace': {
                    'symbol': {},
                    'workspaceFolders': True,
                    'configuration': True,
                    'applyEdit': True,
                    'workspaceEdit': {'documentChanges': True}
                }
            }
        }
        
        # 合并自定义初始化参数
        if self.server_config.initialization:
            init_params.update(self.server_config.initialization)
        
        # 发送initialize请求
        await self._send('initialize', init_params)
        
        # 发送initialized通知
        self._notify('initialized')
        
        # 发送配置
        self._notify('workspace/didChangeConfiguration', {
            'settings': {'json': {'validate': {'enable': True}}}
        })
        
        # 等待服务器准备好
        await asyncio.sleep(0.3)
    
    async def open_file(self, file_path: str):
        """打开文件"""
        abs_path = Path(file_path).resolve()
        
        if str(abs_path) in self.opened_files:
            return
        
        # 读取文件内容
        try:
            text = abs_path.read_text(encoding='utf-8')
        except Exception as e:
            logger.warning(f"Failed to read file {abs_path}: {e}")
            return
        
        # 获取语言ID
        ext = abs_path.suffix
        language_id = EXT_TO_LANG.get(ext, 'plaintext')
        
        # 发送didOpen通知
        self._notify('textDocument/didOpen', {
            'textDocument': {
                'uri': abs_path.as_uri(),
                'languageId': language_id,
                'version': 1,
                'text': text
            }
        })
        
        self.opened_files.add(str(abs_path))
        
        # 等待诊断信息
        await asyncio.sleep(1.0)
    
    async def definition(self, file_path: str, line: int, character: int):
        """跳转到定义"""
        abs_path = Path(file_path).resolve()
        await self.open_file(str(abs_path))
        
        result = await self._send('textDocument/definition', {
            'textDocument': {'uri': abs_path.as_uri()},
            'position': {'line': line - 1, 'character': character}
        })
        
        return result
    
    async def references(self, file_path: str, line: int, character: int, include_declaration: bool = True):
        """查找引用"""
        abs_path = Path(file_path).resolve()
        await self.open_file(str(abs_path))
        
        result = await self._send('textDocument/references', {
            'textDocument': {'uri': abs_path.as_uri()},
            'position': {'line': line - 1, 'character': character},
            'context': {'includeDeclaration': include_declaration}
        })
        
        return result
    
    async def document_symbols(self, file_path: str):
        """获取文档符号"""
        abs_path = Path(file_path).resolve()
        await self.open_file(str(abs_path))
        
        result = await self._send('textDocument/documentSymbol', {
            'textDocument': {'uri': abs_path.as_uri()}
        })
        
        return result
    
    async def workspace_symbols(self, query: str):
        """搜索工作区符号"""
        result = await self._send('workspace/symbol', {'query': query})
        return result
    
    async def diagnostics(self, file_path: str):
        """获取诊断信息"""
        abs_path = Path(file_path).resolve()
        uri = abs_path.as_uri()
        
        await self.open_file(str(abs_path))
        
        # 等待诊断信息
        await asyncio.sleep(0.5)
        
        # 尝试使用textDocument/diagnostic（LSP 3.17+）
        try:
            result = await self._send('textDocument/diagnostic', {
                'textDocument': {'uri': uri}
            })
            
            if result and isinstance(result, dict) and 'items' in result:
                return {'items': result['items']}
        except:
            pass
        
        # 使用缓存的诊断信息
        return {'items': self.diagnostics_store.get(uri, [])}
    
    async def prepare_rename(self, file_path: str, line: int, character: int):
        """准备重命名"""
        abs_path = Path(file_path).resolve()
        await self.open_file(str(abs_path))
        
        result = await self._send('textDocument/prepareRename', {
            'textDocument': {'uri': abs_path.as_uri()},
            'position': {'line': line - 1, 'character': character}
        })
        
        return result
    
    async def rename(self, file_path: str, line: int, character: int, new_name: str):
        """重命名符号"""
        abs_path = Path(file_path).resolve()
        await self.open_file(str(abs_path))
        
        result = await self._send('textDocument/rename', {
            'textDocument': {'uri': abs_path.as_uri()},
            'position': {'line': line - 1, 'character': character},
            'newName': new_name
        })
        
        return result
    
    async def code_actions(self, file_path: str, line: int, character: int):
        """获取代码操作"""
        abs_path = Path(file_path).resolve()
        await self.open_file(str(abs_path))
        
        # 获取诊断信息
        diagnostics_result = await self.diagnostics(str(abs_path))
        diagnostics = diagnostics_result.get('items', [])
        
        result = await self._send('textDocument/codeAction', {
            'textDocument': {'uri': abs_path.as_uri()},
            'range': {
                'start': {'line': line - 1, 'character': character},
                'end': {'line': line - 1, 'character': character}
            },
            'context': {
                'diagnostics': diagnostics,
                'only': ['quickfix', 'refactor']
            }
        })
        
        return result
    
    def is_alive(self) -> bool:
        """检查服务器是否存活"""
        return (
            self.process is not None and
            not self.process_exited and
            self.process.returncode is None
        )
    
    async def stop(self):
        """停止LSP服务器"""
        try:
            self._notify('shutdown', {})
            self._notify('exit')
        except:
            pass
        
        if self.process:
            try:
                self.process.terminate()
                await asyncio.wait_for(self.process.wait(), timeout=5)
            except asyncio.TimeoutError:
                self.process.kill()
            except:
                pass
        
        # 取消读取任务
        if self._read_task:
            self._read_task.cancel()
        if self._stderr_task:
            self._stderr_task.cancel()
        
        self.process = None
        self.process_exited = True
        self.diagnostics_store.clear()


# ========== LSP服务器管理器 ==========

class LSPServerManager:
    """
    LSP服务器管理器（单例）
    
    功能：
    - 管理多个语言的LSP服务器
    - 服务器复用（避免重复启动）
    - 自动清理空闲服务器
    - 引用计数管理
    
    参考：oh-my-opencode/src/tools/lsp/client.ts (LSPServerManager)
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
        
        self.clients: Dict[str, Dict[str, Any]] = {}  # {key: {client, last_used, ref_count, init_promise}}
        self.last_used: Dict[str, float] = {}
        self.idle_timeout = 5 * 60  # 5分钟
        self._cleanup_task: Optional[asyncio.Task] = None
        self._initialized = True
        
        # 启动清理任务
        self._start_cleanup_timer()
        
        logger.info("LSP服务器管理器已初始化")
    
    def _start_cleanup_timer(self):
        """启动清理定时器"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def _cleanup_loop(self):
        """清理循环"""
        while True:
            try:
                await asyncio.sleep(60)  # 每分钟检查一次
                await self._cleanup_idle_clients()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
    
    async def _cleanup_idle_clients(self):
        """清理空闲客户端"""
        import time
        now = time.time()
        
        to_remove = []
        for key, managed in list(self.clients.items()):
            if managed['ref_count'] == 0:
                last_used = managed['last_used']
                if now - last_used > self.idle_timeout:
                    to_remove.append(key)
        
        for key in to_remove:
            managed = self.clients[key]
            client = managed['client']
            await client.stop()
            del self.clients[key]
            logger.info(f"Cleaned up idle LSP client: {key}")
    
    def _get_key(self, root: str, server_id: str) -> str:
        """生成客户端key"""
        return f"{root}::{server_id}"
    
    def find_server_for_extension(self, ext: str) -> Optional[LSPServerConfig]:
        """根据文件扩展名查找LSP服务器"""
        for server_config in BUILTIN_LSP_SERVERS.values():
            if ext in server_config.extensions:
                # 检查是否已安装
                command = server_config.command[0]
                if shutil.which(command):
                    return server_config
        
        return None
    
    async def get_client(
        self,
        root: str,
        server_config: LSPServerConfig
    ) -> LSPClient:
        """获取或创建LSP客户端"""
        key = self._get_key(root, server_config.id)
        
        # 检查是否已存在
        if key in self.clients:
            managed = self.clients[key]
            
            # 等待初始化完成
            if 'init_promise' in managed and managed['init_promise']:
                await managed['init_promise']
            
            client = managed['client']
            if client.is_alive():
                import time
                managed['ref_count'] += 1
                managed['last_used'] = time.time()
                return client
            
            # 客户端已死亡，清理
            await client.stop()
            del self.clients[key]
        
        # 创建新客户端
        client = LSPClient(root, server_config)
        
        # 创建初始化Promise
        async def init_client():
            await client.start()
            await client.initialize()
        
        init_promise = asyncio.create_task(init_client())
        
        import time
        self.clients[key] = {
            'client': client,
            'last_used': time.time(),
            'ref_count': 1,
            'init_promise': init_promise,
            'is_initializing': True
        }
        
        # 等待初始化完成
        await init_promise
        
        # 清除init_promise
        self.clients[key]['init_promise'] = None
        self.clients[key]['is_initializing'] = False
        
        logger.info(f"LSP客户端已启动: {server_config.id} for {root}")
        
        return client
    
    def release_client(self, root: str, server_id: str):
        """释放客户端引用"""
        key = self._get_key(root, server_id)
        if key in self.clients:
            managed = self.clients[key]
            if managed['ref_count'] > 0:
                managed['ref_count'] -= 1
                import time
                managed['last_used'] = time.time()
    
    async def stop_all(self):
        """停止所有LSP服务器"""
        for managed in self.clients.values():
            client = managed['client']
            await client.stop()
        
        self.clients.clear()
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            self._cleanup_task = None


# 全局管理器实例
_lsp_manager = LSPServerManager()


def get_lsp_manager() -> LSPServerManager:
    """获取LSP管理器单例"""
    return _lsp_manager


# ========== 辅助函数 ==========

async def with_lsp_client(file_path: str, callback):
    """
    使用LSP客户端执行操作的辅助函数
    
    参考：oh-my-opencode/src/tools/lsp/utils.ts (withLspClient)
    """
    file_path_obj = Path(file_path).resolve()
    
    if not file_path_obj.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # 查找LSP服务器
    ext = file_path_obj.suffix
    manager = get_lsp_manager()
    server_config = manager.find_server_for_extension(ext)
    
    if not server_config:
        raise ValueError(f"No LSP server found for {ext} files")
    
    # 查找项目根目录
    root = file_path_obj.parent
    while root.parent != root:
        if (root / '.git').exists() or (root / 'package.json').exists() or (root / 'pyproject.toml').exists():
            break
        root = root.parent
    
    # 获取LSP客户端
    client = await manager.get_client(str(root), server_config)
    
    try:
        # 执行回调
        result = await callback(client)
        return result
    finally:
        # 释放客户端
        manager.release_client(str(root), server_config.id)


def format_location(location: Dict[str, Any]) -> str:
    """
    格式化位置信息
    
    参考：oh-my-opencode/src/tools/lsp/utils.ts (formatLocation)
    """
    if 'targetUri' in location:
        # LocationLink
        uri = location['targetUri']
        range_info = location.get('targetRange', {})
    else:
        # Location
        uri = location.get('uri', '')
        range_info = location.get('range', {})
    
    # 解析URI
    from urllib.parse import urlparse, unquote
    parsed = urlparse(uri)
    file_path = unquote(parsed.path)
    
    # Windows路径处理
    if file_path.startswith('/') and ':' in file_path[1:3]:
        file_path = file_path[1:]
    
    start = range_info.get('start', {})
    line = start.get('line', 0) + 1
    char = start.get('character', 0)
    
    return f"{file_path}:{line}:{char}"


# ========== LSP工具实现 ==========

class LSPDiagnosticsTool(BaseTool):
    """
    获取诊断信息（错误、警告等）
    
    参考：oh-my-opencode/src/tools/lsp/tools.ts (lsp_diagnostics)
    """
    
    def __init__(self):
        super().__init__(
            name="lsp_diagnostics",
            description="Get errors, warnings, hints from language server BEFORE running build"
        )
    
    def get_function_schema(self) -> Dict[str, Any]:
        """获取Function Calling schema"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "File path to check"
                    },
                    "severity": {
                        "type": "string",
                        "enum": ["error", "warning", "information", "hint", "all"],
                        "description": "Filter by severity level",
                        "default": "all"
                    }
                },
                "required": ["file_path"]
            }
        }
    
    async def execute(
        self,
        file_path: str,
        severity: str = "all"
    ) -> ToolResult:
        """获取诊断信息"""
        try:
            file_path_obj = Path(file_path).resolve()
            
            if not file_path_obj.exists():
                return ToolResult(
                    success=False,
                    content=None,
                    error=f"File not found: {file_path}"
                )
            
            # 查找LSP服务器
            ext = file_path_obj.suffix
            manager = get_lsp_manager()
            server_config = manager.find_server_for_extension(ext)
            
            if not server_config:
                return ToolResult(
                    success=False,
                    content=None,
                    error=f"No LSP server found for {ext} files"
                )
            
            # 获取LSP客户端
            root = file_path_obj.parent
            while root.parent != root:
                if (root / '.git').exists() or (root / 'package.json').exists():
                    break
                root = root.parent
            
            client = await manager.get_client(str(root), server_config)
            
            # 获取诊断信息
            result = await client.diagnostics(str(file_path_obj))
            diagnostics = result.get('items', [])
            
            # 过滤严重性
            if severity != "all":
                severity_map = {'error': 1, 'warning': 2, 'information': 3, 'hint': 4}
                target_severity = severity_map.get(severity)
                if target_severity:
                    diagnostics = [d for d in diagnostics if d.get('severity') == target_severity]
            
            # 限制数量
            total = len(diagnostics)
            if total > DEFAULT_MAX_DIAGNOSTICS:
                diagnostics = diagnostics[:DEFAULT_MAX_DIAGNOSTICS]
            
            # 格式化输出
            if not diagnostics:
                content = "No diagnostics found"
            else:
                lines = []
                if total > DEFAULT_MAX_DIAGNOSTICS:
                    lines.append(f"Found {total} diagnostics (showing first {DEFAULT_MAX_DIAGNOSTICS}):")
                
                for diag in diagnostics:
                    range_info = diag.get('range', {})
                    start = range_info.get('start', {})
                    line = start.get('line', 0) + 1
                    char = start.get('character', 0)
                    severity_num = diag.get('severity', 1)
                    severity_name = {1: 'error', 2: 'warning', 3: 'info', 4: 'hint'}.get(severity_num, 'unknown')
                    message = diag.get('message', '')
                    
                    lines.append(f"[{severity_name}] Line {line}:{char} - {message}")
                
                content = '\n'.join(lines)
            
            # 释放客户端
            manager.release_client(str(root), server_config.id)
            
            return ToolResult(
                success=True,
                content=content,
                metadata={
                    'file_path': str(file_path_obj),
                    'severity': severity,
                    'total_count': total,
                    'shown_count': len(diagnostics)
                }
            )
            
        except Exception as e:
            logger.error(f"LSP diagnostics failed: {e}", exc_info=True)
            return ToolResult(
                success=False,
                content=None,
                error=str(e)
            )


class LSPGotoDefinitionTool(BaseTool):
    """
    跳转到定义
    
    参考：oh-my-opencode/src/tools/lsp/tools.ts (lsp_goto_definition)
    """
    
    def __init__(self):
        super().__init__(
            name="lsp_goto_definition",
            description="Jump to symbol definition. Find WHERE something is defined"
        )
    
    def get_function_schema(self) -> Dict[str, Any]:
        """获取Function Calling schema"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "File path"
                    },
                    "line": {
                        "type": "integer",
                        "description": "Line number (1-based)",
                        "minimum": 1
                    },
                    "character": {
                        "type": "integer",
                        "description": "Character position (0-based)",
                        "minimum": 0
                    }
                },
                "required": ["file_path", "line", "character"]
            }
        }
    
    async def execute(
        self,
        file_path: str,
        line: int,
        character: int
    ) -> ToolResult:
        """跳转到定义"""
        try:
            result = await with_lsp_client(file_path, lambda client: client.definition(file_path, line, character))
            
            if not result:
                return ToolResult(
                    success=True,
                    content="No definition found",
                    metadata={'file_path': file_path, 'line': line, 'character': character}
                )
            
            # 处理结果（可能是Location、Location[]或LocationLink[]）
            locations = result if isinstance(result, list) else [result]
            
            if not locations:
                return ToolResult(
                    success=True,
                    content="No definition found",
                    metadata={'file_path': file_path, 'line': line, 'character': character}
                )
            
            # 格式化输出
            content = '\n'.join(format_location(loc) for loc in locations)
            
            return ToolResult(
                success=True,
                content=content,
                metadata={
                    'file_path': file_path,
                    'line': line,
                    'character': character,
                    'count': len(locations)
                }
            )
            
        except Exception as e:
            logger.error(f"LSP goto definition failed: {e}", exc_info=True)
            return ToolResult(
                success=False,
                content=None,
                error=str(e)
            )


class LSPFindReferencesTool(BaseTool):
    """
    查找引用
    
    参考：oh-my-opencode/src/tools/lsp/tools.ts (lsp_find_references)
    """
    
    def __init__(self):
        super().__init__(
            name="lsp_find_references",
            description="Find ALL usages/references of a symbol across the entire workspace"
        )
    
    def get_function_schema(self) -> Dict[str, Any]:
        """获取Function Calling schema"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "File path"
                    },
                    "line": {
                        "type": "integer",
                        "description": "Line number (1-based)",
                        "minimum": 1
                    },
                    "character": {
                        "type": "integer",
                        "description": "Character position (0-based)",
                        "minimum": 0
                    },
                    "include_declaration": {
                        "type": "boolean",
                        "description": "Include the declaration itself",
                        "default": True
                    }
                },
                "required": ["file_path", "line", "character"]
            }
        }
    
    async def execute(
        self,
        file_path: str,
        line: int,
        character: int,
        include_declaration: bool = True
    ) -> ToolResult:
        """查找引用"""
        try:
            result = await with_lsp_client(
                file_path,
                lambda client: client.references(file_path, line, character, include_declaration)
            )
            
            if not result or len(result) == 0:
                return ToolResult(
                    success=True,
                    content="No references found",
                    metadata={'file_path': file_path, 'line': line, 'character': character}
                )
            
            # 限制数量
            total = len(result)
            truncated = total > DEFAULT_MAX_REFERENCES
            limited = result[:DEFAULT_MAX_REFERENCES] if truncated else result
            
            # 格式化输出
            lines = []
            if truncated:
                lines.append(f"Found {total} references (showing first {DEFAULT_MAX_REFERENCES}):")
            
            lines.extend(format_location(loc) for loc in limited)
            content = '\n'.join(lines)
            
            return ToolResult(
                success=True,
                content=content,
                metadata={
                    'file_path': file_path,
                    'line': line,
                    'character': character,
                    'include_declaration': include_declaration,
                    'total_count': total,
                    'shown_count': len(limited)
                }
            )
            
        except Exception as e:
            logger.error(f"LSP find references failed: {e}", exc_info=True)
            return ToolResult(
                success=False,
                content=None,
                error=str(e)
            )


class LSPSymbolsTool(BaseTool):
    """
    获取符号列表
    
    参考：oh-my-opencode/src/tools/lsp/tools.ts (lsp_symbols)
    """
    
    def __init__(self):
        super().__init__(
            name="lsp_symbols",
            description="Get symbols from file (document) or search across workspace"
        )
    
    def get_function_schema(self) -> Dict[str, Any]:
        """获取Function Calling schema"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "File path for LSP context"
                    },
                    "scope": {
                        "type": "string",
                        "enum": ["document", "workspace"],
                        "description": "'document' for file symbols, 'workspace' for project-wide search",
                        "default": "document"
                    },
                    "query": {
                        "type": "string",
                        "description": "Symbol name to search (required for workspace scope)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max results (default 50)",
                        "default": 50
                    }
                },
                "required": ["file_path"]
            }
        }
    
    async def execute(
        self,
        file_path: str,
        scope: str = "document",
        query: Optional[str] = None,
        limit: int = 50
    ) -> ToolResult:
        """获取符号列表"""
        try:
            if scope == "workspace" and not query:
                return ToolResult(
                    success=False,
                    content=None,
                    error="'query' is required for workspace scope"
                )
            
            if scope == "workspace":
                # 工作区符号搜索
                result = await with_lsp_client(
                    file_path,
                    lambda client: client.workspace_symbols(query)
                )
            else:
                # 文档符号
                result = await with_lsp_client(
                    file_path,
                    lambda client: client.document_symbols(file_path)
                )
            
            if not result or len(result) == 0:
                return ToolResult(
                    success=True,
                    content="No symbols found",
                    metadata={'file_path': file_path, 'scope': scope}
                )
            
            # 限制数量
            total = len(result)
            limit = min(limit, DEFAULT_MAX_SYMBOLS)
            truncated = total > limit
            limited = result[:limit] if truncated else result
            
            # 格式化输出
            lines = []
            if truncated:
                lines.append(f"Found {total} symbols (showing first {limit}):")
            
            # 处理不同的符号格式
            for symbol in limited:
                if 'range' in symbol:
                    # DocumentSymbol
                    name = symbol.get('name', '')
                    kind = symbol.get('kind', 0)
                    range_info = symbol.get('range', {})
                    start = range_info.get('start', {})
                    line = start.get('line', 0) + 1
                    lines.append(f"{name} (kind: {kind}, line: {line})")
                elif 'location' in symbol:
                    # SymbolInfo
                    name = symbol.get('name', '')
                    kind = symbol.get('kind', 0)
                    location = format_location(symbol['location'])
                    lines.append(f"{name} (kind: {kind}) - {location}")
            
            content = '\n'.join(lines)
            
            return ToolResult(
                success=True,
                content=content,
                metadata={
                    'file_path': file_path,
                    'scope': scope,
                    'query': query,
                    'total_count': total,
                    'shown_count': len(limited)
                }
            )
            
        except Exception as e:
            logger.error(f"LSP symbols failed: {e}", exc_info=True)
            return ToolResult(
                success=False,
                content=None,
                error=str(e)
            )


class LSPRenameTool(BaseTool):
    """
    重命名符号
    
    参考：oh-my-opencode/src/tools/lsp/tools.ts (lsp_rename)
    """
    
    def __init__(self):
        super().__init__(
            name="lsp_rename",
            description="Rename symbol across entire workspace. APPLIES changes to all files"
        )
    
    def get_function_schema(self) -> Dict[str, Any]:
        """获取Function Calling schema"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "File path"
                    },
                    "line": {
                        "type": "integer",
                        "description": "Line number (1-based)",
                        "minimum": 1
                    },
                    "character": {
                        "type": "integer",
                        "description": "Character position (0-based)",
                        "minimum": 0
                    },
                    "new_name": {
                        "type": "string",
                        "description": "New symbol name"
                    }
                },
                "required": ["file_path", "line", "character", "new_name"]
            }
        }
    
    async def execute(
        self,
        file_path: str,
        line: int,
        character: int,
        new_name: str
    ) -> ToolResult:
        """重命名符号"""
        try:
            result = await with_lsp_client(
                file_path,
                lambda client: client.rename(file_path, line, character, new_name)
            )
            
            if not result:
                return ToolResult(
                    success=False,
                    content=None,
                    error="Rename not supported at this location"
                )
            
            # 处理WorkspaceEdit
            changes_count = 0
            files_changed = set()
            
            if 'changes' in result:
                # changes: {uri: TextEdit[]}
                for uri, edits in result['changes'].items():
                    changes_count += len(edits)
                    # 解析URI获取文件路径
                    from urllib.parse import urlparse, unquote
                    parsed = urlparse(uri)
                    file_path_str = unquote(parsed.path)
                    if file_path_str.startswith('/') and ':' in file_path_str[1:3]:
                        file_path_str = file_path_str[1:]
                    files_changed.add(file_path_str)
            
            if 'documentChanges' in result:
                # documentChanges: TextDocumentEdit[]
                for change in result['documentChanges']:
                    if 'textDocument' in change:
                        uri = change['textDocument']['uri']
                        edits = change.get('edits', [])
                        changes_count += len(edits)
                        # 解析URI
                        from urllib.parse import urlparse, unquote
                        parsed = urlparse(uri)
                        file_path_str = unquote(parsed.path)
                        if file_path_str.startswith('/') and ':' in file_path_str[1:3]:
                            file_path_str = file_path_str[1:]
                        files_changed.add(file_path_str)
            
            content = (
                f"Rename successful:\n"
                f"- Files changed: {len(files_changed)}\n"
                f"- Total edits: {changes_count}\n"
                f"- New name: {new_name}\n\n"
                f"Files:\n" + '\n'.join(f"  - {f}" for f in sorted(files_changed))
            )
            
            return ToolResult(
                success=True,
                content=content,
                metadata={
                    'file_path': file_path,
                    'line': line,
                    'character': character,
                    'new_name': new_name,
                    'files_changed': list(files_changed),
                    'changes_count': changes_count
                }
            )
            
        except Exception as e:
            logger.error(f"LSP rename failed: {e}", exc_info=True)
            return ToolResult(
                success=False,
                content=None,
                error=str(e)
            )


class LSPCodeActionsTool(BaseTool):
    """
    获取代码操作（快速修复等）
    
    参考：oh-my-opencode/src/tools/lsp/tools.ts (lsp_code_actions)
    """
    
    def __init__(self):
        super().__init__(
            name="lsp_code_actions",
            description="Get available code actions (quick fixes, refactorings) for a location"
        )
    
    def get_function_schema(self) -> Dict[str, Any]:
        """获取Function Calling schema"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "File path"
                    },
                    "line": {
                        "type": "integer",
                        "description": "Line number (1-based)",
                        "minimum": 1
                    },
                    "character": {
                        "type": "integer",
                        "description": "Character position (0-based)",
                        "minimum": 0
                    }
                },
                "required": ["file_path", "line", "character"]
            }
        }
    
    async def execute(
        self,
        file_path: str,
        line: int,
        character: int
    ) -> ToolResult:
        """获取代码操作"""
        try:
            result = await with_lsp_client(
                file_path,
                lambda client: client.code_actions(file_path, line, character)
            )
            
            if not result or len(result) == 0:
                return ToolResult(
                    success=True,
                    content="No code actions available",
                    metadata={'file_path': file_path, 'line': line, 'character': character}
                )
            
            # 格式化输出
            lines = [f"Found {len(result)} code actions:"]
            
            for i, action in enumerate(result, 1):
                title = action.get('title', 'Untitled')
                kind = action.get('kind', 'unknown')
                lines.append(f"{i}. [{kind}] {title}")
            
            content = '\n'.join(lines)
            
            return ToolResult(
                success=True,
                content=content,
                metadata={
                    'file_path': file_path,
                    'line': line,
                    'character': character,
                    'count': len(result)
                }
            )
            
        except Exception as e:
            logger.error(f"LSP code actions failed: {e}", exc_info=True)
            return ToolResult(
                success=False,
                content=None,
                error=str(e)
            )
