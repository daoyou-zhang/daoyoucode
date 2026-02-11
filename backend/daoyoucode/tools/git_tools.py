"""
Git操作工具

提供Git状态查询、提交、差异查看等功能
"""

import subprocess
from pathlib import Path
from typing import Optional, List
import logging

from .registry import tool

logger = logging.getLogger(__name__)


def _run_git_command(command: List[str], cwd: str = ".") -> str:
    """
    运行Git命令
    
    Args:
        command: Git命令列表
        cwd: 工作目录
    
    Returns:
        命令输出
    """
    try:
        result = subprocess.run(
            ['git'] + command,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            check=True
        )
        return result.stdout.strip() if result.stdout else ""
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        raise RuntimeError(f"Git command failed: {error_msg}")


@tool(category="git")
async def git_status(directory: str = ".") -> str:
    """
    获取Git状态
    
    Args:
        directory: Git仓库目录
    
    Returns:
        Git状态信息
    """
    output = _run_git_command(['status', '--short'], cwd=directory)
    
    if not output:
        return "Working tree clean"
    
    logger.info(f"Git状态: {directory}")
    return f"Git Status:\n{output}"


@tool(category="git")
async def git_diff(file_path: Optional[str] = None, directory: str = ".") -> str:
    """
    查看Git差异
    
    Args:
        file_path: 文件路径（可选，不指定则查看所有差异）
        directory: Git仓库目录
    
    Returns:
        差异内容
    """
    command = ['diff']
    if file_path:
        command.append(file_path)
    
    output = _run_git_command(command, cwd=directory)
    
    if not output:
        return "No changes"
    
    logger.info(f"Git差异: {file_path or 'all files'}")
    return f"Git Diff:\n{output}"


@tool(category="git")
async def git_log(
    max_count: int = 10,
    file_path: Optional[str] = None,
    directory: str = "."
) -> str:
    """
    查看Git提交历史
    
    Args:
        max_count: 最大提交数
        file_path: 文件路径（可选）
        directory: Git仓库目录
    
    Returns:
        提交历史
    """
    command = ['log', f'--max-count={max_count}', '--oneline']
    if file_path:
        command.append(file_path)
    
    output = _run_git_command(command, cwd=directory)
    
    logger.info(f"Git历史: {file_path or 'all'}, 最近{max_count}条")
    return f"Git Log:\n{output}"


@tool(category="git")
async def git_commit(
    message: str,
    files: Optional[List[str]] = None,
    directory: str = "."
) -> str:
    """
    提交更改
    
    Args:
        message: 提交信息
        files: 要提交的文件列表（可选，不指定则提交所有）
        directory: Git仓库目录
    
    Returns:
        提交结果
    """
    # 添加文件
    if files:
        for file in files:
            _run_git_command(['add', file], cwd=directory)
    else:
        _run_git_command(['add', '-A'], cwd=directory)
    
    # 提交
    output = _run_git_command(['commit', '-m', message], cwd=directory)
    
    logger.info(f"Git提交: {message}")
    return f"Committed successfully:\n{output}"


@tool(category="git")
async def git_branch(directory: str = ".") -> str:
    """
    查看Git分支
    
    Args:
        directory: Git仓库目录
    
    Returns:
        分支列表
    """
    output = _run_git_command(['branch', '-a'], cwd=directory)
    
    logger.info(f"Git分支: {directory}")
    return f"Git Branches:\n{output}"


@tool(category="git")
async def git_show(
    commit: str = "HEAD",
    directory: str = "."
) -> str:
    """
    查看提交详情
    
    Args:
        commit: 提交哈希或引用（默认HEAD）
        directory: Git仓库目录
    
    Returns:
        提交详情
    """
    output = _run_git_command(['show', commit, '--stat'], cwd=directory)
    
    logger.info(f"Git show: {commit}")
    return f"Commit Details:\n{output}"


@tool(category="git")
async def git_blame(
    file_path: str,
    start_line: Optional[int] = None,
    end_line: Optional[int] = None,
    directory: str = "."
) -> str:
    """
    查看文件的Git blame（代码归因）
    
    Args:
        file_path: 文件路径
        start_line: 起始行号（可选）
        end_line: 结束行号（可选）
        directory: Git仓库目录
    
    Returns:
        Blame信息
    """
    command = ['blame']
    
    if start_line and end_line:
        command.extend(['-L', f'{start_line},{end_line}'])
    
    command.append(file_path)
    
    output = _run_git_command(command, cwd=directory)
    
    logger.info(f"Git blame: {file_path}")
    return f"Git Blame:\n{output}"


@tool(category="git")
async def git_stash(
    action: str = "list",
    message: Optional[str] = None,
    directory: str = "."
) -> str:
    """
    Git stash操作
    
    Args:
        action: 操作类型（list, save, pop, apply）
        message: stash消息（save时使用）
        directory: Git仓库目录
    
    Returns:
        操作结果
    """
    if action == "save":
        command = ['stash', 'save']
        if message:
            command.append(message)
    elif action == "pop":
        command = ['stash', 'pop']
    elif action == "apply":
        command = ['stash', 'apply']
    elif action == "list":
        command = ['stash', 'list']
    else:
        raise ValueError(f"Invalid stash action: {action}")
    
    output = _run_git_command(command, cwd=directory)
    
    logger.info(f"Git stash {action}")
    return f"Git Stash {action}:\n{output}" if output else f"Git Stash {action}: Done"
