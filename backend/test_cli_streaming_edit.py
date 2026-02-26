"""
测试 CLI 流式编辑显示
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from daoyoucode.agents.tools.file_tools import WriteFileTool
from daoyoucode.agents.tools.base import ToolContext
from cli.commands.edit import display_streaming_edit, display_edit_event_simple
from cli.ui.console import console


async def test_cli_streaming_display():
    """测试 CLI 流式编辑显示"""
    
    console.print("\n" + "=" * 80)
    console.print("[bold cyan]测试 CLI 流式编辑显示[/bold cyan]")
    console.print("=" * 80 + "\n")
    
    # 创建工具
    tool = WriteFileTool()
    tool.set_context(ToolContext(repo_path=Path.cwd()))
    
    # 准备测试内容
    test_content = """# 测试文件 - CLI 流式显示

def hello_world():
    \"\"\"打印 Hello World\"\"\"
    print("Hello, World!")
    return "Hello"

def calculate_sum(numbers):
    \"\"\"计算数字列表的总和\"\"\"
    total = 0
    for num in numbers:
        total += num
    return total

class DataProcessor:
    \"\"\"数据处理器\"\"\"
    
    def __init__(self, name):
        self.name = name
        self.data = []
    
    def add_data(self, item):
        \"\"\"添加数据\"\"\"
        self.data.append(item)
    
    def process(self):
        \"\"\"处理数据\"\"\"
        result = []
        for item in self.data:
            processed = self._process_item(item)
            result.append(processed)
        return result
    
    def _process_item(self, item):
        \"\"\"处理单个数据项\"\"\"
        return item.upper() if isinstance(item, str) else item

if __name__ == "__main__":
    hello_world()
    print(calculate_sum([1, 2, 3, 4, 5]))
    
    processor = DataProcessor("test")
    processor.add_data("hello")
    processor.add_data("world")
    print(processor.process())
"""
    
    # 测试1：使用 Live 显示（推荐）
    console.print("[bold]测试1：使用 Rich Live 显示（推荐）[/bold]\n")
    
    edit_gen = tool.execute_streaming(
        file_path="test_cli_streaming_output.py",
        content=test_content,
        verify=False  # 暂时不验证
    )
    
    await display_streaming_edit(edit_gen, console)
    
    # 等待一下，让用户看到结果
    await asyncio.sleep(2)
    
    # 测试2：使用简单显示（兼容模式）
    console.print("\n\n[bold]测试2：使用简单显示（兼容模式）[/bold]\n")
    
    edit_gen2 = tool.execute_streaming(
        file_path="test_cli_streaming_output2.py",
        content=test_content,
        verify=False
    )
    
    async for event in edit_gen2:
        display_edit_event_simple(event, console)
    
    console.print("\n\n" + "=" * 80)
    console.print("[bold green]✅ 测试完成！[/bold green]")
    console.print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(test_cli_streaming_display())
