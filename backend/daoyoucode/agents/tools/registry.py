"""
全局工具注册表

单例模式，避免重复加载
"""

from .base import ToolRegistry
import logging

logger = logging.getLogger(__name__)

# 全局单例
_tool_registry = None
_registry_id = None  # 用于调试


def get_tool_registry() -> ToolRegistry:
    """获取工具注册表单例"""
    global _tool_registry, _registry_id
    if _tool_registry is None:
        logger.info("创建新的工具注册表实例")
        _tool_registry = ToolRegistry()
        _registry_id = id(_tool_registry)
        _register_builtin_tools()
        logger.info(f"工具注册表ID: {_registry_id}")
    else:
        logger.debug(f"返回现有工具注册表实例 (ID: {_registry_id})")
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
    from .project_docs_tools import (
        DiscoverProjectDocsTool
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
    try:
        _tool_registry.register(SearchReplaceTool())
    except Exception as e:
        logger.error(f"注册SearchReplaceTool失败: {e}")
    
    # RepoMap工具（3个）
    try:
        _tool_registry.register(RepoMapTool())
        logger.info("✓ RepoMapTool注册成功")
    except Exception as e:
        logger.error(f"注册RepoMapTool失败: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        _tool_registry.register(GetRepoStructureTool())
        logger.info("✓ GetRepoStructureTool注册成功")
    except Exception as e:
        logger.error(f"注册GetRepoStructureTool失败: {e}")
    
    try:
        _tool_registry.register(DiscoverProjectDocsTool())
        logger.info("✓ DiscoverProjectDocsTool注册成功")
    except Exception as e:
        logger.error(f"注册DiscoverProjectDocsTool失败: {e}")
    
    # LSP工具（6个）
    try:
        _tool_registry.register(LSPDiagnosticsTool())
        _tool_registry.register(LSPGotoDefinitionTool())
        _tool_registry.register(LSPFindReferencesTool())
        _tool_registry.register(LSPSymbolsTool())
        _tool_registry.register(LSPRenameTool())
        _tool_registry.register(LSPCodeActionsTool())
    except Exception as e:
        logger.error(f"注册LSP工具失败: {e}")
    
    # AST工具（2个）
    try:
        _tool_registry.register(AstGrepSearchTool())
        _tool_registry.register(AstGrepReplaceTool())
    except Exception as e:
        logger.error(f"注册AST工具失败: {e}")
    
    logger.info(f"已注册 {len(_tool_registry.list_tools())} 个内置工具")
    
    # 列出所有已注册的工具
    tools = _tool_registry.list_tools()
    logger.info(f"工具列表: {', '.join(sorted(tools))}")
