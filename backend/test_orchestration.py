"""
测试编排流程

测试不同的编排器和工具调用
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加backend到路径
sys.path.insert(0, str(Path(__file__).parent))

from daoyoucode.agents import execute_skill
from daoyoucode.agents.core.skill import get_skill_loader
from daoyoucode.agents.builtin import register_builtin_agents


async def test_simple_orchestrator_with_tools():
    """测试简单编排器 + 工具调用"""
    print("\n" + "="*60)
    print("测试1: 简单编排器 + 工具调用")
    print("="*60)
    
    # 注册Agent
    register_builtin_agents()
    
    # 测试代码探索Skill（带工具）
    print("\n场景: 使用代码探索Agent查找BaseAgent类")
    print("-" * 40)
    
    try:
        result = await execute_skill(
            skill_name='code-exploration',
            user_input='查找BaseAgent类的定义位置',
            context={
                'search_scope': 'daoyoucode/agents',
                'thoroughness': 'quick'
            }
        )
        
        print(f"\n执行结果:")
        print(f"  成功: {result.get('success')}")
        print(f"  使用的工具: {result.get('tools_used', [])}")
        print(f"  响应内容: {result.get('content', '')[:500]}...")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()


async def test_multi_agent_orchestrator():
    """测试多Agent编排器"""
    print("\n" + "="*60)
    print("测试2: 多Agent编排器")
    print("="*60)
    
    # 注册Agent
    register_builtin_agents()
    
    # 创建一个需要多Agent协作的Skill配置
    print("\n场景: 代码分析 + 重构建议")
    print("-" * 40)
    
    # 这里需要先创建一个multi-agent的skill配置
    print("提示: 需要创建multi-agent skill配置文件")
    print("暂时跳过此测试")


async def test_workflow_orchestrator():
    """测试工作流编排器"""
    print("\n" + "="*60)
    print("测试3: 工作流编排器")
    print("="*60)
    
    # 注册Agent
    register_builtin_agents()
    
    print("\n场景: 分析 -> 重构 -> 测试 工作流")
    print("-" * 40)
    
    # 这里需要先创建一个workflow的skill配置
    print("提示: 需要创建workflow skill配置文件")
    print("暂时跳过此测试")


async def test_programming_with_tools():
    """测试编程Agent + 工具"""
    print("\n" + "="*60)
    print("测试4: 编程Agent + 工具调用")
    print("="*60)
    
    # 注册Agent
    register_builtin_agents()
    
    print("\n场景: 读取文件并分析代码")
    print("-" * 40)
    
    try:
        result = await execute_skill(
            skill_name='programming',
            user_input='读取daoyoucode/agents/core/agent.py文件，分析BaseAgent类的主要功能',
            context={
                'language': 'python'
            }
        )
        
        print(f"\n执行结果:")
        print(f"  成功: {result.get('success')}")
        print(f"  使用的工具: {result.get('tools_used', [])}")
        print(f"  响应内容: {result.get('content', '')[:500]}...")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()


async def test_skill_loading():
    """测试Skill加载"""
    print("\n" + "="*60)
    print("测试5: Skill配置加载")
    print("="*60)
    
    # 获取Skill加载器
    skill_loader = get_skill_loader()
    
    # 测试加载code-exploration skill
    print("\n加载 code-exploration skill")
    print("-" * 40)
    
    try:
        skill = skill_loader.get_skill('code-exploration')
        
        if skill:
            print(f"Skill名称: {skill.name}")
            print(f"版本: {skill.version}")
            print(f"描述: {skill.description}")
            print(f"编排器: {skill.orchestrator}")
            print(f"Agent: {skill.agent}")
            print(f"模型: {skill.llm.get('model')}")
            print(f"可用工具: {getattr(skill, 'tools', [])}")
        else:
            print("未找到 code-exploration skill")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试加载programming skill
    print("\n加载 programming skill")
    print("-" * 40)
    
    try:
        skill = skill_loader.get_skill('programming')
        
        if skill:
            print(f"Skill名称: {skill.name}")
            print(f"版本: {skill.version}")
            print(f"描述: {skill.description}")
            print(f"编排器: {skill.orchestrator}")
            print(f"Agent: {skill.agent}")
            print(f"模型: {skill.llm.get('model')}")
            print(f"可用工具: {getattr(skill, 'tools', [])}")
        else:
            print("未找到 programming skill")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    
    # 列出所有Skill
    print("\n所有已加载的Skill:")
    print("-" * 40)
    
    all_skills = skill_loader.list_skills()
    print(f"共 {len(all_skills)} 个Skill:\n")
    for skill_info in all_skills:
        print(f"  • {skill_info['name']} v{skill_info['version']}")
        print(f"    {skill_info['description']}")
        print(f"    编排器: {skill_info['orchestrator']}")
        print()


async def test_tool_integration():
    """测试工具集成"""
    print("\n" + "="*60)
    print("测试6: 工具集成验证")
    print("="*60)
    
    from daoyoucode.agents.tools import get_tool_registry
    
    registry = get_tool_registry()
    
    # 验证所有工具都已注册
    print("\n已注册的工具:")
    print("-" * 40)
    
    all_tools = registry.list_tools()
    print(f"总共 {len(all_tools)} 个工具\n")
    
    # 按分类显示
    categories = {}
    for tool_name in all_tools:
        tool = registry.get_tool(tool_name)
        if tool.category not in categories:
            categories[tool.category] = []
        categories[tool.category].append(tool_name)
    
    for category, tools in sorted(categories.items()):
        print(f"{category.upper()} ({len(tools)}个):")
        for tool_name in sorted(tools):
            print(f"  ✓ {tool_name}")
        print()
    
    # 验证Function Schemas
    print("Function Schemas验证:")
    print("-" * 40)
    
    schemas = registry.get_function_schemas(['read_file', 'grep_search', 'git_status'])
    print(f"生成了 {len(schemas)} 个Function Schema")
    
    for schema in schemas:
        print(f"\n{schema['name']}:")
        print(f"  参数数量: {len(schema['parameters']['properties'])}")
        print(f"  必需参数: {schema['parameters']['required']}")


async def main():
    """主函数"""
    print("\n" + "="*60)
    print("编排流程综合测试")
    print("="*60)
    
    # 检查API Key
    if not os.getenv('DASHSCOPE_API_KEY'):
        print("\n⚠️  警告: 未设置 DASHSCOPE_API_KEY 环境变量")
        print("请设置后再运行LLM相关测试")
        print("\n将只运行不需要LLM的测试...")
        
        # 只运行不需要LLM的测试
        await test_skill_loading()
        await test_tool_integration()
        
    else:
        print("\n✓ 检测到 DASHSCOPE_API_KEY")
        
        # 运行所有测试
        await test_skill_loading()
        await test_tool_integration()
        
        # LLM相关测试
        print("\n" + "="*60)
        print("开始LLM相关测试")
        print("="*60)
        
        await test_simple_orchestrator_with_tools()
        await test_programming_with_tools()
        # await test_multi_agent_orchestrator()
        # await test_workflow_orchestrator()
    
    print("\n" + "="*60)
    print("测试完成！")
    print("="*60)


if __name__ == '__main__':
    asyncio.run(main())
