"""
测试超时恢复策略
"""

import asyncio
import logging
from daoyoucode.agents.core.timeout_recovery import (
    TimeoutRecoveryStrategy,
    TimeoutRecoveryConfig,
    get_user_friendly_timeout_message
)
from daoyoucode.agents.llm.exceptions import LLMTimeoutError

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


# 模拟函数
async def mock_llm_call_always_timeout():
    """模拟总是超时的 LLM 调用"""
    await asyncio.sleep(0.1)
    raise LLMTimeoutError("模拟超时")


async def mock_llm_call_timeout_then_success(attempt_count: list):
    """模拟前几次超时，最后成功的 LLM 调用"""
    attempt_count[0] += 1
    
    if attempt_count[0] < 3:
        await asyncio.sleep(0.1)
        raise LLMTimeoutError(f"模拟超时（第 {attempt_count[0]} 次）")
    
    return {"success": True, "content": "成功响应"}


async def test_timeout_recovery_all_fail():
    """测试所有重试都失败的情况"""
    print("\n" + "="*60)
    print("测试1: 所有重试都失败")
    print("="*60)
    
    config = TimeoutRecoveryConfig(
        max_retries=3,
        initial_timeout=60.0,
        retry_delay=0.5  # 缩短延迟以加快测试
    )
    
    strategy = TimeoutRecoveryStrategy(config)
    
    try:
        result = await strategy.execute_with_timeout_recovery(
            mock_llm_call_always_timeout
        )
        print("❌ 测试失败：应该抛出 LLMTimeoutError")
    except LLMTimeoutError as e:
        print(f"✅ 测试通过：正确抛出超时错误")
        print(f"   错误消息: {e}")
        print(f"   重试次数: {strategy.retry_count}")
        
        # 测试用户友好消息
        friendly_message = get_user_friendly_timeout_message(strategy.retry_count)
        print(f"\n用户友好消息:\n{friendly_message}")


async def test_timeout_recovery_eventually_success():
    """测试最终成功的情况"""
    print("\n" + "="*60)
    print("测试2: 前几次超时，最后成功")
    print("="*60)
    
    config = TimeoutRecoveryConfig(
        max_retries=3,
        initial_timeout=60.0,
        retry_delay=0.5
    )
    
    strategy = TimeoutRecoveryStrategy(config)
    attempt_count = [0]
    
    try:
        result = await strategy.execute_with_timeout_recovery(
            mock_llm_call_timeout_then_success,
            attempt_count
        )
        print(f"✅ 测试通过：最终成功")
        print(f"   结果: {result}")
        print(f"   总尝试次数: {attempt_count[0]}")
        print(f"   重试次数: {strategy.retry_count}")
    except LLMTimeoutError as e:
        print(f"❌ 测试失败：不应该抛出错误")
        print(f"   错误: {e}")


async def test_prompt_simplification():
    """测试 prompt 简化"""
    print("\n" + "="*60)
    print("测试3: Prompt 简化")
    print("="*60)
    
    strategy = TimeoutRecoveryStrategy()
    
    # 创建一个长 prompt
    long_prompt = "\n".join([f"Line {i}: Some content here" for i in range(100)])
    print(f"原始 prompt 长度: {len(long_prompt)} 字符, {len(long_prompt.split(chr(10)))} 行")
    
    # 简化
    simplified = strategy._simplify_prompt(long_prompt)
    print(f"简化后 prompt 长度: {len(simplified)} 字符, {len(simplified.split(chr(10)))} 行")
    print(f"压缩率: {(1 - len(simplified) / len(long_prompt)) * 100:.1f}%")
    
    # 短 prompt 不应该被简化
    short_prompt = "\n".join([f"Line {i}" for i in range(30)])
    simplified_short = strategy._simplify_prompt(short_prompt)
    
    if simplified_short == short_prompt:
        print("✅ 短 prompt 不被简化")
    else:
        print("❌ 短 prompt 被错误简化")


async def test_fallback_model():
    """测试备用模型"""
    print("\n" + "="*60)
    print("测试4: 备用模型")
    print("="*60)
    
    strategy = TimeoutRecoveryStrategy()
    
    test_cases = [
        ('qwen-max', 'qwen-plus'),
        ('qwen-plus', 'qwen-turbo'),
        ('gpt-4', 'gpt-3.5-turbo'),
        ('deepseek-coder', 'deepseek-chat'),
        ('unknown-model', None),
    ]
    
    for original, expected in test_cases:
        fallback = strategy._get_fallback_model(original)
        if fallback == expected:
            print(f"✅ {original} → {fallback}")
        else:
            print(f"❌ {original} → {fallback} (期望: {expected})")


async def test_recovery_strategy_application():
    """测试恢复策略应用"""
    print("\n" + "="*60)
    print("测试5: 恢复策略应用")
    print("="*60)
    
    config = TimeoutRecoveryConfig(
        initial_timeout=60.0,
        timeout_multiplier=1.5,
        max_timeout=180.0,
        enable_prompt_simplification=True,
        enable_fallback_model=True
    )
    
    strategy = TimeoutRecoveryStrategy(config)
    
    # 创建测试上下文
    context = {
        'prompt': "\n".join([f"Line {i}" for i in range(100)]),
        'model': 'qwen-max',
        'timeout': 60.0
    }
    
    original_prompt = context['prompt']
    original_model = context['model']
    
    # 测试第1次尝试
    print("\n第1次尝试:")
    strategy._apply_recovery_strategy(1, context, original_prompt, original_model)
    print(f"  超时: {context['timeout']}秒")
    print(f"  Prompt 长度: {len(context['prompt'])} 字符")
    print(f"  模型: {context['model']}")
    
    # 测试第3次尝试（应该简化 prompt）
    print("\n第3次尝试:")
    strategy._apply_recovery_strategy(3, context, original_prompt, original_model)
    print(f"  超时: {context['timeout']}秒")
    print(f"  Prompt 长度: {len(context['prompt'])} 字符")
    print(f"  模型: {context['model']}")
    
    # 测试第4次尝试（应该切换模型）
    print("\n第4次尝试:")
    strategy._apply_recovery_strategy(4, context, original_prompt, original_model)
    print(f"  超时: {context['timeout']}秒")
    print(f"  Prompt 长度: {len(context['prompt'])} 字符")
    print(f"  模型: {context['model']}")


async def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("超时恢复策略测试")
    print("="*60)
    
    await test_timeout_recovery_all_fail()
    await test_timeout_recovery_eventually_success()
    await test_prompt_simplification()
    await test_fallback_model()
    await test_recovery_strategy_application()
    
    print("\n" + "="*60)
    print("所有测试完成")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
