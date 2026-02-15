"""
测试IntelligentRouter
"""

import asyncio
from daoyoucode.agents.core.router import get_intelligent_router


async def test_exploration_task():
    """测试探索任务路由"""
    print("\n=== 测试1: 探索任务 ===")
    
    router = get_intelligent_router()
    
    decision = await router.route("查找所有Python文件中的函数定义")
    
    print(f"✓ 用户输入: 查找所有Python文件中的函数定义")
    print(f"  编排器: {decision.orchestrator}")
    print(f"  Agent: {decision.agent}")
    print(f"  置信度: {decision.confidence:.2f}")
    print(f"  理由: {decision.reasoning}")
    
    assert decision.orchestrator == "parallel_explore"
    assert decision.agent == "code_analyzer"


async def test_workflow_task():
    """测试工作流任务路由"""
    print("\n=== 测试2: 工作流任务 ===")
    
    router = get_intelligent_router()
    
    decision = await router.route(
        "先分析代码结构，然后生成重构计划，最后执行重构"
    )
    
    print(f"✓ 用户输入: 先分析代码结构，然后生成重构计划，最后执行重构")
    print(f"  编排器: {decision.orchestrator}")
    print(f"  Agent: {decision.agent}")
    print(f"  置信度: {decision.confidence:.2f}")
    print(f"  理由: {decision.reasoning}")
    
    assert decision.orchestrator == "workflow"


async def test_conditional_task():
    """测试条件任务路由"""
    print("\n=== 测试3: 条件任务 ===")
    
    router = get_intelligent_router()
    
    decision = await router.route(
        "如果代码有bug就修复，否则进行优化"
    )
    
    print(f"✓ 用户输入: 如果代码有bug就修复，否则进行优化")
    print(f"  编排器: {decision.orchestrator}")
    print(f"  Agent: {decision.agent}")
    print(f"  置信度: {decision.confidence:.2f}")
    print(f"  理由: {decision.reasoning}")
    
    assert decision.orchestrator == "conditional"


async def test_debate_task():
    """测试辩论任务路由"""
    print("\n=== 测试4: 辩论任务 ===")
    
    router = get_intelligent_router()
    
    decision = await router.route(
        "从多角度讨论这个设计方案的优缺点"
    )
    
    print(f"✓ 用户输入: 从多角度讨论这个设计方案的优缺点")
    print(f"  编排器: {decision.orchestrator}")
    print(f"  Agent: {decision.agent}")
    print(f"  置信度: {decision.confidence:.2f}")
    print(f"  理由: {decision.reasoning}")
    
    assert decision.orchestrator == "multi_agent"


async def test_parallel_task():
    """测试并行任务路由"""
    print("\n=== 测试5: 并行任务 ===")
    
    router = get_intelligent_router()
    
    decision = await router.route(
        "批量处理所有测试文件"
    )
    
    print(f"✓ 用户输入: 批量处理所有测试文件")
    print(f"  编排器: {decision.orchestrator}")
    print(f"  Agent: {decision.agent}")
    print(f"  置信度: {decision.confidence:.2f}")
    print(f"  理由: {decision.reasoning}")
    
    # 可能是parallel或parallel_explore
    assert decision.orchestrator in ["parallel", "parallel_explore"]


async def test_simple_task():
    """测试简单任务路由"""
    print("\n=== 测试6: 简单任务 ===")
    
    router = get_intelligent_router()
    
    decision = await router.route("生成一个Hello World函数")
    
    print(f"✓ 用户输入: 生成一个Hello World函数")
    print(f"  编排器: {decision.orchestrator}")
    print(f"  Agent: {decision.agent}")
    print(f"  置信度: {decision.confidence:.2f}")
    print(f"  理由: {decision.reasoning}")
    
    assert decision.orchestrator == "simple"
    assert decision.agent == "code_writer"


async def test_agent_selection():
    """测试Agent选择"""
    print("\n=== 测试7: Agent选择 ===")
    
    router = get_intelligent_router()
    
    test_cases = [
        ("分析代码结构", "code_analyzer"),
        ("编写测试用例", "test_writer"),
        ("生成API文档", "doc_writer"),
        ("修复这个bug", "debugger"),
        ("重构这段代码", "code_reviewer"),
    ]
    
    for user_input, expected_agent in test_cases:
        decision = await router.route(user_input)
        print(f"✓ '{user_input}' -> {decision.agent}")
        assert decision.agent == expected_agent


async def test_complexity_calculation():
    """测试复杂度计算"""
    print("\n=== 测试8: 复杂度计算 ===")
    
    router = get_intelligent_router()
    
    test_cases = [
        ("简单任务", 1),
        ("先做A，然后做B，最后做C", 2),
        ("如果条件满足，就执行步骤1、步骤2、步骤3，否则执行步骤4、步骤5", 3),
    ]
    
    for user_input, min_complexity in test_cases:
        decision = await router.route(user_input)
        features = router._extract_features(user_input, {})
        print(f"✓ '{user_input[:30]}...' -> 复杂度: {features.complexity}")
        assert features.complexity >= min_complexity


async def test_alternatives():
    """测试备选方案"""
    print("\n=== 测试9: 备选方案 ===")
    
    router = get_intelligent_router()
    
    decision = await router.route("查找并分析所有Python文件")
    
    print(f"✓ 最优方案: {decision.orchestrator} (置信度: {decision.confidence:.2f})")
    print(f"  备选方案:")
    
    for alt_orch, alt_score in decision.alternatives[:3]:
        print(f"    - {alt_orch}: {alt_score:.2f}")
    
    assert len(decision.alternatives) > 0


async def test_singleton():
    """测试单例模式"""
    print("\n=== 测试10: 单例模式 ===")
    
    router1 = get_intelligent_router()
    router2 = get_intelligent_router()
    
    print(f"✓ router1 is router2: {router1 is router2}")
    assert router1 is router2


async def main():
    """运行所有测试"""
    print("=" * 60)
    print("IntelligentRouter 测试")
    print("=" * 60)
    
    try:
        await test_exploration_task()
        await test_workflow_task()
        await test_conditional_task()
        await test_debate_task()
        await test_parallel_task()
        await test_simple_task()
        await test_agent_selection()
        await test_complexity_calculation()
        await test_alternatives()
        await test_singleton()
        
        print("\n" + "=" * 60)
        print("✓ 所有测试通过！")
        print("=" * 60)
    
    except AssertionError as e:
        print(f"\n✗ 测试失败: {e}")
        raise
    except Exception as e:
        print(f"\n✗ 测试错误: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
