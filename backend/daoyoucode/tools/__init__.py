"""
工具系统

提供Agent可调用的工具集
"""

from .registry import (
    Tool,
    ToolParameter,
    FunctionTool,
    ToolRegistry,
    get_tool_registry,
    register_tool,
    tool
)

# 导入内置工具（自动注册）
from . import file_tools
from . import search_tools
from . import git_tools

__all__ = [
    'Tool',
    'ToolParameter',
    'FunctionTool',
    'ToolRegistry',
    'get_tool_registry',
    'register_tool',
    'tool',
]
