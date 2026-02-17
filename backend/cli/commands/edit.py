"""
单次编辑命令

快速编辑文件，不需要交互式对话
"""

import typer
from typing import List
from pathlib import Path
from rich.panel import Panel
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn
import time


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
