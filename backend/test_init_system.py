"""
测试Agent系统初始化

验证工具注册、Agent注册、编排器注册都正常工作
"""

import sys
from pathlib import Path

# 添加backend到路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

def test_initialization():
    """测试初始化"""
    print("\n" + "="*60)
    print("测试Agent系统初始化")
    print("="*60)
    
    # 1. 第一次初始化
    print("\n1. 第一次初始化...")
    from daoyoucode.agents.init import initialize_agent_system
    tool_registry = initialize_agent_system()
    
    tools = tool_registry.list_tools()
    print(f"   ✓ 工具数量: {len(tools)}")
    print(f"   ✓ 工具列表: {', '.join(sorted(tools)[:10])}...")
    
    # 检查repo_map是否存在
    if 'repo_map' in tools:
        print("   ✓ repo_map工具已注册")
    else:
        print("   ✗ repo_map工具未找到")
        return False
    
    # 2. 第二次初始化（应该跳过）
    print("\n2. 第二次初始化（应该跳过）...")
    tool_registry2 = initialize_agent_system()
    
    # 验证是同一个实例
    if id(tool_registry) == id(tool_registry2):
        print("   ✓ 返回了相同的实例（单例模式正确）")
    else:
        print("   ✗ 返回了不同的实例（单例模式失败）")
        return False
    
    # 3. 检查Agent注册
    print("\n3. 检查Agent注册...")
    from daoyoucode.agents.core.agent import get_agent_registry
    agent_registry = get_agent_registry()
    agents = agent_registry.list_agents()
    print(f"   ✓ Agent数量: {len(agents)}")
    print(f"   ✓ Agent列表: {', '.join(agents)}")
    
    if 'MainAgent' in agents:
        print("   ✓ MainAgent已注册")
    else:
        print("   ✗ MainAgent未找到")
        return False
    
    # 4. 检查编排器注册
    print("\n4. 检查编排器注册...")
    from daoyoucode.agents.core.orchestrator import get_orchestrator_registry
    orchestrator_registry = get_orchestrator_registry()
    orchestrators = orchestrator_registry.list_orchestrators()
    print(f"   ✓ 编排器数量: {len(orchestrators)}")
    print(f"   ✓ 编排器列表: {', '.join(orchestrators)}")
    
    # 5. 测试工具执行
    print("\n5. 测试工具执行...")
    import asyncio
    
    async def test_tool():
        try:
            result = await tool_registry.execute_tool(
                'list_files',
                directory='.',
                recursive=False
            )
            print(f"   ✓ list_files工具执行成功")
            return True
        except Exception as e:
            print(f"   ✗ 工具执行失败: {e}")
            return False
    
    success = asyncio.run(test_tool())
    if not success:
        return False
    
    print("\n" + "="*60)
    print("✓ 所有测试通过")
    print("="*60)
    return True


if __name__ == '__main__':
    success = test_initialization()
    sys.exit(0 if success else 1)
