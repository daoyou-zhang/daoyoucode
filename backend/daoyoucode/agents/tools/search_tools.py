"""
代码搜索工具

提供文本搜索、正则搜索等功能
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
import re
from .base import BaseTool, ToolResult


class TextSearchTool(BaseTool):
    """文本搜索工具（类似ripgrep）"""
    
    def __init__(self):
        super().__init__(
            name="text_search",
            description="在文件中搜索文本"
        )
    
    async def execute(
        self,
        query: str,
        directory: str = ".",
        file_pattern: Optional[str] = None,
        case_sensitive: bool = False,
        max_results: int = 100
    ) -> ToolResult:
        """
        搜索文本
        
        Args:
            query: 搜索关键词
            directory: 搜索目录
            file_pattern: 文件名模式（如 *.py）
            case_sensitive: 是否区分大小写
            max_results: 最大结果数
        """
        try:
            path = Path(directory)
            if not path.exists():
                return ToolResult(
                    success=False,
                    content=None,
                    error=f"Directory not found: {directory}"
                )
            
            results = []
            count = 0
            
            # 准备搜索
            if not case_sensitive:
                query_lower = query.lower()
            
            # 遍历文件
            for file_path in self._iter_files(path, file_pattern):
                if count >= max_results:
                    break
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for line_num, line in enumerate(f, 1):
                            if count >= max_results:
                                break
                            
                            # 搜索
                            if case_sensitive:
                                if query in line:
                                    results.append({
                                        'file': str(file_path),
                                        'line': line_num,
                                        'content': line.rstrip(),
                                        'match': query
                                    })
                                    count += 1
                            else:
                                if query_lower in line.lower():
                                    results.append({
                                        'file': str(file_path),
                                        'line': line_num,
                                        'content': line.rstrip(),
                                        'match': query
                                    })
                                    count += 1
                except Exception:
                    continue
            
            return ToolResult(
                success=True,
                content=results,
                metadata={
                    'query': query,
                    'directory': str(path),
                    'count': len(results),
                    'truncated': count >= max_results
                }
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content=None,
                error=str(e)
            )
    
    def _iter_files(self, path: Path, pattern: Optional[str]):
        """迭代文件"""
        try:
            for item in path.rglob(pattern or '*'):
                if item.is_file() and not self._should_ignore(item):
                    yield item
        except Exception:
            pass
    
    def _should_ignore(self, path: Path) -> bool:
        """是否应该忽略"""
        ignore_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', 'dist', 'build'}
        ignore_exts = {'.pyc', '.pyo', '.so', '.dll', '.exe', '.bin'}
        
        # 检查路径中是否包含忽略的目录
        for part in path.parts:
            if part in ignore_dirs:
                return True
        
        # 检查扩展名
        if path.suffix in ignore_exts:
            return True
        
        return False
    
    def get_function_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词"
                    },
                    "directory": {
                        "type": "string",
                        "description": "搜索目录",
                        "default": "."
                    },
                    "file_pattern": {
                        "type": "string",
                        "description": "文件名模式（如 *.py）"
                    },
                    "case_sensitive": {
                        "type": "boolean",
                        "description": "是否区分大小写",
                        "default": False
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "最大结果数",
                        "default": 100
                    }
                },
                "required": ["query"]
            }
        }


class RegexSearchTool(BaseTool):
    """正则表达式搜索工具"""
    
    def __init__(self):
        super().__init__(
            name="regex_search",
            description="使用正则表达式搜索文件"
        )
    
    async def execute(
        self,
        pattern: str,
        directory: str = ".",
        file_pattern: Optional[str] = None,
        flags: int = 0,
        max_results: int = 100
    ) -> ToolResult:
        """
        正则搜索
        
        Args:
            pattern: 正则表达式
            directory: 搜索目录
            file_pattern: 文件名模式
            flags: 正则标志（如 re.IGNORECASE）
            max_results: 最大结果数
        """
        try:
            path = Path(directory)
            if not path.exists():
                return ToolResult(
                    success=False,
                    content=None,
                    error=f"Directory not found: {directory}"
                )
            
            # 编译正则
            try:
                regex = re.compile(pattern, flags)
            except re.error as e:
                return ToolResult(
                    success=False,
                    content=None,
                    error=f"Invalid regex pattern: {e}"
                )
            
            results = []
            count = 0
            
            # 遍历文件
            for file_path in self._iter_files(path, file_pattern):
                if count >= max_results:
                    break
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for line_num, line in enumerate(f, 1):
                            if count >= max_results:
                                break
                            
                            # 搜索
                            match = regex.search(line)
                            if match:
                                results.append({
                                    'file': str(file_path),
                                    'line': line_num,
                                    'content': line.rstrip(),
                                    'match': match.group(0),
                                    'groups': match.groups()
                                })
                                count += 1
                except Exception:
                    continue
            
            return ToolResult(
                success=True,
                content=results,
                metadata={
                    'pattern': pattern,
                    'directory': str(path),
                    'count': len(results),
                    'truncated': count >= max_results
                }
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content=None,
                error=str(e)
            )
    
    def _iter_files(self, path: Path, pattern: Optional[str]):
        """迭代文件"""
        try:
            for item in path.rglob(pattern or '*'):
                if item.is_file() and not self._should_ignore(item):
                    yield item
        except Exception:
            pass
    
    def _should_ignore(self, path: Path) -> bool:
        """是否应该忽略"""
        ignore_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', 'dist', 'build'}
        ignore_exts = {'.pyc', '.pyo', '.so', '.dll', '.exe', '.bin'}
        
        for part in path.parts:
            if part in ignore_dirs:
                return True
        
        if path.suffix in ignore_exts:
            return True
        
        return False
    
    def get_function_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "正则表达式"
                    },
                    "directory": {
                        "type": "string",
                        "description": "搜索目录",
                        "default": "."
                    },
                    "file_pattern": {
                        "type": "string",
                        "description": "文件名模式（如 *.py）"
                    },
                    "flags": {
                        "type": "integer",
                        "description": "正则标志",
                        "default": 0
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "最大结果数",
                        "default": 100
                    }
                },
                "required": ["pattern"]
            }
        }
