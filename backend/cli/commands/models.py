"""
模型管理命令

查看可用模型
"""

import typer


def main():
    """列出所有可用模型"""
    from cli.ui.console import console
    from rich.table import Table
    
    console.print("\n[bold cyan]🎯 可用模型[/bold cyan]\n")
    
    # TODO: 从LLM管理器读取
    models = [
        {"name": "qwen-max", "provider": "通义千问", "type": "通用"},
        {"name": "qwen-coder-plus", "provider": "通义千问", "type": "代码"},
        {"name": "deepseek-coder", "provider": "DeepSeek", "type": "代码"},
        {"name": "claude-opus-4.5", "provider": "Anthropic", "type": "通用"},
        {"name": "gpt-5.2", "provider": "OpenAI", "type": "通用"},
        {"name": "glm-4.7", "provider": "智谱AI", "type": "通用"},
    ]
    
    table = Table(show_header=True)
    table.add_column("模型名称")
    table.add_column("提供商")
    table.add_column("类型")
    
    for model in models:
        table.add_row(model["name"], model["provider"], model["type"])
    
    console.print(table)
    console.print()
