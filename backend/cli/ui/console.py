"""
Console工具

基于Rich的控制台输出。
（不在此处替换 sys.stdout/stderr，以免导致 I/O operation on closed file / lost sys.stderr）
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
# force_terminal=True: 强制终端模式
# force_interactive=False: 禁用交互式特性，避免输出被缓冲
# legacy_windows=False: 使用现代Windows终端
console = Console(
    theme=custom_theme,
    force_terminal=True,
    force_interactive=False,
    legacy_windows=False
)

__all__ = ["console"]
