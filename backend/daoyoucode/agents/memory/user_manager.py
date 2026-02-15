"""
用户管理器

负责生成和管理用户ID
"""

from pathlib import Path
import json
import uuid
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class UserManager:
    """
    用户管理器
    
    职责：
    1. 生成和管理用户ID
    2. 持久化用户信息
    3. 提供用户配置
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        初始化用户管理器
        
        Args:
            config_dir: 配置目录，默认为 ~/.daoyoucode
        """
        if config_dir is None:
            config_dir = str(Path.home() / '.daoyoucode')
        
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.user_file = self.config_dir / 'user.json'
        
        # 加载或创建用户信息
        self.user_info = self._load_or_create_user()
        
        logger.info(f"用户管理器已初始化: user_id={self.user_info['user_id']}")
    
    def _load_or_create_user(self) -> dict:
        """加载或创建用户信息"""
        if self.user_file.exists():
            try:
                with open(self.user_file, 'r', encoding='utf-8') as f:
                    user_info = json.load(f)
                logger.info(f"加载了现有用户: {user_info['user_id']}")
                return user_info
            except Exception as e:
                logger.warning(f"加载用户信息失败: {e}，将创建新用户")
        
        # 创建新用户
        user_info = {
            'user_id': self._generate_user_id(),
            'created_at': self._get_timestamp(),
            'config': {
                'language': 'zh-CN',
                'theme': 'default'
            }
        }
        
        self._save_user_info(user_info)
        logger.info(f"创建了新用户: {user_info['user_id']}")
        
        return user_info
    
    def _generate_user_id(self) -> str:
        """
        生成用户ID
        
        策略：
        1. 使用机器标识（如果可用）
        2. 否则使用UUID
        
        Returns:
            用户ID字符串
        """
        try:
            # 尝试使用机器标识
            import platform
            machine_id = platform.node()  # 主机名
            
            if machine_id:
                # 使用主机名的hash作为用户ID
                import hashlib
                hash_obj = hashlib.md5(machine_id.encode())
                return f"user-{hash_obj.hexdigest()[:12]}"
        except:
            pass
        
        # 回退到UUID
        return f"user-{uuid.uuid4().hex[:12]}"
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _save_user_info(self, user_info: dict):
        """保存用户信息"""
        try:
            with open(self.user_file, 'w', encoding='utf-8') as f:
                json.dump(user_info, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存用户信息失败: {e}")
    
    def get_user_id(self) -> str:
        """
        获取用户ID
        
        Returns:
            用户ID字符串
        """
        return self.user_info['user_id']
    
    def get_user_config(self, key: str, default=None):
        """
        获取用户配置
        
        Args:
            key: 配置键
            default: 默认值
        
        Returns:
            配置值
        """
        return self.user_info.get('config', {}).get(key, default)
    
    def set_user_config(self, key: str, value):
        """
        设置用户配置
        
        Args:
            key: 配置键
            value: 配置值
        """
        if 'config' not in self.user_info:
            self.user_info['config'] = {}
        
        self.user_info['config'][key] = value
        self._save_user_info(self.user_info)
        
        logger.info(f"更新了用户配置: {key}={value}")
    
    def reset_user(self):
        """重置用户（生成新的用户ID）"""
        self.user_info = {
            'user_id': self._generate_user_id(),
            'created_at': self._get_timestamp(),
            'config': {
                'language': 'zh-CN',
                'theme': 'default'
            }
        }
        
        self._save_user_info(self.user_info)
        logger.info(f"重置了用户: {self.user_info['user_id']}")


# 单例模式
_user_manager_instance = None


def get_user_manager() -> UserManager:
    """获取用户管理器单例"""
    global _user_manager_instance
    
    if _user_manager_instance is None:
        _user_manager_instance = UserManager()
    
    return _user_manager_instance


def get_current_user_id() -> str:
    """
    获取当前用户ID（便捷函数）
    
    Returns:
        用户ID字符串
    """
    return get_user_manager().get_user_id()
