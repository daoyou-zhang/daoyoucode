"""
错误处理工具

友好的错误提示
"""

from cli.ui.console import console
from rich.panel import Panel


class DaoyouError(Exception):
    """DaoyouCode错误基类"""
    
    def __init__(self, message: str, suggestions: list = None):
        self.message = message
        self.suggestions = suggestions or []
        super().__init__(message)
    
    def show(self):
        """显示友好的错误信息"""
        error_text = f"[bold red]错误[/bold red]\n\n{self.message}"
        
        if self.suggestions:
            error_text += "\n\n[bold yellow]建议[/bold yellow]\n"
            for i, suggestion in enumerate(self.suggestions, 1):
                error_text += f"\n{i}. {suggestion}"
        
        console.print(Panel(
            error_text,
            title="❌ 出错了",
            border_style="red",
            padding=(1, 2)
        ))


class FileNotFoundError(DaoyouError):
    """文件不存在错误"""
    
    def __init__(self, filepath: str):
        super().__init__(
            f"文件不存在: {filepath}",
            suggestions=[
                "检查文件路径是否正确",
                "使用绝对路径或相对路径",
                "确认文件确实存在"
            ]
        )


class AgentError(DaoyouError):
    """Agent错误"""
    
    def __init__(self, message: str):
        super().__init__(
            message,
            suggestions=[
                "检查API密钥是否配置",
                "检查网络连接",
                "尝试切换其他模型"
            ]
        )


class ConfigError(DaoyouError):
    """配置错误"""
    
    def __init__(self, message: str):
        super().__init__(
            message,
            suggestions=[
                "运行 daoyoucode config show 查看配置",
                "运行 daoyoucode config reset 重置配置",
                "检查配置文件格式"
            ]
        )


def handle_error(error: Exception):
    """统一错误处理"""
    if isinstance(error, DaoyouError):
        error.show()
    else:
        console.print(f"\n[red]❌ 未知错误: {error}[/red]\n")


__all__ = [
    "DaoyouError",
    "FileNotFoundError",
    "AgentError",
    "ConfigError",
    "handle_error"
]
