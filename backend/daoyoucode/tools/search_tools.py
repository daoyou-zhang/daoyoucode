"""
代码搜索工具

提供文本搜索、正则搜索等功能
"""

import os
import re
from pathlib import Path
from typing import List, Optional, Dict
import logging

from .registry import tool

logger = logging.getLogger(__name__)


@tool(category="search")
async def grep_search(
    pattern: str,
    directory: str = ".",
    file_pattern: str = "*",
    recursive: bool = True,
    case_sensitive: bool = False,
    max_results: int = 100
) -> str:
    """
    文本搜索（类似grep）
    
    Args:
        pattern: 搜索模式（支持正则表达式）
        directory: 搜索目录
        file_pattern: 文件模式（如 *.py）
        recursive: 是否递归搜索
        case_sensitive: 是否区分大小写
        max_results: 最大结果数
    
    Returns:
        搜索结果（格式化字符串）
    """
    dir_path = Path(directory)
    
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    # 编译正则表达式
    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        regex = re.compile(pattern, flags)
    except re.error as e:
        raise ValueError(f"Invalid regex pattern: {pattern}, error: {e}")
    
    results = []
    count = 0
    
    # 搜索文件
    if recursive:
        files = dir_path.rglob(file_pattern)
    else:
        files = dir_path.glob(file_pattern)
    
    for file_path in files:
        if not file_path.is_file():
            continue
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    if regex.search(line):
                        results.append({
                            'file': str(file_path),
                            'line': line_num,
                            'content': line.rstrip()
                        })
                        count += 1
                        
                        if count >= max_results:
                            break
        except Exception as e:
            logger.warning(f"Error reading file {file_path}: {e}")
            continue
        
        if count >= max_results:
            break
    
    # 格式化结果
    if not results:
        return f"No matches found for pattern: {pattern}"
    
    formatted = [f"Found {len(results)} matches:\n"]
    for result in results:
        formatted.append(
            f"{result['file']}:{result['line']}: {result['content']}"
        )
    
    logger.info(f"搜索完成: {pattern}, 找到 {len(results)} 个匹配")
    return "\n".join(formatted)


@tool(category="search")
async def find_function(
    function_name: str,
    directory: str = ".",
    language: str = "python"
) -> str:
    """
    查找函数定义
    
    Args:
        function_name: 函数名
        directory: 搜索目录
        language: 编程语言（python, javascript, java等）
    
    Returns:
        函数定义位置
    """
    # 根据语言构建搜索模式
    patterns = {
        'python': rf'^\s*def\s+{function_name}\s*\(',
        'javascript': rf'^\s*function\s+{function_name}\s*\(',
        'java': rf'^\s*\w+\s+{function_name}\s*\(',
        'go': rf'^\s*func\s+{function_name}\s*\(',
        'rust': rf'^\s*fn\s+{function_name}\s*\(',
    }
    
    pattern = patterns.get(language.lower())
    if not pattern:
        raise ValueError(f"Unsupported language: {language}")
    
    # 文件扩展名
    extensions = {
        'python': '*.py',
        'javascript': '*.js',
        'java': '*.java',
        'go': '*.go',
        'rust': '*.rs',
    }
    
    file_pattern = extensions.get(language.lower(), '*')
    
    # 使用grep_search
    return await grep_search(
        pattern=pattern,
        directory=directory,
        file_pattern=file_pattern,
        recursive=True,
        case_sensitive=True
    )


@tool(category="search")
async def find_class(
    class_name: str,
    directory: str = ".",
    language: str = "python"
) -> str:
    """
    查找类定义
    
    Args:
        class_name: 类名
        directory: 搜索目录
        language: 编程语言
    
    Returns:
        类定义位置
    """
    # 根据语言构建搜索模式
    patterns = {
        'python': rf'^\s*class\s+{class_name}\s*[\(:]',
        'javascript': rf'^\s*class\s+{class_name}\s*[{{]',
        'java': rf'^\s*class\s+{class_name}\s*[{{]',
        'go': rf'^\s*type\s+{class_name}\s+struct',
        'rust': rf'^\s*struct\s+{class_name}\s*[{{]',
    }
    
    pattern = patterns.get(language.lower())
    if not pattern:
        raise ValueError(f"Unsupported language: {language}")
    
    # 文件扩展名
    extensions = {
        'python': '*.py',
        'javascript': '*.js',
        'java': '*.java',
        'go': '*.go',
        'rust': '*.rs',
    }
    
    file_pattern = extensions.get(language.lower(), '*')
    
    # 使用grep_search
    return await grep_search(
        pattern=pattern,
        directory=directory,
        file_pattern=file_pattern,
        recursive=True,
        case_sensitive=True
    )


@tool(category="search")
async def find_imports(
    module_name: str,
    directory: str = ".",
    language: str = "python"
) -> str:
    """
    查找导入语句
    
    Args:
        module_name: 模块名
        directory: 搜索目录
        language: 编程语言
    
    Returns:
        导入语句位置
    """
    # 根据语言构建搜索模式
    patterns = {
        'python': rf'^\s*(from\s+{module_name}|import\s+{module_name})',
        'javascript': rf'^\s*(import.*from\s+["\'].*{module_name}|require\(["\'].*{module_name})',
        'java': rf'^\s*import\s+.*{module_name}',
        'go': rf'^\s*import\s+.*{module_name}',
    }
    
    pattern = patterns.get(language.lower())
    if not pattern:
        raise ValueError(f"Unsupported language: {language}")
    
    # 文件扩展名
    extensions = {
        'python': '*.py',
        'javascript': '*.js',
        'java': '*.java',
        'go': '*.go',
    }
    
    file_pattern = extensions.get(language.lower(), '*')
    
    # 使用grep_search
    return await grep_search(
        pattern=pattern,
        directory=directory,
        file_pattern=file_pattern,
        recursive=True,
        case_sensitive=False
    )
