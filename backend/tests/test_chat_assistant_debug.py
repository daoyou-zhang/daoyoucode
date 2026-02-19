"""
调试chat-assistant为什么不输出
"""
import sys
import asyncio
import logging
from pathlib import Path

# 设置详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

sys.path.insert(0, str(Path(__file__).parent))

async def test():
    from daoyoucode.agents.init import initialize_agent_system
    from daoyoucode.agents.llm.client_manager import get_client_manager
    from daoyoucode.agents.llm.config_loader import auto_configure
    from daoyoucode.agents.executor import execute_skill
    from daoyoucode.agents.tools.registry import get_tool_registry
    from daoyoucode.agents.tools.base import ToolContext
    
    print("\n" + "="*60)
    print("初始化系统...")
    print("="*60)
    initialize_agent_system()
    
    print("\n配置LLM...")
    client_manager = get_client_manager()
    auto_configure(client_manager)
    
    print("\n设置工具上下文...")
    registry = get_tool_registry()
    tool_context = ToolContext(
        repo_path=Path("."),
        subtree_only=True,
        cwd=Path.cwd().resolve(),
    )
    registry.set_context(tool_context)
    
    print("\n" + "="*60)
    print("执行chat-assistant...")
    print("="*60)
    
    result = await execute_skill(
        skill_name='chat-assistant',
        user_input='你好',
        context={
            'repo': '.',
            'subtree_only': True,
            'cwd': str(Path.cwd())
        }
    )
    
    print("\n" + "="*60)
    print("执行结果:")
    print("="*60)
    print(f"Success: {result.get('success')}")
    print(f"Content length: {len(result.get('content', ''))}")
    print(f"Content: {result.get('content', 'EMPTY')[:200]}")
    print(f"Error: {result.get('error')}")
    print("="*60 + "\n")
    
    return result

if __name__ == "__main__":
    result = asyncio.run(test())
    sys.exit(0 if result.get('success') else 1)
