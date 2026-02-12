"""
配置管理工具

读写配置文件
"""

import json
from pathlib import Path
from typing import Any, Dict


class Config:
    """配置管理器"""
    
    def __init__(self, config_file: Path = None):
        if config_file is None:
            config_file = Path.home() / ".daoyoucode" / "config.json"
        
        self.config_file = config_file
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        self._config = self._load()
    
    def _load(self) -> Dict[str, Any]:
        """加载配置"""
        if self.config_file.exists():
            try:
                return json.loads(self.config_file.read_text(encoding='utf-8'))
            except Exception:
                return self._default_config()
        return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """默认配置"""
        return {
            "model": "qwen-max",
            "temperature": 0.7,
            "max_tokens": 8000,
            "stream": True,
            "auto_commit": True,
            "language": "zh-CN",
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any):
        """设置配置项"""
        self._config[key] = value
        self._save()
    
    def _save(self):
        """保存配置"""
        self.config_file.write_text(
            json.dumps(self._config, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
    
    def all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._config.copy()
    
    def reset(self):
        """重置为默认配置"""
        self._config = self._default_config()
        self._save()


# 全局配置实例
_config_instance = None


def get_config() -> Config:
    """获取配置实例"""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance


__all__ = ["Config", "get_config"]
