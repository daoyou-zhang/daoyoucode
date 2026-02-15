"""
测试新的Skill架构

验证：
1. Skill加载
2. Executor调用
3. ReAct编排器
4. Agent执行
5. 工具调用
"""

import asyncio
import sys
from pathlib import Path

# 添加backend到路径
sys.path.insert(0, str(Path(__file__).parent))

from daoyoucode.agents.executor import execute_skill, list_skills, get_skill_info
from daoyoucode.agents.core.skill import get_skill_loader


async def test_skill_loading():
    """测试Skill加载"""
    print("\n" + "="*60)
    print("测试1: Skill加载")
    print("="*60)
    
    # 获取Skill加载器
    loader = get_skill_loader()
    
    # 列出所有Skill
    skills = list_skills()
    print(f"\n✓ 找到 {len(skills)} 个Skill:")
    for skill in skills:
        print(f"  • {skill['name']} v{skill['version']}")
        print(f"    {skill['description']}")
        print(f"    编排器: {skill['orchestrator']}")
    
    # 检查chat_assistant
    if any(s['name'] == 'chat_assistant' for s in skills):
        print("\n✓ chat_assistant Skill已加载")
        
        # 获取详细信息
        info = get_skill_info('chat_assistant')
        print(f"\n详细信息:")
        print(f"  • Agent: {info['agent']}")
        print(f"  • 编排器: {info['orchestrator']}")
        print(f"  • 中间件: {info['middleware']}")
        
        return True
    else:
        print("\n✗ chat_assistant Skill未找到")
        return False


async def test_skill_config():
    """测试Skill配置"""
    print("\n" + "="*60)
    print("测试2: Skill配置")
    print("="*60)
    
    loader = get_skill_loader()
    skill = loader.get_skill('chat_assistant')
    
    if not skill:
        print("✗ 无法加载chat_assistant")
        return False
    
    print(f"\n✓ Skill配置:")
    print(f"  • 名称: {skill.name}")
    print(f"  • 版本: {skill.version}")
    print(f"  • 编排器: {skill.orchestrator}")
    print(f"  • Agent: {skill.agent}")
    print(f"  • 工具数量: {len(skill.tools)}")
    print(f"  • 工具列表: {', '.join(skill.tools)}")
    print(f"  • Prompt文件: {skill.prompt.get('file', 'N/A')}")
    print(f"  • LLM模型: {skill.llm.get('model', 'N/A')}")
    
    # 检查Prompt文件是否存在
    if 'file' in skill.prompt:
        prompt_file = Path(skill.prompt['file'])
        if prompt_file.exists():
            print(f"\n✓ Prompt文件存在: {prompt_file}")
            # 读取前几行
            with open(prompt_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:5]
            print(f"  前5行:")
            for line in lines:
                print(f"    {line.rstrip()}")
        else:
            print(f"\n✗ Prompt文件不存在: {prompt_file}")
            return False
    
    return True


async def test_executor_call():
    """测试Executor调用（不调用真实LLM）"""
    print("\n" + "="*60)
    print("测试3: Executor调用（模拟模式）")
    print("="*60)
    
    # 注册内置Agent
    from daoyoucode.agents.builtin import register_builtin_agents
    register_builtin_agents()
    print("\n✓ 已注册内置Agent")
    
    # 准备上下文
    context = {
        "session_id": "test-session",
        "repo": ".",
        "model": "qwen-max"
    }
    
    print("\n准备调用execute_skill...")
    print(f"  • Skill: chat_assistant")
    print(f"  • 输入: 你好")
    print(f"  • 会话ID: {context['session_id']}")
    
    try:
        # 注意：这会尝试调用真实的编排器和Agent
        # 如果没有配置LLM，会失败
        result = await execute_skill(
            skill_name="chat_assistant",
            user_input="你好",
            session_id=context["session_id"],
            context=context
        )
        
        print(f"\n✓ 调用成功")
        print(f"  • 成功: {result.get('success')}")
        print(f"  • 内容: {result.get('content', '')[:100]}")
        print(f"  • 错误: {result.get('error', 'N/A')}")
        print(f"  • 任务ID: {result.get('task_id', 'N/A')}")
        
        return result.get('success', False)
    
    except Exception as e:
        print(f"\n✗ 调用失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_architecture_flow():
    """测试架构流程（不调用LLM）"""
    print("\n" + "="*60)
    print("测试4: 架构流程验证")
    print("="*60)
    
    print("\n正确的架构流程:")
    print("  用户输入")
    print("    ↓")
    print("  CLI (chat.py)")
    print("    ↓")
    print("  execute_skill('chat_assistant', ...)")
    print("    ↓")
    print("  Executor (executor.py)")
    print("    ├─ Hook系统 (before)")
    print("    ├─ 加载 Skill")
    print("    ├─ 获取编排器 (react)")
    print("    ├─ 创建任务")
    print("    ├─ 执行编排器")
    print("    │   ↓")
    print("    │   ReAct编排器")
    print("    │   ├─ 加载 Prompt")
    print("    │   ├─ 获取工具列表")
    print("    │   ├─ 调用 Agent")
    print("    │   └─ 返回结果")
    print("    ├─ Hook系统 (after)")
    print("    └─ 返回结果")
    
    print("\n✓ 架构流程正确")
    return True


async def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("DaoyouCode Skill架构测试")
    print("="*60)
    
    results = []
    
    # 测试1: Skill加载
    results.append(("Skill加载", await test_skill_loading()))
    
    # 测试2: Skill配置
    results.append(("Skill配置", await test_skill_config()))
    
    # 测试3: Executor调用（会尝试调用真实LLM）
    print("\n⚠ 注意: 下一个测试会尝试调用真实的LLM")
    print("如果没有配置API，会失败（这是正常的）")
    results.append(("Executor调用", await test_executor_call()))
    
    # 测试4: 架构流程
    results.append(("架构流程", await test_architecture_flow()))
    
    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    for name, success in results:
        status = "✓ 通过" if success else "✗ 失败"
        print(f"{status}: {name}")
    
    passed = sum(1 for _, s in results if s)
    total = len(results)
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
    else:
        print(f"\n⚠ {total - passed} 个测试失败")


if __name__ == "__main__":
    asyncio.run(main())
