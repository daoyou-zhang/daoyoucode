"""
测试真实的API调用
"""

import sys
import os
import asyncio

# 添加backend到路径
sys.path.insert(0, os.path.dirname(__file__))


async def test_llm_call():
    """测试LLM API调用"""
    print("=" * 60)
    print("测试 LLM API 调用")
    print("=" * 60)
    
    try:
        # 1. 导入并配置
        from daoyoucode.agents.llm.client_manager import get_client_manager
        from daoyoucode.agents.llm.config_loader import auto_configure
        
        print("\n1. 配置LLM客户端...")
        manager = get_client_manager()
        auto_configure(manager)
        
        if not manager.provider_configs:
            print("✗ 未配置任何提供商")
            return False
        
        print(f"✓ 已配置提供商: {list(manager.provider_configs.keys())}")
        
        # 2. 获取客户端
        print("\n2. 获取客户端...")
        client = manager.get_client(model="qwen-turbo")
        print(f"✓ 客户端创建成功")
        
        # 3. 构建请求
        print("\n3. 发送测试请求...")
        from daoyoucode.agents.llm.base import LLMRequest
        
        request = LLMRequest(
            prompt="你好，请用一句话介绍你自己。",
            model="qwen-turbo",
            temperature=0.7
        )
        
        print(f"   提示词: {request.prompt}")
        
        # 4. 调用API
        print("\n4. 调用API...")
        response = await client.chat(request)
        
        print(f"✓ API调用成功！")
        print(f"\n响应内容:")
        print(f"  {response.content}")
        print(f"\n元数据:")
        print(f"  模型: {response.model}")
        print(f"  Tokens: {response.usage.get('total_tokens', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ API调用失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_agent_with_llm():
    """测试Agent使用LLM"""
    print("\n" + "=" * 60)
    print("测试 Agent 使用 LLM")
    print("=" * 60)
    
    try:
        # 1. 配置LLM
        from daoyoucode.agents.llm.client_manager import get_client_manager
        from daoyoucode.agents.llm.config_loader import auto_configure
        
        manager = get_client_manager()
        auto_configure(manager)
        
        if not manager.provider_configs:
            print("✗ 未配置提供商")
            return False
        
        # 2. 创建Agent
        from daoyoucode.agents.core.agent import BaseAgent, AgentConfig
        
        print("\n1. 创建Agent...")
        config = AgentConfig(
            name="TestAgent",
            description="测试Agent",
            model="qwen-turbo",
            temperature=0.7,
            system_prompt="你是一个友好的AI助手。"
        )
        
        agent = BaseAgent(config)
        print(f"✓ Agent创建成功: {agent.name}")
        
        # 3. 执行任务
        print("\n2. 执行任务...")
        result = await agent.execute(
            prompt_source={"use_agent_default": True},
            user_input="你好，请用一句话介绍你自己。",
            context={}
        )
        
        if result.success:
            print(f"✓ Agent执行成功！")
            print(f"\n响应内容:")
            print(f"  {result.content}")
            return True
        else:
            print(f"✗ Agent执行失败: {result.error}")
            return False
        
    except Exception as e:
        print(f"\n✗ Agent测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """运行所有测试"""
    print("\n🧪 DaoyouCode API 调用测试")
    print("=" * 60)
    
    # 测试1: 直接LLM调用
    test1 = await test_llm_call()
    
    # 测试2: Agent使用LLM
    test2 = await test_agent_with_llm()
    
    # 总结
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    print(f"LLM API调用: {'✓ 通过' if test1 else '✗ 失败'}")
    print(f"Agent使用LLM: {'✓ 通过' if test2 else '✗ 失败'}")
    print("=" * 60)
    
    if test1 and test2:
        print("\n🎉 所有测试通过！API配置正确，可以使用真实AI功能！")
    else:
        print("\n❌ 部分测试失败，请检查配置和网络连接")


if __name__ == "__main__":
    asyncio.run(main())
