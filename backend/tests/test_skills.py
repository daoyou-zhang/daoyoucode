"""
测试不同的 Skill

测试场景：
1. programming - 编程任务
2. code-review - 代码审查
3. refactoring - 代码重构
4. testing - 测试生成
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# 设置 UTF-8 编码
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


async def test_skill(skill_name: str, test_case: dict):
    """测试单个 skill"""
    print(f"\n{'='*60}")
    print(f"测试 Skill: {skill_name}")
    print(f"{'='*60}")
    
    try:
        from daoyoucode.agents.init import initialize_agent_system
        from daoyoucode.agents.core.skill import load_skill
        
        # 初始化系统
        print("初始化 Agent 系统...")
        initialize_agent_system()
        
        # 加载 skill
        print(f"加载 skill: {skill_name}")
        skill_path = backend_dir.parent / "skills" / skill_name / "skill.yaml"
        
        if not skill_path.exists():
            print(f"❌ Skill 文件不存在: {skill_path}")
            return False
        
        skill = load_skill(str(skill_path))
        print(f"✅ Skill 加载成功")
        print(f"  描述: {skill.description}")
        print(f"  编排器: {skill.orchestrator}")
        print(f"  Agent: {skill.agent}")
        print(f"  工具数量: {len(skill.tools)}")
        
        # 验证配置
        print(f"\n验证配置...")
        print(f"  LLM 模型: {skill.llm_config.get('model', 'default')}")
        print(f"  温度: {skill.llm_config.get('temperature', 0.7)}")
        print(f"  最大 tokens: {skill.llm_config.get('max_tokens', 4000)}")
        
        # 验证工具
        print(f"\n验证工具...")
        from daoyoucode.agents.tools.registry import get_tool_registry
        registry = get_tool_registry()
        
        missing_tools = []
        for tool_name in skill.tools:
            if not registry.has_tool(tool_name):
                missing_tools.append(tool_name)
        
        if missing_tools:
            print(f"  ⚠️  缺失工具: {', '.join(missing_tools)}")
        else:
            print(f"  ✅ 所有工具都已注册")
        
        # 验证 prompt
        if skill.prompt_file:
            prompt_path = skill_path.parent / skill.prompt_file
            if prompt_path.exists():
                print(f"  ✅ Prompt 文件存在: {skill.prompt_file}")
            else:
                print(f"  ⚠️  Prompt 文件不存在: {skill.prompt_file}")
        
        print(f"\n✅ Skill '{skill_name}' 测试通过")
        return True
        
    except Exception as e:
        print(f"\n❌ Skill '{skill_name}' 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_all_skills():
    """测试所有 skill"""
    print("="*60)
    print("DaoyouCode Skill 测试")
    print("="*60)
    
    # 定义测试用例
    test_cases = {
        "programming": {
            "description": "编程任务",
            "input": "编写一个计算斐波那契数列的函数"
        },
        "code-review": {
            "description": "代码审查",
            "input": "审查 agent.py 文件"
        },
        "refactoring": {
            "description": "代码重构",
            "input": "重构这个函数，提高可读性"
        },
        "testing": {
            "description": "测试生成",
            "input": "为这个函数生成单元测试"
        },
        "chat-assistant": {
            "description": "对话助手",
            "input": "你好，请介绍一下你的功能"
        },
        "code-exploration": {
            "description": "代码探索",
            "input": "分析这个项目的架构"
        },
        "librarian": {
            "description": "文档管理",
            "input": "查找关于 Agent 的文档"
        },
        "oracle": {
            "description": "知识问答",
            "input": "什么是 LSP？"
        },
    }
    
    results = {}
    
    for skill_name, test_case in test_cases.items():
        success = await test_skill(skill_name, test_case)
        results[skill_name] = success
    
    # 打印总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"\n通过: {passed}/{total} ({passed/total*100:.1f}%)")
    print("\n详细结果:")
    
    for skill_name, success in results.items():
        status = "✅" if success else "❌"
        print(f"  {status} {skill_name}")
    
    return results


async def test_skill_execution(skill_name: str = "programming"):
    """测试 skill 实际执行（需要 LLM）"""
    print(f"\n{'='*60}")
    print(f"测试 Skill 执行: {skill_name}")
    print(f"{'='*60}")
    
    try:
        from daoyoucode.agents.init import initialize_agent_system
        from daoyoucode.agents.core.skill import load_skill
        from daoyoucode.agents.core.orchestrator import get_orchestrator
        
        # 初始化系统
        initialize_agent_system()
        
        # 加载 skill
        skill_path = backend_dir.parent / "skills" / skill_name / "skill.yaml"
        skill = load_skill(str(skill_path))
        
        # 获取编排器
        orchestrator = get_orchestrator(skill.orchestrator)
        
        print(f"✅ 编排器: {orchestrator.__class__.__name__}")
        
        # 准备输入
        user_input = "编写一个简单的 Hello World 函数"
        
        print(f"\n输入: {user_input}")
        print(f"\n开始执行...")
        
        # 执行（这会调用真实的 LLM）
        # 注意：这需要配置好的 API 密钥
        result = await orchestrator.execute(
            agent_name=skill.agent,
            user_input=user_input,
            tools=skill.tools,
            context={}
        )
        
        print(f"\n执行结果:")
        print(f"  成功: {result.get('success', False)}")
        print(f"  输出: {result.get('output', 'N/A')[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="测试 DaoyouCode Skills")
    parser.add_argument("--skill", help="测试特定 skill")
    parser.add_argument("--execute", action="store_true", help="测试实际执行（需要 LLM）")
    args = parser.parse_args()
    
    if args.skill:
        if args.execute:
            success = await test_skill_execution(args.skill)
        else:
            success = await test_skill(args.skill, {})
    else:
        results = await test_all_skills()
        success = all(results.values())
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
