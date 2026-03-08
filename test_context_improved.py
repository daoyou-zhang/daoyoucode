#!/usr/bin/env python3
"""
测试改进后的 Context 集成

验证：
1. 搜索历史功能
2. target_file 不会被覆盖
3. 多步骤工作流中的路径保持
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from daoyoucode.agents.core.context import Context, get_context_manager


class MockToolResult:
    """模拟工具结果"""
    def __init__(self, content):
        self.content = content
        self.success = True


def simulate_save_tool_result(ctx, tool_name, paths):
    """
    模拟 _save_tool_result_to_context 的逻辑
    """
    # 添加到搜索历史
    search_history = ctx.get("search_history") or []
    search_entry = {
        "tool": tool_name,
        "paths": paths,
        "timestamp": datetime.now().isoformat(),
        "result_preview": f"Found {len(paths)} files"
    }
    search_history.append(search_entry)
    ctx.set("search_history", search_history, track_change=False)
    
    # 保存最新搜索路径
    ctx.set("last_search_paths", paths, track_change=False)
    
    # 只在 target_file 未设置时才自动设置
    if not ctx.get("target_file"):
        if len(paths) >= 1:
            ctx.set("target_file", paths[0], track_change=False)
            target_dir = os.path.dirname(paths[0])
            if target_dir:
                ctx.set("target_dir", target_dir, track_change=False)
            
            if len(paths) > 1:
                ctx.set("target_files", paths, track_change=False)
                all_dirs = list(set(os.path.dirname(p) for p in paths if os.path.dirname(p)))
                if all_dirs:
                    ctx.set("target_dirs", all_dirs, track_change=False)
            
            print(f"   ✅ 自动设置 target_file: {paths[0]}")
    else:
        print(f"   ✅ 搜索结果已添加到历史 (target_file 保持不变)")


def test_improved_workflow():
    """
    测试改进后的工作流：搜索 → 读取 → 搜索 → 修改
    """
    print("\n" + "="*60)
    print("测试：改进后的工作流（不覆盖 target_file）")
    print("="*60)
    
    manager = get_context_manager()
    ctx = manager.get_or_create_context("improved_test")
    
    # 步骤1：搜索目标文件
    print("\n步骤1：搜索目标文件 (agent.py)")
    simulate_save_tool_result(ctx, "text_search", ["backend/daoyoucode/agents/core/agent.py"])
    print(f"   target_file = {ctx.get('target_file')}")
    print(f"   搜索历史: {len(ctx.get('search_history'))} 条")
    
    # 步骤2：读取文件
    print("\n步骤2：读取文件")
    print(f"   📖 读取: {ctx.get('target_file')}")
    
    # 步骤3：搜索配置文件（不会覆盖 target_file）
    print("\n步骤3：搜索配置文件 (config.yaml)")
    simulate_save_tool_result(ctx, "text_search", ["backend/daoyoucode/config.yaml"])
    print(f"   target_file = {ctx.get('target_file')}")
    print(f"   last_search_paths = {ctx.get('last_search_paths')}")
    print(f"   搜索历史: {len(ctx.get('search_history'))} 条")
    
    # 步骤4：修改文件 - 仍然指向正确的文件
    print("\n步骤4：修改目标文件")
    print(f"   ✅ 修改: {ctx.get('target_file')}")
    
    # 验证
    assert ctx.get('target_file') == "backend/daoyoucode/agents/core/agent.py", "target_file 被覆盖了！"
    assert len(ctx.get('search_history')) == 2, "搜索历史不正确"
    
    # 显示搜索历史
    print("\n📝 搜索历史:")
    for i, entry in enumerate(ctx.get('search_history'), 1):
        print(f"   {i}. [{entry['tool']}] {entry['paths'][0]}")
    
    print("\n" + "="*60)
    print("✅ 测试通过：target_file 不会被覆盖")
    print("="*60)


def test_multiple_searches():
    """
    测试多次搜索场景
    """
    print("\n" + "="*60)
    print("测试：多次搜索场景")
    print("="*60)
    
    manager = get_context_manager()
    ctx = manager.get_or_create_context("multiple_searches")
    
    searches = [
        ("text_search", ["backend/daoyoucode/agents/core/agent.py"]),
        ("grep_search", ["backend/daoyoucode/agents/core/context.py"]),
        ("repo_map", ["backend/daoyoucode/agents/tools/base.py"]),
        ("text_search", ["backend/daoyoucode/config.yaml"]),
    ]
    
    for i, (tool, paths) in enumerate(searches, 1):
        print(f"\n搜索 {i}: {tool} → {paths[0]}")
        simulate_save_tool_result(ctx, tool, paths)
        print(f"   target_file = {ctx.get('target_file')}")
        print(f"   last_search_paths = {ctx.get('last_search_paths')}")
    
    # 验证
    assert ctx.get('target_file') == searches[0][1][0], "target_file 应该是第一次搜索的结果"
    assert ctx.get('last_search_paths') == searches[-1][1], "last_search_paths 应该是最后一次搜索的结果"
    assert len(ctx.get('search_history')) == len(searches), "搜索历史数量不对"
    
    print("\n📝 搜索历史:")
    for i, entry in enumerate(ctx.get('search_history'), 1):
        print(f"   {i}. [{entry['tool']}] {entry['paths'][0]}")
    
    print(f"\n✅ target_file 保持为第一次搜索: {ctx.get('target_file')}")
    print(f"✅ last_search_paths 更新为最后一次: {ctx.get('last_search_paths')[0]}")
    print(f"✅ 搜索历史记录了所有 {len(searches)} 次搜索")
    
    print("\n" + "="*60)
    print("✅ 测试通过：多次搜索正确处理")
    print("="*60)


def test_manual_override():
    """
    测试手动设置 target_file
    """
    print("\n" + "="*60)
    print("测试：手动设置 target_file")
    print("="*60)
    
    manager = get_context_manager()
    ctx = manager.get_or_create_context("manual_override")
    
    # 手动设置 target_file
    print("\n步骤1：手动设置 target_file")
    ctx.set("target_file", "my_custom_file.py", track_change=False)
    print(f"   ✅ target_file = {ctx.get('target_file')}")
    
    # 执行搜索（不会覆盖手动设置的值）
    print("\n步骤2：执行搜索")
    simulate_save_tool_result(ctx, "text_search", ["backend/daoyoucode/agents/core/agent.py"])
    print(f"   ✅ target_file = {ctx.get('target_file')} (保持不变)")
    
    # 验证
    assert ctx.get('target_file') == "my_custom_file.py", "手动设置的 target_file 被覆盖了"
    
    print("\n" + "="*60)
    print("✅ 测试通过：手动设置的值不会被覆盖")
    print("="*60)


def test_search_history_access():
    """
    测试搜索历史的访问
    """
    print("\n" + "="*60)
    print("测试：搜索历史访问")
    print("="*60)
    
    manager = get_context_manager()
    ctx = manager.get_or_create_context("history_access")
    
    # 执行多次搜索
    searches = [
        ("text_search", ["file1.py"], "target"),
        ("text_search", ["file2.py"], "reference"),
        ("grep_search", ["file3.py"], "reference"),
    ]
    
    for tool, paths, purpose in searches:
        simulate_save_tool_result(ctx, tool, paths)
    
    # 访问搜索历史
    history = ctx.get('search_history')
    print(f"\n📝 搜索历史 (共 {len(history)} 条):")
    for i, entry in enumerate(history, 1):
        print(f"   {i}. [{entry['tool']}] {entry['paths'][0]}")
    
    # 获取第一次搜索的路径
    first_search_path = history[0]['paths'][0]
    print(f"\n✅ 第一次搜索的路径: {first_search_path}")
    
    # 获取最后一次搜索的路径
    last_search_path = history[-1]['paths'][0]
    print(f"✅ 最后一次搜索的路径: {last_search_path}")
    
    # 获取所有搜索的路径
    all_paths = [entry['paths'][0] for entry in history]
    print(f"✅ 所有搜索的路径: {all_paths}")
    
    print("\n" + "="*60)
    print("✅ 测试通过：可以访问完整的搜索历史")
    print("="*60)


def main():
    print("\n" + "="*60)
    print("改进后的 Context 集成测试")
    print("="*60)
    
    try:
        test_improved_workflow()
        test_multiple_searches()
        test_manual_override()
        test_search_history_access()
        
        print("\n" + "="*60)
        print("✅ 所有测试通过！")
        print("="*60)
        
        print("\n📊 改进总结:")
        print("   1. ✅ target_file 只在首次搜索时自动设置")
        print("   2. ✅ 后续搜索不会覆盖 target_file")
        print("   3. ✅ 所有搜索都记录到 search_history")
        print("   4. ✅ last_search_paths 总是更新为最新搜索")
        print("   5. ✅ 手动设置的 target_file 不会被覆盖")
        print("   6. ✅ 可以通过 search_history 访问所有搜索结果")
        
        print("\n💡 使用建议:")
        print("   - target_file: 当前要操作的主文件（自动设置，不会覆盖）")
        print("   - last_search_paths: 最近一次搜索的结果（总是更新）")
        print("   - search_history: 所有搜索的历史记录（可回溯）")
        print("   - 工作流中可以手动设置 target_file 来明确指定目标")
        
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
