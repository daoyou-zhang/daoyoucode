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
    rich_markup_mode="rich",  # 启用rich格式
)


@app.command()
def chat(
    files: Optional[list[Path]] = typer.Argument(None, help="要加载的文件"),
    model: str = typer.Option("qwen-max", "--model", "-m", help="使用的模型"),
    skill: str = typer.Option("chat-assistant", "--skill", "-s", help="使用的Skill (用 'daoyoucode skills' 查看所有)"),
    repo: Path = typer.Option(".", "--repo", "-r", help="仓库路径"),
    examples: bool = typer.Option(False, "--examples", help="显示使用示例"),
):
    """
    启动交互式对话 - DaoyouCode的主要功能
    
    支持指定Skill、模型和文件。在对话中可使用 /skill 切换Skill。
    """
    from cli.commands import chat as chat_cmd
    
    if examples:
        show_chat_examples()
        raise typer.Exit(0)
    
    chat_cmd.main(files, model, skill, repo)


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
def agent(
    agent_name: Optional[str] = typer.Argument(None, help="Agent名称 (不指定则列出所有)"),
    tools: bool = typer.Option(False, "--tools", "-t", help="显示Agent的工具列表"),
    examples: bool = typer.Option(False, "--examples", help="显示使用示例"),
):
    """
    Agent管理 - 查看所有Agent和详情
    
    Agent是执行任务的智能体，每个Agent有不同的职责和工具集。
    """
    from cli.commands import agent as agent_cmd
    
    if examples:
        show_agent_examples()
        raise typer.Exit(0)
    
    agent_cmd.main(agent_name, tools)


@app.command()
def models():
    """列出可用模型"""
    from cli.commands import models as models_cmd
    models_cmd.main()


@app.command()
def skills(
    skill_name: Optional[str] = typer.Argument(None, help="Skill名称 (不指定则列出所有)"),
    orchestrators: bool = typer.Option(False, "--orchestrators", "-o", help="显示编排器列表和说明"),
    examples: bool = typer.Option(False, "--examples", help="显示使用示例"),
):
    """
    Skill和编排器管理 - 查看所有Skill和编排器
    
    Skill定义了使用哪些Agent、工具和编排器。编排器负责协调多Agent工作。
    """
    from cli.commands import skills as skills_cmd
    
    if examples:
        show_skills_examples()
        raise typer.Exit(0)
    
    skills_cmd.main(skill_name, orchestrators)


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


@app.command()
def examples(
    command: Optional[str] = typer.Argument(None, help="命令名称 (chat/agent/skills)"),
):
    """
    显示命令使用示例和模板
    
    查看各命令的详细使用示例、推荐配置和最佳实践。
    """
    from cli.ui.console import console
    
    if not command:
        show_all_examples()
    elif command == "chat":
        show_chat_examples()
    elif command == "agent":
        show_agent_examples()
    elif command == "skills":
        show_skills_examples()
    else:
        console.print(f"[red]未知命令: {command}[/red]")
        console.print("[dim]可用命令: chat, agent, skills[/dim]")
        raise typer.Exit(1)


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
    import logging
    import sys
    
    # 打印调试信息（确认这段代码被执行）
    print(f"[DEBUG] 配置日志: verbose={verbose}, debug={debug}", file=sys.stderr)
    
    # 强制配置根 logger
    root_logger = logging.getLogger()
    
    # 清除现有的 handlers
    root_logger.handlers.clear()
    
    # 设置日志级别
    if debug:
        root_logger.setLevel(logging.DEBUG)
        print("[DEBUG] 设置日志级别为 DEBUG", file=sys.stderr)
    elif verbose:
        root_logger.setLevel(logging.INFO)
        print("[DEBUG] 设置日志级别为 INFO", file=sys.stderr)
    else:
        root_logger.setLevel(logging.WARNING)
    
    # 添加控制台 handler（输出到 stderr，避免与 Rich 冲突）
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.DEBUG if debug else (logging.INFO if verbose else logging.WARNING))
    
    # 设置格式
    formatter = logging.Formatter(
        '[%(asctime)s] %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    print(f"[DEBUG] 日志配置完成，handlers数量: {len(root_logger.handlers)}", file=sys.stderr)


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


def show_all_examples():
    """显示所有命令的示例"""
    from cli.ui.console import console
    from rich.panel import Panel
    
    examples_text = """
[bold cyan]DaoyouCode CLI 使用示例[/bold cyan]

[bold]1. 查看系统信息[/bold]
  daoyoucode agent                    # 列出所有Agent
  daoyoucode skills                   # 列出所有Skill
  daoyoucode skills --orchestrators   # 查看编排器说明

[bold]2. 启动对话[/bold]
  daoyoucode chat                                    # 默认chat模式
  daoyoucode chat --skill sisyphus-orchestrator      # 使用sisyphus编排
  daoyoucode chat --skill oracle                     # 使用oracle咨询
  daoyoucode chat --skill librarian                  # 使用librarian搜索

[bold]3. 查看详情[/bold]
  daoyoucode agent sisyphus           # 查看Agent详情
  daoyoucode agent sisyphus --tools   # 查看Agent工具
  daoyoucode skills oracle            # 查看Skill详情

[bold]4. 查看更多示例[/bold]
  daoyoucode examples chat            # chat命令示例
  daoyoucode examples agent           # agent命令示例
  daoyoucode examples skills          # skills命令示例
  
  或使用 --examples 标志:
  daoyoucode chat --examples
  daoyoucode agent --examples
  daoyoucode skills --examples

[dim]💡 提示: 使用 --help 查看命令参数说明[/dim]
"""
    console.print(Panel(examples_text, border_style="cyan", padding=(1, 2)))


def show_chat_examples():
    """显示chat命令示例"""
    from cli.ui.console import console
    from rich.panel import Panel
    
    examples_text = """
[bold cyan]chat 命令使用示例[/bold cyan]

[bold]基本用法[/bold]
  daoyoucode chat                     # 默认chat模式 (chat-assistant)
  daoyoucode chat --help              # 查看参数说明

[bold]指定Skill[/bold]
  daoyoucode chat --skill sisyphus-orchestrator    # 复杂任务（重构+测试）
  daoyoucode chat --skill oracle                   # 架构分析（只读）
  daoyoucode chat --skill librarian                # 文档搜索（只读）
  daoyoucode chat -s programming                   # 编程专家

[bold]指定模型[/bold]
  daoyoucode chat --model deepseek-coder           # 使用deepseek模型
  daoyoucode chat -m qwen-max                      # 使用qwen-max模型

[bold]加载文件[/bold]
  daoyoucode chat main.py                          # 加载单个文件
  daoyoucode chat main.py utils.py                 # 加载多个文件
  daoyoucode chat src/*.py                         # 加载目录下所有py文件

[bold]组合使用[/bold]
  daoyoucode chat --skill oracle --model qwen-max main.py
  daoyoucode chat -s sisyphus-orchestrator -m deepseek-coder

[bold]交互式命令[/bold]
  在对话中可以使用:
  /skill [name]    # 切换Skill
  /s [name]        # /skill的简写
  /model [name]    # 切换模型
  /add <file>      # 添加文件
  /help            # 显示帮助
  /exit            # 退出对话

[bold]推荐Skill[/bold]
  • chat-assistant (默认) - 日常对话和代码咨询
  • sisyphus-orchestrator - 复杂任务（重构+测试等）
  • oracle - 架构分析和技术建议（只读）
  • librarian - 文档搜索和代码查找（只读）

[dim]💡 提示: 使用 'daoyoucode skills' 查看所有可用Skill[/dim]
"""
    console.print(Panel(examples_text, border_style="cyan", padding=(1, 2)))


def show_agent_examples():
    """显示agent命令示例"""
    from cli.ui.console import console
    from rich.panel import Panel
    
    examples_text = """
[bold cyan]agent 命令使用示例[/bold cyan]

[bold]基本用法[/bold]
  daoyoucode agent                    # 列出所有Agent
  daoyoucode agent --help             # 查看参数说明

[bold]查看Agent详情[/bold]
  daoyoucode agent sisyphus           # 查看sisyphus详情
  daoyoucode agent oracle             # 查看oracle详情
  daoyoucode agent programmer         # 查看programmer详情

[bold]查看Agent工具[/bold]
  daoyoucode agent sisyphus --tools   # 查看sisyphus的工具列表
  daoyoucode agent oracle -t          # 查看oracle的工具列表

[bold]可用Agent[/bold]
  • sisyphus - 主编排Agent（4个工具）
    任务分解和Agent调度
    
  • oracle - 高IQ咨询Agent（10个工具）
    架构分析和技术建议（只读）
    
  • librarian - 文档搜索Agent（8个工具）
    文档和代码搜索（只读）
    
  • programmer - 编程专家（11个工具）
    代码编写和修改
    
  • refactor_master - 重构专家（13个工具）
    代码重构和优化
    
  • test_expert - 测试专家（10个工具）
    测试编写和修复

[bold]Agent与Skill的关系[/bold]
  Agent是执行者，Skill是配置文件。
  一个Skill可以使用一个或多个Agent。
  
  例如:
  • chat-assistant Skill 使用 MainAgent
  • sisyphus-orchestrator Skill 使用 sisyphus + 4个辅助Agent
  • oracle Skill 使用 oracle Agent

[dim]💡 提示: 使用 'daoyoucode skills' 查看Skill配置[/dim]
"""
    console.print(Panel(examples_text, border_style="cyan", padding=(1, 2)))


def show_skills_examples():
    """显示skills命令示例"""
    from cli.ui.console import console
    from rich.panel import Panel
    
    examples_text = """
[bold cyan]skills 命令使用示例[/bold cyan]

[bold]基本用法[/bold]
  daoyoucode skills                   # 列出所有Skill
  daoyoucode skills --help            # 查看参数说明

[bold]查看Skill详情[/bold]
  daoyoucode skills sisyphus-orchestrator    # 查看sisyphus详情
  daoyoucode skills oracle                   # 查看oracle详情
  daoyoucode skills librarian                # 查看librarian详情

[bold]查看编排器[/bold]
  daoyoucode skills --orchestrators   # 查看所有编排器和说明
  daoyoucode skills -o                # 简写

[bold]推荐Skill[/bold]
  • chat-assistant (默认)
    编排器: react
    用途: 日常对话和代码咨询
    
  • sisyphus-orchestrator
    编排器: multi_agent
    用途: 复杂任务（重构+测试等）
    Agent: sisyphus + 4个辅助Agent
    
  • oracle
    编排器: react
    用途: 架构分析和技术建议（只读）
    Agent: oracle
    
  • librarian
    编排器: react
    用途: 文档搜索和代码查找（只读）
    Agent: librarian

[bold]编排器类型[/bold]
  • simple - 简单编排（1个Agent）
  • react - ReAct模式（1个Agent + 工具）
  • multi_agent - 多Agent协作（多个Agent）
  • workflow - 工作流编排（预定义步骤）
  • parallel - 并行执行（多任务同时）

[bold]Multi-Agent协作模式[/bold]
  • sequential - 顺序执行
  • parallel - 并行执行
  • debate - 辩论模式
  • main_with_helpers - 主Agent + 辅助Agent（默认）

[bold]使用Skill[/bold]
  daoyoucode chat --skill sisyphus-orchestrator
  daoyoucode chat --skill oracle
  daoyoucode chat --skill librarian

[dim]💡 提示: 在对话中使用 /skill 命令可以动态切换Skill[/dim]
"""
    console.print(Panel(examples_text, border_style="cyan", padding=(1, 2)))


if __name__ == "__main__":
    main()

