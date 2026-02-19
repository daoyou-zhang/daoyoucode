"""测试CLI交互问题 - 模拟实际场景"""
import sys
import os
import asyncio

# 设置环境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ['PYTHONUNBUFFERED'] = '1'

def test_handle_chat_simplified():
    """简化版的handle_chat测试"""
    print("=== 测试简化版handle_chat ===\n")
    
    # 模拟ui_context
    ui_context = {
        "session_id": "test-session",
        "model": "qwen-max",
        "skill": "chat-assistant",
        "repo": os.getcwd(),
        "initial_files": [],
        "subtree_only": False,
        "cwd": os.getcwd(),
    }
    
    user_input = "你好"
    
    print(f"用户输入: {user_input}")
    print("AI正在思考...")
    sys.stdout.flush()
    
    # 初始化系统
    from daoyoucode.agents.init import initialize_agent_system
    from daoyoucode.agents.tools.registry import get_tool_registry
    from daoyoucode.agents.tools.base import ToolContext
    from pathlib import Path
    from daoyoucode.agents.llm.client_manager import get_client_manager
    from daoyoucode.agents.llm.config_loader import auto_configure
    
    print("初始化Agent系统...")
    sys.stdout.flush()
    
    initialize_agent_system()
    registry = get_tool_registry()
    tool_context = ToolContext(
        repo_path=Path(ui_context["repo"]),
        subtree_only=False,
        cwd=None,
    )
    registry.set_context(tool_context)
    client_manager = get_client_manager()
    auto_configure(client_manager)
    
    print("初始化完成，准备执行...")
    sys.stdout.flush()
    
    # 执行
    from daoyoucode.agents.executor import execute_skill
    
    context = {
        "session_id": ui_context["session_id"],
        "repo": ui_context["repo"],
        "model": ui_context["model"],
        "initial_files": ui_context.get("initial_files", []),
        "subtree_only": ui_context.get("subtree_only", False),
        "cwd": ui_context.get("cwd", os.getcwd()),
        "working_directory": ui_context["repo"],
        "repo_root": ui_context["repo"],
    }
    
    async def run_skill():
        return await execute_skill(
            skill_name="chat-assistant",
            user_input=user_input,
            session_id=context["session_id"],
            context=context,
        )
    
    print("开始执行execute_skill...")
    sys.stdout.flush()
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(asyncio.wait_for(run_skill(), timeout=30))
        print(f"\n执行完成！")
        print(f"Success: {result.get('success')}")
        print(f"Content: {result.get('content')}")
        
        # 显示响应
        ai_response = result.get('content', '')
        if ai_response:
            sys.stdout.write(f"\nAI > {ai_response}\n")
            sys.stdout.flush()
        else:
            print("警告: 没有响应内容")
            
    except asyncio.TimeoutError:
        print("\n执行超时！")
    except Exception as e:
        print(f"\n执行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_handle_chat_simplified()
    print("\n=== 测试完成 ===")
