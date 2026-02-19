"""
测试CLI chat命令
"""
import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

def test_cli_chat():
    """测试CLI chat"""
    from cli.commands.chat import handle_chat
    from cli.ui.console import console
    
    # 模拟UI上下文
    ui_context = {
        "session_id": "test-session",
        "model": "qwen-max",
        "skill": "chat-assistant",
        "repo": ".",
        "initial_files": [],
        "subtree_only": False,
        "cwd": str(Path.cwd())
    }
    
    # 测试输入
    user_input = "你好啊，道友，你能做啥？"
    
    console.print(f"\n[bold green]测试输入[/bold green]: {user_input}\n")
    
    # 调用handle_chat
    handle_chat(user_input, ui_context)
    
    console.print("\n[bold green]测试完成[/bold green]\n")

if __name__ == "__main__":
    test_cli_chat()
