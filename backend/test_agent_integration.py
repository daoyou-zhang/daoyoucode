"""
测试Agent集成
"""

import sys
import os
import asyncio

# 添加backend到路径
sys.path.insert(0, os.path.dirname(__file__))

def test_agent_system():
    """测试Agent系统是否可用"""
    print("=" * 60)
    print("测试 Agent 系统")
    print("=" * 60)
    
    try:
        from daoyoucode.agents.core.agent import (
            get_agent_registry,
            register_agent,
            BaseAgent,
            AgentConfig
        )
        
        print("✓ Agent系统导入成功")
        
        # 获取注册表
        registry = get_agent_registry()
        print(f"✓ Agent注册表获取成功")
        print(f"  已注册的Agent: {registry.list_agents()}")
        
        # 创建测试Agent
        config = AgentConfig(
            name="TestAgent",
            description="测试Agent",
            model="qwen-max",
            temperature=0.7,
            system_prompt="你是一个测试Agent"
        )
        
        agent = BaseAgent(config)
        print(f"✓ 创建Agent成功: {agent.name}")
        
        # 注册Agent
        register_agent(agent)
        print(f"✓ 注册Agent成功")
        print(f"  当前已注册: {registry.list_agents()}")
        
        return True
        
    except Exception as e:
        print(f"✗ Agent系统测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_llm_client():
    """测试LLM客户端"""
    print("\n" + "=" * 60)
    print("测试 LLM 客户端")
    print("=" * 60)
    
    try:
        from daoyoucode.agents.llm.client_manager import get_client_manager
        
        manager = get_client_manager()
        print("✓ LLM客户端管理器获取成功")
        
        # 检查是否有配置
        if not manager.provider_configs:
            print("⚠ 未配置任何LLM提供商")
            print("  需要配置API才能使用真实LLM")
            print("\n  配置示例:")
            print("  manager.configure_provider(")
            print("      provider='qwen',")
            print("      api_key='your-api-key',")
            print("      base_url='https://dashscope.aliyuncs.com/compatible-mode/v1',")
            print("      models=['qwen-max', 'qwen-plus']")
            print("  )")
            return False
        else:
            print(f"✓ 已配置提供商: {list(manager.provider_configs.keys())}")
            return True
            
    except Exception as e:
        print(f"✗ LLM客户端测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_chat_integration():
    """测试chat命令的Agent集成"""
    print("\n" + "=" * 60)
    print("测试 chat 命令 Agent 集成")
    print("=" * 60)
    
    try:
        from cli.commands.chat import initialize_agents
        
        # 测试初始化
        print("正在初始化Agent...")
        agent_available = initialize_agents("qwen-max")
        
        if agent_available:
            print("✓ Agent初始化成功 - 可以使用真实AI")
        else:
            print("⚠ Agent初始化失败 - 将使用模拟模式")
            print("  这是正常的，如果没有配置API的话")
        
        return agent_available
        
    except Exception as e:
        print(f"✗ chat集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_edit_integration():
    """测试edit命令的Agent集成"""
    print("\n" + "=" * 60)
    print("测试 edit 命令 Agent 集成")
    print("=" * 60)
    
    try:
        from cli.commands.edit import initialize_edit_agent
        
        # 测试初始化
        print("正在初始化CodeAgent...")
        agent_available = initialize_edit_agent("qwen-max")
        
        if agent_available:
            print("✓ CodeAgent初始化成功 - 可以使用真实AI")
        else:
            print("⚠ CodeAgent初始化失败 - 将使用模拟模式")
            print("  这是正常的，如果没有配置API的话")
        
        return agent_available
        
    except Exception as e:
        print(f"✗ edit集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "🧪 DaoyouCode CLI Agent 集成测试")
    print("=" * 60)
    
    results = {
        "Agent系统": test_agent_system(),
        "LLM客户端": test_llm_client(),
        "chat集成": test_chat_integration(),
        "edit集成": test_edit_integration()
    }
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for name, result in results.items():
        status = "✓ 通过" if result else "⚠ 需要配置"
        print(f"{name}: {status}")
    
    print("\n" + "=" * 60)
    
    if all(results.values()):
        print("🎉 所有测试通过！可以使用真实AI功能")
    elif results["Agent系统"]:
        print("✅ Agent系统正常，但需要配置API才能使用真实LLM")
        print("💡 当前可以使用模拟模式测试CLI功能")
    else:
        print("❌ Agent系统有问题，请检查")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
