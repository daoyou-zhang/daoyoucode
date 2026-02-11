"""
初始化所有Agents

支持多种加载方式：
1. 内置Agents
2. 项目自定义Agents（.agents/）
3. 用户自定义Agents（~/.daoyoucode/agents/）
4. Python包（entry_points）
"""

import logging

from .core import get_agent_registry, get_agent_loader

logger = logging.getLogger(__name__)


def init_builtin_agents():
    """
    初始化内置Agents（旧方法，保持兼容）
    
    推荐使用 init_all_agents() 来加载所有来源的Agents
    """
    logger.info("开始初始化内置Agents...")
    
    loader = get_agent_loader()
    loader.load_builtin_agents()
    
    # 打印Agent信息
    _print_agents_info()


def init_all_agents(project_root=None):
    """
    初始化所有Agents（推荐）
    
    加载顺序：
    1. 内置Agents
    2. 用户Agents（~/.daoyoucode/agents/）
    3. 项目Agents（.agents/）
    4. Entry points（pip安装的Agent包）
    
    Args:
        project_root: 项目根目录，默认为当前目录
    """
    logger.info("开始初始化所有Agents...")
    
    loader = get_agent_loader()
    loader.load_all(project_root)
    
    # 打印Agent信息
    _print_agents_info()


def load_agent_from_file(file_path: str):
    """
    从文件加载单个Agent
    
    Args:
        file_path: Python文件路径
    """
    loader = get_agent_loader()
    loader.load_from_file(file_path)


def load_agents_from_directory(directory: str, recursive: bool = False):
    """
    从目录加载Agents
    
    Args:
        directory: 目录路径
        recursive: 是否递归扫描子目录
    """
    loader = get_agent_loader()
    loader.load_from_directory(directory, recursive)


def _print_agents_info():
    """打印Agent信息"""
    registry = get_agent_registry()
    agents_info = registry.get_agents_info()
    
    logger.info(f"已注册 {len(agents_info)} 个Agent")
    logger.info("可用的Agents:")
    for name, info in agents_info.items():
        logger.info(
            f"  - {name}: {info['description']} "
            f"(模型: {info['model']}, "
            f"只读: {info['read_only']})"
        )


def get_agent(name: str):
    """
    获取Agent实例
    
    Args:
        name: Agent名称
    
    Returns:
        Agent实例，如果不存在返回None
    """
    registry = get_agent_registry()
    return registry.get_agent(name)


def list_agents():
    """列出所有可用的Agent"""
    registry = get_agent_registry()
    return registry.list_agents()


def get_agents_info():
    """获取所有Agent的详细信息"""
    registry = get_agent_registry()
    return registry.get_agents_info()
