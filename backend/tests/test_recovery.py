"""
测试失败恢复系统
"""

import asyncio
import sys
import os

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from daoyoucode.agents.core.recovery import (
    RecoveryManager,
    RecoveryConfig,
    MaxRetriesExceeded,
    validate_non_empty,
    validate_success_flag,
    validate_no_error,
    simple_analyzer
)


# 测试函数
class TestFunction:
    """测试函数类"""
    
    def __init__(self):
        self.call_count = 0
    
    async def success_on_first(self, user_input: str) -> dict:
        """第一次就成功"""
        self.call_count += 1
        return {'success': True, 'content': f'处理: {user_input}'}
    
    async def success_on_third(self, user_input: str) -> dict:
        """第三次才成功"""
        self.call_count += 1
        if self.call_count < 3:
            raise ValueError(f"模拟错误 (第{self.call_count}次)")
        return {'success': True, 'content': f'处理: {user_input}'}
    
    async def always_fail(self, user_input: str) -> dict:
        """总是失败"""
        self.call_count += 1
        raise ValueError(f"总是失败 (第{self.call_count}次)")
    
    async def invalid_result(self, user_input: str) -> dict:
        """返回无效结果"""
        self.call_count += 1
        if self.call_count < 2:
            return {'success': False, 'content': ''}
        return {'success': True, 'content': f'修复后: {user_input}'}


async def test_basic_recovery():
    """测试基本恢复功能"""
    print("\n" + "="*60)
    print("测试1: 基本恢复功能")
    print("="*60)
    
    # 1. 第一次就成功
    print("\n1. 测试第一次就成功...")
    test_func = TestFunction()
    manager = RecoveryManager()
    
    result = await manager.execute_with_recovery(
        test_func.success_on_first,
        user_input="测试输入"
    )
    
    print(f"   结果: {result}")
    print(f"   调用次数: {test_func.call_count}")
    assert test_func.call_count == 1, "应该只调用1次"
    assert result['success'], "应该成功"
    print("   ✅ 通过")
    
    # 2. 第三次才成功
    print("\n2. 测试第三次才成功...")
    test_func = TestFunction()
    manager = RecoveryManager(RecoveryConfig(max_retries=5))
    
    result = await manager.execute_with_recovery(
        test_func.success_on_third,
        user_input="测试输入"
    )
    
    print(f"   结果: {result}")
    print(f"   调用次数: {test_func.call_count}")
    assert test_func.call_count == 3, "应该调用3次"
    assert result['success'], "应该成功"
    print("   ✅ 通过")
    
    # 3. 总是失败
    print("\n3. 测试总是失败...")
    test_func = TestFunction()
    manager = RecoveryManager(RecoveryConfig(max_retries=3))
    
    try:
        result = await manager.execute_with_recovery(
            test_func.always_fail,
            user_input="测试输入"
        )
        print("   ❌ 应该抛出异常")
        assert False, "应该抛出MaxRetriesExceeded"
    except MaxRetriesExceeded as e:
        print(f"   正确抛出异常: {e}")
        print(f"   调用次数: {test_func.call_count}")
        assert test_func.call_count == 3, "应该调用3次"
        print("   ✅ 通过")
    
    print("\n✅ 基本恢复功能测试通过")


async def test_validators():
    """测试验证器"""
    print("\n" + "="*60)
    print("测试2: 验证器")
    print("="*60)
    
    # 1. validate_non_empty
    print("\n1. 测试 validate_non_empty...")
    assert validate_non_empty({'content': 'test'}), "有内容应该通过"
    assert not validate_non_empty({'content': ''}), "空内容应该失败"
    assert not validate_non_empty({}), "空字典应该失败"
    print("   ✅ 通过")
    
    # 2. validate_success_flag
    print("\n2. 测试 validate_success_flag...")
    assert validate_success_flag({'success': True}), "success=True应该通过"
    assert not validate_success_flag({'success': False}), "success=False应该失败"
    assert not validate_success_flag({}), "无success应该失败"
    print("   ✅ 通过")
    
    # 3. validate_no_error
    print("\n3. 测试 validate_no_error...")
    assert validate_no_error({'content': 'test'}), "无error应该通过"
    assert not validate_no_error({'error': 'test'}), "有error应该失败"
    print("   ✅ 通过")
    
    print("\n✅ 验证器测试通过")


async def test_with_validator():
    """测试带验证器的恢复"""
    print("\n" + "="*60)
    print("测试3: 带验证器的恢复")
    print("="*60)
    
    print("\n1. 测试无效结果自动修复...")
    test_func = TestFunction()
    manager = RecoveryManager(RecoveryConfig(max_retries=5))
    
    result = await manager.execute_with_recovery(
        test_func.invalid_result,
        user_input="测试输入",
        validator=validate_success_flag,
        analyzer=simple_analyzer
    )
    
    print(f"   结果: {result}")
    print(f"   调用次数: {test_func.call_count}")
    assert test_func.call_count == 2, "应该调用2次"
    assert result['success'], "应该成功"
    print("   ✅ 通过")
    
    print("\n✅ 带验证器的恢复测试通过")


async def test_history():
    """测试执行历史"""
    print("\n" + "="*60)
    print("测试4: 执行历史")
    print("="*60)
    
    test_func = TestFunction()
    manager = RecoveryManager(RecoveryConfig(max_retries=5))
    
    result = await manager.execute_with_recovery(
        test_func.success_on_third,
        user_input="测试输入"
    )
    
    history = manager.get_history()
    print(f"\n执行历史:")
    for record in history:
        print(f"   尝试 {record['attempt']}: {'成功' if record['success'] else '失败'}")
        if not record['success']:
            print(f"      错误: {record['error']}")
    
    assert len(history) == 3, "应该有3条历史记录"
    assert not history[0]['success'], "第1次应该失败"
    assert not history[1]['success'], "第2次应该失败"
    assert history[2]['success'], "第3次应该成功"
    print("\n✅ 执行历史测试通过")


async def test_retry_delay():
    """测试重试延迟"""
    print("\n" + "="*60)
    print("测试5: 重试延迟")
    print("="*60)
    
    import time
    
    test_func = TestFunction()
    manager = RecoveryManager(RecoveryConfig(
        max_retries=3,
        retry_delay=0.5
    ))
    
    start_time = time.time()
    
    try:
        await manager.execute_with_recovery(
            test_func.always_fail,
            user_input="测试输入"
        )
    except MaxRetriesExceeded:
        pass
    
    elapsed = time.time() - start_time
    
    print(f"\n总耗时: {elapsed:.2f}秒")
    # 3次尝试，2次延迟（第1次失败后延迟，第2次失败后延迟）
    assert elapsed >= 1.0, f"应该至少延迟1秒，实际: {elapsed:.2f}秒"
    print("✅ 重试延迟测试通过")


async def main():
    """运行所有测试"""
    print("🚀 开始测试失败恢复系统")
    
    try:
        await test_basic_recovery()
        await test_validators()
        await test_with_validator()
        await test_history()
        await test_retry_delay()
        
        print("\n" + "="*60)
        print("🎉 所有测试通过！")
        print("="*60)
    
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
