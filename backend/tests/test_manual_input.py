"""
模拟手动输入测试
"""
import sys
from pathlib import Path
from unittest.mock import patch
import io

sys.path.insert(0, str(Path(__file__).parent))

def test():
    # 模拟用户输入
    user_inputs = iter(["你好啊，道友，你能做什么？", "/exit"])
    
    def mock_input(prompt):
        try:
            value = next(user_inputs)
            print(f"{prompt}{value}")
            return value
        except StopIteration:
            return "/exit"
    
    # 替换console.input
    with patch('cli.ui.console.console.input', side_effect=mock_input):
        from cli.commands.chat import main
        try:
            main(
                files=None,
                model="qwen-max",
                skill="chat-assistant",
                repo=Path("."),
                subtree_only=True
            )
        except SystemExit:
            pass

if __name__ == "__main__":
    test()
