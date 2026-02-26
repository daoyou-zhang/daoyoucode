"""
测试 Agent 流式编辑集成
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from daoyoucode.agents.init import initialize_agent_system
from daoyoucode.agents.executor import execute_skill
from daoyoucode.agents.tools.base import ToolContext
from daoyoucode.agents.tools.registry import get_tool_registry
from cli.ui.console import console


async def test_agent_streaming_edit():
    """测试 Agent 使用流式编辑工具"""
    
    console.print("\n" + "=" * 80)
    console.print("[bold cyan]测试 Agent 流式编辑集成[/bold cyan]")
    console.print("=" * 80 + "\n")
    
    # 初始化系统
    initialize_agent_system()
    
    # 设置工具上下文
    registry = get_tool_registry()
    registry.set_context(ToolContext(repo_path=Path.cwd()))
    
    # 准备测试内容
    test_code = """# 测试文件 - Agent 流式编辑

def calculate_fibonacci(n):
    \"\"\"计算斐波那契数列\"\"\"
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

def factorial(n):
    \"\"\"计算阶乘\"\"\"
    if n <= 1:
        return 1
    return n * factorial(n-1)

class MathUtils:
    \"\"\"数学工具类\"\"\"
    
    @staticmethod
    def is_prime(n):
        \"\"\"判断是否为质数\"\"\"
        if n < 2:
            return False
        for i in range(2, int(n ** 0.5) + 1):
            if n % i == 0:
                return False
        return True
    
    @staticmethod
    def gcd(a, b):
        \"\"\"计算最大公约数\"\"\"
        while b:
            a, b = b, a % b
        return a

if __name__ == "__main__":
    print(f"Fibonacci(10) = {calculate_fibonacci(10)}")
    print(f"Factorial(5) = {factorial(5)}")
    print(f"Is 17 prime? {MathUtils.is_prime(17)}")
    print(f"GCD(48, 18) = {MathUtils.gcd(48, 18)}")
"""
    
    # 构造用户输入（让 Agent 使用 write_file 工具）
    user_input = f"""请创建一个新文件 test_agent_streaming.py，内容如下：

{test_code}

请使用 write_file 工具创建这个文件。
"""
    
    # 执行上下文
    context = {
        'session_id': 'test-agent-streaming',
        'repo': str(Path.cwd()),
        'working_directory': str(Path.cwd()),
        'enable_streaming': True,  # 启用流式输出
        'enable_edit_streaming': True,  # 启用流式编辑
        'subtree_only': False,
        'cwd': str(Path.cwd())
    }
    
    console.print("[bold]执行 Agent...[/bold]\n")
    
    # 执行 skill（使用 simple 编排器）
    result = await execute_skill(
        skill_name='chat-assistant',
        user_input=user_input,
        session_id=context['session_id'],
        context=context
    )
    
    # 检查是否是生成器
    import inspect
    if inspect.isasyncgen(result):
        console.print("[cyan]检测到流式输出，开始处理...[/cyan]\n")
        
        # 处理流式事件
        async for event in result:
            if event.get('type') == 'token':
                # 文本 token
                token = event.get('content', '')
                try:
                    sys.stdout.write(token)
                    sys.stdout.flush()
                except UnicodeEncodeError:
                    pass
            
            elif event.get('type') == 'edit_event':
                # 编辑事件
                edit_event = event.get('event')
                if edit_event:
                    from cli.commands.edit import display_edit_event_simple
                    display_edit_event_simple(edit_event, console)
            
            elif event.get('type') == 'metadata':
                # 元数据
                tools_used = event.get('tools_used', [])
                if tools_used:
                    console.print(f"\n[dim]使用的工具: {', '.join(tools_used)}[/dim]")
        
        console.print()
    else:
        # 非流式输出
        console.print(f"\n[yellow]AI >[/yellow] {result.get('content', 'No response')}")
    
    console.print("\n" + "=" * 80)
    console.print("[bold green]✅ 测试完成！[/bold green]")
    console.print("=" * 80 + "\n")
    
    # 检查文件是否创建
    test_file = Path("test_agent_streaming.py")
    if test_file.exists():
        console.print(f"[green]✓ 文件已创建: {test_file}[/green]")
        console.print(f"[dim]  大小: {test_file.stat().st_size} 字节[/dim]")
    else:
        console.print(f"[red]✗ 文件未创建: {test_file}[/red]")


if __name__ == "__main__":
    asyncio.run(test_agent_streaming_edit())
