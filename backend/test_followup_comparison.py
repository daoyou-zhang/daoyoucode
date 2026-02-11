"""
追问判断能力对比测试
对比新旧实现的追问判断准确率
"""

import asyncio
from daoyoucode.llm.context import get_followup_detector


async def test_followup_detection():
    """测试追问判断能力"""
    
    detector = get_followup_detector()
    
    # 测试用例
    test_cases = [
        # (当前消息, 历史, 预期结果, 说明)
        ("继续", [{"user": "介绍Python", "ai": "Python是..."}], True, "明显追问标志"),
        ("还有吗？", [{"user": "Python特点", "ai": "简洁..."}], True, "追问标志+疑问"),
        ("详细说说", [{"user": "装饰器", "ai": "装饰器是..."}], True, "追问标志"),
        ("怎么用？", [{"user": "装饰器", "ai": "装饰器是..."}], True, "疑问词+话题相关"),
        
        ("换个话题", [{"user": "Python", "ai": "..."}], False, "新话题标志"),
        ("介绍Java", [{"user": "Python", "ai": "..."}], False, "完全不同话题"),
        ("重新开始", [{"user": "Python", "ai": "..."}], False, "新话题标志"),
        
        ("装饰器的例子", [{"user": "Python装饰器", "ai": "..."}], True, "关键词重叠"),
        ("函数参数怎么传", [{"user": "Python函数", "ai": "..."}], True, "关键词重叠"),
        
        ("好的", [{"user": "明白了吗", "ai": "..."}], True, "简单回应"),
        ("谢谢", [{"user": "帮助", "ai": "..."}], True, "简单回应"),
    ]
    
    print("=" * 80)
    print("追问判断能力测试")
    print("=" * 80)
    
    correct = 0
    total = len(test_cases)
    
    for message, history, expected, description in test_cases:
        is_followup, confidence, reason = await detector.is_followup(
            message, history
        )
        
        result = "✅" if is_followup == expected else "❌"
        correct += (is_followup == expected)
        
        print(f"\n{result} {description}")
        print(f"   消息: {message}")
        print(f"   预期: {'追问' if expected else '新话题'}")
        print(f"   实际: {'追问' if is_followup else '新话题'}")
        print(f"   置信度: {confidence:.2f}")
        print(f"   原因: {reason}")
    
    print("\n" + "=" * 80)
    print(f"准确率: {correct}/{total} = {correct/total*100:.1f}%")
    print("=" * 80)
    
    # 性能测试
    print("\n性能测试:")
    import time
    
    history = [{"user": "介绍Python", "ai": "Python是一种编程语言"}]
    message = "继续说"
    
    start = time.time()
    for _ in range(100):
        await detector.is_followup(message, history)
    elapsed = time.time() - start
    
    print(f"100次判断耗时: {elapsed*1000:.2f}ms")
    print(f"平均每次: {elapsed/100*1000:.2f}ms")
    print(f"{'✅ 性能优秀' if elapsed/100 < 0.005 else '⚠️ 性能需优化'}")


async def compare_with_old_approach():
    """对比旧方法（无追问判断）"""
    
    print("\n" + "=" * 80)
    print("与旧方法对比")
    print("=" * 80)
    
    # 模拟对话场景
    conversation = [
        ("介绍Python", False),  # 新话题
        ("继续", True),         # 追问
        ("还有吗", True),       # 追问
        ("换个话题，介绍Java", False),  # 新话题
        ("Java的特点", True),   # 追问
    ]
    
    print("\n旧方法（daoyouCodePilot）:")
    print("  - 无追问判断")
    print("  - 每次都发送完整上下文")
    print("  - 假设每次1000 tokens")
    old_total_tokens = len(conversation) * 1000
    print(f"  - 总tokens: {old_total_tokens}")
    
    print("\n新方法（LLM模块）:")
    print("  - 智能追问判断")
    print("  - 新话题: 1000 tokens")
    print("  - 追问: 300 tokens")
    
    new_total_tokens = 0
    for msg, is_followup in conversation:
        tokens = 300 if is_followup else 1000
        new_total_tokens += tokens
        print(f"  - '{msg}': {tokens} tokens ({'追问' if is_followup else '新话题'})")
    
    print(f"  - 总tokens: {new_total_tokens}")
    
    savings = (1 - new_total_tokens / old_total_tokens) * 100
    print(f"\n💰 节省: {savings:.1f}%")
    print(f"   旧方法: {old_total_tokens} tokens")
    print(f"   新方法: {new_total_tokens} tokens")
    print(f"   节省: {old_total_tokens - new_total_tokens} tokens")


if __name__ == "__main__":
    asyncio.run(test_followup_detection())
    asyncio.run(compare_with_old_approach())
