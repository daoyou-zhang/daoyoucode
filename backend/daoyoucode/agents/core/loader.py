"""
Agent加载器

支持从多个来源加载Agent：
1. 内置Agents（builtin/）
2. 项目自定义Agents（项目根目录/.agents/）
3. 用户自定义Agents（~/.daoyoucode/agents/）
4. Python包（通过entry_points）

参考：
- oh-my-opencode的agent加载机制
- daoyouCodePilot的skill加载机制
"""

import os
import sys
import importlib
import importlib.util
from pathlib import Path
from typing import List, Dict, Optional
import logging

from .base import BaseAgent
from .registry import get_agent_registry

logger = logging.getLogger(__name__)


class AgentLoader:
    """
    Agent加载器
    
    支持多种加载方式：
    1. 从Python模块加载
    2. 从文件路径加载
    3. 从目录扫描加载
    """
    
    def __init__(self):
        self.registry = get_agent_registry()
        self.loaded_paths: List[str] = []
    
    def load_builtin_agents(self):
        """
        加载内置Agents
        
        从builtin/目录加载所有Agent
        """
        from ..builtin import (
            create_sisyphus_agent,
            create_chinese_editor_agent,
            create_oracle_agent,
            create_librarian_agent,
            create_explore_agent,
        )
        
        agents = [
            create_sisyphus_agent(),
            create_chinese_editor_agent(),
            create_oracle_agent(),
            create_librarian_agent(),
            create_explore_agent(),
        ]
        
        for agent in agents:
            self.registry.register(agent)
        
        logger.info(f"已加载 {len(agents)} 个内置Agent")
    
    def load_from_directory(self, directory: str, recursive: bool = False):
        """
        从目录加载Agents
        
        扫描目录中的Python文件，查找Agent类
        
        Args:
            directory: 目录路径
            recursive: 是否递归扫描子目录
        """
        directory = Path(directory)
        
        if not directory.exists():
            logger.warning(f"目录不存在: {directory}")
            return
        
        if not directory.is_dir():
            logger.warning(f"不是目录: {directory}")
            return
        
        # 扫描Python文件
        pattern = "**/*.py" if recursive else "*.py"
        py_files = list(directory.glob(pattern))
        
        loaded_count = 0
        for py_file in py_files:
            # 跳过__init__.py
            if py_file.name == "__init__.py":
                continue
            
            try:
                agents = self._load_from_file(py_file)
                loaded_count += len(agents)
            except Exception as e:
                logger.error(f"加载Agent失败: {py_file}, 错误: {e}")
        
        logger.info(f"从 {directory} 加载了 {loaded_count} 个Agent")
    
    def load_from_file(self, file_path: str):
        """
        从单个文件加载Agent
        
        Args:
            file_path: Python文件路径
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.warning(f"文件不存在: {file_path}")
            return
        
        agents = self._load_from_file(file_path)
        logger.info(f"从 {file_path} 加载了 {len(agents)} 个Agent")
    
    def _load_from_file(self, file_path: Path) -> List[BaseAgent]:
        """
        从文件加载Agent（内部方法）
        
        查找文件中所有继承自BaseAgent的类
        """
        # 构建模块名
        module_name = f"custom_agent_{file_path.stem}"
        
        # 动态导入模块
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            logger.warning(f"无法加载模块: {file_path}")
            return []
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        
        # 查找Agent类
        agents = []
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            
            # 检查是否是BaseAgent的子类（但不是BaseAgent本身）
            if (isinstance(attr, type) and 
                issubclass(attr, BaseAgent) and 
                attr is not BaseAgent):
                
                try:
                    # 实例化Agent
                    agent = attr()
                    
                    # 注册
                    self.registry.register(agent)
                    agents.append(agent)
                    
                    logger.info(f"加载Agent: {agent.name} from {file_path.name}")
                except Exception as e:
                    logger.error(f"实例化Agent失败: {attr_name}, 错误: {e}")
        
        return agents
    
    def load_project_agents(self, project_root: Optional[str] = None):
        """
        加载项目自定义Agents
        
        从项目根目录的.agents/目录加载
        
        Args:
            project_root: 项目根目录，默认为当前目录
        """
        if project_root is None:
            project_root = os.getcwd()
        
        agents_dir = Path(project_root) / ".agents"
        
        if agents_dir.exists():
            logger.info(f"加载项目Agents: {agents_dir}")
            self.load_from_directory(str(agents_dir), recursive=True)
        else:
            logger.debug(f"项目Agents目录不存在: {agents_dir}")
    
    def load_user_agents(self):
        """
        加载用户自定义Agents
        
        从用户目录的~/.daoyoucode/agents/加载
        """
        user_agents_dir = Path.home() / ".daoyoucode" / "agents"
        
        if user_agents_dir.exists():
            logger.info(f"加载用户Agents: {user_agents_dir}")
            self.load_from_directory(str(user_agents_dir), recursive=True)
        else:
            logger.debug(f"用户Agents目录不存在: {user_agents_dir}")
    
    def load_from_entry_points(self):
        """
        从Python包的entry_points加载Agents
        
        支持通过pip安装的Agent包
        
        在setup.py中定义：
        entry_points={
            'daoyoucode.agents': [
                'my_agent = my_package.agents:MyAgent',
            ]
        }
        """
        try:
            # Python 3.10+
            from importlib.metadata import entry_points
        except ImportError:
            # Python 3.9-
            from importlib_metadata import entry_points
        
        try:
            eps = entry_points()
            
            # 获取daoyoucode.agents组
            if hasattr(eps, 'select'):
                # Python 3.10+
                agent_eps = eps.select(group='daoyoucode.agents')
            else:
                # Python 3.9-
                agent_eps = eps.get('daoyoucode.agents', [])
            
            loaded_count = 0
            for ep in agent_eps:
                try:
                    # 加载Agent类
                    agent_class = ep.load()
                    
                    # 实例化
                    agent = agent_class()
                    
                    # 注册
                    self.registry.register(agent)
                    loaded_count += 1
                    
                    logger.info(f"从entry_point加载Agent: {agent.name}")
                except Exception as e:
                    logger.error(f"加载entry_point失败: {ep.name}, 错误: {e}")
            
            if loaded_count > 0:
                logger.info(f"从entry_points加载了 {loaded_count} 个Agent")
        
        except Exception as e:
            logger.error(f"加载entry_points失败: {e}")
    
    def load_all(self, project_root: Optional[str] = None):
        """
        加载所有来源的Agents
        
        顺序：
        1. 内置Agents
        2. 用户Agents
        3. 项目Agents
        4. Entry points
        
        Args:
            project_root: 项目根目录
        """
        logger.info("开始加载所有Agents...")
        
        # 1. 内置Agents
        self.load_builtin_agents()
        
        # 2. 用户Agents
        self.load_user_agents()
        
        # 3. 项目Agents
        self.load_project_agents(project_root)
        
        # 4. Entry points
        self.load_from_entry_points()
        
        # 统计
        total = len(self.registry.list_agents())
        logger.info(f"总共加载了 {total} 个Agent")
    
    def get_loaded_paths(self) -> List[str]:
        """获取已加载的路径"""
        return self.loaded_paths.copy()


def get_agent_loader() -> AgentLoader:
    """获取Agent加载器单例"""
    if not hasattr(get_agent_loader, '_instance'):
        get_agent_loader._instance = AgentLoader()
    return get_agent_loader._instance
