"""
测试工具显示UI
"""

import asyncio
import time
from daoyoucode.agents.ui import get_tool_display


async def test_tool_display():
    """测试工具显示"""
    display = get_tool_display()
    
    print("\n" + "="*60)
    print("测试工具显示UI")
    print("="*60)
    
    # 测试1: 成功的工具执行
    print("\n测试1: 成功的工具执行")
    tool_name = "repo_map"
    args = {
        'repo_path': '/path/to/repo',
        'chat_files': ['file1.py', 'file2.py'],
        'mentioned_idents': ['MyClass', 'my_function']
    }
    
    display.show_tool_start(tool_name, args)
    
    with display.show_progress(tool_name) as progress:
        task = progress.add_task(f"正在执行 {tool_name}...", total=100)
        
        # 模拟工作
        await asyncio.sleep(0.5)
        progress.update(task, advance=30, description="分析文件结构...")
        
        await asyncio.sleep(0.5)
        progress.update(task, advance=40, description="生成代码地图...")
        
        await asyncio.sleep(0.5)
        progress.update(task, advance=30, description="完成")
    
    display.show_success(tool_name, 1.5)
    
    # 测试2: 失败的工具执行
    print("\n测试2: 失败的工具执行")
    tool_name = "search_files"
    args = {'pattern': '*.py', 'path': '/invalid/path'}
    
    display.show_tool_start(tool_name, args)
    
    with display.show_progress(tool_name) as progress:
        task = progress.add_task(f"正在执行 {tool_name}...", total=100)
        await asyncio.sleep(0.3)
        progress.update(task, advance=50)
    
    error = FileNotFoundError("路径不存在: /invalid/path")
    display.show_error(tool_name, error, 0.3)
    
    # 测试3: 警告
    print("\n测试3: 警告信息")
    display.show_warning("read_file", "文件内容过大，已截断")
    
    # 测试4: 结果预览
    print("\n测试4: 结果预览")
    result = """# 代码地图

## 文件1: main.py
- class MyClass
- def my_function()

## 文件2: utils.py
- def helper()
- def process()

## 文件3: config.py
- CONFIG = {}
- def load_config()
"""
    display.show_result_preview(result, max_lines=5)
    
    print("\n" + "="*60)
    print("✓ 测试完成")
    print("="*60)


if __name__ == '__main__':
    asyncio.run(test_tool_display())
