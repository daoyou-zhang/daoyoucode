"""
交互式对话命令

最重要的命令，提供完整的交互式体验
"""

import typer
from typing import Optional, List
from pathlib import Path
from rich.panel import Panel
from rich.markdown import Markdown
from rich.live import Live
from rich.spinner import Spinner
import time


def determine_repo_path(files: Optional[List[Path]], repo_arg: Path) -> Path:
    """
    确定仓库路径
    
    优先级：
    1. 如果提供了文件，从文件推断 git 仓库
    2. 如果提供了 --repo 参数，使用该路径
    3. 否则，从当前目录向上查找 git 仓库
    4. 如果找不到 git 仓库，使用当前目录
    
    采用智能路径解析策略
    """
    try:
        import git
    except ImportError:
        # 如果没有 gitpython，使用当前目录
        if str(repo_arg) != ".":
            return Path(repo_arg).resolve()
        return Path.cwd()
    
    # 1. 从文件推断
    if files:
        repo_paths = set()
        for file in files:
            file_path = Path(file).resolve()
            
            # 如果文件不存在，使用父目录
            if not file_path.exists() and file_path.parent.exists():
                file_path = file_path.parent
            
            try:
                repo = git.Repo(file_path, search_parent_directories=True)
                repo_paths.add(Path(repo.working_tree_dir).resolve())
            except (git.InvalidGitRepositoryError, FileNotFoundError, git.GitCommandError):
                # 文件不在 git 仓库中，使用文件所在目录
                if file_path.is_file():
                    repo_paths.add(file_path.parent)
                else:
                    repo_paths.add(file_path)
        
        if len(repo_paths) > 1:
            from cli.ui.console import console
            console.print("[red]错误: 提供的文件来自不同的 git 仓库[/red]")
            raise typer.Exit(1)
        
        if repo_paths:
            return repo_paths.pop()
    
    # 2. 使用 --repo 参数
    if str(repo_arg) != ".":
        return Path(repo_arg).resolve()
    
    # 3. 从当前目录向上查找 git 仓库
    try:
        repo = git.Repo(Path.cwd(), search_parent_directories=True)
        return Path(repo.working_tree_dir).resolve()
    except (git.InvalidGitRepositoryError, FileNotFoundError, git.GitCommandError):
        pass
    
    # 4. 使用当前目录
    return Path.cwd()


def main(
    files: Optional[List[Path]] = typer.Argument(None, help="要加载的文件"),
    model: str = typer.Option("qwen-plus", "--model", "-m", help="使用的模型"),
    skill: str = typer.Option("chat-assistant", "--skill", "-s", help="使用的Skill"),
    repo: Path = typer.Option(".", "--repo", "-r", help="仓库路径"),
    subtree_only: bool = typer.Option(False, "--subtree-only", help="只扫描当前目录及其子目录"),
):
    """
    启动交互式对话 - DaoyouCode的主要功能
    
    \b
    示例:
        daoyoucode chat                                    # 默认chat模式
        daoyoucode chat --skill sisyphus-orchestrator      # 使用sisyphus编排
        daoyoucode chat --skill oracle                     # 使用oracle咨询
        daoyoucode chat --skill librarian                  # 使用librarian搜索
        daoyoucode chat main.py utils.py                   # 加载文件
        daoyoucode chat --model deepseek-coder             # 指定模型
    
    \b
    说明:
        启动交互式对话，可以指定Skill、模型和文件。
        在对话中可以使用 /skill 切换Skill，/help 查看所有命令。
    
    \b
    推荐Skill:
        • chat-assistant (默认) - 日常对话和代码咨询
        • sisyphus-orchestrator - 复杂任务（重构+测试等）
        • oracle - 架构分析和技术建议（只读）
        • librarian - 文档搜索和代码查找（只读）
    
    \b
    交互式命令:
        /skill [name]  - 切换Skill
        /model [name]  - 切换模型
        /add <file>    - 添加文件
        /help          - 显示帮助
        /exit          - 退出对话
    """
    from cli.ui.console import console
    import uuid
    import os
    
    # 使用智能 repo_path 确定逻辑
    repo_path = determine_repo_path(files, repo)
    
    # 显示欢迎横幅
    show_banner(model, repo_path, files, skill, subtree_only)
    
    # ✅ 提前初始化Agent系统（避免在交互过程中初始化导致冲突）
    console.print("\n[dim]正在初始化Agent系统...[/dim]")
    
    try:
        from daoyoucode.agents.init import initialize_agent_system
        from daoyoucode.agents.tools.registry import get_tool_registry
        from daoyoucode.agents.tools.base import ToolContext
        from daoyoucode.agents.llm.client_manager import get_client_manager
        from daoyoucode.agents.llm.config_loader import auto_configure
        from daoyoucode.agents.memory.manager import get_memory_manager
        
        # 🆕 初始化记忆管理器（支持项目级存储）
        # 注意：必须在 initialize_agent_system() 之前初始化，这样 Agent 才能获取到正确的实例
        memory_manager = get_memory_manager(project_path=repo_path, force_new=True)
        
        initialize_agent_system()
        
        registry = get_tool_registry()
        tool_context = ToolContext(
            repo_path=repo_path,
            subtree_only=subtree_only,
            cwd=Path.cwd() if subtree_only else None,
        )
        registry.set_context(tool_context)
        
        client_manager = get_client_manager()
        auto_configure(client_manager)
        
        console.print("[dim]✓ 初始化完成[/dim]")
    except Exception as e:
        console.print(f"[red]初始化失败: {e}[/red]")
        import traceback
        traceback.print_exc()
        raise typer.Exit(1)
    
    # 生成会话ID（用于记忆系统）
    session_id = str(uuid.uuid4())
    
    # 简单的上下文（只存储UI状态）
    ui_context = {
        "session_id": session_id,
        "model": model,
        "skill": skill,  # ← 添加skill
        "repo": str(repo_path),
        "initial_files": [str(f) for f in files] if files else [],
        "subtree_only": subtree_only,
        "cwd": str(Path.cwd())  # 保存当前工作目录（用于 subtree_only）
    }
    
    try:
        # 主循环
        while True:
            # 获取用户输入
            try:
                user_input = console.input("\n[bold green]你[/bold green] > ")
            except EOFError:
                # 管道输入结束
                console.print("\n[cyan]输入结束[/cyan]\n")
                break
            except KeyboardInterrupt:
                raise
            
            # 立即刷新输出流，避免Rich缓冲导致后续输出丢失
            import sys
            sys.stdout.flush()
            sys.stderr.flush()
            
            if not user_input.strip():
                continue
            
            # 处理命令
            if user_input.startswith("/"):
                if not handle_command(user_input, ui_context):
                    break  # /exit命令返回False
                continue
            
            # 处理普通对话（通过Skill系统）
            handle_chat(user_input, ui_context)
            
            # 对话完成后再次刷新
            sys.stdout.flush()
            sys.stderr.flush()
    
    except KeyboardInterrupt:
        console.print("\n\n[cyan]👋 再见！[/cyan]\n")
        raise typer.Exit(0)
    except Exception as e:
        console.print(f"\n[red]❌ 错误: {e}[/red]\n")
        raise typer.Exit(1)


def show_banner(model: str, repo: Path, files: Optional[List[Path]], skill: str, subtree_only: bool = False):
    """显示欢迎横幅"""
    from cli.ui.console import console
    import os
    
    banner = """
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║     DaoyouCode 交互式对话                                ║
║                                                          ║
║     精简而强大，基于18大核心系统                         ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
"""
    console.print(f"[bold cyan]{banner}[/bold cyan]")
    
    # 显示配置信息（仓库始终为 git 根；扫描范围仅影响 repo_map 等工具的路径过滤，不影响文档检索）
    scope_info = ""
    if subtree_only:
        cwd = Path.cwd()
        try:
            rel_cwd = cwd.relative_to(repo)
            scope_info = f"\n* 扫描范围: [yellow]{rel_cwd}/ (仅当前目录，代码地图等)[/yellow]"
        except ValueError:
            scope_info = f"\n* 扫描范围: [yellow]当前目录[/yellow]"
    
    info_panel = f"""
[bold]当前配置[/bold]
* Skill: [cyan]{skill}[/cyan]
* 模型: [cyan]{model}[/cyan]
* 仓库: [dim]{repo}[/dim] (git 根，文档检索用此)
* 文件: [dim]{len(files) if files else 0} 个[/dim]{scope_info}
"""
    console.print(Panel(info_panel, border_style="cyan", padding=(0, 2)))
    
    # 显示提示
    console.print("\n[yellow]提示:[/yellow]")
    console.print("  * 输入 [cyan]/help[/cyan] 查看所有命令")
    console.print("  * 输入 [cyan]/skill[/cyan] 切换Skill")
    console.print("  * 输入 [cyan]/exit[/cyan] 退出对话")
    console.print("  * 按 [cyan]Ctrl+C[/cyan] 也可退出")


def show_current_config(ui_context: dict):
    """显示当前配置（用于切换后更新显示）"""
    from cli.ui.console import console
    from pathlib import Path
    
    repo = Path(ui_context['repo'])
    skill = ui_context.get('skill', 'chat-assistant')
    model = ui_context.get('model', 'qwen-plus')
    files = ui_context.get('initial_files', [])
    subtree_only = ui_context.get('subtree_only', False)
    
    scope_info = ""
    if subtree_only:
        cwd = Path(ui_context.get('cwd', Path.cwd()))
        try:
            rel_cwd = cwd.relative_to(repo)
            scope_info = f"\n* 扫描范围: [yellow]{rel_cwd}/ (仅当前目录，代码地图等)[/yellow]"
        except ValueError:
            scope_info = f"\n* 扫描范围: [yellow]当前目录[/yellow]"
    
    info_panel = f"""
[bold]当前配置[/bold]
* Skill: [cyan]{skill}[/cyan]
* 模型: [cyan]{model}[/cyan]
* 仓库: [dim]{repo}[/dim] (git 根，文档检索用此)
* 文件: [dim]{len(files)} 个[/dim]{scope_info}
"""
    console.print(Panel(info_panel, border_style="cyan", padding=(0, 2)))


def handle_command(cmd: str, ui_context: dict) -> bool:
    """
    处理命令
    
    Returns:
        True: 继续对话
        False: 退出对话
    """
    from cli.ui.console import console
    
    parts = cmd.split(maxsplit=1)
    command = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""
    
    if command == "/exit" or command == "/quit":
        console.print("\n[cyan]👋 再见！[/cyan]\n")
        return False
    
    elif command == "/help":
        show_help()
    
    elif command == "/model":
        if not args:
            console.print(f"[cyan]当前模型: {ui_context['model']}[/cyan]")
        else:
            ui_context['model'] = args
            console.print(f"[green]✓[/green] 已切换到模型: [cyan]{args}[/cyan]")
    
    elif command == "/clear":
        clear_history(ui_context)
    
    elif command == "/history":
        show_history(ui_context)
    
    elif command == "/session":
        console.print(f"[cyan]会话ID: {ui_context['session_id']}[/cyan]")
    
    elif command == "/skill" or command == "/s":
        if not args:
            # 显示当前Skill和可用Skill
            show_skills(ui_context)
        else:
            # 切换Skill
            switch_skill(args, ui_context)
    
    else:
        console.print(f"[red]未知命令: {command}[/red]")
        console.print("[dim]输入 /help 查看所有命令[/dim]")
    
    return True


def show_help():
    """显示帮助信息"""
    from cli.ui.console import console
    
    help_text = """
[bold cyan]可用命令[/bold cyan]

[bold]对话控制[/bold]
  /exit, /quit     退出对话
  /clear           清空对话历史
  /history         查看对话历史

[bold]Skill管理[/bold]
  /skill [name]    切换Skill（不带参数显示列表）
  /s [name]        /skill的简写

[bold]文件管理[/bold]
  /add <file>      添加文件到上下文
  /drop <file>     从上下文移除文件
  /files           查看已加载的文件

[bold]配置[/bold]
  /model [name]    查看或切换模型
  /help            显示此帮助

[bold]快捷键[/bold]
  Ctrl+C           退出对话
"""
    console.print(Panel(help_text, border_style="cyan", padding=(1, 2)))


def add_file(filepath: str, context: dict):
    """添加文件到上下文"""
    from cli.ui.console import console
    
    path = Path(filepath)
    if not path.exists():
        console.print(f"[red]文件不存在: {filepath}[/red]")
        return
    
    if str(path) in context["files"]:
        console.print(f"[yellow]文件已在上下文中: {filepath}[/yellow]")
        return
    
    # 读取文件内容
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 保存文件路径和内容
        context["files"].append(str(path))
        if "file_contents" not in context:
            context["file_contents"] = {}
        context["file_contents"][str(path)] = content
        
        # 显示文件信息
        lines = len(content.splitlines())
        size = len(content)
        console.print(f"[green]✓[/green] 已添加文件: [cyan]{filepath}[/cyan]")
        console.print(f"[dim]  {lines} 行, {size} 字符[/dim]")
    
    except Exception as e:
        console.print(f"[red]读取文件失败: {e}[/red]")


def drop_file(filepath: str, context: dict):
    """从上下文移除文件"""
    from cli.ui.console import console
    
    if filepath in context["files"]:
        context["files"].remove(filepath)
        if "file_contents" in context and filepath in context["file_contents"]:
            del context["file_contents"][filepath]
        console.print(f"[green]✓[/green] 已移除文件: [cyan]{filepath}[/cyan]")
    else:
        console.print(f"[yellow]文件不在上下文中: {filepath}[/yellow]")


def auto_load_project_files(context: dict, repo: Path):
    """自动加载项目关键文件"""
    from cli.ui.console import console
    import os
    
    # 定义要自动加载的文件模式
    key_files = [
        "README.md",
        "README.txt",
        "STRUCTURE.txt",
        "PROJECT_STRUCTURE.md",
        "ARCHITECTURE.md",
        "核心设计文档.md",
        "项目结构设计.md",
    ]
    
    loaded_files = []
    repo_path = Path(repo)
    
    # 尝试加载关键文件
    for filename in key_files:
        file_path = repo_path / filename
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 限制文件大小（避免加载过大的文件）
                if len(content) > 50000:  # 50KB限制
                    console.print(f"[yellow]⚠[/yellow] 跳过大文件: [dim]{filename}[/dim]")
                    continue
                
                context["files"].append(str(file_path))
                context["file_contents"][str(file_path)] = content
                loaded_files.append(filename)
            
            except Exception as e:
                console.print(f"[yellow]⚠[/yellow] 无法读取: [dim]{filename}[/dim]")
    
    # 显示加载结果
    if loaded_files:
        console.print(f"\n[dim]✓ 自动加载了 {len(loaded_files)} 个项目文件:[/dim]")
        for filename in loaded_files:
            console.print(f"[dim]  • {filename}[/dim]")
        console.print()
    else:
        console.print(f"\n[dim]💡 未找到项目文档，使用 /add 命令添加文件[/dim]\n")


def show_files(context: dict):
    """显示已加载的文件"""
    from cli.ui.console import console
    from rich.table import Table
    
    if not context["files"]:
        console.print("[yellow]未加载任何文件[/yellow]")
        return
    
    table = Table(title="已加载的文件", show_header=True, border_style="cyan")
    table.add_column("#", style="dim")
    table.add_column("文件路径", style="cyan")
    
    for i, file in enumerate(context["files"], 1):
        table.add_row(str(i), file)
    
    console.print(table)


def clear_history(context: dict):
    """清空对话历史"""
    from cli.ui.console import console
    
    context["history"].clear()
    console.print("[green]✓[/green] 对话历史已清空")


def change_model(model: str, context: dict):
    """切换模型"""
    from cli.ui.console import console
    
    context["model"] = model
    console.print(f"[green]✓[/green] 已切换到模型: [cyan]{model}[/cyan]")


def show_history(context: dict):
    """显示对话历史"""
    from cli.ui.console import console
    
    if not context["history"]:
        console.print("[yellow]暂无对话历史[/yellow]")
        return
    
    console.print("\n[bold cyan]对话历史[/bold cyan]\n")
    for i, (user_msg, ai_msg) in enumerate(context["history"], 1):
        console.print(f"[dim]--- 第 {i} 轮 ---[/dim]")
        console.print(f"[bold green]你[/bold green]: {user_msg}")
        console.print(f"[bold blue]AI[/bold blue]: {ai_msg}\n")


def handle_chat(user_input: str, ui_context: dict):
    """处理对话 - 通过Skill系统"""
    import sys
    try:
        _handle_chat_impl(user_input, ui_context)
    except Exception as e:
        try:
            sys.stdout.write("\nAI > [Error] ")
            sys.stdout.write(str(e).encode("ascii", errors="replace").decode("ascii")[:200])
            sys.stdout.write("\n")
            sys.stdout.flush()
        except Exception:
            sys.stdout.write("\nAI > [Error]\n")
            sys.stdout.flush()


def _handle_chat_impl(user_input: str, ui_context: dict):
    """实际对话逻辑（内层）"""
    from cli.ui.console import console
    import asyncio
    import os
    import sys
    
    # 立即刷新输出流，确保之前的输出都显示出来
    sys.stdout.flush()
    sys.stderr.flush()

    ai_response = ""  # 保证后续显示块一定有定义
    repo_path = os.path.abspath(ui_context["repo"])
    skill_name = ui_context.get("skill", "chat-assistant")
    
    context = {
        "session_id": ui_context["session_id"],
        "repo": repo_path,
        "model": ui_context["model"],
        "initial_files": ui_context.get("initial_files", []),
        "subtree_only": ui_context.get("subtree_only", False),
        "cwd": ui_context.get("cwd", os.getcwd()),
        "working_directory": repo_path,
        "repo_root": repo_path,
        "enable_streaming": False,  # 🆕 启用流式输出
    }
    
    # 会话级初始化已在main函数中完成，这里不再需要
    
    try:
        # 通过Skill系统执行（带超时，避免一直无返回）
        from daoyoucode.agents.executor import execute_skill
        import asyncio
        import sys

        # 显示思考提示并立即刷新
        sys.stdout.write("\n")
        sys.stdout.flush()
        _safe_console_print(console, "[bold blue]AI正在思考...[/bold blue]")
        sys.stdout.flush()
        sys.stderr.flush()
        
        # 获取或创建事件循环
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError as e:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        async def _run():
            # 🔥 预热LSP服务器（在后台运行，不阻塞）
            try:
                from daoyoucode.agents.init import warmup_lsp_async
                warmup_lsp_async()  # 创建后台任务
            except Exception:
                pass  # 忽略预热失败
            
            result = await execute_skill(
                skill_name=skill_name,
                user_input=user_input,
                session_id=context["session_id"],
                context=context,
            )
            return result
        
        try:
            # 从配置读取超时时间，默认30分钟
            from daoyoucode.agents.llm.config_loader import load_llm_config
            try:
                llm_config = load_llm_config()
                cli_timeout = llm_config.get('default', {}).get('timeout', 1800)
            except:
                cli_timeout = 1800  # 默认30分钟
            
            result = loop.run_until_complete(asyncio.wait_for(_run(), timeout=cli_timeout))
        except asyncio.TimeoutError:
            console.print(f"[yellow]警告: 请求超时（{cli_timeout}秒），请检查网络或稍后重试。[/yellow]")
            ai_response = "抱歉，本次请求超时。请检查网络与 API 配置后重试。"
            result = None
        
        if result is not None:
            # 检查是否是流式结果（生成器）
            import inspect
            if inspect.isasyncgen(result):
                # 🌊 流式输出模式
                sys.stdout.write("\nAI > ")
                sys.stdout.flush()
                
                async def consume_stream():
                    content = ""
                    async for event in result:
                        if event.get('type') == 'token':
                            token = event.get('content', '')
                            content += token
                            try:
                                sys.stdout.write(token)
                                sys.stdout.flush()
                            except (UnicodeEncodeError, UnicodeDecodeError):
                                # 编码错误，跳过这个 token
                                pass
                        elif event.get('type') == 'edit_event':
                            # 🔥 编辑事件
                            edit_event = event.get('event')
                            if edit_event:
                                # 导入显示函数
                                from cli.commands.edit import display_edit_event_simple
                                from cli.ui.console import console
                                
                                # 显示编辑事件
                                display_edit_event_simple(edit_event, console)
                        elif event.get('type') == 'result':
                            # 流式输出完成
                            pass
                    sys.stdout.write("\n")
                    sys.stdout.flush()
                    return content
                
                ai_response = loop.run_until_complete(consume_stream())
                
            elif result.get("success"):
                ai_response = result.get("content")
                if ai_response is None:
                    ai_response = ""
                if not (ai_response and ai_response.strip()):
                    ai_response = "（未收到模型回复，请重试或检查 API 配置。）"
                
                # 非流式模式，一次性显示
                body = (ai_response or "(no response)").strip()
                
                try:
                    sys.stdout.write("\nAI > ")
                    sys.stdout.flush()
                    
                    # 控制台编码可能不是 UTF-8，只输出可安全编码的字符
                    out = body
                    try:
                        sys.stdout.write(out + "\n")
                        sys.stdout.flush()
                    except (UnicodeEncodeError, UnicodeDecodeError):
                        out = (body or "").encode("utf-8", errors="replace").decode("ascii", errors="replace") or "(no response)"
                        sys.stdout.write(out + "\n")
                        sys.stdout.flush()
                except Exception as e:
                    try:
                        sys.stdout.write("\nAI > (output omitted)\n")
                        sys.stdout.flush()
                    except Exception:
                        pass
            else:
                error_msg = result.get("error", "未知错误")
                console.print(f"[yellow]警告: 执行失败: {error_msg}[/yellow]")
                ai_response = "抱歉，我遇到了一些问题。请重试。"
    except Exception as e:
        ai_response = "Sorry, something went wrong. Please try again."
        try:
            _safe_console_print(console, f"[yellow]Warning: {_safe_str(e)[:200]}[/yellow]")
        except Exception:
            pass
    
    # 最后再次刷新，确保所有输出都显示
    sys.stdout.flush()
    sys.stderr.flush()


def _safe_str(s: object) -> str:
    """转为字符串且避免编码问题（仅 ASCII 安全字符用于控制台）"""
    t = str(s) if s is not None else ""
    try:
        t.encode("ascii")
        return t
    except UnicodeEncodeError:
        return t.encode("ascii", errors="replace").decode("ascii")


def _safe_console_print(console, *args, **kwargs):
    """调用 console.print，若编码错误则用 ASCII 回退"""
    try:
        console.print(*args, **kwargs)
    except (UnicodeEncodeError, UnicodeDecodeError):
        fallback = " ".join(_safe_str(a) for a in args)
        if fallback.strip():
            console.print(fallback[:500], **{k: v for k, v in kwargs.items() if k != "end"})
        if kwargs.get("end") is not None:
            console.print(end=kwargs.get("end"))


def generate_mock_response(user_input: str, context: dict) -> str:
    """生成模拟响应（临时）"""
    
    # 简单的关键词响应
    if "你好" in user_input or "hello" in user_input.lower():
        return "你好！我是DaoyouCode AI助手，基于18大核心系统。我可以帮你编写代码、重构项目、解答问题。有什么我可以帮助你的吗？"
    
    elif "帮助" in user_input or "help" in user_input.lower():
        return "我可以帮你：\n\n1. 📝 编写和修改代码\n2. 🔍 分析代码结构\n3. 🐛 调试和修复bug\n4. 📚 解答编程问题\n5. 🚀 优化代码性能\n\n请告诉我你需要什么帮助！"
    
    elif "功能" in user_input or "能做什么" in user_input:
        return """我基于DaoyouCode的18大核心系统，拥有以下能力：

**核心功能**
• 智能代码编辑和重构
• 多Agent协作（6个专业Agent）
• 完整的记忆系统
• 智能任务路由
• 权限控制（100+规则）
• 4级验证机制

**工具系统**
• 25个专业工具
• LSP集成
• Git操作
• 文件管理
• 代码搜索

目前CLI功能正在集成中，敬请期待！"""
    
    elif "代码" in user_input or "code" in user_input.lower():
        return """当然！我可以帮你编写代码。例如：

```python
def hello_world():
    \"\"\"一个简单的示例函数\"\"\"
    print("Hello, DaoyouCode!")
    return "Success"

# 调用函数
hello_world()
```

请告诉我你需要什么样的代码，我会为你生成！"""
    
    else:
        return f"收到你的消息：「{user_input}」\n\n目前我还在学习中，完整的AI对话功能即将上线！\n\n💡 提示：输入 /help 查看可用命令"


def initialize_agents(model: str) -> bool:
    """
    初始化Agent系统
    
    Returns:
        True: Agent初始化成功
        False: Agent初始化失败，使用模拟模式
    """
    from cli.ui.console import console
    
    try:
        # 1. 配置LLM客户端
        from daoyoucode.agents.llm.client_manager import get_client_manager
        from daoyoucode.agents.llm.config_loader import auto_configure
        
        client_manager = get_client_manager()
        auto_configure(client_manager)
        
        # 检查是否有可用的提供商
        if not client_manager.provider_configs:
            console.print("[yellow]⚠ 未配置LLM提供商，使用模拟模式[/yellow]")
            console.print("[dim]请配置 backend/config/llm_config.yaml[/dim]")
            return False
        
        # 2. 导入Agent系统
        from daoyoucode.agents.core.agent import (
            get_agent_registry,
            register_agent,
            BaseAgent,
            AgentConfig
        )
        
        # 3. 检查是否已有Agent
        registry = get_agent_registry()
        if "MainAgent" in registry.list_agents():
            console.print("[dim]✓ Agent系统已就绪[/dim]")
            return True
        
        # 创建并注册MainAgent
        config = AgentConfig(
            name="MainAgent",
            description="主对话Agent，负责处理用户交互",
            model=model,
            temperature=0.7,
            system_prompt="""你是DaoyouCode AI助手，基于18大核心系统。

你的能力：
- 智能代码编写和重构
- 多Agent协作
- 完整的记忆系统
- 智能任务路由
- 权限控制
- 4级验证机制
- **可以主动调用工具来理解项目代码**

你的风格：
- 专业但友好
- 简洁而清晰
- 注重实用性
- 提供可运行的代码

当前项目：DaoyouCode
- 位置: backend/
- 核心模块: daoyoucode/agents/
- CLI工具: cli/
- 配置: config/

可用工具（你可以主动调用）：
1. **repo_map** - 生成智能代码地图
   - 自动分析项目结构
   - PageRank排序最相关的代码
   - 当用户问"项目结构"、"有哪些模块"时使用

2. **get_repo_structure** - 获取目录树
   - 显示文件和目录结构
   - 当用户问"目录结构"、"文件列表"时使用

3. **read_file** - 读取文件内容
   - 读取具体文件
   - 当需要查看代码细节时使用

4. **search_files** - 搜索文件
   - 按文件名搜索
   - 当用户问"哪个文件"时使用

5. **grep_search** - 搜索代码
   - 在代码中搜索关键词
   - 当用户问"在哪里实现"时使用

重要提示：
1. 当用户询问项目相关问题时，**主动调用工具**获取信息
2. 不要说"我需要查看文件"，而是直接调用工具
3. 例如：
   - 用户："这个项目的结构是什么？"
   - 你：调用 repo_map 工具 → 基于结果回答
   
   - 用户："Agent系统在哪里实现的？"
   - 你：调用 search_files("agent") → 找到文件 → 调用 read_file → 回答

4. 系统已自动加载项目的关键文档（README、STRUCTURE等）
5. 用户也可以通过 /add 命令手动添加文件

用户命令：
- /add <文件路径> - 添加文件到上下文
- /files - 查看已加载的文件
- /drop <文件路径> - 移除文件

请主动使用工具，帮助用户理解和改进代码。"""
        )
        
        agent = BaseAgent(config)
        register_agent(agent)
        
        console.print("[dim]✓ Agent系统初始化完成[/dim]")
        return True
        
    except Exception as e:
        console.print(f"[yellow]⚠ Agent初始化失败，使用模拟模式[/yellow]")
        console.print(f"[dim]原因: {str(e)[:100]}[/dim]")
        return False


def handle_chat_with_agent(user_input: str, context: dict) -> str:
    """使用真实Agent处理对话 - 通过Skill系统"""
    from cli.ui.console import console
    import asyncio
    
    try:
        # 准备上下文
        agent_context = {
            "session_id": context.get("session_id", "default"),
            "files": context.get("files", []),
            "repo": context.get("repo", "."),
            "conversation_history": context.get("history", [])[-3:]  # 最近3轮
        }
        
        # 如果有文件内容，添加到上下文
        if "file_contents" in context and context["file_contents"]:
            agent_context["file_contents"] = context["file_contents"]
            
            # 构建文件信息
            file_info = "\n\n已加载的文件:\n"
            for filepath, content in context["file_contents"].items():
                lines = len(content.splitlines())
                file_info += f"\n--- {filepath} ({lines} 行) ---\n{content}\n"
            
            # 将文件信息添加到用户输入前
            user_input = file_info + "\n\n用户问题: " + user_input
        
        # 显示思考动画
        with console.status("[bold blue]AI正在思考...[/bold blue]", spinner="dots"):
            # 使用 get_event_loop 而不是 run 来避免 event loop closed 问题
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # 通过Skill系统执行（正确的架构）
            from daoyoucode.agents.executor import execute_skill
            
            result = loop.run_until_complete(execute_skill(
                skill_name="chat-assistant",
                user_input=user_input,
                session_id=agent_context["session_id"],
                context=agent_context
            ))
        
        # 检查结果
        if result.get('success'):
            return result.get('content', '')
        else:
            error_msg = result.get('error', '未知错误')
            console.print(f"[yellow]⚠ 执行失败: {error_msg}[/yellow]")
            return generate_mock_response(user_input, context)
    
    except Exception as e:
        console.print(f"[yellow]⚠ 调用异常: {str(e)[:100]}[/yellow]")
        return generate_mock_response(user_input, context)



def show_skills(ui_context: dict):
    """显示Skill列表"""
    from cli.ui.console import console
    from rich.table import Table
    
    try:
        from daoyoucode.agents.core.skill import get_skill_loader
        
        loader = get_skill_loader()
        skills = loader.list_skills()
        
        current_skill = ui_context.get('skill', 'chat-assistant')
        
        console.print("\n[bold cyan]📦 可用Skill[/bold cyan]\n")
        
        table = Table(show_header=True, border_style="cyan")
        table.add_column("", style="dim", width=2)
        table.add_column("名称", style="cyan")
        table.add_column("编排器", style="yellow")
        table.add_column("描述")
        
        for skill in skills:
            marker = "→" if skill['name'] == current_skill else ""
            table.add_row(
                marker,
                skill['name'],
                skill['orchestrator'],
                skill['description'][:60] + '...' if len(skill['description']) > 60 else skill['description']
            )
        
        console.print(table)
        console.print(f"\n[dim]当前Skill: [cyan]{current_skill}[/cyan][/dim]")
        console.print(f"[dim]使用 [cyan]/skill <name>[/cyan] 切换Skill[/dim]\n")
    
    except Exception as e:
        console.print(f"[red]加载Skill列表失败: {e}[/red]")


def switch_skill(skill_name: str, ui_context: dict):
    """切换Skill"""
    from cli.ui.console import console
    
    try:
        from daoyoucode.agents.core.skill import get_skill_loader
        
        loader = get_skill_loader()
        skill = loader.get_skill(skill_name)
        
        if not skill:
            console.print(f"[red]Skill不存在: {skill_name}[/red]")
            console.print("[dim]输入 [cyan]/skill[/cyan] 查看所有可用Skill[/dim]")
            return
        
        ui_context['skill'] = skill_name
        console.print(f"[green]✓[/green] 已切换到 [cyan]{skill_name}[/cyan]")
        console.print(f"[dim]{skill.description}[/dim]")
        console.print(f"[dim]编排器: {skill.orchestrator}[/dim]")
        
        # 显示更新后的配置
        show_current_config(ui_context)
    
    except Exception as e:
        console.print(f"[red]切换Skill失败: {e}[/red]")
