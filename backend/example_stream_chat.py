"""
流式聊天示例

演示如何使用Agent的流式输出功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from daoyoucode.agents.core.agent import BaseAgent, AgentConfig
from daoyoucode.agents.llm import get_client_manager


async def stream_chat_example():
    """流式聊天示例"""
    print("="*60)
    print("流式聊天示例")
    print("="*60)
    
    # 1. 配置LLM客户端
    print("\n1. 配置LLM客户端...")
    client_manager = get_client_manager()
    
    # 配置通义千问（需要设置环境变量 DASHSCOPE_API_KEY）
    import os
    api_key = os.getenv('DASHSCOPE_API_KEY', 'your-api-key-here')
    
    if api_key == 'your-api-key-here':
        print("⚠️ 警告: 未设置 DASHSCOPE_API_KEY 环境变量")
        print("   请设置环境变量或修改代码中的 api_key")
        print("\n使用Mock模式演示...")
        use_mock = True
    else:
        client_manager.configure_provider(
            provider='qwen',
            api_key=api_key,
            base_url='https://dashscope.aliyuncs.com/compatible-mode/v1'
        )
        use_mock = False
        print("✓ LLM客户端配置完成")
    
    # 2. 创建Agent
    print("\n2. 创建Agent...")
    config = AgentConfig(
        name="chat_agent",
        description="聊天助手",
        model="qwen-turbo",
        temperature=0.7,
        system_prompt="你是一个友好的AI助手，用中文回答问题。"
    )
    agent = BaseAgent(config)
    print("✓ Agent创建完成")
    
    # 3. 流式对话
    print("\n3. 开始流式对话...")
    print("="*60)
    
    questions = [
        "介绍一下Python的主要特点",
        "什么是异步编程？",
        "解释一下装饰器的作用"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n问题 {i}: {question}")
        print("-"*60)
        print("AI: ", end='', flush=True)
        
        if use_mock:
            # Mock模式
            from unittest.mock import patch, AsyncMock
            
            async def mock_stream(*args, **kwargs):
                response = f"这是对'{question}'的模拟回答。流式输出可以让用户实时看到响应内容，提升用户体验。"
                for char in response:
                    yield char
                    await asyncio.sleep(0.02)
            
            with patch.object(agent.memory, 'load_context_smart', new_callable=AsyncMock) as mock_load:
                mock_load.return_value = {
                    'history': [],
                    'strategy': 'new_conversation',
                    'cost': 0,
                    'filtered': False
                }
                
                with patch.object(agent.memory, 'is_followup', new_callable=AsyncMock) as mock_followup:
                    mock_followup.return_value = (False, 0.0, "新对话")
                    
                    with patch.object(agent, '_stream_llm', side_effect=mock_stream):
                        async for event in agent.execute_stream(
                            prompt_source={'use_agent_default': True},
                            user_input=question,
                            context={'session_id': f'demo_{i}', 'user_id': 'demo_user'}
                        ):
                            if event['type'] == 'token':
                                print(event['content'], end='', flush=True)
        else:
            # 真实模式
            async for event in agent.execute_stream(
                prompt_source={'use_agent_default': True},
                user_input=question,
                context={'session_id': f'demo_{i}', 'user_id': 'demo_user'}
            ):
                if event['type'] == 'token':
                    print(event['content'], end='', flush=True)
                elif event['type'] == 'error':
                    print(f"\n[错误] {event['error']}")
        
        print("\n")
    
    print("="*60)
    print("✅ 流式对话演示完成")


async def compare_stream_vs_normal():
    """对比流式输出和普通输出"""
    print("\n" + "="*60)
    print("对比：流式输出 vs 普通输出")
    print("="*60)
    
    config = AgentConfig(
        name="test_agent",
        description="测试Agent",
        model="qwen-turbo",
        temperature=0.7,
        system_prompt="你是一个友好的AI助手。"
    )
    agent = BaseAgent(config)
    
    question = "解释一下什么是机器学习"
    
    from unittest.mock import patch, AsyncMock
    import time
    
    # Mock响应
    mock_response = "机器学习是人工智能的一个分支，它使计算机能够从数据中学习并改进性能，而无需明确编程。" * 3
    
    # 1. 普通模式
    print("\n1. 普通模式（等待完整响应）:")
    print("-"*60)
    
    with patch.object(agent.memory, 'load_context_smart', new_callable=AsyncMock) as mock_load:
        mock_load.return_value = {
            'history': [],
            'strategy': 'new_conversation',
            'cost': 0,
            'filtered': False
        }
        
        with patch.object(agent, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response
            
            start = time.time()
            await asyncio.sleep(2)  # 模拟网络延迟
            result = await agent.execute(
                prompt_source={'use_agent_default': True},
                user_input=question,
                context={'session_id': 'compare_1', 'user_id': 'demo_user'}
            )
            end = time.time()
            
            print(f"[等待 {end-start:.1f}秒...]")
            print(f"AI: {result.content}")
            print(f"\n用户体验: 需要等待 {end-start:.1f}秒 才能看到响应")
    
    # 2. 流式模式
    print("\n2. 流式模式（实时显示）:")
    print("-"*60)
    
    async def mock_stream(*args, **kwargs):
        for char in mock_response:
            yield char
            await asyncio.sleep(0.02)  # 模拟逐字输出
    
    with patch.object(agent.memory, 'load_context_smart', new_callable=AsyncMock) as mock_load:
        mock_load.return_value = {
            'history': [],
            'strategy': 'new_conversation',
            'cost': 0,
            'filtered': False
        }
        
        with patch.object(agent.memory, 'is_followup', new_callable=AsyncMock) as mock_followup:
            mock_followup.return_value = (False, 0.0, "新对话")
            
            with patch.object(agent, '_stream_llm', side_effect=mock_stream):
                start = time.time()
                first_token_time = None
                
                print("AI: ", end='', flush=True)
                async for event in agent.execute_stream(
                    prompt_source={'use_agent_default': True},
                    user_input=question,
                    context={'session_id': 'compare_2', 'user_id': 'demo_user'}
                ):
                    if event['type'] == 'token':
                        if first_token_time is None:
                            first_token_time = time.time()
                        print(event['content'], end='', flush=True)
                
                end = time.time()
                ttft = first_token_time - start if first_token_time else 0
                
                print(f"\n\n用户体验: 首字延迟 {ttft*1000:.0f}ms，实时看到输出")
    
    print("\n" + "="*60)
    print("对比总结：")
    print("  普通模式: 等待时间长，用户体验差")
    print("  流式模式: 实时反馈，用户体验好")
    print("="*60)


if __name__ == "__main__":
    print("\n🚀 流式输出功能演示\n")
    
    # 运行示例
    asyncio.run(stream_chat_example())
    asyncio.run(compare_stream_vs_normal())
    
    print("\n✅ 演示完成")
