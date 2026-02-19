"""直接测试CLI命令 - 不通过typer"""
import sys
import os

# 设置环境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ['PYTHONUNBUFFERED'] = '1'

def test_direct():
    """直接调用_handle_chat_impl"""
    print("=== 直接测试_handle_chat_impl ===\n")
    
    from pathlib import Path
    
    # 先初始化Agent系统
    print("初始化Agent系统...")
    from daoyoucode.agents.init import initialize_agent_system
    from daoyoucode.agents.tools.registry import get_tool_registry
    from daoyoucode.agents.tools.base import ToolContext
    from daoyoucode.agents.llm.client_manager import get_client_manager
    from daoyoucode.agents.llm.config_loader import auto_configure
    
    initialize_agent_system()
    registry = get_tool_registry()
    tool_context = ToolContext(
        repo_path=Path.cwd(),
        subtree_only=False,
        cwd=None,
    )
    registry.set_context(tool_context)
    client_manager = get_client_manager()
    auto_configure(client_manager)
    
    print(f"LLM提供商数量: {len(client_manager.provider_configs)}")
    
    from daoyoucode.agents.core.agent import get_agent_registry
    agent_registry = get_agent_registry()
    agents = agent_registry.list_agents()
    print(f"已注册Agent数量: {len(agents)}")
    print(f"Agent列表: {', '.join(agents)}")
    print("初始化完成\n")
    
    # 模拟ui_context
    ui_context = {
        "session_id": "test-session",
        "model": "qwen-max",
        "skill": "chat-assistant",
        "repo": str(Path.cwd()),
        "initial_files": [],
        "subtree_only": False,
        "cwd": str(Path.cwd()),
    }
    
    user_input = "你好"
    
    print(f"用户输入: {user_input}")
    print("=" * 60)
    
    # 导入并调用
    from cli.commands.chat import _handle_chat_impl
    
    try:
        _handle_chat_impl(user_input, ui_context)
        print("\n" + "=" * 60)
        print("执行完成")
    except Exception as e:
        print(f"\n执行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_direct()
