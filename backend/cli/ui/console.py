"""
Console工具

基于Rich的控制台输出
"""

from rich.console import Console
from rich.theme import Theme

# 自定义主题
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
})

# 全局Console实例
console = Console(theme=custom_theme)

__all__ = ["console"]
