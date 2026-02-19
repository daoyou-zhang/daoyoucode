"""
测试chat命令的问题
"""
import asyncio
import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

async def test_chat():
    """测试chat命令"""
    from daoyoucode.agents.init import initialize_agent_system
    from daoyoucode.agents.llm.client_manager import get_client_manager
    from daoyoucode.agents.llm.config_loader import auto_configure
    from daoyoucode.agents.executor import execute_skill
    
    # 初始化
    print("1. 初始化Agent系统...")
    initialize_agent_system()
    
    print("2. 配置LLM...")
    client_manager = get_client_manager()
    auto_configure(client_manager)
    
    print(f"3. 配置的提供商: {list(client_manager.provider_configs.keys())}")
    
    # 执行
    print("4. 执行Skill...")
    result = await execute_skill(
        skill_name='chat-assistant',
        user_input='你好啊，道友，你能做啥？',
        context={'repo': '.'}
    )
    
    print(f"\n5. 结果:")
    print(f"   Success: {result.get('success')}")
    print(f"   Content: {result.get('content', 'EMPTY')[:200]}")
    print(f"   Error: {result.get('error')}")
    
    return result

if __name__ == "__main__":
    result = asyncio.run(test_chat())
    
    if result.get('success'):
        print("\n✅ 测试通过")
    else:
        print("\n❌ 测试失败")
        sys.exit(1)
