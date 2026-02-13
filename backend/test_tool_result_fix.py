"""
测试工具结果修复
"""

import sys
from pathlib import Path
import asyncio

sys.path.insert(0, str(Path(__file__).parent))

async def test():
    print("\n" + "="*60)
    print("测试工具结果处理")
    print("="*60)
    
    from daoyoucode.agents.init import initialize_agent_system
    from daoyoucode.agents.llm.client_manager import get_client_manager
    from daoyoucode.agents.llm.config_loader import auto_configure
    
    # 初始化
    initialize_agent_system()
    
    # 配置LLM
    client_manager = get_client_manager()
    auto_configure(client_manager)
    
    # 执行Skill
    from daoyoucode.agents.executor import execute_skill
    
    print("\n测试问题: 列出backend目录的文件")
    
    result = await execute_skill(
        skill_name="chat_assistant",
        user_input="列出backend目录下有哪些主要的子目录？",
        session_id="test",
        context={}
    )
    
    print(f"\n成功: {result.get('success')}")
    if result.get('success'):
        print(f"\n响应:")
        print("-"*60)
        print(result.get('content', '')[:500])
        print("-"*60)
        print(f"\n使用的工具: {result.get('tools_used', [])}")
    else:
        print(f"错误: {result.get('error')}")
    
    print("\n" + "="*60)

if __name__ == '__main__':
    asyncio.run(test())
