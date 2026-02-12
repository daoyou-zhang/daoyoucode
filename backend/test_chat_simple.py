"""
简单测试chat命令 - 使用模拟模式
"""

import sys
import os

# 添加backend到路径
sys.path.insert(0, os.path.dirname(__file__))

def test_chat_mock():
    """测试chat命令的模拟模式"""
    print("=" * 60)
    print("测试 chat 命令 - 模拟模式")
    print("=" * 60)
    
    from cli.commands.chat import generate_mock_response
    
    # 测试用例
    test_cases = [
        "你好",
        "帮助",
        "你能做什么",
        "写个Python函数",
        "其他问题"
    ]
    
    context = {
        "files": [],
        "repo": ".",
        "model": "qwen-max",
        "history": []
    }
    
    for user_input in test_cases:
        print(f"\n用户: {user_input}")
        response = generate_mock_response(user_input, context)
        print(f"AI: {response[:100]}...")
        print("-" * 60)

if __name__ == "__main__":
    test_chat_mock()
