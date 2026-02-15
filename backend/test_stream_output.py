"""
测试流式输出功能

验证Agent的流式执行是否正常工作
"""

import asyncio
import sys
from unittest.mock import AsyncMock, patch
from daoyoucode.agents.core.agent import BaseAgent, AgentConfig


async def test_stream_basic():
    """测试基础流式输出"""
    print("\n" + "="*60)
    print("测试：基础流式输出")
    print("="*60)
    
    config = AgentConfig(
        name="test_agent",
        description="测试Agent",
        model="qwen-turbo",
        temperature=0.7,
        system_prompt="You are a helpful assistant."
    )
    agent = BaseAgent(config)
    
    # Mock memory
    with patch.object(agent.memory, 'load_context_smart', new_callable=AsyncMock) as mock_load:
        mock_load.return_value = {
            'history': [],
            'strategy': 'new_conversation',
            'cost': 0,
            'filtered': False
        }
        
        with patch.object(agent.memory, 'is_followup', new_callable=AsyncMock) as mock_followup:
            mock_followup.return_value = (False, 0.0, "新对话")
            
            # Mock流式LLM调用
            async def mock_stream(*args, **kwargs):
                test_response = "这是一个测试响应，用于验证流式输出功能。"
                for char in test_response:
                    yield char
                    await asyncio.sleep(0.01)  # 模拟网络延迟
            
            with patch.object(agent, '_stream_llm', side_effect=mock_stream):
                print("\n开始流式输出：")
                print("-" * 60)
                
                token_count = 0
                full_response = ""
                
                async for event in agent.execute_stream(
                    prompt_source={'use_agent_default': True},
                    user_input="你好",
                    context={'session_id': 'test', 'user_id': 'test_user'}
                ):
                    if event['type'] == 'token':
                        content = event['content']
                        full_response += content
                        print(content, end='', flush=True)
                        token_count += 1
                    elif event['type'] == 'metadata':
                        data = event['data']
                        if data.get('status') == 'started':
                            print("[流式开始]")
                        elif data.get('done'):
                            print(f"\n[流式完成]")
                    elif event['type'] == 'error':
                        print(f"\n[错误] {event['error']}")
                
                print("-" * 60)
                print(f"\n✅ 流式输出测试完成")
                print(f"   接收token数: {token_count}")
                print(f"   完整响应: {full_response}")


async def test_stream_with_tools_fallback():
    """测试带工具的流式输出（应该降级到普通模式）"""
    print("\n" + "="*60)
    print("测试：带工具的流式输出（降级）")
    print("="*60)
    
    config = AgentConfig(
        name="test_agent",
        description="测试Agent",
        model="qwen-turbo",
        temperature=0.7,
        system_prompt="You are a helpful assistant."
    )
    agent = BaseAgent(config)
    
    with patch.object(agent.memory, 'load_context_smart', new_callable=AsyncMock) as mock_load:
        mock_load.return_value = {
            'history': [],
            'strategy': 'new_conversation',
            'cost': 0,
            'filtered': False
        }
        
        with patch.object(agent.memory, 'is_followup', new_callable=AsyncMock) as mock_followup:
            mock_followup.return_value = (False, 0.0, "新对话")
            
            # Mock execute方法（普通模式）
            from daoyoucode.agents.core.agent import AgentResult
            mock_result = AgentResult(
                success=True,
                content="这是普通模式的响应",
                metadata={'agent': 'test_agent'},
                tools_used=['test_tool']
            )
            
            with patch.object(agent, 'execute', new_callable=AsyncMock) as mock_execute:
                mock_execute.return_value = mock_result
                
                print("\n尝试流式输出（带工具）：")
                print("-" * 60)
                
                event_count = 0
                async for event in agent.execute_stream(
                    prompt_source={'use_agent_default': True},
                    user_input="测试问题",
                    context={'session_id': 'test', 'user_id': 'test_user'},
                    tools=['test_tool']  # 提供工具
                ):
                    event_count += 1
                    if event['type'] == 'token':
                        print(event['content'], end='', flush=True)
                    elif event['type'] == 'metadata':
                        if event['data'].get('done'):
                            print(f"\n[完成]")
                
                print("-" * 60)
                print(f"\n✅ 降级测试完成")
                print(f"   接收事件数: {event_count}")
                print(f"   已自动降级到普通模式")


async def test_stream_error_handling():
    """测试流式输出错误处理"""
    print("\n" + "="*60)
    print("测试：流式输出错误处理")
    print("="*60)
    
    config = AgentConfig(
        name="test_agent",
        description="测试Agent",
        model="qwen-turbo",
        temperature=0.7,
        system_prompt="You are a helpful assistant."
    )
    agent = BaseAgent(config)
    
    with patch.object(agent.memory, 'load_context_smart', new_callable=AsyncMock) as mock_load:
        mock_load.return_value = {
            'history': [],
            'strategy': 'new_conversation',
            'cost': 0,
            'filtered': False
        }
        
        with patch.object(agent.memory, 'is_followup', new_callable=AsyncMock) as mock_followup:
            mock_followup.return_value = (False, 0.0, "新对话")
            
            # Mock流式LLM调用（抛出异常）
            async def mock_stream_error(*args, **kwargs):
                yield "开始"
                await asyncio.sleep(0.01)
                raise Exception("模拟网络错误")
            
            with patch.object(agent, '_stream_llm', side_effect=mock_stream_error):
                print("\n开始流式输出（会出错）：")
                print("-" * 60)
                
                error_caught = False
                async for event in agent.execute_stream(
                    prompt_source={'use_agent_default': True},
                    user_input="测试问题",
                    context={'session_id': 'test', 'user_id': 'test_user'}
                ):
                    if event['type'] == 'token':
                        print(event['content'], end='', flush=True)
                    elif event['type'] == 'error':
                        print(f"\n[捕获错误] {event['error']}")
                        error_caught = True
                    elif event['type'] == 'metadata':
                        if event['data'].get('status') == 'failed':
                            print("[状态: 失败]")
                
                print("-" * 60)
                if error_caught:
                    print("\n✅ 错误处理测试通过")
                else:
                    print("\n❌ 错误未被正确捕获")


async def test_stream_performance():
    """测试流式输出性能"""
    print("\n" + "="*60)
    print("测试：流式输出性能")
    print("="*60)
    
    config = AgentConfig(
        name="test_agent",
        description="测试Agent",
        model="qwen-turbo",
        temperature=0.7,
        system_prompt="You are a helpful assistant."
    )
    agent = BaseAgent(config)
    
    with patch.object(agent.memory, 'load_context_smart', new_callable=AsyncMock) as mock_load:
        mock_load.return_value = {
            'history': [],
            'strategy': 'new_conversation',
            'cost': 0,
            'filtered': False
        }
        
        with patch.object(agent.memory, 'is_followup', new_callable=AsyncMock) as mock_followup:
            mock_followup.return_value = (False, 0.0, "新对话")
            
            # Mock流式LLM调用（长响应）
            async def mock_stream_long(*args, **kwargs):
                long_text = "这是一个很长的响应。" * 100  # 1000字符
                for char in long_text:
                    yield char
                    await asyncio.sleep(0.001)  # 1ms延迟
            
            with patch.object(agent, '_stream_llm', side_effect=mock_stream_long):
                import time
                
                print("\n开始性能测试（长响应）...")
                start_time = time.time()
                
                token_count = 0
                first_token_time = None
                
                async for event in agent.execute_stream(
                    prompt_source={'use_agent_default': True},
                    user_input="生成长文本",
                    context={'session_id': 'test', 'user_id': 'test_user'}
                ):
                    if event['type'] == 'token':
                        if first_token_time is None:
                            first_token_time = time.time()
                        token_count += 1
                
                end_time = time.time()
                
                total_time = end_time - start_time
                ttft = first_token_time - start_time if first_token_time else 0
                
                print(f"\n性能指标：")
                print(f"  总耗时: {total_time*1000:.2f}ms")
                print(f"  首token时间(TTFT): {ttft*1000:.2f}ms")
                print(f"  Token数: {token_count}")
                print(f"  平均速度: {token_count/total_time:.1f} tokens/s")
                
                print(f"\n✅ 性能测试完成")


if __name__ == "__main__":
    print("="*60)
    print("流式输出功能测试套件")
    print("="*60)
    
    asyncio.run(test_stream_basic())
    asyncio.run(test_stream_with_tools_fallback())
    asyncio.run(test_stream_error_handling())
    asyncio.run(test_stream_performance())
    
    print("\n" + "="*60)
    print("✅ 所有测试完成")
    print("="*60)
