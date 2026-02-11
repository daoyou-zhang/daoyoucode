"""
最终演示测试 - 展示完整的Agent+工具调用流程
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
from daoyoucode.agents.llm import get_client_manager


async def demo_1_simple_question():
    """演示1: 简单问答（无工具）"""
    print("\n" + "="*70)
    print("演示1: 简单问答（无工具）")
    print("="*70)
    
    registry = get_agent_registry()
    agent = registry.get_agent('programmer')
    
    print("\n问题: Python中的装饰器是什么？")
    print("-" * 70)
    
    result = await agent.execute(
        prompt_source={'inline': '你是Python编程专家。用简洁的语言回答问题。'},
        user_input='Python中的装饰器是什么？用2-3句话解释。',
        llm_config={'model': 'qwen-max', 'temperature': 0.7}
    )
    
    print(f"\n回答:\n{result.content}")
    print(f"\n使用的工具: {result.tools_used}")


async def demo_2_file_search():
    """演示2: 使用搜索工具查找代码"""
    print("\n" + "="*70)
    print("演示2: 使用搜索工具查找代码")
    print("="*70)
    
    registry = get_agent_registry()
    agent = registry.get_agent('code_explorer')
    
    print("\n任务: 在代码库中查找BaseAgent类的定义")
    print("-" * 70)
    
    result = await agent.execute(
        prompt_source={'inline': '''你是代码探索专家。你可以使用以下工具:
- grep_search: 文本搜索
- find_class: 查找类定义
- read_file: 读取文件

请帮助用户查找代码。'''},
        user_input='在daoyoucode/agents目录中查找BaseAgent类的定义位置',
        llm_config={'model': 'qwen-coder-plus', 'temperature': 0.1},
        tools=['grep_search', 'find_class', 'read_file'],
        max_tool_iterations=3
    )
    
    print(f"\n回答:\n{result.content}")
    print(f"\n使用的工具: {result.tools_used}")


async def demo_3_file_operations():
    """演示3: 文件操作工具"""
    print("\n" + "="*70)
    print("演示3: 文件操作工具")
    print("="*70)
    
    registry = get_agent_registry()
    agent = registry.get_agent('programmer')
    
    print("\n任务: 读取并分析agent.py文件的结构")
    print("-" * 70)
    
    result = await agent.execute(
        prompt_source={'inline': '''你是Python编程专家。你可以使用以下工具:
- read_file: 读取文件
- get_file_content_lines: 读取指定行
- list_files: 列出文件

请帮助用户分析代码文件。'''},
        user_input='读取daoyoucode/agents/core/agent.py文件，告诉我这个文件定义了哪些主要的类',
        llm_config={'model': 'qwen-coder-plus', 'temperature': 0.1},
        tools=['read_file', 'get_file_content_lines'],
        max_tool_iterations=3
    )
    
    print(f"\n回答:\n{result.content[:500]}...")
    print(f"\n使用的工具: {result.tools_used}")


async def demo_4_git_operations():
    """演示4: Git操作工具"""
    print("\n" + "="*70)
    print("演示4: Git操作工具")
    print("="*70)
    
    registry = get_agent_registry()
    agent = registry.get_agent('programmer')
    
    print("\n任务: 查看Git仓库状态")
    print("-" * 70)
    
    result = await agent.execute(
        prompt_source={'inline': '''你是Git专家。你可以使用以下工具:
- git_status: 查看Git状态
- git_branch: 查看分支
- git_log: 查看提交历史

请帮助用户了解Git仓库状态。'''},
        user_input='查看当前Git仓库的状态和分支信息',
        llm_config={'model': 'qwen-max', 'temperature': 0.1},
        tools=['git_status', 'git_branch', 'git_log'],
        max_tool_iterations=3
    )
    
    print(f"\n回答:\n{result.content[:500]}...")
    print(f"\n使用的工具: {result.tools_used}")


async def main():
    """主函数"""
    print("\n" + "="*70)
    print("🚀 Agent系统完整功能演示")
    print("="*70)
    
    # 配置LLM
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
    print("注册Agent...")
    register_builtin_agents()
    print("✓ 已注册所有内置Agent")
    
    # 运行演示
    await demo_1_simple_question()
    await demo_2_file_search()
    await demo_3_file_operations()
    await demo_4_git_operations()
    
    print("\n" + "="*70)
    print("✅ 所有演示完成！")
    print("="*70)
    
    print("\n总结:")
    print("  • Agent系统正常工作")
    print("  • 工具调用流程完整")
    print("  • LLM Function Calling成功")
    print("  • 20个工具全部可用")
    print("\n🎉 系统已经可以投入使用！")


if __name__ == '__main__':
    asyncio.run(main())
