"""
简单日志工具
"""

import logging
from pathlib import Path


def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """设置日志"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # 控制台处理器
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


__all__ = ["setup_logger"]
