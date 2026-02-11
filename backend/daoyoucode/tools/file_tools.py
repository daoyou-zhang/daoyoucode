"""
文件操作工具

提供基础的文件读写、列表等操作
"""

import os
from pathlib import Path
from typing import List, Optional
import logging

from .registry import tool

logger = logging.getLogger(__name__)


@tool(category="file")
async def read_file(path: str, encoding: str = "utf-8") -> str:
    """
    读取文件内容
    
    Args:
        path: 文件路径
        encoding: 文件编码（默认utf-8）
    
    Returns:
        文件内容
    """
    file_path = Path(path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    if not file_path.is_file():
        raise ValueError(f"Not a file: {path}")
    
    with open(file_path, 'r', encoding=encoding) as f:
        content = f.read()
    
    logger.info(f"读取文件: {path}, 大小: {len(content)} 字符")
    return content


@tool(category="file")
async def write_file(path: str, content: str, encoding: str = "utf-8", create_dirs: bool = True) -> str:
    """
    写入文件内容
    
    Args:
        path: 文件路径
        content: 文件内容
        encoding: 文件编码（默认utf-8）
        create_dirs: 是否自动创建目录（默认True）
    
    Returns:
        成功消息
    """
    file_path = Path(path)
    
    # 自动创建目录
    if create_dirs and not file_path.parent.exists():
        file_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"创建目录: {file_path.parent}")
    
    with open(file_path, 'w', encoding=encoding) as f:
        f.write(content)
    
    logger.info(f"写入文件: {path}, 大小: {len(content)} 字符")
    return f"Successfully wrote {len(content)} characters to {path}"


@tool(category="file")
async def list_files(
    directory: str,
    pattern: str = "*",
    recursive: bool = False,
    include_dirs: bool = False
) -> List[str]:
    """
    列出目录中的文件
    
    Args:
        directory: 目录路径
        pattern: 文件模式（支持通配符，如 *.py）
        recursive: 是否递归搜索子目录
        include_dirs: 是否包含目录
    
    Returns:
        文件路径列表
    """
    dir_path = Path(directory)
    
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    if not dir_path.is_dir():
        raise ValueError(f"Not a directory: {directory}")
    
    files = []
    
    if recursive:
        # 递归搜索
        for item in dir_path.rglob(pattern):
            if item.is_file() or (include_dirs and item.is_dir()):
                files.append(str(item))
    else:
        # 只搜索当前目录
        for item in dir_path.glob(pattern):
            if item.is_file() or (include_dirs and item.is_dir()):
                files.append(str(item))
    
    logger.info(f"列出文件: {directory}, 模式: {pattern}, 找到: {len(files)} 个")
    return files


@tool(category="file")
async def get_file_info(path: str) -> dict:
    """
    获取文件信息
    
    Args:
        path: 文件路径
    
    Returns:
        文件信息字典
    """
    file_path = Path(path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    stat = file_path.stat()
    
    info = {
        "path": str(file_path.absolute()),
        "name": file_path.name,
        "size": stat.st_size,
        "is_file": file_path.is_file(),
        "is_dir": file_path.is_dir(),
        "created": stat.st_ctime,
        "modified": stat.st_mtime,
        "extension": file_path.suffix
    }
    
    logger.info(f"获取文件信息: {path}")
    return info


@tool(category="file")
async def create_directory(path: str, parents: bool = True, exist_ok: bool = True) -> str:
    """
    创建目录
    
    Args:
        path: 目录路径
        parents: 是否创建父目录
        exist_ok: 如果目录已存在是否报错
    
    Returns:
        成功消息
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=parents, exist_ok=exist_ok)
    
    logger.info(f"创建目录: {path}")
    return f"Successfully created directory: {path}"


@tool(category="file")
async def delete_file(path: str, recursive: bool = False) -> str:
    """
    删除文件或目录
    
    Args:
        path: 文件/目录路径
        recursive: 如果是目录，是否递归删除
    
    Returns:
        成功消息
    """
    file_path = Path(path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Path not found: {path}")
    
    if file_path.is_file():
        file_path.unlink()
        logger.info(f"删除文件: {path}")
        return f"Successfully deleted file: {path}"
    elif file_path.is_dir():
        if recursive:
            import shutil
            shutil.rmtree(file_path)
            logger.info(f"递归删除目录: {path}")
            return f"Successfully deleted directory recursively: {path}"
        else:
            file_path.rmdir()
            logger.info(f"删除空目录: {path}")
            return f"Successfully deleted empty directory: {path}"
    else:
        raise ValueError(f"Unknown path type: {path}")


@tool(category="file")
async def file_exists(path: str) -> bool:
    """
    检查文件是否存在
    
    Args:
        path: 文件路径
    
    Returns:
        是否存在
    """
    exists = Path(path).exists()
    logger.info(f"检查文件存在: {path} = {exists}")
    return exists


@tool(category="file")
async def get_file_content_lines(
    path: str,
    start_line: int = 1,
    end_line: Optional[int] = None,
    encoding: str = "utf-8"
) -> str:
    """
    读取文件的指定行
    
    Args:
        path: 文件路径
        start_line: 起始行号（从1开始）
        end_line: 结束行号（None表示到文件末尾）
        encoding: 文件编码
    
    Returns:
        指定行的内容
    """
    file_path = Path(path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    with open(file_path, 'r', encoding=encoding) as f:
        lines = f.readlines()
    
    # 转换为0-based索引
    start_idx = max(0, start_line - 1)
    end_idx = len(lines) if end_line is None else min(len(lines), end_line)
    
    selected_lines = lines[start_idx:end_idx]
    content = ''.join(selected_lines)
    
    logger.info(f"读取文件行: {path}, 行 {start_line}-{end_idx}")
    return content
