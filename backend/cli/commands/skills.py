"""
Skill管理命令

查看和管理Skill
"""

import typer
from typing import Optional
from rich.table import Table
from rich.panel import Panel


def main(
    skill_name: Optional[str] = typer.Argument(None, help="Skill名称"),
    orchestrators: bool = typer.Option(False, "--orchestrators", "-o", help="显示编排器列表"),
):
    """
    Skill和编排器管理 - 查看所有Skill和编排器
    
    \b
    示例:
        daoyoucode skills                    # 列出所有Skill
        daoyoucode skills sisyphus           # 查看Skill详情
        daoyoucode skills --orchestrators    # 查看所有编排器
    
    \b
    说明:
        Skill是配置文件，定义了使用哪些Agent、工具和编排器。
        编排器负责协调多个Agent的工作方式（顺序、并行、辩论等）。
    
    \b
    推荐Skill:
        • chat-assistant - 日常对话（react编排器）
        • sisyphus-orchestrator - 复杂任务（multi_agent编排器）
        • oracle - 架构咨询（react编排器，只读）
        • librarian - 文档搜索（react编排器，只读）
    
    \b
    编排器类型:
        • simple - 简单编排（1个Agent）
        • react - ReAct模式（1个Agent + 工具）
        • multi_agent - 多Agent协作（多个Agent）
        • workflow - 工作流编排（预定义步骤）
        • parallel - 并行执行（多任务同时）
    """
    from cli.ui.console import console
    
    if orchestrators:
        # 显示编排器列表
        show_orchestrators()
    elif not skill_name:
        # 列出所有Skill
        list_all_skills()
    else:
        # 显示Skill详情
        show_skill_details(skill_name)


def list_all_skills():
    """列出所有Skill"""
    from cli.ui.console import console
    
    try:
        from daoyoucode.agents.core.skill import get_skill_loader
        
        loader = get_skill_loader()
        skills = loader.list_skills()
        
        if not skills:
            console.print("[yellow]未找到任何Skill[/yellow]")
            console.print("[dim]Skill配置位于: skills/*/skill.yaml[/dim]")
            return
        
        console.print("\n[bold cyan]📦 可用Skill ({} 个)[/bold cyan]\n".format(len(skills)))
        
        # 创建一个统一的表格
        table = Table(
            show_header=True,
            border_style="cyan",
            header_style="bold cyan",
            show_lines=False,
            padding=(0, 1)
        )
        table.add_column("#", style="dim", width=4, justify="right")
        table.add_column("名称", style="cyan bold", no_wrap=True, min_width=25)
        table.add_column("编排器", style="yellow", width=14)
        table.add_column("描述", style="white")
        
        # 按名称排序
        sorted_skills = sorted(skills, key=lambda x: x['name'])
        
        for i, skill in enumerate(sorted_skills, 1):
            desc = skill['description']
            # 截断过长的描述
            if len(desc) > 55:
                desc = desc[:52] + '...'
            
            table.add_row(
                str(i),
                skill['name'],
                skill['orchestrator'],
                desc
            )
        
        console.print(table)
        
        # 按编排器分组统计
        orchestrator_count = {}
        for skill in skills:
            orch = skill['orchestrator']
            orchestrator_count[orch] = orchestrator_count.get(orch, 0) + 1
        
        console.print(f"\n[dim]编排器统计:[/dim]")
        for orch, count in sorted(orchestrator_count.items()):
            console.print(f"[dim]  • {orch}: {count} 个Skill[/dim]")
        
        console.print(f"\n[dim]💡 提示:[/dim]")
        console.print(f"[dim]  • 使用 [cyan]daoyoucode skills <name>[/cyan] 查看详情[/dim]")
        console.print(f"[dim]  • 使用 [cyan]daoyoucode skills --orchestrators[/cyan] 查看编排器说明[/dim]")
        console.print(f"[dim]  • 使用 [cyan]daoyoucode chat --skill <name>[/cyan] 启动对话[/dim]\n")
    
    except Exception as e:
        console.print(f"[red]加载Skill失败: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")


def show_skill_details(skill_name: str):
    """显示Skill详情"""
    from cli.ui.console import console
    
    try:
        from daoyoucode.agents.core.skill import get_skill_loader
        
        loader = get_skill_loader()
        skill = loader.get_skill(skill_name)
        
        if not skill:
            console.print(f"[red]Skill不存在: {skill_name}[/red]")
            console.print("[dim]使用 [cyan]daoyoucode skills[/cyan] 查看所有可用Skill[/dim]")
            return
        
        # 基本信息
        info = f"""
[bold]名称[/bold]: {skill.name}
[bold]版本[/bold]: {skill.version}
[bold]描述[/bold]: {skill.description}
[bold]编排器[/bold]: {skill.orchestrator}
"""
        
        # 工具信息
        if skill.tools:
            info += f"\n[bold]工具[/bold] ({len(skill.tools)}个):\n"
            for tool in skill.tools[:10]:  # 只显示前10个
                info += f"  • {tool}\n"
            if len(skill.tools) > 10:
                info += f"  ... 还有 {len(skill.tools) - 10} 个工具\n"
        
        # LLM配置
        if skill.llm:
            info += f"\n[bold]LLM配置[/bold]:\n"
            info += f"  • 模型: {skill.llm.get('model', 'default')}\n"
            info += f"  • 温度: {skill.llm.get('temperature', 0.7)}\n"
        
        # 元数据
        if skill.metadata:
            metadata = skill.metadata
            
            if metadata.get('triggers'):
                info += f"\n[bold]触发词[/bold]:\n"
                for trigger in metadata['triggers'][:5]:
                    info += f"  • {trigger}\n"
            
            if metadata.get('use_when'):
                info += f"\n[bold]使用场景[/bold]:\n"
                for use_case in metadata['use_when'][:5]:
                    info += f"  • {use_case}\n"
            
            if metadata.get('cost'):
                cost_color = {
                    'LOW': 'green',
                    'MEDIUM': 'yellow',
                    'HIGH': 'red'
                }.get(metadata['cost'], 'white')
                info += f"\n[bold]成本[/bold]: [{cost_color}]{metadata['cost']}[/{cost_color}]\n"
        
        console.print(Panel(
            info,
            title=f"📦 {skill.name}",
            border_style="cyan",
            padding=(1, 2)
        ))
        
        # 使用示例
        console.print("\n[bold cyan]使用示例[/bold cyan]")
        console.print(f"[dim]$ daoyoucode chat --skill {skill.name} \"你的问题\"[/dim]\n")
    
    except Exception as e:
        console.print(f"[red]加载Skill详情失败: {e}[/red]")


def show_orchestrators():
    """显示编排器列表"""
    from cli.ui.console import console
    
    try:
        from daoyoucode.agents.core.orchestrator import get_orchestrator_registry
        
        registry = get_orchestrator_registry()
        orchestrators = registry.list_orchestrators()
        
        if not orchestrators:
            console.print("[yellow]未找到任何编排器[/yellow]")
            return
        
        console.print("\n[bold cyan]🎯 可用编排器[/bold cyan]\n")
        
        # 编排器描述
        orchestrator_info = {
            'simple': {
                'name': 'Simple',
                'description': '简单编排器，单Agent顺序执行',
                'use_when': '简单任务，单一Agent即可完成',
                'agents': '1个',
                'complexity': 'LOW'
            },
            'react': {
                'name': 'ReAct',
                'description': 'ReAct模式，推理-行动循环',
                'use_when': '需要工具调用的任务',
                'agents': '1个',
                'complexity': 'MEDIUM'
            },
            'multi_agent': {
                'name': 'Multi-Agent',
                'description': '多Agent协作，支持4种协作模式',
                'use_when': '复杂任务，需要多个专业Agent',
                'agents': '多个',
                'complexity': 'HIGH'
            },
            'workflow': {
                'name': 'Workflow',
                'description': '工作流编排，预定义步骤',
                'use_when': '固定流程的任务',
                'agents': '多个',
                'complexity': 'MEDIUM'
            },
            'parallel': {
                'name': 'Parallel',
                'description': '并行执行，多任务同时处理',
                'use_when': '独立任务可并行执行',
                'agents': '多个',
                'complexity': 'MEDIUM'
            },
            'parallel_explore': {
                'name': 'Parallel Explore',
                'description': '并行探索，多路径同时尝试',
                'use_when': '探索性任务，需要多种方案',
                'agents': '多个',
                'complexity': 'HIGH'
            },
            'conditional': {
                'name': 'Conditional',
                'description': '条件编排，根据条件选择路径',
                'use_when': '需要条件判断的任务',
                'agents': '多个',
                'complexity': 'MEDIUM'
            }
        }
        
        table = Table(show_header=True, border_style="cyan")
        table.add_column("编排器", style="cyan")
        table.add_column("名称", style="bold")
        table.add_column("Agent数", style="yellow")
        table.add_column("复杂度", style="dim")
        table.add_column("描述")
        
        for orch_id in sorted(orchestrators):
            info = orchestrator_info.get(orch_id, {
                'name': orch_id.title(),
                'description': '自定义编排器',
                'agents': '?',
                'complexity': 'UNKNOWN'
            })
            
            complexity_color = {
                'LOW': 'green',
                'MEDIUM': 'yellow',
                'HIGH': 'red',
                'UNKNOWN': 'dim'
            }.get(info['complexity'], 'white')
            
            table.add_row(
                orch_id,
                info['name'],
                info['agents'],
                f"[{complexity_color}]{info['complexity']}[/{complexity_color}]",
                info['description']
            )
        
        console.print(table)
        
        # 详细说明
        console.print("\n[bold cyan]编排器详细说明[/bold cyan]\n")
        
        for orch_id in sorted(orchestrators):
            info = orchestrator_info.get(orch_id)
            if info:
                console.print(f"[bold cyan]{info['name']}[/bold cyan] ([dim]{orch_id}[/dim])")
                console.print(f"  {info['description']}")
                console.print(f"  [dim]使用场景: {info['use_when']}[/dim]\n")
        
        # Multi-Agent的协作模式
        console.print("\n[bold cyan]Multi-Agent协作模式[/bold cyan]\n")
        
        modes_table = Table(show_header=True, border_style="dim")
        modes_table.add_column("模式", style="cyan")
        modes_table.add_column("说明")
        modes_table.add_column("使用场景")
        
        modes_table.add_row(
            "sequential",
            "顺序执行，每个Agent处理前一个的输出",
            "需要逐步处理的任务"
        )
        modes_table.add_row(
            "parallel",
            "并行执行，所有Agent同时处理",
            "独立任务可并行"
        )
        modes_table.add_row(
            "debate",
            "辩论模式，Agent之间讨论",
            "需要多角度分析"
        )
        modes_table.add_row(
            "main_with_helpers",
            "主Agent + 辅助Agent（默认）",
            "复杂任务分解"
        )
        
        console.print(modes_table)
        
        console.print(f"\n[dim]💡 提示:[/dim]")
        console.print(f"[dim]  • 在Skill配置中指定编排器: orchestrator: multi_agent[/dim]")
        console.print(f"[dim]  • 在Skill配置中指定协作模式: collaboration_mode: main_with_helpers[/dim]")
        console.print(f"[dim]  • 使用 [cyan]daoyoucode skills[/cyan] 查看使用各编排器的Skill[/dim]\n")
    
    except Exception as e:
        console.print(f"[red]加载编排器失败: {e}[/red]")


def test_skill(skill_name: str, test_input: str):
    """测试Skill"""
    from cli.ui.console import console
    import asyncio
    
    console.print(f"\n[bold cyan]🧪 测试Skill: {skill_name}[/bold cyan]\n")
    console.print(f"[dim]输入: {test_input}[/dim]\n")
    
    try:
        from daoyoucode.agents.executor import execute_skill
        
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(execute_skill(
            skill_name=skill_name,
            user_input=test_input,
            session_id="test",
            context={}
        ))
        
        if result.get('success'):
            console.print("[green]✓ 测试成功[/green]\n")
            console.print("[bold]输出:[/bold]")
            console.print(result.get('content', ''))
        else:
            console.print("[red]✗ 测试失败[/red]\n")
            console.print(f"[red]错误: {result.get('error', '未知错误')}[/red]")
    
    except Exception as e:
        console.print(f"[red]测试异常: {e}[/red]")
