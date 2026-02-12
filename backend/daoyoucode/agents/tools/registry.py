"""
全局工具注册表

单例模式，避免重复加载
"""

from .base import ToolRegistry
import logging

logger = logging.getLogger(__name__)

# 全局单例
_tool_registry = None


def get_tool_registry() -> ToolRegistry:
    """获取工具注册表单例"""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
        _register_builtin_tools()
    return _tool_registry


def _register_builtin_tools():
    """注册内置工具"""
    from .file_tools import (
        ReadFileTool,
        WriteFileTool,
        ListFilesTool,
        GetFileInfoTool,
        CreateDirectoryTool,
        DeleteFileTool
    )
    from .search_tools import (
        TextSearchTool,
        RegexSearchTool
    )
    from .git_tools import (
        GitStatusTool,
        GitDiffTool,
        GitCommitTool,
        GitLogTool
    )
    from .command_tools import (
        RunCommandTool,
        RunTestTool
    )
    from .diff_tools import (
        SearchReplaceTool
    )
    from .repomap_tools import (
        RepoMapTool,
        GetRepoStructureTool
    )
    from .lsp_tools import (
        LSPDiagnosticsTool,
        LSPGotoDefinitionTool,
        LSPFindReferencesTool,
        LSPSymbolsTool,
        LSPRenameTool,
        LSPCodeActionsTool
    )
    from .ast_tools import (
        AstGrepSearchTool,
        AstGrepReplaceTool
    )
    
    # 文件操作工具（6个）
    _tool_registry.register(ReadFileTool())
    _tool_registry.register(WriteFileTool())
    _tool_registry.register(ListFilesTool())
    _tool_registry.register(GetFileInfoTool())
    _tool_registry.register(CreateDirectoryTool())
    _tool_registry.register(DeleteFileTool())
    
    # 搜索工具（2个）
    _tool_registry.register(TextSearchTool())
    _tool_registry.register(RegexSearchTool())
    
    # Git工具（4个）
    _tool_registry.register(GitStatusTool())
    _tool_registry.register(GitDiffTool())
    _tool_registry.register(GitCommitTool())
    _tool_registry.register(GitLogTool())
    
    # 命令执行工具（2个）
    _tool_registry.register(RunCommandTool())
    _tool_registry.register(RunTestTool())
    
    # Diff工具（1个）
    _tool_registry.register(SearchReplaceTool())
    
    # RepoMap工具（2个）
    _tool_registry.register(RepoMapTool())
    _tool_registry.register(GetRepoStructureTool())
    
    # LSP工具（6个）
    _tool_registry.register(LSPDiagnosticsTool())
    _tool_registry.register(LSPGotoDefinitionTool())
    _tool_registry.register(LSPFindReferencesTool())
    _tool_registry.register(LSPSymbolsTool())
    _tool_registry.register(LSPRenameTool())
    _tool_registry.register(LSPCodeActionsTool())
    
    # AST工具（2个）
    _tool_registry.register(AstGrepSearchTool())
    _tool_registry.register(AstGrepReplaceTool())
    
    logger.info(f"已注册 {len(_tool_registry.list_tools())} 个内置工具")
    
    logger.info(f"已注册 {len(_tool_registry.list_tools())} 个内置工具")
