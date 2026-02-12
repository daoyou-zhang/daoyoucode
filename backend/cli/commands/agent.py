"""
Agent管理命令

查看和管理Agent
"""

import typer


def main():
    """列出所有Agent"""
    from cli.ui.console import console
    from rich.table import Table
    
    console.print("\n[bold cyan]🤖 Agent列表[/bold cyan]\n")
    
    # TODO: 从Agent注册表读取
    agents = [
        {"name": "MainAgent", "model": "claude-opus-4.5", "status": "active"},
        {"name": "PlanAgent", "model": "claude-opus-4.5", "status": "active"},
        {"name": "CodeAgent", "model": "qwen-coder-plus", "status": "active"},
        {"name": "DebugAgent", "model": "gpt-5.2", "status": "active"},
        {"name": "TestAgent", "model": "deepseek-coder", "status": "active"},
        {"name": "DocAgent", "model": "glm-4.7", "status": "active"},
    ]
    
    table = Table(show_header=True)
    table.add_column("Agent")
    table.add_column("模型")
    table.add_column("状态")
    
    for agent in agents:
        status_color = "green" if agent["status"] == "active" else "red"
        table.add_row(
            agent["name"],
            agent["model"],
            f"[{status_color}]{agent['status']}[/{status_color}]"
        )
    
    console.print(table)
    console.print()
