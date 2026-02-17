"""
文件操作工具

提供read_file, write_file, list_files等基础文件操作
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
import os
import shutil
from .base import BaseTool, ToolResult


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
                        "description": "文件路径"
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


class WriteFileTool(BaseTool):
    """写入文件工具"""
    
    def __init__(self):
        super().__init__(
            name="write_file",
            description="写入文件内容（自动创建目录）"
        )
    
    async def execute(
        self,
        file_path: str,
        content: str,
        encoding: str = "utf-8",
        create_dirs: bool = True
    ) -> ToolResult:
        """
        写入文件
        
        Args:
            file_path: 文件路径
            content: 文件内容
            encoding: 编码格式
            create_dirs: 是否自动创建目录
        """
        try:
            path = Path(file_path)
            
            # 创建目录
            if create_dirs and not path.parent.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding=encoding) as f:
                f.write(content)
            
            return ToolResult(
                success=True,
                content=f"Successfully wrote {len(content)} bytes to {file_path}",
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
                        "description": "文件路径"
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
                    }
                },
                "required": ["file_path", "content"]
            }
        }


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
