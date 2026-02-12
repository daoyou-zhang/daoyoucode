"""
测试ContextManager
"""

import asyncio
from daoyoucode.agents.core.context import get_context_manager


def test_context_basic():
    """测试基本上下文操作"""
    print("\n=== 测试1: 基本上下文操作 ===")
    
    manager = get_context_manager()
    
    # 创建上下文
    ctx = manager.create_context('session1')
    
    # 设置变量
    ctx.set('user_name', 'Alice')
    ctx.set('user_age', 25)
    ctx.set('user_role', 'developer')
    
    print(f"✓ 设置了3个变量")
    
    # 获取变量
    assert ctx.get('user_name') == 'Alice'
    assert ctx.get('user_age') == 25
    assert ctx.get('user_role') == 'developer'
    print(f"✓ 变量获取正确")
    
    # 检查存在
    assert ctx.has('user_name')
    assert not ctx.has('non_existent')
    print(f"✓ 存在性检查正确")
    
    # 更新变量
    ctx.set('user_age', 26)
    assert ctx.get('user_age') == 26
    print(f"✓ 变量更新成功")
    
    # 删除变量
    ctx.delete('user_role')
    assert not ctx.has('user_role')
    print(f"✓ 变量删除成功")


def test_context_snapshot():
    """测试快照和回滚"""
    print("\n=== 测试2: 快照和回滚 ===")
    
    manager = get_context_manager()
    ctx = manager.create_context('session2')
    
    # 初始状态
    ctx.set('counter', 0)
    ctx.set('status', 'init')
    
    # 创建快照1
    snapshot1 = ctx.create_snapshot('初始状态')
    print(f"✓ 创建快照1: {snapshot1[:8]}...")
    
    # 修改状态
    ctx.set('counter', 10)
    ctx.set('status', 'running')
    ctx.set('new_field', 'value')
    
    assert ctx.get('counter') == 10
    assert ctx.get('status') == 'running'
    print(f"✓ 修改了状态")
    
    # 创建快照2
    snapshot2 = ctx.create_snapshot('运行状态')
    print(f"✓ 创建快照2: {snapshot2[:8]}...")
    
    # 继续修改
    ctx.set('counter', 20)
    ctx.set('status', 'completed')
    
    # 回滚到快照1
    success = ctx.rollback_to_snapshot(snapshot1)
    assert success
    assert ctx.get('counter') == 0
    assert ctx.get('status') == 'init'
    assert not ctx.has('new_field')
    print(f"✓ 回滚到快照1成功")
    
    # 列出快照
    snapshots = ctx.list_snapshots()
    print(f"✓ 共有 {len(snapshots)} 个快照")
    assert len(snapshots) == 2


def test_context_history():
    """测试变更历史"""
    print("\n=== 测试3: 变更历史 ===")
    
    manager = get_context_manager()
    ctx = manager.create_context('session3')
    
    # 执行一系列操作
    ctx.set('x', 1)
    ctx.set('y', 2)
    ctx.set('x', 10)  # 更新
    ctx.delete('y')   # 删除
    ctx.set('z', 3)
    
    # 获取历史
    history = ctx.get_history()
    print(f"✓ 共有 {len(history)} 条变更记录")
    assert len(history) == 5
    
    # 检查操作类型
    operations = [h['operation'] for h in history]
    assert 'set' in operations
    assert 'update' in operations
    assert 'delete' in operations
    print(f"✓ 操作类型: {set(operations)}")
    
    # 获取特定变量的历史
    x_history = ctx.get_changes_for_key('x')
    print(f"✓ 变量x的变更: {len(x_history)} 次")
    assert len(x_history) == 2  # set + update


def test_nested_context():
    """测试嵌套上下文"""
    print("\n=== 测试4: 嵌套上下文 ===")
    
    manager = get_context_manager()
    
    # 创建父上下文
    parent = manager.create_context('parent')
    parent.set('global_var', 'global_value')
    parent.set('parent_var', 'parent_value')
    
    # 创建子上下文
    child = parent.create_child()
    child.set('child_var', 'child_value')
    child.set('parent_var', 'overridden')  # 覆盖父变量
    
    # 子上下文可以访问父变量
    assert child.get('global_var') == 'global_value'
    print(f"✓ 子上下文可以访问父变量")
    
    # 子上下文覆盖父变量
    assert child.get('parent_var') == 'overridden'
    assert parent.get('parent_var') == 'parent_value'
    print(f"✓ 子上下文可以覆盖父变量")
    
    # 子上下文的变量不影响父上下文
    assert not parent.has('child_var')
    print(f"✓ 子变量不影响父上下文")
    
    # keys包含父上下文的key
    child_keys = child.keys()
    assert 'global_var' in child_keys
    assert 'parent_var' in child_keys
    assert 'child_var' in child_keys
    print(f"✓ 子上下文keys包含父变量")


def test_batch_operations():
    """测试批量操作"""
    print("\n=== 测试5: 批量操作 ===")
    
    manager = get_context_manager()
    ctx = manager.create_context('session5')
    
    # 批量更新
    ctx.update({
        'var1': 'value1',
        'var2': 'value2',
        'var3': 'value3'
    })
    
    assert ctx.get('var1') == 'value1'
    assert ctx.get('var2') == 'value2'
    assert ctx.get('var3') == 'value3'
    print(f"✓ 批量更新成功")
    
    # 转换为字典
    ctx_dict = ctx.to_dict()
    assert len(ctx_dict) == 3
    print(f"✓ 转换为字典: {len(ctx_dict)} 个变量")
    
    # 清空
    ctx.clear()
    assert len(ctx.keys()) == 0
    print(f"✓ 清空成功")


def test_context_manager():
    """测试上下文管理器"""
    print("\n=== 测试6: 上下文管理器 ===")
    
    manager = get_context_manager()
    
    # 创建多个上下文
    ctx1 = manager.create_context('session_a')
    ctx2 = manager.create_context('session_b')
    ctx3 = manager.create_context('session_c')
    
    ctx1.set('name', 'Alice')
    ctx2.set('name', 'Bob')
    ctx3.set('name', 'Charlie')
    
    # 获取上下文
    retrieved = manager.get_context('session_b')
    assert retrieved.get('name') == 'Bob'
    print(f"✓ 获取上下文成功")
    
    # 列出所有上下文
    contexts = manager.list_contexts()
    print(f"✓ 共有 {len(contexts)} 个上下文")
    
    # 获取或创建
    ctx4 = manager.get_or_create_context('session_d')
    assert ctx4 is not None
    print(f"✓ 获取或创建成功")
    
    # 删除上下文
    manager.delete_context('session_a')
    assert manager.get_context('session_a') is None
    print(f"✓ 删除上下文成功")
    
    # 统计信息
    stats = manager.get_stats()
    print(f"✓ 统计信息:")
    print(f"  总上下文数: {stats['total_contexts']}")
    print(f"  总变量数: {stats['total_variables']}")


def test_snapshot_limit():
    """测试快照数量限制"""
    print("\n=== 测试7: 快照数量限制 ===")
    
    manager = get_context_manager()
    ctx = manager.create_context('session7')
    
    # 创建超过限制的快照
    for i in range(15):
        ctx.set('counter', i)
        ctx.create_snapshot(f'快照{i}')
    
    snapshots = ctx.list_snapshots()
    print(f"✓ 快照数量: {len(snapshots)} (限制: {ctx.max_snapshots})")
    assert len(snapshots) == ctx.max_snapshots


def test_singleton():
    """测试单例模式"""
    print("\n=== 测试8: 单例模式 ===")
    
    manager1 = get_context_manager()
    manager2 = get_context_manager()
    
    print(f"✓ manager1 is manager2: {manager1 is manager2}")
    assert manager1 is manager2
    
    # 在manager1创建上下文
    ctx = manager1.create_context('singleton_test')
    ctx.set('test', 'value')
    
    # 在manager2应该能看到
    ctx2 = manager2.get_context('singleton_test')
    assert ctx2 is not None
    assert ctx2.get('test') == 'value'
    print(f"✓ 单例模式工作正常")


def main():
    """运行所有测试"""
    print("=" * 60)
    print("ContextManager 测试")
    print("=" * 60)
    
    try:
        test_context_basic()
        test_context_snapshot()
        test_context_history()
        test_nested_context()
        test_batch_operations()
        test_context_manager()
        test_snapshot_limit()
        test_singleton()
        
        print("\n" + "=" * 60)
        print("✓ 所有测试通过！")
        print("=" * 60)
    
    except AssertionError as e:
        print(f"\n✗ 测试失败: {e}")
        raise
    except Exception as e:
        print(f"\n✗ 测试错误: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
