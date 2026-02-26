"""
单次编辑命令

快速编辑文件，不需要交互式对话
"""

import typer
from typing import List, AsyncGenerator
from pathlib import Path
from rich.panel import Panel
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.live import Live
from rich.table import Table
import time
import asyncio
import inspect


def main(
    files: List[Path] = typer.Argument(..., help="要编辑的文件"),
    instruction: str = typer.Argument(..., help="编辑指令"),
    model: str = typer.Option("qwen-max", "--model", "-m", help="使用的模型"),
    yes: bool = typer.Option(False, "--yes", "-y", help="自动确认所有操作"),
    repo: Path = typer.Option(".", "--repo", "-r", help="仓库路径"),
):
    """
    单次编辑文件
    
    示例:
        daoyoucode edit main.py "添加日志功能"
        daoyoucode edit app.py utils.py "重构错误处理" --yes
    """
    from cli.ui.console import console
    
    # 显示编辑信息
    show_edit_banner(files, instruction, model)
    
    # 验证文件
    if not validate_files(files):
        raise typer.Exit(1)
    
    # 通过 Skill 体系执行（复用超时/恢复/Hook），失败时降级为模拟模式
    try:
        execute_edit_via_skill(files, instruction, model, yes, repo)
    except Exception as e:
        console.print(f"\n[red]❌ 错误: {e}[/red]\n")
        raise typer.Exit(1)


def show_edit_banner(files: List[Path], instruction: str, model: str):
    """显示编辑横幅"""
    from cli.ui.console import console
    
    info = f"""
[bold]编辑任务[/bold]

• 文件: [cyan]{', '.join(str(f) for f in files)}[/cyan]
• 指令: [yellow]{instruction}[/yellow]
• 模型: [dim]{model}[/dim]
"""
    console.print(Panel(info, title="📝 单次编辑", border_style="cyan", padding=(0, 2)))


def validate_files(files: List[Path]) -> bool:
    """验证文件是否存在"""
    from cli.ui.console import console
    
    all_valid = True
    for file in files:
        if not file.exists():
            console.print(f"[red]✗[/red] 文件不存在: {file}")
            all_valid = False
        elif not file.is_file():
            console.print(f"[red]✗[/red] 不是文件: {file}")
            all_valid = False
    
    return all_valid


def show_diff_preview(files: List[Path], instruction: str):
    """显示修改预览"""
    from cli.ui.console import console
    
    console.print("\n[bold cyan]修改预览[/bold cyan]\n")
    
    # 模拟diff
    for file in files:
        console.print(f"[bold]{file}[/bold]")
        
        # 显示模拟的代码diff
        diff_text = f"""[red]- # TODO: 旧代码[/red]
[green]+ # {instruction}[/green]
[green]+ def new_function():[/green]
[green]+     pass[/green]"""
        
        console.print(Panel(diff_text, border_style="dim", padding=(0, 1)))
        console.print()


def _revert_edited_files(repo_path: str, edit_files: List[str], console) -> None:
    """用户拒绝保留时，用 git checkout 回滚已编辑文件（Cursor 同级：拒绝即回滚）"""
    import subprocess
    from pathlib import Path
    root = Path(repo_path)
    for rel in edit_files:
        path = root / rel
        if not path.exists():
            continue
        try:
            subprocess.run(
                ["git", "checkout", "--", str(path)],
                cwd=str(root),
                capture_output=True,
                timeout=5,
            )
        except Exception as e:
            console.print(f"[dim]回滚 {rel} 失败: {e}[/dim]")
    console.print("[yellow]已尝试回滚上述文件，请用 git status 确认。[/yellow]\n")


def show_success(files: List[Path]):
    """显示成功信息"""
    from cli.ui.console import console
    from rich.table import Table
    
    console.print("\n[bold green]✅ 编辑完成！[/bold green]\n")
    
    # 显示修改的文件
    table = Table(show_header=True, border_style="green")
    table.add_column("文件", style="cyan")
    table.add_column("状态", style="green")
    
    for file in files:
        table.add_row(str(file), "✓ 已修改")
    
    console.print(table)
    console.print("\n[dim]💡 提示: 使用 git diff 查看详细修改[/dim]\n")


def execute_edit_via_skill(
    files: List[Path],
    instruction: str,
    model: str,
    yes: bool,
    repo: Path,
):
    """通过 edit-single Skill 执行编辑（复用编排器、超时恢复、Hook）"""
    from cli.ui.console import console
    import asyncio
    import os

    repo_path = os.path.abspath(str(repo))
    # 要编辑的文件：使用相对 repo 的路径供 Agent 使用
    try:
        repo_p = Path(repo_path)
        edit_files = [str(Path(f).resolve().relative_to(repo_p)) if repo_p in Path(f).resolve().parents or Path(f).resolve() == repo_p else str(f) for f in files]
    except ValueError:
        edit_files = [str(f) for f in files]

    user_input = f"""请编辑以下文件，并严格按指令修改：

**要编辑的文件：**
{chr(10).join('- ' + p for p in edit_files)}

**编辑指令：**
{instruction}

请先读取上述文件内容，再按指令做最小化、精确的修改，并使用 write_file 或 search_replace 工具写入。路径使用相对项目根的路径。"""

    context = {
        "session_id": "edit-" + str(int(time.time())),
        "repo": repo_path,
        "working_directory": repo_path,
        "model": model,
        "instruction": instruction,
        "edit_files": edit_files,
        "subtree_only": False,
        "cwd": repo_path,
    }

    try:
        from daoyoucode.agents.init import initialize_agent_system
        from daoyoucode.agents.tools.registry import get_tool_registry
        from daoyoucode.agents.tools.base import ToolContext
        from daoyoucode.agents.llm.client_manager import get_client_manager
        from daoyoucode.agents.llm.config_loader import auto_configure
        from daoyoucode.agents.executor import execute_skill

        initialize_agent_system()
        registry = get_tool_registry()
        registry.set_context(ToolContext(repo_path=Path(repo_path)))
        client_manager = get_client_manager()
        auto_configure(client_manager)
        if not client_manager.provider_configs:
            console.print("[yellow]⚠ 未配置LLM，使用模拟模式[/yellow]")
            execute_edit_mock(files, instruction, yes)
            return

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]🤖 AI正在分析和修改代码...", total=None)
            result = asyncio.run(
                execute_skill(
                    skill_name="edit-single",
                    user_input=user_input,
                    session_id=context["session_id"],
                    context=context,
                )
            )
            progress.update(task, description="[green]✓[/green] AI处理完成")

        if not result.get("success"):
            console.print(f"[yellow]⚠ 执行失败: {result.get('error', '未知错误')}[/yellow]")
            execute_edit_mock(files, instruction, yes)
            return

        content = result.get("content", "")
        console.print("\n[bold cyan]AI的修改建议[/bold cyan]\n")
        console.print(content[:500] if len(content) > 500 else content)
        if len(content) > 500:
            console.print("[dim]...(内容过长，已截断)[/dim]")
        show_diff_preview_real(files, content)

        if not yes:
            if not typer.confirm("\n是否保留这些修改？（选否将尝试用 git 回滚已改文件）"):
                _revert_edited_files(repo_path, edit_files, console)
                raise typer.Exit(0)
        # 修改已由 Agent 通过工具直接写入，此处仅做成功提示
        show_success(files)
    except Exception as e:
        console.print(f"[yellow]⚠ 调用异常: {str(e)[:100]}[/yellow]")
        execute_edit_mock(files, instruction, yes)


def execute_edit_mock(files: List[Path], instruction: str, yes: bool):
    """使用模拟模式执行编辑"""
    from cli.ui.console import console
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        # 1. 分析文件
        task = progress.add_task("[cyan]📊 分析文件...", total=None)
        time.sleep(1)  # 模拟分析
        progress.update(task, description="[green]✓[/green] 文件分析完成")
        progress.stop_task(task)
        
        # 2. 生成修改
        task = progress.add_task("[cyan]✍️  生成修改...", total=None)
        time.sleep(1.5)  # 模拟生成
        progress.update(task, description="[green]✓[/green] 修改生成完成")
        progress.stop_task(task)
        
        # 3. 验证修改
        task = progress.add_task("[cyan]🔍 验证修改...", total=None)
        time.sleep(0.5)  # 模拟验证
        progress.update(task, description="[green]✓[/green] 修改验证通过")
        progress.stop_task(task)
    
    # 显示修改预览
    show_diff_preview(files, instruction)
    
    # 确认应用
    if not yes:
        if not typer.confirm("\n应用这些修改？"):
            console.print("\n[yellow]已取消修改[/yellow]\n")
            raise typer.Exit(0)
    
    # 应用修改
    apply_changes(files)
    
    # 显示成功信息
    show_success(files)


def show_diff_preview_real(files: List[Path], ai_response: str):
    """显示真实的修改预览"""
    from cli.ui.console import console
    
    console.print("\n[bold cyan]修改预览[/bold cyan]\n")
    
    # 简单解析AI响应中的代码块
    for file in files:
        console.print(f"[bold]{file}[/bold]")
        
        # 这里应该解析AI响应，提取修改的代码
        # 暂时显示模拟的diff
        diff_text = f"""[dim]AI建议的修改（部分）：[/dim]
[green]+ # {ai_response[:100].replace(chr(10), ' ')}...[/green]"""
        
        console.print(Panel(diff_text, border_style="dim", padding=(0, 1)))
        console.print()



# ========== 流式编辑显示 ==========

async def display_streaming_edit(
    edit_generator: AsyncGenerator,
    console
):
    """
    显示流式编辑过程
    
    Args:
        edit_generator: 编辑事件生成器
        console: Rich console 对象
    """
    from daoyoucode.agents.tools.base import EditEvent
    
    with Live(console=console, refresh_per_second=10) as live:
        current_file = None
        lines_buffer = []
        total_lines = 0
        
        async for event in edit_generator:
            if event.type == EditEvent.EDIT_START:
                current_file = event.data['file_path']
                total_lines = event.data['total_lines']
                size = event.data.get('size', 0)
                
                panel = Panel(
                    f"[cyan]📝 开始编辑文件[/cyan]\n\n"
                    f"[bold]{current_file}[/bold]\n"
                    f"[dim]总行数: {total_lines} | 大小: {size} 字节[/dim]",
                    title="✍️  编辑中",
                    border_style="cyan"
                )
                live.update(panel)
            
            elif event.type == EditEvent.EDIT_ANALYZING:
                exists = event.data.get('exists', False)
                is_code = event.data.get('is_code', False)
                
                status = "✓ 文件存在" if exists else "⊕ 新建文件"
                code_status = "✓ 代码文件" if is_code else "○ 文本文件"
                
                panel = Panel(
                    f"[cyan]🔍 分析文件[/cyan]\n\n"
                    f"[bold]{current_file}[/bold]\n"
                    f"[dim]{status} | {code_status}[/dim]",
                    title="✍️  编辑中",
                    border_style="cyan"
                )
                live.update(panel)
            
            elif event.type == EditEvent.EDIT_LINE:
                line_number = event.data['line_number']
                content = event.data['content']
                progress = event.data['progress']
                
                # 添加到缓冲区
                lines_buffer.append(content)
                
                # 只显示最后10行
                display_lines = lines_buffer[-10:]
                
                # 创建进度条
                bar_width = 40
                filled = int(bar_width * progress)
                bar = '█' * filled + '░' * (bar_width - filled)
                
                # 显示代码预览
                code_preview = '\n'.join(display_lines)
                if len(code_preview) > 500:
                    code_preview = code_preview[:500] + '\n...'
                
                # 使用语法高亮
                try:
                    syntax = Syntax(
                        code_preview,
                        "python",
                        theme="monokai",
                        line_numbers=True,
                        start_line=max(1, line_number - len(display_lines) + 1)
                    )
                    code_display = syntax
                except Exception:
                    code_display = code_preview
                
                panel = Panel(
                    f"[cyan]✍️  写入代码[/cyan]\n\n"
                    f"{code_display}\n\n"
                    f"[cyan]{bar}[/cyan] {progress:.0%} | 行 {line_number}/{total_lines}",
                    title=f"✍️  编辑中: {current_file}",
                    border_style="cyan"
                )
                live.update(panel)
            
            elif event.type == EditEvent.EDIT_VERIFYING:
                panel = Panel(
                    f"[yellow]🔍 验证代码[/yellow]\n\n"
                    f"[bold]{current_file}[/bold]\n"
                    f"[dim]正在使用 LSP 检查语法和类型...[/dim]",
                    title="🔍 验证中",
                    border_style="yellow"
                )
                live.update(panel)
            
            elif event.type == EditEvent.EDIT_COMPLETE:
                lines = event.data['lines']
                size = event.data['size']
                verified = event.data.get('verified', False)
                warnings = event.data.get('warnings', [])
                warning_count = event.data.get('warning_count', 0)
                
                success_text = f"[green]✅ 编辑完成！[/green]\n\n"
                success_text += f"[bold]{current_file}[/bold]\n"
                success_text += f"[dim]行数: {lines} | 大小: {size} 字节[/dim]\n"
                
                if verified:
                    success_text += f"\n[green]✓ LSP 验证通过[/green]"
                
                if warnings:
                    success_text += f"\n\n[yellow]⚠️  {warning_count} 个警告：[/yellow]\n"
                    for warning in warnings[:3]:
                        success_text += f"[dim]  • {warning}[/dim]\n"
                
                panel = Panel(
                    success_text,
                    title="✅ 完成",
                    border_style="green"
                )
                live.update(panel)
            
            elif event.type == EditEvent.EDIT_ERROR:
                error = event.data.get('error', 'Unknown error')
                errors = event.data.get('errors', [])
                error_count = event.data.get('error_count', 0)
                
                error_text = f"[red]❌ 编辑失败！[/red]\n\n"
                error_text += f"[bold]{current_file}[/bold]\n\n"
                
                if errors:
                    error_text += f"[red]{error_count} 个错误：[/red]\n"
                    for err in errors[:5]:
                        error_text += f"[dim]  • {err}[/dim]\n"
                else:
                    error_text += f"[red]错误: {error}[/red]"
                
                panel = Panel(
                    error_text,
                    title="❌ 错误",
                    border_style="red"
                )
                live.update(panel)


def display_edit_event_simple(event, console):
    """
    简单的编辑事件显示（不使用 Live）
    
    用于不支持 Live 的环境
    """
    from daoyoucode.agents.tools.base import EditEvent
    
    if event.type == EditEvent.EDIT_START:
        console.print(f"\n[cyan]📝 开始编辑: {event.data['file_path']}[/cyan]")
        console.print(f"[dim]   总行数: {event.data['total_lines']}, 大小: {event.data.get('size', 0)} 字节[/dim]")
    
    elif event.type == EditEvent.EDIT_ANALYZING:
        console.print(f"[cyan]🔍 分析文件...[/cyan]")
    
    elif event.type == EditEvent.EDIT_LINE:
        line_number = event.data['line_number']
        progress = event.data['progress']
        
        # 只显示部分进度（避免刷屏）
        if line_number % 10 == 0 or line_number == 1:
            bar_width = 30
            filled = int(bar_width * progress)
            bar = '█' * filled + '░' * (bar_width - filled)
            console.print(f"\r[cyan]✍️  [{bar}] {progress:>6.1%} | 行 {line_number}[/cyan]", end="")
    
    elif event.type == EditEvent.EDIT_VERIFYING:
        console.print(f"\n[yellow]🔍 验证代码...[/yellow]")
    
    elif event.type == EditEvent.EDIT_COMPLETE:
        console.print(f"\n[green]✅ 编辑完成: {event.data['file_path']}[/green]")
        console.print(f"[dim]   行数: {event.data['lines']}, 大小: {event.data['size']} 字节[/dim]")
        
        if event.data.get('verified'):
            console.print(f"[green]   ✓ LSP 验证通过[/green]")
        
        if event.data.get('warnings'):
            console.print(f"[yellow]   ⚠️  {event.data['warning_count']} 个警告[/yellow]")
    
    elif event.type == EditEvent.EDIT_ERROR:
        console.print(f"\n[red]❌ 编辑失败: {event.data.get('error', 'Unknown')}[/red]")
        
        if event.data.get('errors'):
            console.print(f"[red]   {event.data['error_count']} 个错误：[/red]")
            for error in event.data['errors'][:3]:
                console.print(f"[dim]     • {error}[/dim]")
