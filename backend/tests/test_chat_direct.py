"""
直接测试chat功能，不通过CLI交互
"""
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

async def test():
    from daoyoucode.agents.init import initialize_agent_system
    from daoyoucode.agents.llm.client_manager import get_client_manager
    from daoyoucode.agents.llm.config_loader import auto_configure
    from daoyoucode.agents.executor import execute_skill
    from daoyoucode.agents.tools.registry import get_tool_registry
    from daoyoucode.agents.tools.base import ToolContext
    
    print("初始化系统...")
    initialize_agent_system()
    
    print("配置LLM...")
    client_manager = get_client_manager()
    auto_configure(client_manager)
    
    print("设置工具上下文...")
    registry = get_tool_registry()
    tool_context = ToolContext(
        repo_path=Path("."),
        subtree_only=True,
        cwd=Path.cwd().resolve(),
    )
    registry.set_context(tool_context)
    
    print("\n执行查询: 你好啊，道友，你能做什么？\n")
    
    result = await execute_skill(
        skill_name='chat-assistant',
        user_input='你好啊，道友，你能做什么？',
        context={
            'repo': '.',
            'subtree_only': True,
            'cwd': str(Path.cwd())
        }
    )
    
    print(f"\n{'='*60}")
    print(f"Success: {result.get('success')}")
    print(f"{'='*60}")
    if result.get('success'):
        print(f"\nAI回复:\n{result.get('content')}")
    else:
        print(f"\n错误: {result.get('error')}")
    print(f"{'='*60}\n")
    
    return result

if __name__ == "__main__":
    result = asyncio.run(test())
    sys.exit(0 if result.get('success') else 1)
