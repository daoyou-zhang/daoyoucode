"""
简单的LLM测试（不使用中间件）
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加backend到路径
sys.path.insert(0, str(Path(__file__).parent))

# 设置API Key
os.environ['DASHSCOPE_API_KEY'] = 'sk-d2971f2015574377bdf97046b1a03b87'

from daoyoucode.agents.builtin import register_builtin_agents
from daoyoucode.agents.core.agent import get_agent_registry
from daoyoucode.agents.core.skill import get_skill_loader
from daoyoucode.agents.llm import get_client_manager


async def test_direct_agent_call():
    """直接调用Agent（不通过Skill）"""
    print("\n" + "="*60)
    print("测试: 直接调用Agent")
    print("="*60)
    
    # 配置LLM提供商
    print("\n配置LLM提供商...")
    client_manager = get_client_manager()
    client_manager.configure_provider(
        provider='qwen',
        api_key=os.environ['DASHSCOPE_API_KEY'],
        base_url='https://dashscope.aliyuncs.com/compatible-mode/v1',
        models=['qwen-max', 'qwen-plus', 'qwen-turbo', 'qwen-coder-plus']
    )
    print("✓ 已配置qwen提供商")
    
    # 注册Agent
    register_builtin_agents()
    
    # 获取Agent
    registry = get_agent_registry()
    agent = registry.get_agent('programmer')
    
    if not agent:
        print("❌ Agent 'programmer' 未找到")
        return
    
    print(f"✓ 找到Agent: {agent.name}")
    
    # 直接调用（不使用工具）
    print("\n场景1: 简单问答（无工具）")
    print("-" * 40)
    
    try:
        result = await agent.execute(
            prompt_source={'inline': '你是一个Python编程专家。请简短回答用户的问题。'},
            user_input='什么是装饰器？用一句话解释。',
            llm_config={'model': 'qwen-max', 'temperature': 0.7}
        )
        
        print(f"\n执行结果:")
        print(f"  成功: {result.success}")
        print(f"  响应: {result.content}")
        print(f"  使用的工具: {result.tools_used}")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    
    # 使用工具
    print("\n场景2: 使用工具")
    print("-" * 40)
    
    try:
        result = await agent.execute(
            prompt_source={'inline': '你是一个Python编程专家。你可以使用工具来读取文件。'},
            user_input='读取daoyoucode/agents/core/agent.py文件的前50行',
            llm_config={'model': 'qwen-max', 'temperature': 0.7},
            tools=['read_file', 'get_file_content_lines'],
            max_tool_iterations=3
        )
        
        print(f"\n执行结果:")
        print(f"  成功: {result.success}")
        print(f"  响应长度: {len(result.content)} 字符")
        print(f"  使用的工具: {result.tools_used}")
        print(f"  响应预览: {result.content[:200]}...")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """主函数"""
    print("\n" + "="*60)
    print("简单LLM测试")
    print("="*60)
    
    await test_direct_agent_call()
    
    print("\n" + "="*60)
    print("测试完成！")
    print("="*60)


if __name__ == '__main__':
    asyncio.run(main())
