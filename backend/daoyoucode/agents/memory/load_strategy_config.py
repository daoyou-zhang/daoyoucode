"""
Memory加载策略配置

支持从配置文件加载策略，实现灵活配置
"""

import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


# 默认策略配置
DEFAULT_STRATEGIES = {
    # 新对话：不加载
    'new_conversation': {
        'load_history': False,
        'load_summary': False,
        'load_profile': False,
        'cost': 0,
        'description': '新对话，不加载任何记忆'
    },
    # 简单追问（2轮内）
    'simple_followup': {
        'load_history': True,
        'history_limit': 2,
        'load_summary': False,
        'load_profile': False,
        'cost': 1,
        'description': '简单追问，加载最近2轮'
    },
    # 中等追问（3-5轮）
    'medium_followup': {
        'load_history': True,
        'history_limit': 3,
        'load_summary': False,
        'cost': 2,
        'description': '中等追问，加载最近3轮'
    },
    # 复杂追问（>5轮）
    'complex_followup': {
        'load_history': True,
        'history_limit': 2,  # 只加载最近2轮
        'load_summary': True,  # 加载摘要代替早期对话
        'cost': 3,
        'description': '复杂追问，加载摘要+最近2轮'
    },
    # 跨session（需要向量检索）
    'cross_session': {
        'load_history': True,
        'history_limit': 3,
        'load_summary': True,
        'use_vector_search': True,  # 使用向量检索
        'cost': 5,
        'description': '跨session，使用向量检索'
    }
}


class LoadStrategyConfig:
    """
    加载策略配置管理器
    
    功能：
    1. 从配置文件加载策略
    2. 支持YAML和JSON格式
    3. 提供默认策略
    4. 验证配置有效性
    5. 支持热重载
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径（可选）
        """
        self.config_path = config_path
        self.strategies = DEFAULT_STRATEGIES.copy()
        
        # 如果提供了配置文件，加载它
        if config_path:
            self.load_from_file(config_path)
        else:
            logger.info("使用默认加载策略配置")
    
    def load_from_file(self, config_path: str) -> bool:
        """
        从文件加载配置
        
        Args:
            config_path: 配置文件路径
        
        Returns:
            是否加载成功
        """
        try:
            path = Path(config_path)
            
            if not path.exists():
                logger.warning(f"配置文件不存在: {config_path}，使用默认配置")
                return False
            
            # 根据文件扩展名选择解析器
            if path.suffix in ['.yaml', '.yml']:
                with open(path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
            elif path.suffix == '.json':
                with open(path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            else:
                logger.error(f"不支持的配置文件格式: {path.suffix}")
                return False
            
            # 验证配置
            if not self._validate_config(config):
                logger.error("配置验证失败，使用默认配置")
                return False
            
            # 合并配置（用户配置覆盖默认配置）
            self.strategies.update(config.get('strategies', {}))
            
            logger.info(f"✅ 加载策略配置: {config_path}")
            logger.info(f"   策略数量: {len(self.strategies)}")
            
            return True
        
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}", exc_info=True)
            return False
    
    def _validate_config(self, config: Dict[str, Any]) -> bool:
        """
        验证配置有效性
        
        Args:
            config: 配置字典
        
        Returns:
            是否有效
        """
        if not isinstance(config, dict):
            logger.error("配置必须是字典")
            return False
        
        if 'strategies' not in config:
            logger.error("配置缺少 'strategies' 字段")
            return False
        
        strategies = config['strategies']
        if not isinstance(strategies, dict):
            logger.error("'strategies' 必须是字典")
            return False
        
        # 验证每个策略
        for name, strategy in strategies.items():
            if not isinstance(strategy, dict):
                logger.error(f"策略 '{name}' 必须是字典")
                return False
            
            # 检查必需字段
            if 'cost' not in strategy:
                logger.warning(f"策略 '{name}' 缺少 'cost' 字段，使用默认值0")
                strategy['cost'] = 0
        
        return True
    
    def get_strategy(self, name: str) -> Optional[Dict[str, Any]]:
        """
        获取策略配置
        
        Args:
            name: 策略名称
        
        Returns:
            策略配置字典
        """
        return self.strategies.get(name)
    
    def get_all_strategies(self) -> Dict[str, Dict[str, Any]]:
        """获取所有策略"""
        return self.strategies.copy()
    
    def add_strategy(self, name: str, config: Dict[str, Any]):
        """
        添加或更新策略
        
        Args:
            name: 策略名称
            config: 策略配置
        """
        self.strategies[name] = config
        logger.info(f"添加/更新策略: {name}")
    
    def remove_strategy(self, name: str) -> bool:
        """
        删除策略
        
        Args:
            name: 策略名称
        
        Returns:
            是否删除成功
        """
        if name in self.strategies:
            del self.strategies[name]
            logger.info(f"删除策略: {name}")
            return True
        return False
    
    def save_to_file(self, config_path: Optional[str] = None) -> bool:
        """
        保存配置到文件
        
        Args:
            config_path: 配置文件路径（可选，默认使用初始化时的路径）
        
        Returns:
            是否保存成功
        """
        path = config_path or self.config_path
        
        if not path:
            logger.error("未指定配置文件路径")
            return False
        
        try:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            config = {
                'strategies': self.strategies
            }
            
            # 根据文件扩展名选择格式
            if path.suffix in ['.yaml', '.yml']:
                with open(path, 'w', encoding='utf-8') as f:
                    yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
            elif path.suffix == '.json':
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
            else:
                logger.error(f"不支持的配置文件格式: {path.suffix}")
                return False
            
            logger.info(f"✅ 保存策略配置: {path}")
            return True
        
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}", exc_info=True)
            return False
    
    def export_default_config(self, output_path: str) -> bool:
        """
        导出默认配置到文件（用于生成模板）
        
        Args:
            output_path: 输出文件路径
        
        Returns:
            是否导出成功
        """
        try:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            config = {
                'strategies': DEFAULT_STRATEGIES
            }
            
            # 根据文件扩展名选择格式
            if path.suffix in ['.yaml', '.yml']:
                with open(path, 'w', encoding='utf-8') as f:
                    yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
            elif path.suffix == '.json':
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
            else:
                logger.error(f"不支持的配置文件格式: {path.suffix}")
                return False
            
            logger.info(f"✅ 导出默认配置: {output_path}")
            return True
        
        except Exception as e:
            logger.error(f"导出默认配置失败: {e}", exc_info=True)
            return False
    
    def reload(self) -> bool:
        """
        重新加载配置（热重载）
        
        Returns:
            是否重载成功
        """
        if not self.config_path:
            logger.warning("未指定配置文件路径，无法重载")
            return False
        
        logger.info("重新加载配置...")
        return self.load_from_file(self.config_path)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取配置统计信息"""
        return {
            'total_strategies': len(self.strategies),
            'strategy_names': list(self.strategies.keys()),
            'config_path': self.config_path,
            'using_default': self.config_path is None
        }


# 全局配置实例
_config_instance: Optional[LoadStrategyConfig] = None


def get_load_strategy_config(config_path: Optional[str] = None) -> LoadStrategyConfig:
    """
    获取加载策略配置实例（单例）
    
    Args:
        config_path: 配置文件路径（可选，仅首次调用时有效）
    
    Returns:
        LoadStrategyConfig实例
    """
    global _config_instance
    
    if _config_instance is None:
        _config_instance = LoadStrategyConfig(config_path)
    
    return _config_instance


def set_load_strategy_config(config: LoadStrategyConfig):
    """
    设置全局配置实例
    
    Args:
        config: LoadStrategyConfig实例
    """
    global _config_instance
    _config_instance = config
