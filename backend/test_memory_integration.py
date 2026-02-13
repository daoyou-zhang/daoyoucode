"""
测试Memory系统与Function Calling的集成
"""

import sys
from pathlib import Path
import asyncio

sys.path.insert(0, str(Path(__file__).parent))

async def test():
    print("\n" + "="*60)
    print("测试Memory系统集成")
    print("="*60)
    
    from daoyoucode.agents.init import initialize_agent_system
    from daoyoucode.agents.llm.client_manager import get_client_manager
    from daoyoucode.agents.llm.config_loader import auto_configure
    from daoyoucode.agents.executor import execute_skill
    
    # 初始化
    initialize_agent_system()
    client_manager = get_client_manager()
    auto_configure(client_manager)
    
    session_id = "test_memory_session"
    
    # 第一轮对话
    print("\n第一轮对话:")
    print("-"*60)
    result1 = await execute_skill(
        skill_name="chat_assistant",
        user_input="我的项目在backend目录",
        session_id=session_id,
        context={}
    )
    
    if result1.get('success'):
        print(f"AI: {result1.get('content', '')[:200]}...")
    
    # 第二轮对话（追问，应该记得之前说的backend目录）
    print("\n\n第二轮对话（追问）:")
    print("-"*60)
    result2 = await execute_skill(
        skill_name="chat_assistant",
        user_input="那个目录下有哪些子目录？",  # 应该理解"那个目录"指的是backend
        session_id=session_id,
        context={}
    )
    
    if result2.get('success'):
        print(f"AI: {result2.get('content', '')[:500]}...")
        print(f"\n使用的工具: {result2.get('tools_used', [])}")
    
    # 检查Memory
    print("\n\n检查Memory系统:")
    print("-"*60)
    from daoyoucode.agents.memory import get_memory_manager
    memory = get_memory_manager()
    
    history = memory.get_conversation_history(session_id)
    print(f"对话历史数量: {len(history)}")
    for i, h in enumerate(history, 1):
        print(f"\n第{i}轮:")
        print(f"  用户: {h.get('user_message', '')[:50]}...")
        print(f"  AI: {h.get('ai_response', '')[:50]}...")
    
    print("\n" + "="*60)

if __name__ == '__main__':
    asyncio.run(test())
