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
    
    _initialized = True
    logger.info("Agent系统初始化完成")
    
    return tool_registry
