"""
文件操作工具

提供read_file, write_file, list_files等基础文件操作
"""

from pathlib import Path
from typing import Dict, Any, Optional, List, AsyncGenerator
import os
import shutil
import asyncio
from .base import BaseTool, ToolResult, EditEvent, StreamingEditTool


class ReadFileTool(BaseTool):
    """读取文件工具"""
    
    # 单个文件不要太长
    MAX_OUTPUT_CHARS = 5000
    MAX_OUTPUT_LINES = 200
    
    def __init__(self):
        super().__init__(
            name="read_file",
            description="读取文件内容"
        )
    
    async def execute(self, file_path: str, encoding: str = "utf-8") -> ToolResult:
        """
        读取文件
        
        Args:
            file_path: 文件路径
            encoding: 编码格式
        """
        try:
            # 使用 resolve_path 解析路径
            path = self.resolve_path(file_path)
            
            if not path.exists():
                return ToolResult(
                    success=False,
                    content=None,
                    error=f"File not found: {file_path} (resolved to {path})"
                )
            
            with open(path, 'r', encoding=encoding) as f:
                content = f.read()
            
            return ToolResult(
                success=True,
                content=content,
                metadata={
                    'file_path': str(path),
                    'size': len(content),
                    'lines': content.count('\n') + 1
                }
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content=None,
                error=str(e)
            )
    
    def get_function_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "文件的相对路径。例如: 'backend/config.py' 或 'README.md'。不要使用占位符！"
                    },
                    "encoding": {
                        "type": "string",
                        "description": "编码格式",
                        "default": "utf-8"
                    }
                },
                "required": ["file_path"]
            }
        }


class WriteFileTool(StreamingEditTool):
    """写入文件工具（支持LSP验证和流式显示）"""
    
    def __init__(self):
        super().__init__(
            name="write_file",
            description="写入文件内容（自动创建目录，可选LSP验证，支持流式显示）"
        )
    
    async def execute(
        self,
        file_path: str,
        content: str,
        encoding: str = "utf-8",
        create_dirs: bool = True,
        verify: bool = True  # 🔥 新增：是否验证代码
    ) -> ToolResult:
        """
        写入文件
        
        Args:
            file_path: 文件路径
            content: 文件内容
            encoding: 编码格式
            create_dirs: 是否自动创建目录
            verify: 是否使用LSP验证代码（默认True）
        """
        try:
            path = self.resolve_path(file_path)
            
            # 创建目录
            if create_dirs and not path.parent.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入文件
            with open(path, 'w', encoding=encoding) as f:
                f.write(content)
            
            result_metadata = {
                'file_path': str(path),
                'size': len(content),
                'lines': content.count('\n') + 1
            }
            
            # 🔥 LSP验证（仅对代码文件）
            if verify and self._should_verify(path):
                diagnostics = await self._verify_with_lsp(path)
                
                if diagnostics:
                    # 有错误
                    error_count = len([d for d in diagnostics if d.get('severity') == 1])
                    warning_count = len([d for d in diagnostics if d.get('severity') == 2])
                    
                    result_metadata['diagnostics'] = diagnostics
                    result_metadata['error_count'] = error_count
                    result_metadata['warning_count'] = warning_count
                    
                    if error_count > 0:
                        # 有错误，返回失败
                        error_messages = [
                            f"Line {d.get('range', {}).get('start', {}).get('line', '?') + 1}: {d.get('message', 'Unknown error')}"
                            for d in diagnostics if d.get('severity') == 1
                        ]
                        
                        return ToolResult(
                            success=False,
                            content=None,
                            error=f"代码有{error_count}个错误:\n" + "\n".join(error_messages[:5]),
                            metadata=result_metadata
                        )
                    else:
                        # 只有警告，成功但提示
                        warning_messages = [
                            f"Line {d.get('range', {}).get('start', {}).get('line', '?') + 1}: {d.get('message', 'Unknown warning')}"
                            for d in diagnostics if d.get('severity') == 2
                        ]
                        
                        return ToolResult(
                            success=True,
                            content=f"文件已写入，但有{warning_count}个警告:\n" + "\n".join(warning_messages[:3]),
                            metadata=result_metadata
                        )
                else:
                    # 验证通过
                    result_metadata['verified'] = True
                    return ToolResult(
                        success=True,
                        content=f"文件已写入并验证通过: {file_path}",
                        metadata=result_metadata
                    )
            else:
                # 不验证或不支持验证
                return ToolResult(
                    success=True,
                    content=f"文件已写入: {file_path}",
                    metadata=result_metadata
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                content=None,
                error=str(e)
            )
    
    def _should_verify(self, path: Path) -> bool:
        """判断是否应该验证文件"""
        # 只验证代码文件
        code_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.rs'}
        return path.suffix in code_extensions
    
    async def _verify_with_lsp(self, file_path: Path) -> List[Dict]:
        """
        使用LSP验证代码
        
        Returns:
            诊断信息列表（错误和警告）
        """
        try:
            from .lsp_tools import with_lsp_client
            import asyncio
            import logging
            
            logger = logging.getLogger(__name__)
            
            # 🔥 获取诊断信息（内部会处理文件打开和等待）
            # 使用更长的等待时间确保pyright完成分析
            result = await with_lsp_client(
                str(file_path),
                lambda client: client.diagnostics(str(file_path), wait_time=3.0)
            )
            
            diagnostics = result.get('items', [])
            logger.debug(f"LSP返回{len(diagnostics)}个诊断信息")
            
            # 只返回错误和警告（忽略信息和提示）
            filtered = [
                d for d in diagnostics 
                if d.get('severity') in [1, 2]  # 1=Error, 2=Warning
            ]
            
            logger.debug(f"过滤后{len(filtered)}个错误/警告")
            return filtered
        
        except Exception as e:
            # LSP验证失败不影响文件写入
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"LSP验证失败: {e}")
            return []
    
    def get_function_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "文件路径（相对于项目根目录）"
                    },
                    "content": {
                        "type": "string",
                        "description": "文件内容"
                    },
                    "encoding": {
                        "type": "string",
                        "description": "编码格式",
                        "default": "utf-8"
                    },
                    "create_dirs": {
                        "type": "boolean",
                        "description": "是否自动创建目录",
                        "default": True
                    },
                    "verify": {
                        "type": "boolean",
                        "description": "是否使用LSP验证代码（默认True，自动检测代码文件）",
                        "default": True
                    }
                },
                "required": ["file_path", "content"]
            }
        }
    
    async def execute_streaming(
        self,
        file_path: str,
        content: str,
        encoding: str = "utf-8",
        create_dirs: bool = True,
        verify: bool = True
    ) -> AsyncGenerator[EditEvent, None]:
        """
        流式写入文件
        
        Yields:
            EditEvent - 编辑事件
        """
        try:
            path = self.resolve_path(file_path)
            lines = content.split('\n')
            total_lines = len(lines)
            
            # 1. 开始编辑
            yield EditEvent(
                type=EditEvent.EDIT_START,
                data={
                    'file_path': file_path,
                    'total_lines': total_lines,
                    'size': len(content)
                }
            )
            
            # 2. 分析文件
            yield EditEvent(
                type=EditEvent.EDIT_ANALYZING,
                data={
                    'file_path': file_path,
                    'exists': path.exists(),
                    'is_code': self._should_verify(path)
                }
            )
            
            # 3. 创建目录
            if create_dirs and not path.parent.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
            
            # 4. 逐行写入（模拟流式显示）
            # 注意：实际写入是一次性的，这里只是为了显示进度
            for i, line in enumerate(lines):
                yield EditEvent(
                    type=EditEvent.EDIT_LINE,
                    data={
                        'line_number': i + 1,
                        'content': line[:100],  # 只显示前100个字符
                        'progress': (i + 1) / total_lines
                    }
                )
                
                # 模拟延迟（让用户看到过程）
                # 小文件快速，大文件适当延迟
                if total_lines > 100:
                    if i % 10 == 0:  # 每10行更新一次
                        await asyncio.sleep(0.01)
                elif total_lines > 20:
                    if i % 5 == 0:  # 每5行更新一次
                        await asyncio.sleep(0.01)
                else:
                    await asyncio.sleep(0.005)  # 小文件也要有延迟
            
            # 5. 实际写入文件
            with open(path, 'w', encoding=encoding) as f:
                f.write(content)
            
            # 6. LSP验证
            if verify and self._should_verify(path):
                yield EditEvent(
                    type=EditEvent.EDIT_VERIFYING,
                    data={'file_path': file_path}
                )
                
                diagnostics = await self._verify_with_lsp(path)
                
                if diagnostics:
                    error_count = len([d for d in diagnostics if d.get('severity') == 1])
                    warning_count = len([d for d in diagnostics if d.get('severity') == 2])
                    
                    if error_count > 0:
                        # 有错误
                        error_messages = [
                            f"Line {d.get('range', {}).get('start', {}).get('line', '?') + 1}: {d.get('message', 'Unknown')}"
                            for d in diagnostics if d.get('severity') == 1
                        ]
                        
                        yield EditEvent(
                            type=EditEvent.EDIT_ERROR,
                            data={
                                'file_path': file_path,
                                'error_count': error_count,
                                'errors': error_messages[:5]
                            }
                        )
                        return
                    elif warning_count > 0:
                        # 只有警告，继续但提示
                        warning_messages = [
                            f"Line {d.get('range', {}).get('start', {}).get('line', '?') + 1}: {d.get('message', 'Unknown')}"
                            for d in diagnostics if d.get('severity') == 2
                        ]
                        
                        yield EditEvent(
                            type=EditEvent.EDIT_COMPLETE,
                            data={
                                'file_path': file_path,
                                'lines': total_lines,
                                'size': len(content),
                                'verified': True,
                                'warnings': warning_messages[:3],
                                'warning_count': warning_count
                            }
                        )
                        return
            
            # 7. 完成
            yield EditEvent(
                type=EditEvent.EDIT_COMPLETE,
                data={
                    'file_path': file_path,
                    'lines': total_lines,
                    'size': len(content),
                    'verified': verify and self._should_verify(path)
                }
            )
            
        except Exception as e:
            yield EditEvent(
                type=EditEvent.EDIT_ERROR,
                data={
                    'file_path': file_path,
                    'error': str(e)
                }
            )


class ListFilesTool(BaseTool):
    """列出目录工具"""
    
    def __init__(self):
        super().__init__(
            name="list_files",
            description="列出目录内容（支持递归和模式匹配）"
        )
    
    async def execute(
        self,
        directory: str = ".",
        recursive: bool = False,
        pattern: Optional[str] = None,
        max_depth: Optional[int] = 3  # 🆕 改为 Optional[int]
    ) -> ToolResult:
        """
        列出目录
        
        Args:
            directory: 目录路径
            recursive: 是否递归
            pattern: 文件名模式（如 *.py）
            max_depth: 最大递归深度（None 表示无限制）
        """
        try:
            # 使用 resolve_path 解析路径
            path = self.resolve_path(directory)
            
            if not path.exists():
                return ToolResult(
                    success=False,
                    content=None,
                    error=f"Directory not found: {directory} (resolved to {path})"
                )
            
            if not path.is_dir():
                return ToolResult(
                    success=False,
                    content=None,
                    error=f"Not a directory: {directory}"
                )
            
            files = []
            
            if recursive:
                # 🆕 如果 max_depth 是 None，使用一个很大的数字
                effective_max_depth = max_depth if max_depth is not None else 999
                files = self._list_recursive(path, pattern, effective_max_depth, 0)
            else:
                for item in path.iterdir():
                    if pattern and not item.match(pattern):
                        continue
                    files.append({
                        'path': self.normalize_path(str(item)),  # 标准化路径
                        'name': item.name,
                        'type': 'dir' if item.is_dir() else 'file',
                        'size': item.stat().st_size if item.is_file() else 0
                    })
            
            return ToolResult(
                success=True,
                content=files,
                metadata={
                    'directory': str(path),
                    'count': len(files),
                    'recursive': recursive
                }
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content=None,
                error=str(e)
            )
    
    def _list_recursive(
        self,
        path: Path,
        pattern: Optional[str],
        max_depth: int,
        current_depth: int
    ) -> List[Dict[str, Any]]:
        """递归列出文件"""
        if current_depth >= max_depth:
            return []
        
        files = []
        try:
            for item in path.iterdir():
                if pattern and not item.match(pattern):
                    if not item.is_dir():
                        continue
                
                files.append({
                    'path': self.normalize_path(str(item)),  # 标准化路径
                    'name': item.name,
                    'type': 'dir' if item.is_dir() else 'file',
                    'size': item.stat().st_size if item.is_file() else 0,
                    'depth': current_depth
                })
                
                if item.is_dir():
                    files.extend(self._list_recursive(
                        item, pattern, max_depth, current_depth + 1
                    ))
        except PermissionError:
            pass
        
        return files
    
    def get_function_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "目录路径（相对于项目根目录，使用 '.' 表示当前目录）",
                        "default": "."
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "是否递归列出子目录",
                        "default": False
                    },
                    "pattern": {
                        "type": "string",
                        "description": "文件名模式（如 '*.py' 或 '**/test_*.py'）"
                    },
                    "max_depth": {
                        "type": "integer",
                        "description": "最大递归深度（默认3，设置为较大值如999表示无限制）",
                        "default": 3
                    }
                },
                "required": []
            }
        }


class GetFileInfoTool(BaseTool):
    """获取文件信息工具"""
    
    def __init__(self):
        super().__init__(
            name="get_file_info",
            description="获取文件或目录的详细信息"
        )
    
    async def execute(self, path: str) -> ToolResult:
        """
        获取文件信息
        
        Args:
            path: 文件或目录路径
        """
        try:
            p = Path(path)
            if not p.exists():
                return ToolResult(
                    success=False,
                    content=None,
                    error=f"Path not found: {path}"
                )
            
            stat = p.stat()
            info = {
                'path': str(p),
                'name': p.name,
                'type': 'dir' if p.is_dir() else 'file',
                'size': stat.st_size,
                'created': stat.st_ctime,
                'modified': stat.st_mtime,
                'accessed': stat.st_atime,
                'is_symlink': p.is_symlink(),
                'parent': str(p.parent),
                'suffix': p.suffix if p.is_file() else None
            }
            
            return ToolResult(
                success=True,
                content=info
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content=None,
                error=str(e)
            )
    
    def get_function_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "文件或目录路径"
                    }
                },
                "required": ["path"]
            }
        }


class CreateDirectoryTool(BaseTool):
    """创建目录工具"""
    
    def __init__(self):
        super().__init__(
            name="create_directory",
            description="创建目录（支持递归创建）"
        )
    
    async def execute(self, directory: str, parents: bool = True) -> ToolResult:
        """
        创建目录
        
        Args:
            directory: 目录路径
            parents: 是否递归创建父目录
        """
        try:
            path = Path(directory)
            path.mkdir(parents=parents, exist_ok=True)
            
            return ToolResult(
                success=True,
                content=f"Successfully created directory: {directory}",
                metadata={'directory': str(path)}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content=None,
                error=str(e)
            )
    
    def get_function_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "目录路径"
                    },
                    "parents": {
                        "type": "boolean",
                        "description": "是否递归创建父目录",
                        "default": True
                    }
                },
                "required": ["directory"]
            }
        }


class DeleteFileTool(BaseTool):
    """删除文件/目录工具"""
    
    def __init__(self):
        super().__init__(
            name="delete_file",
            description="删除文件或目录"
        )
    
    async def execute(self, path: str, recursive: bool = False) -> ToolResult:
        """
        删除文件或目录
        
        Args:
            path: 文件或目录路径
            recursive: 是否递归删除目录
        """
        try:
            p = Path(path)
            if not p.exists():
                return ToolResult(
                    success=False,
                    content=None,
                    error=f"Path not found: {path}"
                )
            
            if p.is_dir():
                if recursive:
                    shutil.rmtree(p)
                else:
                    p.rmdir()
            else:
                p.unlink()
            
            return ToolResult(
                success=True,
                content=f"Successfully deleted: {path}",
                metadata={'path': str(p)}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content=None,
                error=str(e)
            )
    
    def get_function_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "文件或目录路径"
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "是否递归删除目录",
                        "default": False
                    }
                },
                "required": ["path"]
            }
        }


class BatchReadFilesTool(BaseTool):
    """批量读取文件工具"""
    
    MAX_OUTPUT_CHARS = 20000  # 批量读取允许更多内容
    MAX_OUTPUT_LINES = 1000
    
    def __init__(self):
        super().__init__(
            name="batch_read_files",
            description="批量读取多个文件内容（并行处理，提高效率）"
        )
    
    async def execute(
        self,
        file_paths: List[str],
        encoding: str = "utf-8"
    ) -> ToolResult:
        """
        批量读取文件
        
        Args:
            file_paths: 文件路径列表
            encoding: 编码格式
        
        Returns:
            ToolResult，content 为字典 {file_path: content}
        """
        try:
            results = {}
            errors = {}
            
            # 并行读取所有文件
            async def read_one_file(file_path: str):
                try:
                    path = self.resolve_path(file_path)
                    
                    if not path.exists():
                        return file_path, None, f"File not found: {file_path}"
                    
                    with open(path, 'r', encoding=encoding) as f:
                        content = f.read()
                    
                    return file_path, content, None
                except Exception as e:
                    return file_path, None, str(e)
            
            # 并行执行
            tasks = [read_one_file(fp) for fp in file_paths]
            read_results = await asyncio.gather(*tasks)
            
            # 整理结果
            for file_path, content, error in read_results:
                if error:
                    errors[file_path] = error
                else:
                    results[file_path] = content
            
            # 构建响应消息
            success_count = len(results)
            error_count = len(errors)
            
            message = f"✅ 成功读取 {success_count} 个文件"
            if error_count > 0:
                message += f"，{error_count} 个失败"
            
            message += "\n\n"
            
            # 显示每个文件的内容
            for file_path, content in results.items():
                lines = content.count('\n') + 1
                size = len(content)
                message += f"📄 {file_path} ({lines} 行, {size} 字节)\n"
                message += "```\n"
                message += content
                message += "\n```\n\n"
            
            # 显示错误
            if errors:
                message += "❌ 失败的文件:\n"
                for file_path, error in errors.items():
                    message += f"  • {file_path}: {error}\n"
            
            return ToolResult(
                success=error_count == 0,  # 只有全部成功才算成功
                content=message,
                metadata={
                    'success_count': success_count,
                    'error_count': error_count,
                    'results': results,
                    'errors': errors
                }
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content=None,
                error=str(e)
            )
    
    def get_function_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "file_paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "文件路径列表，例如: ['backend/file1.py', 'backend/file2.py']"
                    },
                    "encoding": {
                        "type": "string",
                        "description": "编码格式",
                        "default": "utf-8"
                    }
                },
                "required": ["file_paths"]
            }
        }


class BatchWriteFilesTool(StreamingEditTool):
    """批量写入文件工具（支持流式显示）"""
    
    def __init__(self):
        super().__init__(
            name="batch_write_files",
            description="批量写入多个文件（并行处理，支持流式显示）"
        )
    
    async def execute(
        self,
        files: List[Dict[str, str]],
        encoding: str = "utf-8",
        verify: bool = True
    ) -> ToolResult:
        """
        批量写入文件
        
        Args:
            files: 文件列表，每个元素为 {"path": "file_path", "content": "content"}
            encoding: 编码格式
            verify: 是否使用 LSP 验证
        
        Returns:
            ToolResult
        """
        try:
            results = []
            errors = {}
            
            # 并行写入所有文件
            async def write_one_file(file_info: Dict[str, str]):
                file_path = file_info.get('path')
                content = file_info.get('content', '')
                
                try:
                    path = self.resolve_path(file_path)
                    
                    # 创建目录
                    path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # 写入文件
                    with open(path, 'w', encoding=encoding) as f:
                        f.write(content)
                    
                    # LSP 验证（如果需要）
                    diagnostics = []
                    if verify and self._should_verify(path):
                        diagnostics = await self._verify_with_lsp(path)
                        
                        # 如果有错误，回退
                        if diagnostics:
                            error_count = len([d for d in diagnostics if d.get('severity') == 1])
                            if error_count > 0:
                                return file_path, False, f"LSP 验证失败: {error_count} 个错误"
                    
                    return file_path, True, None
                except Exception as e:
                    return file_path, False, str(e)
            
            # 并行执行
            tasks = [write_one_file(f) for f in files]
            write_results = await asyncio.gather(*tasks)
            
            # 整理结果
            for file_path, success, error in write_results:
                if success:
                    results.append(file_path)
                else:
                    errors[file_path] = error
            
            # 构建响应消息
            success_count = len(results)
            error_count = len(errors)
            
            message = f"✅ 成功写入 {success_count} 个文件"
            if error_count > 0:
                message += f"，{error_count} 个失败"
            
            message += "\n\n"
            
            # 显示成功的文件
            if results:
                message += "📝 成功写入:\n"
                for file_path in results:
                    message += f"  • {file_path}\n"
            
            # 显示错误
            if errors:
                message += "\n❌ 失败的文件:\n"
                for file_path, error in errors.items():
                    message += f"  • {file_path}: {error}\n"
            
            return ToolResult(
                success=error_count == 0,
                content=message,
                metadata={
                    'success_count': success_count,
                    'error_count': error_count,
                    'results': results,
                    'errors': errors
                }
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content=None,
                error=str(e)
            )
    
    async def execute_streaming(
        self,
        files: List[Dict[str, str]],
        encoding: str = "utf-8",
        verify: bool = True
    ) -> AsyncGenerator[EditEvent, None]:
        """
        流式批量写入文件
        
        Yields:
            EditEvent - 编辑事件
        """
        try:
            total_files = len(files)
            
            # 事件1: 开始编辑
            yield EditEvent(
                type=EditEvent.EDIT_START,
                data={
                    'action': 'batch_write_files',
                    'total_files': total_files
                }
            )
            
            await asyncio.sleep(0.01)
            
            # 逐个处理文件（显示进度）
            success_count = 0
            error_count = 0
            
            for index, file_info in enumerate(files, 1):
                file_path = file_info.get('path')
                content = file_info.get('content', '')
                
                # 事件2: 处理当前文件
                yield EditEvent(
                    type=EditEvent.EDIT_APPLYING,
                    data={
                        'file_path': file_path,
                        'progress': index / total_files,
                        'current': index,
                        'total': total_files
                    }
                )
                
                await asyncio.sleep(0.01)
                
                try:
                    path = self.resolve_path(file_path)
                    
                    # 创建目录
                    path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # 写入文件
                    with open(path, 'w', encoding=encoding) as f:
                        f.write(content)
                    
                    success_count += 1
                    
                    # 事件3: 文件写入成功
                    yield EditEvent(
                        type=EditEvent.EDIT_LINE,
                        data={
                            'file_path': file_path,
                            'status': 'success',
                            'size': len(content)
                        }
                    )
                    
                except Exception as e:
                    error_count += 1
                    
                    # 事件4: 文件写入失败
                    yield EditEvent(
                        type=EditEvent.EDIT_ERROR,
                        data={
                            'file_path': file_path,
                            'error': str(e)
                        }
                    )
                
                await asyncio.sleep(0.01)
            
            # 事件5: 批量写入完成
            yield EditEvent(
                type=EditEvent.EDIT_COMPLETE,
                data={
                    'total_files': total_files,
                    'success_count': success_count,
                    'error_count': error_count
                }
            )
            
        except Exception as e:
            yield EditEvent(
                type=EditEvent.EDIT_ERROR,
                data={'error': str(e)}
            )
    
    def _should_verify(self, path: Path) -> bool:
        """判断是否应该验证文件"""
        code_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.rs'}
        return path.suffix in code_extensions
    
    async def _verify_with_lsp(self, file_path: Path) -> List[Dict]:
        """使用 LSP 验证代码"""
        try:
            from .lsp_tools import with_lsp_client
            
            result = await with_lsp_client(
                str(file_path),
                lambda client: client.diagnostics(str(file_path), wait_time=3.0)
            )
            
            diagnostics = result.get('items', [])
            
            # 只返回错误和警告
            return [
                d for d in diagnostics 
                if d.get('severity') in [1, 2]
            ]
        except Exception:
            return []
    
    def get_function_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "files": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "path": {"type": "string"},
                                "content": {"type": "string"}
                            },
                            "required": ["path", "content"]
                        },
                        "description": "文件列表，每个元素包含 path 和 content"
                    },
                    "encoding": {
                        "type": "string",
                        "description": "编码格式",
                        "default": "utf-8"
                    },
                    "verify": {
                        "type": "boolean",
                        "description": "是否使用 LSP 验证代码",
                        "default": True
                    }
                },
                "required": ["files"]
            }
        }


class DeleteFileTool(BaseTool):
    """删除文件工具"""
    
    def __init__(self):
        super().__init__(
            name="delete_file",
            description="删除文件或目录（谨慎使用）"
        )
    
    async def execute(
        self,
        file_path: str,
        recursive: bool = False
    ) -> ToolResult:
        """
        删除文件或目录
        
        Args:
            file_path: 文件或目录的相对路径
            recursive: 如果是目录，是否递归删除（默认False）
        
        Returns:
            ToolResult: 删除结果
        """
        try:
            # 解析路径
            path = self.resolve_path(file_path)
            
            if not path.exists():
                return ToolResult(
                    success=False,
                    content=None,
                    error=f"File or directory not found: {file_path} (resolved to {path})"
                )
            
            # 删除文件
            if path.is_file():
                path.unlink()
                return ToolResult(
                    success=True,
                    content=f"File deleted: {file_path}",
                    metadata={
                        'file_path': str(path),
                        'type': 'file'
                    }
                )
            
            # 删除目录
            elif path.is_dir():
                if not recursive:
                    return ToolResult(
                        success=False,
                        content=None,
                        error=f"Cannot delete directory without recursive=True: {file_path}"
                    )
                
                shutil.rmtree(path)
                return ToolResult(
                    success=True,
                    content=f"Directory deleted: {file_path}",
                    metadata={
                        'file_path': str(path),
                        'type': 'directory'
                    }
                )
            
            else:
                return ToolResult(
                    success=False,
                    content=None,
                    error=f"Unknown file type: {file_path}"
                )
        
        except Exception as e:
            return ToolResult(
                success=False,
                content=None,
                error=f"Failed to delete {file_path}: {str(e)}"
            )
    
    def get_function_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "要删除的文件或目录的相对路径。例如: 'temp.txt' 或 'old_folder/'"
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "如果是目录，是否递归删除（默认False，需要明确指定才能删除目录）",
                        "default": False
                    }
                },
                "required": ["file_path"]
            }
        }


class BatchDeleteFilesTool(BaseTool):
    """批量删除文件工具"""
    
    def __init__(self):
        super().__init__(
            name="batch_delete_files",
            description="批量删除多个文件"
        )
    
    async def execute(
        self,
        file_paths: List[str]
    ) -> ToolResult:
        """
        批量删除文件
        
        Args:
            file_paths: 文件路径列表
        
        Returns:
            ToolResult: 删除结果
        """
        try:
            results = []
            errors = []
            
            for file_path in file_paths:
                try:
                    path = self.resolve_path(file_path)
                    
                    if not path.exists():
                        errors.append(f"Not found: {file_path}")
                        continue
                    
                    if path.is_file():
                        path.unlink()
                        results.append(f"Deleted: {file_path}")
                    else:
                        errors.append(f"Not a file: {file_path}")
                
                except Exception as e:
                    errors.append(f"Failed to delete {file_path}: {str(e)}")
            
            # 构建结果消息
            message_parts = []
            if results:
                message_parts.append(f"Successfully deleted {len(results)} file(s):")
                message_parts.extend([f"  - {r}" for r in results])
            
            if errors:
                message_parts.append(f"\nErrors ({len(errors)}):")
                message_parts.extend([f"  - {e}" for e in errors])
            
            success = len(results) > 0
            content = "\n".join(message_parts) if message_parts else "No files deleted"
            
            return ToolResult(
                success=success,
                content=content,
                metadata={
                    'deleted_count': len(results),
                    'error_count': len(errors),
                    'deleted_files': results,
                    'errors': errors
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                content=None,
                error=f"Batch delete failed: {str(e)}"
            )
    
    def get_function_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "file_paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "要删除的文件路径列表。例如: ['temp1.txt', 'temp2.txt']"
                    }
                },
                "required": ["file_paths"]
            }
        }
