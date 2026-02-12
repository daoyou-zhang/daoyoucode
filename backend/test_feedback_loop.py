"""
测试FeedbackLoop
"""

import asyncio
from daoyoucode.agents.core.feedback import get_feedback_loop


async def test_evaluate_success():
    """测试成功结果评估"""
    print("\n=== 测试1: 成功结果评估 ===")
    
    feedback = get_feedback_loop()
    
    result = {
        'success': True,
        'content': '这是一个详细的分析结果，包含了代码结构、潜在问题和改进建议。' * 10,
        'tokens_used': 800,
        'tools_used': ['file_reader', 'code_analyzer']
    }
    
    evaluation = await feedback.evaluate("分析代码结构", result)
    
    print(f"✓ 质量分数: {evaluation.quality_score:.2f}")
    print(f"  问题数: {len(evaluation.issues)}")
    print(f"  优点数: {len(evaluation.strengths)}")
    print(f"  建议数: {len(evaluation.suggestions)}")
    
    assert 0 <= evaluation.quality_score <= 1
    assert isinstance(evaluation.issues, list)
    assert isinstance(evaluation.strengths, list)


async def test_evaluate_failure():
    """测试失败结果评估"""
    print("\n=== 测试2: 失败结果评估 ===")
    
    feedback = get_feedback_loop()
    
    result = {
        'success': False,
        'content': '',
        'error': '执行超时',
        'tokens_used': 0
    }
    
    evaluation = await feedback.evaluate("复杂任务", result)
    
    print(f"✓ 质量分数: {evaluation.quality_score:.2f}")
    print(f"  识别的问题:")
    for issue in evaluation.issues:
        print(f"    - {issue}")
    
    assert evaluation.quality_score < 0.6  # 失败任务分数应该较低
    assert len(evaluation.issues) > 0


async def test_analyze_failure():
    """测试失败分析"""
    print("\n=== 测试3: 失败分析 ===")
    
    feedback = get_feedback_loop()
    
    error = Exception("Connection timeout: Failed to connect to API")
    
    analysis = await feedback.analyze_failure("调用API", error)
    
    print(f"✓ 错误类型: {analysis.error_type}")
    print(f"  根本原因: {analysis.root_cause}")
    print(f"  恢复建议:")
    for sug in analysis.recovery_suggestions:
        print(f"    - {sug}")
    
    assert analysis.error_type in ['timeout', 'network', 'unknown']
    assert len(analysis.recovery_suggestions) > 0


async def test_learning_stats():
    """测试学习统计"""
    print("\n=== 测试4: 学习统计 ===")
    
    feedback = get_feedback_loop()
    
    # 评估几个任务
    for i in range(5):
        result = {
            'success': i % 2 == 0,
            'content': f'结果{i}',
            'tokens_used': 500
        }
        await feedback.evaluate(f"任务{i}", result)
    
    stats = feedback.get_learning_stats()
    
    print(f"✓ 学习统计:")
    print(f"  总任务数: {stats['total_tasks']}")
    print(f"  成功率: {stats['success_rate']:.2%}")
    print(f"  平均质量: {stats['average_quality']:.2f}")
    
    assert stats['total_tasks'] > 0


async def main():
    """运行所有测试"""
    print("=" * 60)
    print("FeedbackLoop 测试")
    print("=" * 60)
    
    try:
        await test_evaluate_success()
        await test_evaluate_failure()
        await test_analyze_failure()
        await test_learning_stats()
        
        print("\n" + "=" * 60)
        print("✓ 所有测试通过！")
        print("=" * 60)
    
    except Exception as e:
        print(f"\n✗ 测试错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
