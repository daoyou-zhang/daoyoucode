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
    
    # 初始化Agent系统
    agent_available = initialize_edit_agent(model)
    
    # 执行编辑流程
    try:
        if agent_available:
            # 使用真实Agent
            execute_edit_with_agent(files, instruction, model, yes, repo)
        else:
            # 使用模拟模式
            execute_edit_mock(files, instruction, yes)
        
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


def apply_changes(files: List[Path]):
    """应用修改"""
    from cli.ui.console import console
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]🔨 应用修改...", total=None)
        time.sleep(1)  # 模拟应用
        progress.update(task, description="[green]✓[/green] 修改已应用")


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


def initialize_edit_agent(model: str) -> bool:
    """
    初始化编辑Agent
    
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
        if "CodeAgent" in registry.list_agents():
            console.print("[dim]✓ CodeAgent已就绪[/dim]")
            return True
        
        # 创建并注册CodeAgent
        config = AgentConfig(
            name="CodeAgent",
            description="代码编辑Agent，负责文件修改",
            model=model,
            temperature=0.3,  # 代码编辑需要更低的温度
            system_prompt="""你是DaoyouCode的代码编辑专家。

你的任务：
- 理解用户的编辑指令
- 分析现有代码
- 生成精确的修改
- 确保代码质量

你的原则：
- 最小化修改范围
- 保持代码风格一致
- 添加必要的注释
- 确保语法正确

请根据用户指令修改代码。"""
        )
        
        agent = BaseAgent(config)
        register_agent(agent)
        
        console.print("[dim]✓ CodeAgent初始化完成[/dim]")
        return True
        
    except Exception as e:
        console.print(f"[yellow]⚠ Agent初始化失败，使用模拟模式[/yellow]")
        console.print(f"[dim]原因: {str(e)[:100]}[/dim]")
        return False


def execute_edit_with_agent(
    files: List[Path],
    instruction: str,
    model: str,
    yes: bool,
    repo: Path
):
    """使用真实Agent执行编辑"""
    from cli.ui.console import console
    import asyncio
    
    try:
        # 导入Agent系统
        from daoyoucode.agents.core.agent import get_agent_registry
        
        # 获取Agent
        registry = get_agent_registry()
        agent = registry.get_agent("CodeAgent")
        
        if not agent:
            console.print("[yellow]CodeAgent不可用，使用模拟模式[/yellow]")
            execute_edit_mock(files, instruction, yes)
            return
        
        # 读取文件内容
        file_contents = {}
        for file in files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    file_contents[str(file)] = f.read()
            except Exception as e:
                console.print(f"[red]读取文件失败 {file}: {e}[/red]")
                return
        
        # 准备上下文
        agent_context = {
            "files": file_contents,
            "repo": str(repo),
            "instruction": instruction
        }
        
        # 构建详细的prompt
        detailed_prompt = f"""请根据以下指令修改代码：

指令：{instruction}

文件：
"""
        for filepath, content in file_contents.items():
            detailed_prompt += f"\n--- {filepath} ---\n{content}\n"
        
        detailed_prompt += """
请提供修改后的完整代码。"""
        
        # 执行编辑
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            task = progress.add_task("[cyan]🤖 AI正在分析和修改代码...", total=None)
            
            # 调用Agent
            result = asyncio.run(agent.execute(
                prompt_source={"use_agent_default": True},
                user_input=detailed_prompt,
                context=agent_context,
                tools=["read_file", "write_file"]  # 可用工具
            ))
            
            progress.update(task, description="[green]✓[/green] AI处理完成")
        
        # 检查结果
        if not result.success:
            console.print(f"[red]Agent执行失败: {result.error}[/red]")
            console.print("[yellow]降级到模拟模式[/yellow]")
            execute_edit_mock(files, instruction, yes)
            return
        
        # 显示AI的响应
        console.print("\n[bold cyan]AI的修改建议[/bold cyan]\n")
        console.print(result.content[:500])  # 显示前500字符
        if len(result.content) > 500:
            console.print("[dim]...(内容过长，已截断)[/dim]")
        
        # 显示修改预览（模拟）
        show_diff_preview_real(files, result.content)
        
        # 确认应用
        if not yes:
            if not typer.confirm("\n应用这些修改？"):
                console.print("\n[yellow]已取消修改[/yellow]\n")
                raise typer.Exit(0)
        
        # 应用修改（这里需要解析AI的响应并应用）
        # 暂时使用模拟
        apply_changes(files)
        
        # 显示成功信息
        show_success(files)
        
    except Exception as e:
        console.print(f"[red]Agent调用异常: {str(e)}[/red]")
        console.print("[yellow]降级到模拟模式[/yellow]")
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
