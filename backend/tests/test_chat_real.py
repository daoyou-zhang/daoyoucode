"""
测试chat命令的真实AI功能
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))


def test_chat_with_real_ai():
    """测试chat命令使用真实AI"""
    print("=" * 60)
    print("测试 chat 命令 - 真实AI")
    print("=" * 60)
    
    from cli.commands.chat import initialize_agents, handle_chat_with_agent
    
    # 1. 初始化Agent
    print("\n1. 初始化Agent...")
    agent_available = initialize_agents("qwen-turbo")
    
    if not agent_available:
        print("✗ Agent初始化失败")
        return False
    
    print("✓ Agent初始化成功")
    
    # 2. 测试对话
    print("\n2. 测试对话...")
    
    context = {
        "session_id": "test-session",
        "files": [],
        "repo": ".",
        "history": []
    }
    
    test_inputs = [
        "你好",
        "你能做什么",
        "写一个Python函数计算1到10的和"
    ]
    
    for user_input in test_inputs:
        print(f"\n用户: {user_input}")
        print("AI正在思考...")
        
        try:
            response = handle_chat_with_agent(user_input, context)
            print(f"AI: {response[:200]}...")
            print("✓ 对话成功")
        except Exception as e:
            print(f"✗ 对话失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    return True


if __name__ == "__main__":
    success = test_chat_with_real_ai()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 chat命令真实AI测试通过！")
        print("\n现在可以运行:")
        print("  python daoyoucode.py chat")
    else:
        print("❌ 测试失败")
    print("=" * 60)
