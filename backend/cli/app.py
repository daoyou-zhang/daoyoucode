"""
DaoyouCode CLI 主应用

精简而强大的命令行界面
"""

import typer
from typing import Optional
from pathlib import Path

# 版本号
__version__ = "0.1.0"

# 创建主应用
app = typer.Typer(
    name="daoyoucode",
    help="DaoyouCode - 智能AI代码助手",
    add_completion=True,
    no_args_is_help=True,
)


@app.command()
def chat(
    files: Optional[list[Path]] = typer.Argument(None, help="要加载的文件"),
    model: str = typer.Option("qwen-max", "--model", "-m", help="使用的模型"),
    repo: Path = typer.Option(".", "--repo", "-r", help="仓库路径"),
):
    """启动交互式对话"""
    from cli.commands import chat as chat_cmd
    chat_cmd.main(files, model, repo)


@app.command()
def edit(
    files: list[Path] = typer.Argument(..., help="要编辑的文件"),
    instruction: str = typer.Argument(..., help="编辑指令"),
    model: str = typer.Option("qwen-max", "--model", "-m", help="使用的模型"),
    yes: bool = typer.Option(False, "--yes", "-y", help="自动确认所有操作"),
    repo: Path = typer.Option(".", "--repo", "-r", help="仓库路径"),
):
    """单次编辑文件"""
    from cli.commands import edit as edit_cmd
    edit_cmd.main(files, instruction, model, yes, repo)


@app.command()
def doctor(
    fix: bool = typer.Option(False, "--fix", help="自动修复问题"),
):
    """诊断系统环境"""
    from cli.commands import doctor as doctor_cmd
    doctor_cmd.main(fix)


@app.command()
def config():
    """配置管理"""
    from cli.commands import config as config_cmd
    config_cmd.main()


@app.command()
def session():
    """会话管理"""
    from cli.commands import session as session_cmd
    session_cmd.main()


@app.command()
def agent():
    """列出所有Agent"""
    from cli.commands import agent as agent_cmd
    agent_cmd.main()


@app.command()
def models():
    """列出可用模型"""
    from cli.commands import models as models_cmd
    models_cmd.main()


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="监听地址"),
    port: int = typer.Option(8000, "--port", "-p", help="监听端口"),
):
    """启动HTTP服务器"""
    from cli.commands import serve as serve_cmd
    serve_cmd.main(host, port)


@app.command()
def version():
    """显示版本信息"""
    typer.echo(f"DaoyouCode CLI v{__version__}")
    typer.echo("基于18大核心系统的智能AI代码助手")


@app.callback()
def callback(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="显示详细日志"),
    debug: bool = typer.Option(False, "--debug", help="开启调试模式"),
):
    """
    DaoyouCode - 智能AI代码助手
    
    精简而强大，基于18大核心系统
    """
    # 设置全局选项
    ctx.obj = {
        "verbose": verbose,
        "debug": debug,
    }
    
    # 配置日志
    if debug:
        import logging
        logging.basicConfig(level=logging.DEBUG)
    elif verbose:
        import logging
        logging.basicConfig(level=logging.INFO)


def main():
    """主入口"""
    try:
        app()
    except KeyboardInterrupt:
        typer.echo("\n\n👋 再见！")
        raise typer.Exit(0)
    except Exception as e:
        typer.echo(f"\n❌错误: {e}", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    main()
