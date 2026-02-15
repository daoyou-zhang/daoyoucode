"""
测试完整的chat流程（使用新的初始化系统）

模拟实际的CLI chat命令执行流程
"""

import sys
from pathlib import Path
import asyncio

# 添加backend到路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

async def test_chat_flow():
    """测试完整的chat流程"""
    print("\n" + "="*60)
    print("测试完整的Chat流程")
    print("="*60)
    
    # 1. 初始化Agent系统
    print("\n1. 初始化Agent系统...")
    from daoyoucode.agents.init import initialize_agent_system
    tool_registry = initialize_agent_system()
    print(f"   ✓ 工具数量: {len(tool_registry.list_tools())}")
    
    # 2. 配置LLM客户端
    print("\n2. 配置LLM客户端...")
    from daoyoucode.agents.llm.client_manager import get_client_manager
    from daoyoucode.agents.llm.config_loader import auto_configure
    
    client_manager = get_client_manager()
    auto_configure(client_manager)
    
    if client_manager.provider_configs:
        print(f"   ✓ 已配置 {len(client_manager.provider_configs)} 个提供商")
    else:
        print("   ⚠ 未配置LLM提供商（将使用模拟模式）")
    
    # 3. 准备上下文
    print("\n3. 准备上下文...")
    context = {
        "session_id": "test_session",
        "repo": ".",
        "model": "qwen-plus",
        "initial_files": []
    }
    print("   ✓ 上下文已准备")
    
    # 4. 执行Skill
    print("\n4. 执行chat_assistant Skill...")
    from daoyoucode.agents.executor import execute_skill
    
    user_input = "你好，你能理解这个项目吗？"
    print(f"   用户输入: {user_input}")
    
    try:
        result = await execute_skill(
            skill_name="chat_assistant",
            user_input=user_input,
            session_id=context["session_id"],
            context=context
        )
        
        if result.get('success'):
            print("   ✓ Skill执行成功")
            response = result.get('content', '')
            print(f"\n   AI响应: {response[:200]}...")
            
            # 检查是否使用了工具
            tools_used = result.get('tools_used', [])
            if tools_used:
                print(f"\n   使用的工具: {', '.join(tools_used)}")
            else:
                print("\n   未使用工具（可能是LLM不支持function calling）")
            
            return True
        else:
            error = result.get('error', '未知错误')
            print(f"   ✗ Skill执行失败: {error}")
            return False
    
    except Exception as e:
        print(f"   ✗ 执行异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    success = asyncio.run(test_chat_flow())
    
    print("\n" + "="*60)
    if success:
        print("✓ 测试通过")
    else:
        print("✗ 测试失败")
    print("="*60)
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
