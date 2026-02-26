"""
测试智能 Diff 编辑工具
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from daoyoucode.agents.tools.diff_tools import IntelligentDiffEditTool
from daoyoucode.agents.tools.base import ToolContext
from cli.ui.console import console


async def test_intelligent_diff_edit():
    """测试智能 Diff 编辑"""
    
    console.print("\n" + "=" * 80)
    console.print("[bold cyan]测试智能 Diff 编辑工具[/bold cyan]")
    console.print("=" * 80 + "\n")
    
    # 创建工具
    tool = IntelligentDiffEditTool()
    tool.set_context(ToolContext(repo_path=Path.cwd()))
    
    # 创建测试文件
    test_file = Path("test_diff_edit_target.py")
    original_code = """# 测试文件

def calculate_sum(numbers):
    \"\"\"计算数字列表的总和\"\"\"
    total = 0
    for num in numbers:
        total += num
    return total

def calculate_average(numbers):
    \"\"\"计算平均值\"\"\"
    if not numbers:
        return 0
    return calculate_sum(numbers) / len(numbers)

class Calculator:
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        result = a + b
        self.history.append(('add', a, b, result))
        return result
    
    def subtract(self, a, b):
        result = a - b
        self.history.append(('subtract', a, b, result))
        return result

if __name__ == "__main__":
    calc = Calculator()
    print(calc.add(5, 3))
    print(calc.subtract(10, 4))
"""
    
    test_file.write_text(original_code, encoding='utf-8')
    console.print(f"[green]✓ 创建测试文件: {test_file}[/green]\n")
    
    # 测试1：精确匹配
    console.print("[bold]测试1：精确匹配[/bold]\n")
    
    search_block1 = """def calculate_sum(numbers):
    \"\"\"计算数字列表的总和\"\"\"
    total = 0
    for num in numbers:
        total += num
    return total"""
    
    replace_block1 = """def calculate_sum(numbers):
    \"\"\"计算数字列表的总和（优化版）\"\"\"
    return sum(numbers)"""
    
    result1 = await tool.execute(
        file_path=str(test_file),
        search_block=search_block1,
        replace_block=replace_block1,
        fuzzy_match=False,
        verify=False
    )
    
    if result1.success:
        console.print(f"[green]✓ 精确匹配成功[/green]")
        console.print(f"[dim]{result1.content[:300]}...[/dim]\n")
    else:
        console.print(f"[red]✗ 精确匹配失败: {result1.error}[/red]\n")
    
    # 测试2：模糊匹配（带空白差异）
    console.print("[bold]测试2：模糊匹配（带空白差异）[/bold]\n")
    
    # 故意添加一些空白差异
    search_block2 = """def calculate_average(numbers):
    \"\"\"计算平均值\"\"\"
        if not numbers:
            return 0
        return calculate_sum(numbers) / len(numbers)"""  # 缩进不对
    
    replace_block2 = """def calculate_average(numbers):
    \"\"\"计算平均值（改进版）\"\"\"
    if not numbers:
        return 0
    total = calculate_sum(numbers)
    return total / len(numbers)"""
    
    result2 = await tool.execute(
        file_path=str(test_file),
        search_block=search_block2,
        replace_block=replace_block2,
        fuzzy_match=True,
        similarity_threshold=0.7,
        verify=False
    )
    
    if result2.success:
        console.print(f"[green]✓ 模糊匹配成功[/green]")
        console.print(f"[dim]相似度: {result2.metadata.get('similarity', 0):.1%}[/dim]")
        console.print(f"[dim]{result2.content[:300]}...[/dim]\n")
    else:
        console.print(f"[red]✗ 模糊匹配失败: {result2.error}[/red]\n")
    
    # 测试3：匹配失败
    console.print("[bold]测试3：匹配失败（不存在的代码）[/bold]\n")
    
    search_block3 = """def nonexistent_function():
    pass"""
    
    replace_block3 = """def new_function():
    pass"""
    
    result3 = await tool.execute(
        file_path=str(test_file),
        search_block=search_block3,
        replace_block=replace_block3,
        fuzzy_match=True,
        verify=False
    )
    
    if result3.success:
        console.print(f"[yellow]? 意外成功（应该失败）[/yellow]\n")
    else:
        console.print(f"[green]✓ 正确失败: {result3.error}[/green]\n")
    
    # 测试4：类方法编辑
    console.print("[bold]测试4：类方法编辑[/bold]\n")
    
    search_block4 = """    def add(self, a, b):
        result = a + b
        self.history.append(('add', a, b, result))
        return result"""
    
    replace_block4 = """    def add(self, a, b):
        \"\"\"加法运算\"\"\"
        result = a + b
        self.history.append(('add', a, b, result))
        return result"""
    
    result4 = await tool.execute(
        file_path=str(test_file),
        search_block=search_block4,
        replace_block=replace_block4,
        fuzzy_match=True,
        verify=False
    )
    
    if result4.success:
        console.print(f"[green]✓ 类方法编辑成功[/green]")
        console.print(f"[dim]{result4.content[:300]}...[/dim]\n")
    else:
        console.print(f"[red]✗ 类方法编辑失败: {result4.error}[/red]\n")
    
    # 显示最终文件内容
    console.print("[bold]最终文件内容（前30行）：[/bold]\n")
    final_content = test_file.read_text(encoding='utf-8')
    lines = final_content.split('\n')[:30]
    for i, line in enumerate(lines, 1):
        console.print(f"[dim]{i:2d}[/dim] {line}")
    
    console.print("\n" + "=" * 80)
    console.print("[bold green]✅ 测试完成！[/bold green]")
    console.print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(test_intelligent_diff_edit())
