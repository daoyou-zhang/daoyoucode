"""
配置管理命令

查看和修改配置
"""

import typer
from typing import Optional


app = typer.Typer(help="配置管理")


@app.command()
def show():
    """显示当前配置"""
    from cli.ui.console import console
    from cli.utils.config import get_config
    from rich.table import Table
    
    config = get_config()
    
    console.print("\n[bold cyan]⚙️  当前配置[/bold cyan]\n")
    
    table = Table(show_header=True, border_style="cyan")
    table.add_column("配置项", style="bold")
    table.add_column("值", style="cyan")
    
    for key, value in config.all().items():
        table.add_row(key, str(value))
    
    console.print(table)
    console.print(f"\n[dim]配置文件: {config.config_file}[/dim]\n")


@app.command()
def set(
    key: str = typer.Argument(..., help="配置项"),
    value: str = typer.Argument(..., help="配置值"),
):
    """设置配置项"""
    from cli.ui.console import console
    from cli.utils.config import get_config
    
    config = get_config()
    
    # 类型转换
    if value.lower() in ('true', 'false'):
        value = value.lower() == 'true'
    elif value.isdigit():
        value = int(value)
    elif value.replace('.', '', 1).isdigit():
        value = float(value)
    
    config.set(key, value)
    console.print(f"\n[green]✓[/green] 已设置 [bold]{key}[/bold] = [cyan]{value}[/cyan]\n")


@app.command()
def reset():
    """重置为默认配置"""
    from cli.ui.console import console
    from cli.utils.config import get_config
    
    if typer.confirm("确定要重置配置吗？"):
        config = get_config()
        config.reset()
        console.print("\n[green]✓[/green] 配置已重置为默认值\n")
    else:
        console.print("\n[yellow]已取消[/yellow]\n")


def main():
    """配置管理入口"""
    app()
