"""
Git 工具 - Git 状态感知

提供 Git 仓库状态信息，帮助 AI 理解项目当前状态
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

from .base import BaseTool, ToolResult

logger = logging.getLogger(__name__)

try:
    import git
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False
    logger.warning("GitPython 未安装，Git 功能不可用")


class GitStatusTool(BaseTool):
    """
    获取 Git 仓库状态
    
    功能：
    - 列出已修改的文件
    - 列出已暂存的文件
    - 列出未跟踪的文件
    - 显示当前分支
    - 显示最近的提交
    """
    
    def __init__(self):
        super().__init__(
            name="git_status",
            description="获取 Git 仓库状态，包括修改的文件、暂存的文件、当前分支等"
        )
    
    def get_function_schema(self) -> Dict[str, Any]:
        """获取 Function Calling schema"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "repo_path": {
                        "type": "string",
                        "description": "仓库根目录路径（默认为当前工作目录）",
                        "default": "."
                    },
                    "include_diff": {
                        "type": "boolean",
                        "description": "是否包含文件差异（默认 false）",
                        "default": False
                    }
                },
                "required": []
            }
        }
    
    async def execute(
        self,
        repo_path: str = ".",
        include_diff: bool = False
    ) -> ToolResult:
        """
        获取 Git 状态
        
        Args:
            repo_path: 仓库根目录
            include_diff: 是否包含文件差异
            
        Returns:
            ToolResult
        """
        if not GIT_AVAILABLE:
            return ToolResult(
                success=False,
                content=None,
                error="GitPython 未安装，请运行: pip install gitpython"
            )
        
        try:
            # 解析路径
            repo_path_resolved = self.resolve_path(repo_path)
            
            # 打开 Git 仓库
            try:
                repo = git.Repo(repo_path_resolved, search_parent_directories=True)
            except git.InvalidGitRepositoryError:
                return ToolResult(
                    success=False,
                    content=None,
                    error=f"不是有效的 Git 仓库: {repo_path}"
                )
            
            # 获取仓库根目录
            repo_root = Path(repo.working_tree_dir)
            
            # 获取当前分支
            try:
                current_branch = repo.active_branch.name
            except TypeError:
                current_branch = "(detached HEAD)"
            
            # 获取已修改的文件（未暂存）
            modified_files = []
            for item in repo.index.diff(None):
                file_path = self.normalize_path(str(repo_root / item.a_path))
                modified_files.append({
                    "path": file_path,
                    "change_type": item.change_type
                })
            
            # 获取已暂存的文件
            staged_files = []
            for item in repo.index.diff("HEAD"):
                file_path = self.normalize_path(str(repo_root / item.a_path))
                staged_files.append({
                    "path": file_path,
                    "change_type": item.change_type
                })
            
            # 获取未跟踪的文件
            untracked_files = []
            for file_path in repo.untracked_files:
                normalized = self.normalize_path(str(repo_root / file_path))
                # 应用 subtree_only 过滤
                if self.context.should_include_path(normalized):
                    untracked_files.append(normalized)
            
            # 获取最近的提交
            recent_commits = []
            try:
                for commit in repo.iter_commits(max_count=5):
                    recent_commits.append({
                        "hash": commit.hexsha[:7],
                        "message": commit.message.strip().split('\n')[0],
                        "author": commit.author.name,
                        "date": commit.committed_datetime.isoformat()
                    })
            except Exception as e:
                logger.warning(f"无法获取提交历史: {e}")
            
            # 构建结果
            status = {
                "branch": current_branch,
                "repo_root": str(repo_root),
                "modified_files": modified_files,
                "staged_files": staged_files,
                "untracked_files": untracked_files,
                "recent_commits": recent_commits,
                "is_dirty": repo.is_dirty()
            }
            
            # 生成可读的文本输出
            output_lines = [
                f"📁 Git 仓库: {repo_root}",
                f"🌿 当前分支: {current_branch}",
                ""
            ]
            
            if modified_files:
                output_lines.append(f"📝 已修改的文件 ({len(modified_files)}):")
                for file in modified_files[:10]:  # 最多显示 10 个
                    output_lines.append(f"  • {file['path']}")
                if len(modified_files) > 10:
                    output_lines.append(f"  ... 还有 {len(modified_files) - 10} 个文件")
                output_lines.append("")
            
            if staged_files:
                output_lines.append(f"✅ 已暂存的文件 ({len(staged_files)}):")
                for file in staged_files[:10]:
                    output_lines.append(f"  • {file['path']}")
                if len(staged_files) > 10:
                    output_lines.append(f"  ... 还有 {len(staged_files) - 10} 个文件")
                output_lines.append("")
            
            if untracked_files:
                output_lines.append(f"❓ 未跟踪的文件 ({len(untracked_files)}):")
                for file in untracked_files[:10]:
                    output_lines.append(f"  • {file}")
                if len(untracked_files) > 10:
                    output_lines.append(f"  ... 还有 {len(untracked_files) - 10} 个文件")
                output_lines.append("")
            
            if not modified_files and not staged_files and not untracked_files:
                output_lines.append("✨ 工作目录干净，没有未提交的更改")
                output_lines.append("")
            
            if recent_commits:
                output_lines.append(f"📜 最近的提交:")
                for commit in recent_commits:
                    output_lines.append(
                        f"  • {commit['hash']} - {commit['message']} "
                        f"({commit['author']})"
                    )
            
            content = "\n".join(output_lines)
            
            return ToolResult(
                success=True,
                content=content,
                metadata=status
            )
            
        except Exception as e:
            logger.error(f"获取 Git 状态失败: {e}", exc_info=True)
            return ToolResult(
                success=False,
                content=None,
                error=str(e)
            )



class GitDiffTool(BaseTool):
    """获取 Git 差异"""
    
    def __init__(self):
        super().__init__(
            name="git_diff",
            description="获取 Git 文件差异（显示修改内容）"
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
                        "description": "文件路径（可选，不指定则显示所有修改）"
                    },
                    "staged": {
                        "type": "boolean",
                        "description": "是否只显示已暂存的修改",
                        "default": False
                    }
                },
                "required": []
            }
        }
    
    async def execute(self, file_path: str = None, staged: bool = False) -> ToolResult:
        """
        获取 Git 差异
        
        Args:
            file_path: 文件路径（可选）
            staged: 是否只显示已暂存的修改
        """
        try:
            import subprocess
            
            # 构建 git diff 命令
            cmd = ["git", "diff"]
            
            if staged:
                cmd.append("--staged")
            
            if file_path:
                # 解析路径
                path = self.resolve_path(file_path)
                cmd.append(str(path))
            
            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            if result.returncode != 0:
                return ToolResult(
                    success=False,
                    content=None,
                    error=f"Git diff failed: {result.stderr}"
                )
            
            diff_output = result.stdout
            
            if not diff_output.strip():
                return ToolResult(
                    success=True,
                    content="No changes" if not file_path else f"No changes in {file_path}",
                    metadata={'has_changes': False}
                )
            
            return ToolResult(
                success=True,
                content=diff_output,
                metadata={
                    'has_changes': True,
                    'file_path': file_path,
                    'staged': staged
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                content=None,
                error=str(e)
            )


class GitCommitTool(BaseTool):
    """Git 提交工具（占位符，待实现）"""
    
    def __init__(self):
        super().__init__(
            name="git_commit",
            description="提交 Git 更改"
        )
    
    def get_function_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    
    async def execute(self, **kwargs) -> ToolResult:
        return ToolResult(
            success=False,
            content=None,
            error="GitCommitTool 尚未实现"
        )


class GitLogTool(BaseTool):
    """Git 日志工具（占位符，待实现）"""
    
    def __init__(self):
        super().__init__(
            name="git_log",
            description="查看 Git 提交历史"
        )
    
    def get_function_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    
    async def execute(self, **kwargs) -> ToolResult:
        return ToolResult(
            success=False,
            content=None,
            error="GitLogTool 尚未实现"
        )
