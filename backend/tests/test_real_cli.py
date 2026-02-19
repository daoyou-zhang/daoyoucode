"""测试真实CLI场景 - 模拟用户输入"""
import sys
import os

# 设置环境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ['PYTHONUNBUFFERED'] = '1'

def test_with_mock_input():
    """使用模拟输入测试"""
    print("=== 测试真实CLI场景 ===\n")
    
    # 模拟用户输入
    from io import StringIO
    mock_input = StringIO("你好\n/exit\n")
    
    # 保存原始stdin
    original_stdin = sys.stdin
    
    try:
        # 替换stdin
        sys.stdin = mock_input
        
        # 导入并运行chat命令
        from cli.commands.chat import main
        from pathlib import Path
        
        print("启动chat命令...")
        sys.stdout.flush()
        
        try:
            main(
                files=None,
                model="qwen-max",
                skill="chat-assistant",
                repo=Path("."),
                subtree_only=False
            )
        except SystemExit:
            pass  # 正常退出
            
    finally:
        # 恢复stdin
        sys.stdin = original_stdin
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_with_mock_input()
