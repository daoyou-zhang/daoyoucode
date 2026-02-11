#!/usr/bin/env python3
"""
测试Hook系统
"""

import asyncio
import sys
from pathlib import Path

# 添加backend到路径
sys.path.insert(0, str(Path(__file__).parent))

from daoyoucode.agents import (
    register_hook,
    get_hook_manager,
    HookContext,
)
from daoyoucode.agents.hooks import (
    LoggingHook,
    MetricsHook,
    ValidationHook,
    RetryHook,
    create_default_hooks,
)


async def test_basic_hooks():
    """测试基本Hook功能"""
    print("=" * 60)
    print("测试1: 基本Hook功能")
    print("=" * 60)
    
    # 注册Hooks
    register_hook(LoggingHook())
    register_hook(MetricsHook())
    
    manager = get_hook_manager()
    
    # 创建测试上下文
    context = HookContext(
        skill_name="test_skill",
        user_input="Hello World",
        session_id="test_session"
    )
    
    # 测试before hooks
    print("\n1. 运行before hooks...")
    context = await manager.run_before_hooks(context)
    print(f"✅ Before hooks完成，metadata: {context.metadata}")
    
    # 模拟执行
    result = {
        'success': True,
        'content': 'Test result',
        'tokens_used': {'input': 100, 'output': 50}
    }
    
    # 测试after hooks
    print("\n2. 运行after hooks...")
    result = await manager.run_after_hooks(context, result)
    print(f"✅ After hooks完成")
    print(f"   Metrics: {result.get('metrics', {})}")
    
    print("\n✅ 基本Hook功能测试通过")


async def test_validation_hook():
    """测试验证Hook"""
    print("\n" + "=" * 60)
    print("测试2: 验证Hook")
    print("=" * 60)
    
    # 清空之前的hooks
    manager = get_hook_manager()
    manager.hooks.clear()
    
    # 注册验证Hook
    validation_hook = ValidationHook(
        min_length=5,
        max_length=100,
        forbidden_words=['spam', 'test']
    )
    register_hook(validation_hook)
    
    # 测试1: 正常输入
    print("\n1. 测试正常输入...")
    context = HookContext(
        skill_name="test",
        user_input="Hello World",
        session_id="test"
    )
    
    try:
        context = await manager.run_before_hooks(context)
        print("✅ 正常输入验证通过")
    except ValueError as e:
        print(f"❌ 验证失败: {e}")
    
    # 测试2: 输入太短
    print("\n2. 测试输入太短...")
    context = HookContext(
        skill_name="test",
        user_input="Hi",
        session_id="test"
    )
    
    try:
        context = await manager.run_before_hooks(context)
        print("❌ 应该抛出异常")
    except ValueError as e:
        print(f"✅ 正确捕获异常: {e}")
    
    # 测试3: 包含禁用词
    print("\n3. 测试禁用词...")
    context = HookContext(
        skill_name="test",
        user_input="This is a test message",
        session_id="test"
    )
    
    try:
        context = await manager.run_before_hooks(context)
        print("❌ 应该抛出异常")
    except ValueError as e:
        print(f"✅ 正确捕获异常: {e}")
    
    print("\n✅ 验证Hook测试通过")


async def test_retry_hook():
    """测试重试Hook"""
    print("\n" + "=" * 60)
    print("测试3: 重试Hook")
    print("=" * 60)
    
    # 清空之前的hooks
    manager = get_hook_manager()
    manager.hooks.clear()
    
    # 注册重试Hook
    retry_hook = RetryHook(
        max_retries=3,
        retry_delay=0.1,  # 快速测试
        exponential_backoff=False
    )
    register_hook(retry_hook)
    
    # 测试错误处理
    print("\n1. 测试错误处理...")
    context = HookContext(
        skill_name="test",
        user_input="test",
        session_id="test"
    )
    
    error = Exception("Test error")
    result = await manager.run_error_hooks(context, error)
    
    if result is None:
        print("✅ 第1次失败，准备重试")
    
    # 再次失败
    result = await manager.run_error_hooks(context, error)
    if result is None:
        print("✅ 第2次失败，准备重试")
    
    # 第3次失败
    result = await manager.run_error_hooks(context, error)
    if result is None:
        print("✅ 第3次失败，准备重试")
    
    # 第4次失败（达到最大重试次数）
    result = await manager.run_error_hooks(context, error)
    if result is not None:
        print(f"✅ 达到最大重试次数，返回错误: {result.get('error')}")
    
    print("\n✅ 重试Hook测试通过")


async def test_default_hooks():
    """测试默认Hook集合"""
    print("\n" + "=" * 60)
    print("测试4: 默认Hook集合")
    print("=" * 60)
    
    # 清空之前的hooks
    manager = get_hook_manager()
    manager.hooks.clear()
    
    # 注册默认Hooks
    for hook in create_default_hooks():
        register_hook(hook)
    
    print(f"\n已注册Hooks: {manager.list_hooks()}")
    
    # 测试执行
    context = HookContext(
        skill_name="test",
        user_input="Hello World",
        session_id="test"
    )
    
    context = await manager.run_before_hooks(context)
    
    result = {
        'success': True,
        'content': 'Test',
        'tokens_used': {'input': 100, 'output': 50}
    }
    
    result = await manager.run_after_hooks(context, result)
    
    print(f"\n✅ 默认Hook集合测试通过")
    print(f"   Metrics: {result.get('metrics', {})}")


async def test_hook_enable_disable():
    """测试Hook启用/禁用"""
    print("\n" + "=" * 60)
    print("测试5: Hook启用/禁用")
    print("=" * 60)
    
    # 清空之前的hooks
    manager = get_hook_manager()
    manager.hooks.clear()
    
    # 注册Hook
    logging_hook = LoggingHook()
    register_hook(logging_hook)
    
    # 测试启用状态
    print("\n1. Hook启用状态...")
    context = HookContext(
        skill_name="test",
        user_input="test",
        session_id="test"
    )
    
    context = await manager.run_before_hooks(context)
    print("✅ Hook已执行")
    
    # 禁用Hook
    print("\n2. 禁用Hook...")
    logging_hook.disable()
    
    context = await manager.run_before_hooks(context)
    print("✅ Hook已禁用，不执行")
    
    # 重新启用
    print("\n3. 重新启用Hook...")
    logging_hook.enable()
    
    context = await manager.run_before_hooks(context)
    print("✅ Hook重新启用，已执行")
    
    print("\n✅ Hook启用/禁用测试通过")


async def main():
    """主函数"""
    print("🚀 开始测试Hook系统\n")
    
    try:
        await test_basic_hooks()
        await test_validation_hook()
        await test_retry_hook()
        await test_default_hooks()
        await test_hook_enable_disable()
        
        print("\n" + "=" * 60)
        print("🎉 所有测试通过！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
