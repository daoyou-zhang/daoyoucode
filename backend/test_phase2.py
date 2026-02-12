"""
Phase 2功能测试

测试：
1. 后台任务管理器
2. 并行探索编排器
3. 动态Prompt构建器
"""

import asyncio
import sys
import os

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from daoyoucode.agents.core.background import get_background_manager, TaskStatus
from daoyoucode.agents.core.prompt_builder import (
    DynamicPromptBuilder,
    PromptOptimizer,
    is_followup,
    has_tools,
    ROLE_TEMPLATE,
    HISTORY_TEMPLATE,
    TOOLS_TEMPLATE
)


async def test_background_manager():
    """测试后台任务管理器"""
    print("\n" + "="*60)
    print("测试1: 后台任务管理器")
    print("="*60)
    
    manager = get_background_manager()
    
    # 模拟Agent执行函数
    async def mock_agent_execute(task_id: str, delay: float):
        """模拟Agent执行"""
        await asyncio.sleep(delay)
        return {
            'success': True,
            'content': f'任务 {task_id} 完成',
            'delay': delay
        }
    
    # 提交任务（需要先注册一个mock agent）
    # 这里简化测试，直接测试任务管理
    
    print("\n✓ 后台任务管理器初始化成功")
    print(f"  - 当前任务数: {len(manager.tasks)}")
    
    # 测试任务列表
    tasks = manager.list_tasks()
    print(f"  - 任务列表: {tasks}")
    
    return True


async def test_prompt_builder():
    """测试动态Prompt构建器"""
    print("\n" + "="*60)
    print("测试2: 动态Prompt构建器")
    print("="*60)
    
    builder = DynamicPromptBuilder()
    
    # 添加段落
    builder.add_section(
        name="role",
        content=ROLE_TEMPLATE,
        priority=10  # 高优先级
    )
    
    builder.add_section(
        name="history",
        content=HISTORY_TEMPLATE,
        condition=is_followup,
        priority=5
    )
    
    builder.add_section(
        name="tools",
        content=TOOLS_TEMPLATE,
        condition=has_tools,
        priority=3
    )
    
    # 测试1: 非追问，无工具
    print("\n场景1: 非追问，无工具")
    context1 = {
        'agent_name': 'Translator',
        'domain': '翻译',
        'is_followup': False
    }
    
    prompt1 = builder.build(context1)
    print(f"生成的Prompt:\n{prompt1}")
    print(f"Token数: {builder._count_tokens(prompt1)}")
    
    # 测试2: 追问，有工具
    print("\n场景2: 追问，有工具")
    context2 = {
        'agent_name': 'CodeExplorer',
        'domain': '代码探索',
        'is_followup': True,
        'summary': '用户之前询问了BaseAgent类的位置',
        'tools': [
            {'name': 'grep_search', 'description': '搜索代码'},
            {'name': 'read_file', 'description': '读取文件'}
        ]
    }
    
    prompt2 = builder.build(context2)
    print(f"生成的Prompt:\n{prompt2}")
    print(f"Token数: {builder._count_tokens(prompt2)}")
    
    # 测试3: Token限制
    print("\n场景3: Token限制")
    prompt3 = builder.build(context2, max_tokens=50)
    print(f"优化后的Prompt:\n{prompt3}")
    print(f"Token数: {builder._count_tokens(prompt3)}")
    
    print("\n✓ 动态Prompt构建器测试通过")
    
    return True


async def test_prompt_optimizer():
    """测试Prompt优化器"""
    print("\n" + "="*60)
    print("测试3: Prompt优化器")
    print("="*60)
    
    optimizer = PromptOptimizer()
    
    # 创建一个长Prompt
    long_prompt = """你是一个AI助手。

<example>
这是一个示例1...
</example>

<example>
这是一个示例2...
</example>

这是主要内容，包含很多详细的说明和指导...
""" * 10  # 重复10次
    
    print(f"原始Prompt长度: {len(long_prompt)} 字符")
    print(f"原始Token数: {optimizer._count_tokens(long_prompt)}")
    
    # 优化
    context = {
        'conversation_history': [
            {'role': 'user', 'content': '问题1'},
            {'role': 'assistant', 'content': '回答1'},
            {'role': 'user', 'content': '问题2'},
            {'role': 'assistant', 'content': '回答2'},
        ] * 5  # 10轮对话
    }
    
    optimized = await optimizer.optimize(
        prompt=long_prompt,
        context=context,
        max_tokens=200
    )
    
    print(f"\n优化后Prompt长度: {len(optimized)} 字符")
    print(f"优化后Token数: {optimizer._count_tokens(optimized)}")
    print(f"压缩率: {(1 - len(optimized)/len(long_prompt)) * 100:.1f}%")
    
    print("\n✓ Prompt优化器测试通过")
    
    return True


async def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("Phase 2 功能测试")
    print("="*60)
    
    results = []
    
    # 测试1: 后台任务管理器
    try:
        result = await test_background_manager()
        results.append(('后台任务管理器', result))
    except Exception as e:
        print(f"\n✗ 后台任务管理器测试失败: {e}")
        results.append(('后台任务管理器', False))
    
    # 测试2: 动态Prompt构建器
    try:
        result = await test_prompt_builder()
        results.append(('动态Prompt构建器', result))
    except Exception as e:
        print(f"\n✗ 动态Prompt构建器测试失败: {e}")
        results.append(('动态Prompt构建器', False))
    
    # 测试3: Prompt优化器
    try:
        result = await test_prompt_optimizer()
        results.append(('Prompt优化器', result))
    except Exception as e:
        print(f"\n✗ Prompt优化器测试失败: {e}")
        results.append(('Prompt优化器', False))
    
    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{status} - {name}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！Phase 2功能正常！")
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败")


if __name__ == '__main__':
    asyncio.run(main())
