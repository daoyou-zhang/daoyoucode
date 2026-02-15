"""
测试缓存层功能

验证缓存是否正常工作，以及性能提升效果
"""

import asyncio
import time
from daoyoucode.agents.core.cache import (
    SimpleCache, get_cache, get_namespaced_cache,
    get_profile_cache, get_summary_cache
)


def test_basic_cache():
    """测试基础缓存功能"""
    print("\n" + "="*60)
    print("测试：基础缓存功能")
    print("="*60)
    
    cache = SimpleCache(default_ttl=2)  # 2秒TTL
    
    # 1. 设置和获取
    print("\n1. 设置和获取")
    cache.set("key1", "value1")
    value = cache.get("key1")
    assert value == "value1", "获取失败"
    print(f"✓ 设置和获取成功: {value}")
    
    # 2. 缓存命中
    print("\n2. 缓存命中")
    value = cache.get("key1")
    assert value == "value1", "缓存命中失败"
    print(f"✓ 缓存命中: {value}")
    
    # 3. 缓存未命中
    print("\n3. 缓存未命中")
    value = cache.get("nonexistent", default="default_value")
    assert value == "default_value", "默认值失败"
    print(f"✓ 缓存未命中，返回默认值: {value}")
    
    # 4. TTL过期
    print("\n4. TTL过期")
    cache.set("key2", "value2", ttl=1)  # 1秒TTL
    print("等待2秒...")
    time.sleep(2)
    value = cache.get("key2", default="expired")
    assert value == "expired", "TTL过期失败"
    print(f"✓ TTL过期，返回默认值: {value}")
    
    # 5. 删除
    print("\n5. 删除")
    cache.set("key3", "value3")
    deleted = cache.delete("key3")
    assert deleted, "删除失败"
    value = cache.get("key3")
    assert value is None, "删除后仍能获取"
    print(f"✓ 删除成功")
    
    # 6. 统计信息
    print("\n6. 统计信息")
    stats = cache.get_stats()
    print(f"✓ 统计信息: {stats}")
    
    print("\n✅ 基础缓存功能测试通过")


def test_get_or_set():
    """测试get_or_set功能"""
    print("\n" + "="*60)
    print("测试：get_or_set功能")
    print("="*60)
    
    cache = SimpleCache()
    
    call_count = 0
    
    def expensive_function():
        nonlocal call_count
        call_count += 1
        print(f"  调用expensive_function (第{call_count}次)")
        time.sleep(0.1)  # 模拟耗时操作
        return "expensive_result"
    
    # 第1次调用（缓存未命中，执行函数）
    print("\n第1次调用（应该执行函数）:")
    start = time.time()
    result1 = cache.get_or_set("expensive_key", expensive_function)
    time1 = time.time() - start
    print(f"  结果: {result1}, 耗时: {time1*1000:.0f}ms")
    
    # 第2次调用（缓存命中，不执行函数）
    print("\n第2次调用（应该使用缓存）:")
    start = time.time()
    result2 = cache.get_or_set("expensive_key", expensive_function)
    time2 = time.time() - start
    print(f"  结果: {result2}, 耗时: {time2*1000:.0f}ms")
    
    assert result1 == result2, "结果不一致"
    assert call_count == 1, "函数被多次调用"
    assert time2 < time1 * 0.5, "缓存未生效"
    
    print(f"\n✅ get_or_set测试通过")
    print(f"   函数调用次数: {call_count}")
    if time2 > 0:
        print(f"   性能提升: {time1/time2:.1f}x")
    else:
        print(f"   性能提升: 极快（缓存命中时间<1ms）")


def test_namespaced_cache():
    """测试命名空间缓存"""
    print("\n" + "="*60)
    print("测试：命名空间缓存")
    print("="*60)
    
    cache1 = get_namespaced_cache("namespace1")
    cache2 = get_namespaced_cache("namespace2")
    
    # 设置相同的键，不同的命名空间
    cache1.set("key", "value1")
    cache2.set("key", "value2")
    
    # 获取应该返回不同的值
    value1 = cache1.get("key")
    value2 = cache2.get("key")
    
    print(f"namespace1:key = {value1}")
    print(f"namespace2:key = {value2}")
    
    assert value1 == "value1", "命名空间1值错误"
    assert value2 == "value2", "命名空间2值错误"
    
    print("\n✅ 命名空间缓存测试通过")


def test_cache_performance():
    """测试缓存性能提升"""
    print("\n" + "="*60)
    print("测试：缓存性能提升")
    print("="*60)
    
    cache = SimpleCache()
    
    # 模拟文件读取
    def read_file(filename):
        time.sleep(0.01)  # 模拟10ms的文件I/O
        return f"content of {filename}"
    
    files = [f"file{i}.txt" for i in range(10)]
    
    # 第1轮：无缓存（全部读取）
    print("\n第1轮：无缓存")
    start = time.time()
    for filename in files:
        content = read_file(filename)
    time_no_cache = time.time() - start
    print(f"  耗时: {time_no_cache*1000:.0f}ms")
    
    # 第2轮：有缓存（第1次读取）
    print("\n第2轮：有缓存（第1次读取）")
    start = time.time()
    for filename in files:
        content = cache.get_or_set(filename, lambda f=filename: read_file(f))
    time_first_cache = time.time() - start
    print(f"  耗时: {time_first_cache*1000:.0f}ms")
    
    # 第3轮：有缓存（第2次读取，全部命中）
    print("\n第3轮：有缓存（第2次读取，全部命中）")
    start = time.time()
    for filename in files:
        content = cache.get_or_set(filename, lambda f=filename: read_file(f))
    time_cached = time.time() - start
    print(f"  耗时: {time_cached*1000:.0f}ms")
    
    # 统计
    stats = cache.get_stats()
    print(f"\n缓存统计:")
    print(f"  命中率: {stats['hit_rate']}")
    print(f"  命中次数: {stats['hits']}")
    print(f"  未命中次数: {stats['misses']}")
    
    speedup = time_no_cache / time_cached if time_cached > 0 else float('inf')
    print(f"\n✅ 性能提升: {speedup:.1f}x" if speedup != float('inf') else "\n✅ 性能提升: 极快（>100x）")
    print(f"   无缓存: {time_no_cache*1000:.0f}ms")
    print(f"   有缓存: {time_cached*1000:.0f}ms")


def test_memory_integration():
    """测试Memory模块集成"""
    print("\n" + "="*60)
    print("测试：Memory模块集成")
    print("="*60)
    
    from daoyoucode.agents.memory import get_memory_manager
    
    memory = get_memory_manager()
    
    # 测试对话历史缓存
    print("\n1. 对话历史缓存")
    session_id = "test_session_cache"
    
    # 添加对话
    memory.add_conversation(
        session_id,
        "你好",
        "你好！有什么可以帮助你的吗？",
        user_id="test_user"
    )
    
    # 第1次获取（从存储）
    start = time.time()
    history1 = memory.get_conversation_history(session_id)
    time1 = time.time() - start
    print(f"  第1次获取: {time1*1000:.2f}ms")
    
    # 第2次获取（从缓存）
    start = time.time()
    history2 = memory.get_conversation_history(session_id)
    time2 = time.time() - start
    print(f"  第2次获取: {time2*1000:.2f}ms")
    
    assert len(history1) == len(history2), "历史不一致"
    if time1 > 0:
        speedup = time1 / time2 if time2 > 0 else float('inf')
        print(f"  性能提升: {speedup:.1f}x")
    
    # 测试用户偏好缓存
    print("\n2. 用户偏好缓存")
    user_id = "test_user_cache"
    
    # 设置偏好
    memory.remember_preference(user_id, "language", "python")
    
    # 第1次获取（从存储）
    start = time.time()
    prefs1 = memory.get_preferences(user_id)
    time1 = time.time() - start
    print(f"  第1次获取: {time1*1000:.2f}ms")
    
    # 第2次获取（从缓存）
    start = time.time()
    prefs2 = memory.get_preferences(user_id)
    time2 = time.time() - start
    print(f"  第2次获取: {time2*1000:.2f}ms")
    
    assert prefs1 == prefs2, "偏好不一致"
    if time1 > 0:
        speedup = time1 / time2 if time2 > 0 else float('inf')
        print(f"  性能提升: {speedup:.1f}x")
    
    print("\n✅ Memory模块集成测试通过")


def test_cache_stats():
    """测试缓存统计"""
    print("\n" + "="*60)
    print("测试：缓存统计")
    print("="*60)
    
    # 创建独立的缓存实例
    cache = SimpleCache()
    
    # 执行一些操作
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.get("key1")  # 命中
    cache.get("key1")  # 命中
    cache.get("key3")  # 未命中
    cache.delete("key2")
    
    # 获取统计
    stats = cache.get_stats()
    
    print("\n缓存统计:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    assert stats['hits'] == 2, f"命中次数错误: 期望2, 实际{stats['hits']}"
    assert stats['misses'] == 1, f"未命中次数错误: 期望1, 实际{stats['misses']}"
    assert stats['sets'] == 2, f"设置次数错误: 期望2, 实际{stats['sets']}"
    assert stats['deletes'] == 1, f"删除次数错误: 期望1, 实际{stats['deletes']}"
    
    print("\n✅ 缓存统计测试通过")


if __name__ == "__main__":
    print("="*60)
    print("缓存层功能测试套件")
    print("="*60)
    
    test_basic_cache()
    test_get_or_set()
    test_namespaced_cache()
    test_cache_performance()
    test_memory_integration()
    test_cache_stats()
    
    print("\n" + "="*60)
    print("✅ 所有测试完成")
    print("="*60)
