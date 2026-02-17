"""
Agent管理命令

查看和管理Agent
"""

import typer
from typing import Optional


def main(
    agent_name: Optional[str] = typer.Argument(None, help="Agent名称"),
    tools: bool = typer.Option(False, "--tools", "-t", help="显示Agent的工具"),
):
    """
    Agent管理 - 查看和管理所有Agent
    
    \b
    示例:
        daoyoucode agent                    # 列出所有Agent
        daoyoucode agent sisyphus           # 查看Agent详情
        daoyoucode agent sisyphus --tools   # 查看Agent的工具列表
    
    \b
    说明:
        Agent是执行具体任务的智能体，每个Agent有不同的职责和工具集。
        Agent通过Skill配置使用，一个Skill可以使用一个或多个Agent。
    
    \b
    可用Agent:
        • sisyphus - 主编排Agent（4个工具）
        • oracle - 高IQ咨询Agent（10个工具）
        • librarian - 文档搜索Agent（8个工具）
        • programmer - 编程专家（11个工具）
        • refactor_master - 重构专家（13个工具）
        • test_expert - 测试专家（10个工具）
        • 更多...
    """
    from cli.ui.console import console
    
    if not agent_name:
        # 列出所有Agent
        list_all_agents()
    else:
        # 显示Agent详情
        show_agent_details(agent_name, show_tools=tools)


def list_all_agents():
    """列出所有Agent"""
    from cli.ui.console import console
    from rich.table import Table
    
    try:
        # 初始化Agent系统
        from daoyoucode.agents.init import initialize_agent_system
        initialize_agent_system()
        
        from daoyoucode.agents.core.agent import get_agent_registry
        from daoyoucode.agents.tools.tool_groups import get_tools_for_agent
        
        registry = get_agent_registry()
        agent_names = registry.list_agents()
        
        if not agent_names:
            console.print("[yellow]未找到任何Agent[/yellow]")
            return
        
        console.print("\n[bold cyan]🤖 可用Agent ({} 个)[/bold cyan]\n".format(len(agent_names)))
        
        table = Table(
            show_header=True,
            border_style="cyan",
            header_style="bold cyan",
            show_lines=False,
            padding=(0, 1)
        )
        table.add_column("#", style="dim", width=4, justify="right")
        table.add_column("名称", style="cyan bold", no_wrap=True, min_width=20)
        table.add_column("工具数", style="yellow", width=8, justify="right")
        table.add_column("描述", style="white")
        
        # 获取每个Agent的信息
        agents_info = []
        for agent_name in sorted(agent_names):
            agent = registry.get_agent(agent_name)
            if agent:
                tools = get_tools_for_agent(agent_name)
                agents_info.append({
                    'name': agent_name,
                    'description': agent.config.description,
                    'tool_count': len(tools)
                })
        
        # 显示Agent列表
        for i, info in enumerate(agents_info, 1):
            desc = info['description']
            if len(desc) > 50:
                desc = desc[:47] + '...'
            
            table.add_row(
                str(i),
                info['name'],
                str(info['tool_count']),
                desc
            )
        
        console.print(table)
        
        # 按工具数分组统计
        tool_groups = {
            '少量 (1-5)': 0,
            '中等 (6-10)': 0,
            '较多 (11-15)': 0,
            '很多 (15+)': 0
        }
        
        for info in agents_info:
            count = info['tool_count']
            if count <= 5:
                tool_groups['少量 (1-5)'] += 1
            elif count <= 10:
                tool_groups['中等 (6-10)'] += 1
            elif count <= 15:
                tool_groups['较多 (11-15)'] += 1
            else:
                tool_groups['很多 (15+)'] += 1
        
        console.print(f"\n[dim]工具数量分布:[/dim]")
        for group, count in tool_groups.items():
            if count > 0:
                console.print(f"[dim]  • {group}: {count} 个Agent[/dim]")
        
        console.print(f"\n[dim]💡 提示:[/dim]")
        console.print(f"[dim]  • 使用 [cyan]daoyoucode agent <name>[/cyan] 查看详情[/dim]")
        console.print(f"[dim]  • 使用 [cyan]daoyoucode agent <name> --tools[/cyan] 查看工具列表[/dim]")
        console.print(f"[dim]  • Agent通过Skill使用，参考 [cyan]daoyoucode skills[/cyan][/dim]\n")
    
    except Exception as e:
        console.print(f"[red]加载Agent失败: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")


def show_agent_details(agent_name: str, show_tools: bool = False):
    """显示Agent详情"""
    from cli.ui.console import console
    from rich.panel import Panel
    
    try:
        # 初始化Agent系统
        from daoyoucode.agents.init import initialize_agent_system
        initialize_agent_system()
        
        from daoyoucode.agents.core.agent import get_agent_registry
        from daoyoucode.agents.tools.tool_groups import get_tools_for_agent
        
        registry = get_agent_registry()
        agent = registry.get_agent(agent_name)
        
        if not agent:
            console.print(f"[red]Agent不存在: {agent_name}[/red]")
            console.print("[dim]使用 [cyan]daoyoucode agent[/cyan] 查看所有可用Agent[/dim]")
            return
        
        # 获取工具列表
        tools = get_tools_for_agent(agent_name)
        
        # 基本信息
        info = f"""
[bold]名称[/bold]: {agent.config.name}
[bold]描述[/bold]: {agent.config.description}
[bold]模型[/bold]: {agent.config.model}
[bold]温度[/bold]: {agent.config.temperature}
[bold]工具数量[/bold]: {len(tools)} 个
"""
        
        # 如果有system_prompt，显示摘要
        if agent.config.system_prompt:
            prompt_preview = agent.config.system_prompt[:100].replace('\n', ' ')
            if len(agent.config.system_prompt) > 100:
                prompt_preview += '...'
            info += f"\n[bold]Prompt[/bold]: {prompt_preview}\n"
        
        console.print(Panel(
            info,
            title=f"🤖 {agent_name}",
            border_style="cyan",
            padding=(1, 2)
        ))
        
        # 显示工具列表
        if show_tools and tools:
            console.print("\n[bold cyan]工具列表[/bold cyan]\n")
            
            from rich.table import Table
            table = Table(show_header=True, border_style="dim")
            table.add_column("#", style="dim", width=4, justify="right")
            table.add_column("工具名称", style="cyan")
            table.add_column("类型", style="yellow")
            
            # 工具分类
            tool_categories = {
                'repo_map': '项目理解',
                'get_repo_structure': '项目理解',
                'read_file': '文件操作',
                'write_file': '文件操作',
                'list_files': '文件操作',
                'get_file_info': '文件操作',
                'text_search': '搜索',
                'regex_search': '搜索',
                'find_function': '搜索',
                'git_status': 'Git',
                'git_diff': 'Git',
                'git_commit': 'Git',
                'git_log': 'Git',
                'run_command': '执行',
                'run_tests': '执行',
                'get_diagnostics': 'LSP',
                'find_references': 'LSP',
                'semantic_rename': 'LSP',
                'get_symbols': 'LSP',
                'parse_ast': 'AST',
                'generate_project_doc': '文档'
            }
            
            for i, tool in enumerate(tools, 1):
                category = tool_categories.get(tool, '其他')
                table.add_row(str(i), tool, category)
            
            console.print(table)
        
        # 查找使用该Agent的Skill
        console.print("\n[bold cyan]使用该Agent的Skill[/bold cyan]\n")
        
        from daoyoucode.agents.core.skill import get_skill_loader
        loader = get_skill_loader()
        skills = loader.list_skills()
        
        using_skills = []
        for skill in skills:
            # 检查单个agent
            if skill.get('agent') == agent_name:
                using_skills.append(skill['name'])
            # 检查agents列表
            elif agent_name in skill.get('agents', []):
                using_skills.append(skill['name'])
        
        if using_skills:
            for skill_name in using_skills:
                console.print(f"  • [cyan]{skill_name}[/cyan]")
        else:
            console.print("[dim]  暂无Skill使用该Agent[/dim]")
        
        console.print(f"\n[dim]💡 提示:[/dim]")
        console.print(f"[dim]  • 使用 [cyan]daoyoucode skills <skill_name>[/cyan] 查看Skill详情[/dim]")
        console.print(f"[dim]  • 使用 [cyan]daoyoucode chat --skill <skill_name>[/cyan] 启动对话[/dim]\n")
    
    except Exception as e:
        console.print(f"[red]加载Agent详情失败: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
