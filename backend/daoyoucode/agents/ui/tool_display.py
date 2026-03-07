"""
工具执行UI显示

提供美观的工具执行进度和结果显示
"""

from typing import Optional
import time

# 尝试导入 rich
try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich.panel import Panel
    from rich.table import Table
    from rich.syntax import Syntax
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class ToolDisplay:
    """工具执行显示器"""
    
    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
    
    def show_tool_start(self, tool_name: str, args: dict, agent_name: Optional[str] = None):
        """显示工具开始执行"""
        if RICH_AVAILABLE:
            # 创建参数表格
            table = Table(show_header=False, box=None, padding=(0, 1))
            table.add_column("Key", style="cyan")
            table.add_column("Value", style="white")
            
            for key, value in args.items():
                # 截断长值
                value_str = str(value)
                if len(value_str) > 60:
                    value_str = value_str[:57] + "..."
                table.add_row(key, value_str)
            
            # 如果有 agent_name，显示在工具名称后面
            tool_display = f"[cyan]{tool_name}[/cyan]"
            if agent_name:
                tool_display += f" [dim]({agent_name})[/dim]"
            
            self.console.print(f"\n[bold blue]🔧 执行工具:[/bold blue] {tool_display}")
            self.console.print(table)
        else:
            agent_info = f" ({agent_name})" if agent_name else ""
            print(f"\n🔧 执行工具: {tool_name}{agent_info}")
            print(f"   参数: {args}")
    
    def show_progress(self, tool_name: str, message: str = "正在执行..."):
        """
        显示进度条
        
        返回一个上下文管理器，用于 with 语句
        """
        if RICH_AVAILABLE:
            return Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=self.console,
                transient=True  # 完成后自动消失
            )
        else:
            # 简单的进度显示
            class SimpleProgress:
                def __enter__(self):
                    print(f"   ⏳ {message}")
                    return self
                
                def __exit__(self, *args):
                    pass
                
                def add_task(self, description, total=100):
                    return 0
                
                def update(self, task_id, **kwargs):
                    pass
            
            return SimpleProgress()
    
    def show_success(self, tool_name: str, duration: float, note: str = None):
        """显示执行成功"""
        if RICH_AVAILABLE:
            msg = f"   [green]✓[/green] 执行完成 [dim]({duration:.2f}秒)[/dim]"
            if note:
                msg += f" [cyan]{note}[/cyan]"
            self.console.print(msg)
        else:
            msg = f"   ✓ 执行完成 ({duration:.2f}秒)"
            if note:
                msg += f" {note}"
            print(msg)
    
    def show_error(self, tool_name: str, error: Exception, duration: float):
        """显示执行错误"""
        if RICH_AVAILABLE:
            error_msg = f"[red]✗ 执行失败[/red] [dim]({duration:.2f}秒)[/dim]\n\n{str(error)}"
            
            # 如果错误信息很长，截断显示
            if len(str(error)) > 200:
                error_msg = f"[red]✗ 执行失败[/red] [dim]({duration:.2f}秒)[/dim]\n\n{str(error)[:200]}..."
            
            self.console.print(Panel(
                error_msg,
                title=f"工具执行错误: {tool_name}",
                border_style="red",
                padding=(1, 2)
            ))
        else:
            print(f"   ✗ 执行失败 ({duration:.2f}秒): {error}")
    
    def show_warning(self, tool_name: str, message: str):
        """显示警告"""
        if RICH_AVAILABLE:
            self.console.print(f"   [yellow]⚠️  {message}[/yellow]")
        else:
            print(f"   ⚠️  {message}")
    
    def show_result_preview(self, result: str, max_lines: int = 5):
        """显示结果预览"""
        if not result:
            return
        
        lines = result.split('\n')
        preview_lines = lines[:max_lines]
        
        if RICH_AVAILABLE:
            if len(lines) > max_lines:
                preview = '\n'.join(preview_lines) + f"\n\n[dim]... (还有 {len(lines) - max_lines} 行)[/dim]"
            else:
                preview = '\n'.join(preview_lines)
            
            self.console.print(Panel(
                preview,
                title="结果预览",
                border_style="green",
                padding=(1, 2)
            ))
        else:
            print("\n   结果预览:")
            for line in preview_lines:
                print(f"   {line}")
            if len(lines) > max_lines:
                print(f"   ... (还有 {len(lines) - max_lines} 行)")


# 全局实例
_display = None


def get_tool_display() -> ToolDisplay:
    """获取工具显示器实例（单例）"""
    global _display
    if _display is None:
        _display = ToolDisplay()
    return _display
