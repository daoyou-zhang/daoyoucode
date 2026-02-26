"""
简单测试 Agent 编辑集成（不需要 LLM）
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from daoyoucode.agents.tools.file_tools import WriteFileTool
from daoyoucode.agents.tools.base import ToolContext, EditEvent
from cli.ui.console import console


async def test_simple_edit():
    """简单测试编辑工具"""
    
    console.print("\n" + "=" * 80)
    console.print("[bold cyan]简单测试 Agent 编辑集成[/bold cyan]")
    console.print("=" * 80 + "\n")
    
    # 创建工具
    tool = WriteFileTool()
    tool.set_context(ToolContext(repo_path=Path.cwd()))
    
    # 测试代码
    test_code = """# 简单测试文件

def hello():
    print("Hello from Agent!")

if __name__ == "__main__":
    hello()
"""
    
    console.print("[bold]测试1：普通执行（非流式）[/bold]\n")
    
    # 普通执行
    result = await tool.execute(
        file_path="test_agent_edit_normal.py",
        content=test_code,
        verify=False
    )
    
    if result.success:
        console.print(f"[green]✓ 普通执行成功: {result.content}[/green]")
    else:
        console.print(f"[red]✗ 普通执行失败: {result.error}[/red]")
    
    console.print("\n[bold]测试2：流式执行[/bold]\n")
    
    # 流式执行
    edit_events = []
    async for event in tool.execute_streaming(
        file_path="test_agent_edit_streaming.py",
        content=test_code,
        verify=False
    ):
        edit_events.append(event)
        
        # 简单显示
        if event.type == EditEvent.EDIT_START:
            console.print(f"[cyan]📝 开始: {event.data['file_path']}[/cyan]")
        elif event.type == EditEvent.EDIT_LINE:
            if event.data['line_number'] % 5 == 0:
                progress = event.data['progress']
                console.print(f"[dim]  进度: {progress:.0%}[/dim]")
        elif event.type == EditEvent.EDIT_COMPLETE:
            console.print(f"[green]✅ 完成: {event.data['file_path']}[/green]")
        elif event.type == EditEvent.EDIT_ERROR:
            console.print(f"[red]❌ 错误: {event.data.get('error')}[/red]")
    
    console.print(f"\n[dim]收集了 {len(edit_events)} 个编辑事件[/dim]")
    
    console.print("\n" + "=" * 80)
    console.print("[bold green]✅ 测试完成！[/bold green]")
    console.print("=" * 80 + "\n")
    
    # 检查文件
    for filename in ["test_agent_edit_normal.py", "test_agent_edit_streaming.py"]:
        test_file = Path(filename)
        if test_file.exists():
            console.print(f"[green]✓ 文件已创建: {filename}[/green]")
        else:
            console.print(f"[red]✗ 文件未创建: {filename}[/red]")


if __name__ == "__main__":
    asyncio.run(test_simple_edit())
