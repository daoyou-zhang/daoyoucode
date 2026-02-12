"""
流式输出工具

实现打字机效果的流式输出
"""

import time
from cli.ui.console import console


def stream_text(text: str, delay: float = 0.02):
    """
    流式输出文本（打字机效果）
    
    Args:
        text: 要输出的文本
        delay: 每个字符的延迟（秒）
    """
    for char in text:
        console.print(char, end="")
        time.sleep(delay)
    console.print()  # 换行


def stream_markdown(text: str, delay: float = 0.01):
    """
    流式输出Markdown（逐行）
    
    Args:
        text: Markdown文本
        delay: 每行的延迟（秒）
    """
    from rich.markdown import Markdown
    
    lines = text.split('\n')
    for line in lines:
        if line.strip():
            console.print(line)
            time.sleep(delay)
        else:
            console.print()


__all__ = ["stream_text", "stream_markdown"]
