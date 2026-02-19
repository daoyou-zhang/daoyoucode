"""
测试handle_chat函数
"""
import sys
from pathlib import Path
import os

sys.path.insert(0, str(Path(__file__).parent))

# 设置环境变量避免编码问题
os.environ['PYTHONIOENCODING'] = 'utf-8'

def test():
    from cli.commands.chat import handle_chat
    
    # 模拟UI上下文
    ui_context = {
        "session_id": "test-session",
        "model": "qwen-max",
        "skill": "chat-assistant",
        "repo": ".",
        "initial_files": [],
        "subtree_only": True,
        "cwd": str(Path.cwd())
    }
    
    print("开始测试handle_chat...")
    print("="*60)
    
    # 调用handle_chat
    handle_chat("你好啊，道友，你能做什么？", ui_context)
    
    print("="*60)
    print("测试完成")

if __name__ == "__main__":
    test()
