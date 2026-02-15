#!/usr/bin/env python
"""逐步测试app.py"""

import sys
sys.path.insert(0, '.')

print("Step 1: 导入typer")
import typer
print("✓")

print("Step 2: 导入typing")
from typing import Optional
print("✓")

print("Step 3: 导入pathlib")
from pathlib import Path
print("✓")

print("Step 4: 定义版本")
__version__ = "0.1.0"
print("✓")

print("Step 5: 创建Typer应用")
app = typer.Typer(
    name="daoyoucode",
    help="DaoyouCode - 智能AI代码助手",
    add_completion=True,
    no_args_is_help=True,
)
print("✓")

print("Step 6: 定义chat命令")
@app.command()
def chat(
    files: Optional[list[Path]] = typer.Argument(None, help="要加载的文件"),
    model: str = typer.Option("qwen-max", "--model", "-m", help="使用的模型"),
    repo: Path = typer.Option(".", "--repo", "-r", help="仓库路径"),
):
    """启动交互式对话"""
    print("chat命令")
print("✓")

print("\n所有步骤完成！")
print(f"app对象: {app}")
print(f"app命令: {app.registered_commands}")
