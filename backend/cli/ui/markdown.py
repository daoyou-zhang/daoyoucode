"""
Markdown渲染

用于显示AI响应
"""

from rich.markdown import Markdown
from cli.ui.console import console


def render_markdown(text: str):
    """渲染Markdown文本"""
    md = Markdown(text)
    console.print(md)


__all__ = ["render_markdown"]
