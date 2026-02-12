"""
Git工具

提供Git操作功能（基础+高级）
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
import subprocess
from .base import BaseTool, ToolResult


class GitStatusTool(BaseTool):
    """Git状态工具"""
    
    def __init__(self):
        super().__init__(
            name="git_status",
            description="获取Git仓库状态"
        )
    
    async def execute(self, repo_path: str = ".") -> ToolResult:
        """获取Git状态"""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            # 解析状态
            files = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                status = line[:2]
                file_path = line[3:]
                files.append({
                    'status': status.strip(),
                    'file': file_path
                })
            
            return ToolResult(
                success=True,
                content=files,
                metadata={'repo_path': repo_path, 'count': len(files)}
            )
        except subprocess.CalledProcessError as e:
            return ToolResult(
                success=False,
                content=None,
                error=f"Git command failed: {e.stderr}"
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
                    "repo_path": {
                        "type": "string",
                        "description": "仓库路径",
                        "default": "."
                    }
                },
                "required": []
            }
        }


class GitDiffTool(BaseTool):
    """Git diff工具"""
    
    def __init__(self):
        super().__init__(
            name="git_diff",
            description="获取Git diff"
        )
    
    async def execute(
        self,
        repo_path: str = ".",
        file_path: Optional[str] = None,
        staged: bool = False
    ) -> ToolResult:
        """
        获取Git diff
        
        Args:
            repo_path: 仓库路径
            file_path: 文件路径（可选）
            staged: 是否查看暂存区diff
        """
        try:
            cmd = ["git", "diff"]
            if staged:
                cmd.append("--cached")
            if file_path:
                cmd.append(file_path)
            
            result = subprocess.run(
                cmd,
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            return ToolResult(
                success=True,
                content=result.stdout,
                metadata={
                    'repo_path': repo_path,
                    'file_path': file_path,
                    'staged': staged
                }
            )
        except subprocess.CalledProcessError as e:
            return ToolResult(
                success=False,
                content=None,
                error=f"Git command failed: {e.stderr}"
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
                    "repo_path": {
                        "type": "string",
                        "description": "仓库路径",
                        "default": "."
                    },
                    "file_path": {
                        "type": "string",
                        "description": "文件路径（可选）"
                    },
                    "staged": {
                        "type": "boolean",
                        "description": "是否查看暂存区diff",
                        "default": False
                    }
                },
                "required": []
            }
        }


class GitCommitTool(BaseTool):
    """Git提交工具"""
    
    def __init__(self):
        super().__init__(
            name="git_commit",
            description="提交Git更改"
        )
    
    async def execute(
        self,
        message: str,
        repo_path: str = ".",
        files: Optional[List[str]] = None,
        all_files: bool = False
    ) -> ToolResult:
        """
        提交更改
        
        Args:
            message: 提交信息
            repo_path: 仓库路径
            files: 要提交的文件列表
            all_files: 是否提交所有更改
        """
        try:
            # 添加文件
            if all_files:
                subprocess.run(
                    ["git", "add", "-A"],
                    cwd=repo_path,
                    check=True
                )
            elif files:
                subprocess.run(
                    ["git", "add"] + files,
                    cwd=repo_path,
                    check=True
                )
            
            # 提交
            result = subprocess.run(
                ["git", "commit", "-m", message],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            return ToolResult(
                success=True,
                content=result.stdout,
                metadata={
                    'repo_path': repo_path,
                    'message': message,
                    'files': files,
                    'all_files': all_files
                }
            )
        except subprocess.CalledProcessError as e:
            return ToolResult(
                success=False,
                content=None,
                error=f"Git command failed: {e.stderr}"
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
                    "message": {
                        "type": "string",
                        "description": "提交信息"
                    },
                    "repo_path": {
                        "type": "string",
                        "description": "仓库路径",
                        "default": "."
                    },
                    "files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "要提交的文件列表"
                    },
                    "all_files": {
                        "type": "boolean",
                        "description": "是否提交所有更改",
                        "default": False
                    }
                },
                "required": ["message"]
            }
        }


class GitLogTool(BaseTool):
    """Git日志工具"""
    
    def __init__(self):
        super().__init__(
            name="git_log",
            description="获取Git提交历史"
        )
    
    async def execute(
        self,
        repo_path: str = ".",
        max_count: int = 10,
        file_path: Optional[str] = None
    ) -> ToolResult:
        """
        获取提交历史
        
        Args:
            repo_path: 仓库路径
            max_count: 最大数量
            file_path: 文件路径（可选）
        """
        try:
            cmd = [
                "git", "log",
                f"--max-count={max_count}",
                "--pretty=format:%H|%an|%ae|%ad|%s",
                "--date=iso"
            ]
            if file_path:
                cmd.append(file_path)
            
            result = subprocess.run(
                cmd,
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            # 解析日志
            commits = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                parts = line.split('|')
                if len(parts) >= 5:
                    commits.append({
                        'hash': parts[0],
                        'author': parts[1],
                        'email': parts[2],
                        'date': parts[3],
                        'message': parts[4]
                    })
            
            return ToolResult(
                success=True,
                content=commits,
                metadata={
                    'repo_path': repo_path,
                    'count': len(commits),
                    'file_path': file_path
                }
            )
        except subprocess.CalledProcessError as e:
            return ToolResult(
                success=False,
                content=None,
                error=f"Git command failed: {e.stderr}"
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
                    "repo_path": {
                        "type": "string",
                        "description": "仓库路径",
                        "default": "."
                    },
                    "max_count": {
                        "type": "integer",
                        "description": "最大数量",
                        "default": 10
                    },
                    "file_path": {
                        "type": "string",
                        "description": "文件路径（可选）"
                    }
                },
                "required": []
            }
        }
