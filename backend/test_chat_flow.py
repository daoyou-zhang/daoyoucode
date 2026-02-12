"""
测试完整的chat流程
"""

import asyncio
import sys
from pathlib import Path

# 添加backend到路径
sys.path.insert(0, str(Path(__file__).parent))

async def test_chat():
    print("="*60)
    print("测试完整chat流程")
    print("="*60)
    
    # 1. 配置LLM
    print("\n1. 配置LLM...")
    from daoyoucode.agents.llm.client_manager import get_client_manager
    from daoyoucode.agents.llm.config_loader import auto_configure
    
    client_manager = get_client_manager()
    auto_configure(client_manager)
    
    if not client_manager.provider_configs:
        print("❌ 未找到LLM配置")
        return False
    
    print(f"✓ 已配置 {len(client_manager.provider_configs)} 个提供商")
    
    # 2. 注册Agent
    print("\n2. 注册Agent...")
    from daoyoucode.agents.builtin import register_builtin_agents
    register_builtin_agents()
    
    from daoyoucode.agents.core.agent import get_agent_registry
    registry = get_agent_registry()
    agents = registry.list_agents()
    
    if "MainAgent" not in agents:
        print("❌ MainAgent未注册")
        return False
    
    print(f"✓ 已注册 {len(agents)} 个Agent: {', '.join(agents)}")
    
    # 3. 测试execute_skill
    print("\n3. 测试execute_skill...")
    from daoyoucode.agents.executor import execute_skill
    
    context = {
        "session_id": "test-session",
        "repo": ".",
        "model": "qwen-max"
    }
    
    try:
        result = await execute_skill(
            skill_name="chat_assistant",
            user_input="你好",
            session_id=context["session_id"],
            context=context
        )
        
        print(f"\n✓ 执行完成")
        print(f"  • 成功: {result.get('success')}")
        print(f"  • 内容: {result.get('content', '')[:200]}")
        print(f"  • 错误: {result.get('error', 'N/A')}")
        
        return result.get('success', False)
    
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_chat())
    print("\n" + "="*60)
    if success:
        print("✅ 测试通过！可以使用chat命令了")
    else:
        print("❌ 测试失败")
    print("="*60)
