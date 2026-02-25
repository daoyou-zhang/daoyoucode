"""
测试流式输出功能
"""

import asyncio
import sys
from pathlib import Path

# 添加backend到路径
sys.path.insert(0, str(Path(__file__).parent))

from daoyoucode.agents.init import initialize_agent_system
from daoyoucode.agents.executor import execute_skill
from daoyoucode.agents.llm.client_manager import get_client_manager
from daoyoucode.agents.llm.config_loader import auto_configure


async def test_streaming():
    """测试流式输出"""
    
    print("=" * 60)
    print("测试流式输出功能")
    print("=" * 60)
    
    # 初始化系统
    print("\n1. 初始化Agent系统...")
    initialize_agent_system()
    
    # 配置LLM
    print("2. 配置LLM客户端...")
    client_manager = get_client_manager()
    auto_configure(client_manager)
    
    # 测试1：简单对话（无工具调用）
    print("\n" + "=" * 60)
    print("测试1：简单对话（无工具调用，应该流式输出）")
    print("=" * 60)
    
    context = {
        'session_id': 'test_streaming_1',
        'repo': '.',
        'enable_streaming': True
    }
    
    print("\n用户 > 你好，请简单介绍一下你自己")
    print("AI > ", end='', flush=True)
    
    result = await execute_skill(
        skill_name='chat-assistant',
        user_input='你好，请简单介绍一下你自己',
        session_id='test_streaming_1',
        context=context
    )
    
    # 检查是否是生成器
    import inspect
    if inspect.isasyncgen(result):
        print("✅ 返回了生成器（流式输出）")
        
        content = ""
        async for event in result:
            if event.get('type') == 'token':
                token = event.get('content', '')
                content += token
                print(token, end='', flush=True)
            elif event.get('type') == 'result':
                final_result = event.get('result')
                print(f"\n\n✅ 流式输出完成")
                print(f"   总长度: {len(content)} 字符")
                print(f"   成功: {final_result.success}")
    else:
        print("❌ 返回了普通结果（非流式）")
        print(f"   内容: {result.get('content', '')[:100]}...")
    
    # 测试2：带工具调用（应该在最后一轮流式输出）
    print("\n" + "=" * 60)
    print("测试2：带工具调用（工具调用后应该流式输出最终回复）")
    print("=" * 60)
    
    context2 = {
        'session_id': 'test_streaming_2',
        'repo': '.',
        'enable_streaming': True
    }
    
    print("\n用户 > 这个项目的结构是什么？")
    print("AI > ", end='', flush=True)
    
    result2 = await execute_skill(
        skill_name='chat-assistant',
        user_input='这个项目的结构是什么？',
        session_id='test_streaming_2',
        context=context2
    )
    
    if inspect.isasyncgen(result2):
        print("✅ 返回了生成器（流式输出）")
        
        content2 = ""
        async for event in result2:
            if event.get('type') == 'token':
                token = event.get('content', '')
                content2 += token
                print(token, end='', flush=True)
            elif event.get('type') == 'result':
                final_result = event.get('result')
                print(f"\n\n✅ 流式输出完成")
                print(f"   总长度: {len(content2)} 字符")
                print(f"   成功: {final_result.success}")
                print(f"   使用的工具: {final_result.tools_used}")
    else:
        print("❌ 返回了普通结果（非流式）")
        print(f"   内容: {result2.get('content', '')[:100]}...")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == '__main__':
    asyncio.run(test_streaming())
