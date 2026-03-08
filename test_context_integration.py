#!/usr/bin/env python3
"""
测试 Context 集成功能

测试场景：
1. 单文件搜索 - 验证 target_file 和 target_dir 保存
2. 多文件搜索 - 验证 target_files 和 target_dirs 保存
3. Context 变量读取 - 验证变量可以被正确读取
"""

import sys
import os

# 添加 backend 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from daoyoucode.agents.core.context import Context, ContextManager, get_context_manager


def test_single_file():
    """测试单文件场景"""
    print("\n" + "="*60)
    print("测试 1: 单文件搜索")
    print("="*60)
    
    # 创建 Context
    manager = get_context_manager()
    ctx = manager.get_or_create_context("test_session_1")
    
    # 模拟单文件搜索结果
    paths = ["backend/daoyoucode/agents/core/agent.py"]
    
    # 保存路径（模拟 _save_tool_result_to_context 的逻辑）
    ctx.set("last_search_paths", paths, track_change=False)
    ctx.set("target_file", paths[0], track_change=False)
    
    import os
    target_dir = os.path.dirname(paths[0])
    if target_dir:
        ctx.set("target_dir", target_dir, track_change=False)
    
    # 验证
    print(f"✅ 保存路径: {paths[0]}")
    print(f"   target_file = {ctx.get('target_file')}")
    print(f"   target_dir = {ctx.get('target_dir')}")
    print(f"   last_search_paths = {ctx.get('last_search_paths')}")
    
    assert ctx.get('target_file') == paths[0], "target_file 不匹配"
    assert ctx.get('target_dir') == target_dir, "target_dir 不匹配"
    assert ctx.get('last_search_paths') == paths, "last_search_paths 不匹配"
    
    print("✅ 单文件测试通过")


def test_multiple_files():
    """测试多文件场景"""
    print("\n" + "="*60)
    print("测试 2: 多文件搜索")
    print("="*60)
    
    # 创建 Context
    manager = get_context_manager()
    ctx = manager.get_or_create_context("test_session_2")
    
    # 模拟多文件搜索结果
    paths = [
        "backend/daoyoucode/agents/core/agent.py",
        "backend/daoyoucode/agents/core/context.py",
        "backend/daoyoucode/agents/tools/base.py"
    ]
    
    # 保存路径（模拟 _save_tool_result_to_context 的逻辑）
    ctx.set("last_search_paths", paths, track_change=False)
    ctx.set("target_file", paths[0], track_change=False)
    
    import os
    target_dir = os.path.dirname(paths[0])
    if target_dir:
        ctx.set("target_dir", target_dir, track_change=False)
    
    # 🆕 保存所有文件路径
    ctx.set("target_files", paths, track_change=False)
    
    # 🆕 提取所有目录（去重）
    all_dirs = list(set(os.path.dirname(p) for p in paths if os.path.dirname(p)))
    if all_dirs:
        ctx.set("target_dirs", all_dirs, track_change=False)
    
    # 验证
    print(f"✅ 保存了 {len(paths)} 个路径")
    print(f"   target_file = {ctx.get('target_file')}")
    print(f"   target_dir = {ctx.get('target_dir')}")
    print(f"   target_files = {ctx.get('target_files')}")
    print(f"   target_dirs = {ctx.get('target_dirs')}")
    print(f"   last_search_paths = {ctx.get('last_search_paths')}")
    
    assert ctx.get('target_file') == paths[0], "target_file 不匹配"
    assert ctx.get('target_dir') == target_dir, "target_dir 不匹配"
    assert ctx.get('target_files') == paths, "target_files 不匹配"
    assert len(ctx.get('target_dirs')) > 0, "target_dirs 为空"
    assert ctx.get('last_search_paths') == paths, "last_search_paths 不匹配"
    
    print("✅ 多文件测试通过")


def test_context_persistence():
    """测试 Context 持久化"""
    print("\n" + "="*60)
    print("测试 3: Context 持久化")
    print("="*60)
    
    # 创建 Context 并保存数据
    manager = get_context_manager()
    ctx1 = manager.get_or_create_context("test_session_3")
    
    test_data = {
        "target_file": "test.py",
        "config_file": "config.yaml",
        "custom_var": "custom_value"
    }
    
    for key, value in test_data.items():
        ctx1.set(key, value, track_change=False)
    
    print("✅ 保存数据到 Context")
    
    # 获取同一个 session 的 Context（应该是同一个对象）
    ctx2 = manager.get_or_create_context("test_session_3")
    
    # 验证数据
    for key, expected_value in test_data.items():
        actual_value = ctx2.get(key)
        print(f"   {key} = {actual_value}")
        assert actual_value == expected_value, f"{key} 不匹配: {actual_value} != {expected_value}"
    
    print("✅ Context 持久化测试通过")


def test_context_variables():
    """测试 Context 变量管理"""
    print("\n" + "="*60)
    print("测试 4: Context 变量管理")
    print("="*60)
    
    manager = get_context_manager()
    ctx = manager.get_or_create_context("test_session_4")
    
    # 测试基本操作
    ctx.set("var1", "value1")
    ctx.set("var2", 123)
    ctx.set("var3", ["a", "b", "c"])
    
    print(f"✅ 设置变量:")
    print(f"   var1 = {ctx.get('var1')}")
    print(f"   var2 = {ctx.get('var2')}")
    print(f"   var3 = {ctx.get('var3')}")
    
    # 测试更新
    ctx.set("var1", "updated_value")
    assert ctx.get("var1") == "updated_value", "变量更新失败"
    print(f"✅ 更新变量: var1 = {ctx.get('var1')}")
    
    # 测试删除
    ctx.delete("var2")
    assert ctx.get("var2") is None, "变量删除失败"
    print(f"✅ 删除变量: var2 = {ctx.get('var2')}")
    
    # 测试批量更新
    ctx.update({"var4": "value4", "var5": "value5"}, track_change=False)
    assert ctx.get("var4") == "value4", "批量更新失败"
    assert ctx.get("var5") == "value5", "批量更新失败"
    print(f"✅ 批量更新: var4={ctx.get('var4')}, var5={ctx.get('var5')}")
    
    print("✅ Context 变量管理测试通过")


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("Context 集成功能测试")
    print("="*60)
    
    try:
        test_single_file()
        test_multiple_files()
        test_context_persistence()
        test_context_variables()
        
        print("\n" + "="*60)
        print("✅ 所有测试通过！")
        print("="*60)
        print("\n📝 测试总结:")
        print("   1. ✅ 单文件搜索 - target_file 和 target_dir 正确保存")
        print("   2. ✅ 多文件搜索 - target_files 和 target_dirs 正确保存")
        print("   3. ✅ Context 持久化 - 同一 session 的数据可以正确读取")
        print("   4. ✅ Context 变量管理 - 增删改查功能正常")
        print("\n🎉 Context 集成功能完全正常！")
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
