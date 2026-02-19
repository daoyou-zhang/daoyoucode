"""
Agent系统统一初始化

提供幂等的初始化函数，确保工具、Agent、编排器都正确注册
"""

import logging

logger = logging.getLogger(__name__)

_initialized = False


def initialize_agent_system():
    """
    初始化Agent系统（幂等操作）
    
    这个函数可以被多次调用，不会重复初始化
    
    Returns:
        工具注册表实例
    """
    global _initialized
    
    if _initialized:
        logger.debug("Agent系统已初始化，跳过")
        from .tools import get_tool_registry
        return get_tool_registry()
    
    logger.info("开始初始化Agent系统...")
    
    # 1. 初始化工具注册表
    from .tools import get_tool_registry
    tool_registry = get_tool_registry()
    logger.info(f"✓ 工具注册表已初始化: {len(tool_registry.list_tools())} 个工具")
    
    # 2. 注册内置Agent
    from .builtin import register_builtin_agents
    register_builtin_agents()
    logger.info("✓ 内置Agent已注册")
    
    # 3. 注册内置编排器（已在__init__.py中完成）
    from .core.orchestrator import get_orchestrator_registry
    orchestrator_registry = get_orchestrator_registry()
    logger.info(f"✓ 编排器已注册: {len(orchestrator_registry.list_orchestrators())} 个")
    
    # 4. 注册内置中间件
    from .core.middleware import register_middleware
    from .middleware.context import ContextMiddleware
    from .middleware.followup import FollowupMiddleware
    
    register_middleware('context_management', ContextMiddleware)
    register_middleware('memory_integration', ContextMiddleware)  # 暂时使用ContextMiddleware
    register_middleware('followup', FollowupMiddleware)
    logger.info("✓ 中间件已注册")
    
    # 5. 🔥 检查LSP服务器状态（同步检查，不启动）
    try:
        from .tools.lsp_tools import get_lsp_manager
        
        manager = get_lsp_manager()
        
        # 检查Python LSP是否已安装
        from .tools.lsp_tools import BUILTIN_LSP_SERVERS
        pyright_config = BUILTIN_LSP_SERVERS.get("pyright")
        
        if pyright_config and manager.is_server_installed(pyright_config):
            logger.info("✓ LSP系统已就绪（pyright已安装）")
            logger.info("  提示: LSP将在首次使用时自动启动")
        else:
            logger.info("✓ LSP系统已就绪（按需启动）")
            logger.info("  提示: 安装 'pip install pyright' 以启用Python LSP增强")
    
    except Exception as e:
        logger.debug(f"LSP检查失败: {e}")
    
    _initialized = True
    logger.info("Agent系统初始化完成")
    
    return tool_registry


def warmup_lsp_async():
    """
    异步预热LSP服务器（可选，在后台运行）
    
    这个函数应该在有事件循环的环境中调用，
    例如在CLI命令的async函数中
    """
    import asyncio
    from .tools.lsp_tools import get_lsp_manager
    
    async def _warmup():
        try:
            logger.info("🔥 预热LSP服务器...")
            manager = get_lsp_manager()
            
            # 尝试启动Python LSP
            available = await manager.ensure_server_available("python")
            
            if available:
                logger.info("✅ LSP服务器预热完成（Python支持）")
            else:
                logger.debug("LSP服务器未安装，跳过预热")
        
        except Exception as e:
            logger.debug(f"LSP预热失败: {e}")
    
    # 创建任务但不等待
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_warmup())
    except RuntimeError:
        # 没有运行的事件循环
        logger.debug("没有运行的事件循环，跳过LSP预热")

