"""
内置Hooks

提供常用的Hook实现
"""

from .logging import LoggingHook
from .metrics import MetricsHook
from .validation import ValidationHook
from .retry import RetryHook

__all__ = [
    'LoggingHook',
    'MetricsHook',
    'ValidationHook',
    'RetryHook',
]


# 便捷函数：创建默认Hook集合
def create_default_hooks():
    """创建默认的Hook集合"""
    return [
        LoggingHook(),
        MetricsHook(),
        ValidationHook(),
    ]


def create_production_hooks():
    """创建生产环境的Hook集合"""
    return [
        LoggingHook(),
        MetricsHook(),
        ValidationHook(
            min_length=1,
            max_length=5000,
            forbidden_words=['test', 'debug']  # 示例
        ),
        RetryHook(max_retries=3),
    ]
