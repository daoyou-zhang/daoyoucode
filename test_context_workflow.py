#!/usr/bin/env python3
"""
测试 Context 在工作流中的使用场景

场景：搜索 → 读取 → 理解 → 修改
问题：中间如果调用了其他搜索工具，target_file 会被覆盖吗？
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from daoyoucode.agents.core.context import Context, get_context_manager


def test_workflow_scenario():
    """
    模拟真实工作流场景：
    1. 搜索目标文件（agent.py）
    2. 读取文件
    3. 搜索配置文件（config.yaml）- 这会覆盖 target_file 吗？
    4. 修改目标文件 - 还能找到 agent.py 吗？
    """
    print("\n" + "="*60)
    print("测试场景：工作流中的路径保持")
    print("="*60)
    
    manager = get_context_manager()
    ctx = manager.get_or_create_context("workflow_test")
    
    # 步骤1：搜索目标文件
    print("\n步骤1：搜索目标文件 (agent.py)")
    paths1 = ["backend/daoyoucode/agents/core/agent.py"]
    ctx.set("last_search_paths", paths1, track_change=False)
    ctx.set("target_file", paths1[0], track_change=False)
    ctx.set("target_dir", "backend/daoyoucode/agents/core", track_change=False)
    print(f"   ✅ target_file = {ctx.get('target_file')}")
    
    # 步骤2：读取文件（模拟 read_file 工具）
    print("\n步骤2：读取文件")
    print(f"   📖 读取: {ctx.get('target_file')}")
    
    # 步骤3：搜索配置文件（这会覆盖 target_file！）
    print("\n步骤3：搜索配置文件 (config.yaml)")
    paths2 = ["backend/daoyoucode/config.yaml"]
    ctx.set("last_search_paths", paths2, track_change=False)
    ctx.set("target_file", paths2[0], track_change=False)  # ❌ 覆盖了！
    ctx.set("target_dir", "backend/daoyoucode", track_change=False)
    print(f"   ⚠️  target_file = {ctx.get('target_file')}")
    print(f"   ❌ 问题：target_file 被覆盖了！")
    
    # 步骤4：修改文件 - 现在 target_file 指向错误的文件
    print("\n步骤4：修改文件")
    print(f"   ❌ 当前 target_file = {ctx.get('target_file')}")
    print(f"   ❌ 期望修改 agent.py，但实际会修改 config.yaml！")
    
    print("\n" + "="*60)
    print("❌ 测试结果：路径会被覆盖！")
    print("="*60)


def test_solution_with_history():
    """
    解决方案：使用历史记录保存所有搜索结果
    """
    print("\n" + "="*60)
    print("解决方案：使用搜索历史")
    print("="*60)
    
    manager = get_context_manager()
    ctx = manager.get_or_create_context("solution_test")
    
    # 初始化搜索历史
    search_history = []
    
    # 步骤1：搜索目标文件
    print("\n步骤1：搜索目标文件 (agent.py)")
    search1 = {
        "query": "agent.py",
        "paths": ["backend/daoyoucode/agents/core/agent.py"],
        "timestamp": "2024-01-01 10:00:00",
        "purpose": "target"  # 标记为目标文件
    }
    search_history.append(search1)
    ctx.set("search_history", search_history, track_change=False)
    ctx.set("target_file", search1["paths"][0], track_change=False)
    print(f"   ✅ target_file = {ctx.get('target_file')}")
    print(f"   ✅ 搜索历史: {len(search_history)} 条")
    
    # 步骤2：读取文件
    print("\n步骤2：读取文件")
    print(f"   📖 读取: {ctx.get('target_file')}")
    
    # 步骤3：搜索配置文件
    print("\n步骤3：搜索配置文件 (config.yaml)")
    search2 = {
        "query": "config.yaml",
        "paths": ["backend/daoyoucode/config.yaml"],
        "timestamp": "2024-01-01 10:01:00",
        "purpose": "reference"  # 标记为参考文件
    }
    search_history.append(search2)
    ctx.set("search_history", search_history, track_change=False)
    # 不覆盖 target_file！
    print(f"   ✅ target_file = {ctx.get('target_file')} (未被覆盖)")
    print(f"   ✅ 搜索历史: {len(search_history)} 条")
    
    # 步骤4：修改文件 - 仍然指向正确的文件
    print("\n步骤4：修改文件")
    print(f"   ✅ 当前 target_file = {ctx.get('target_file')}")
    print(f"   ✅ 正确！仍然指向 agent.py")
    
    # 显示搜索历史
    print("\n📝 搜索历史:")
    for i, search in enumerate(search_history, 1):
        print(f"   {i}. [{search['purpose']}] {search['query']} → {search['paths'][0]}")
    
    print("\n" + "="*60)
    print("✅ 解决方案有效：使用搜索历史保持路径")
    print("="*60)


def test_solution_with_explicit_vars():
    """
    解决方案2：使用明确的变量名
    """
    print("\n" + "="*60)
    print("解决方案2：使用明确的变量名")
    print("="*60)
    
    manager = get_context_manager()
    ctx = manager.get_or_create_context("explicit_vars_test")
    
    # 步骤1：搜索目标文件
    print("\n步骤1：搜索目标文件 (agent.py)")
    ctx.set("target_file", "backend/daoyoucode/agents/core/agent.py", track_change=False)
    ctx.set("target_dir", "backend/daoyoucode/agents/core", track_change=False)
    print(f"   ✅ target_file = {ctx.get('target_file')}")
    
    # 步骤2：读取文件
    print("\n步骤2：读取文件")
    print(f"   📖 读取: {ctx.get('target_file')}")
    
    # 步骤3：搜索配置文件 - 使用不同的变量名
    print("\n步骤3：搜索配置文件 (config.yaml)")
    ctx.set("config_file", "backend/daoyoucode/config.yaml", track_change=False)
    ctx.set("config_dir", "backend/daoyoucode", track_change=False)
    print(f"   ✅ config_file = {ctx.get('config_file')}")
    print(f"   ✅ target_file = {ctx.get('target_file')} (未被覆盖)")
    
    # 步骤4：修改文件
    print("\n步骤4：修改目标文件")
    print(f"   ✅ 修改: {ctx.get('target_file')}")
    
    print("\n步骤5：读取配置文件")
    print(f"   ✅ 读取: {ctx.get('config_file')}")
    
    print("\n" + "="*60)
    print("✅ 解决方案有效：使用明确的变量名")
    print("="*60)


def main():
    print("\n" + "="*60)
    print("Context 工作流场景测试")
    print("="*60)
    
    # 测试问题
    test_workflow_scenario()
    
    # 测试解决方案
    test_solution_with_history()
    test_solution_with_explicit_vars()
    
    print("\n" + "="*60)
    print("📊 测试总结")
    print("="*60)
    print("\n❌ 当前问题:")
    print("   - target_file 会被后续搜索覆盖")
    print("   - 无法在多步骤工作流中保持路径")
    
    print("\n✅ 解决方案:")
    print("   1. 使用搜索历史 (search_history)")
    print("      - 保存所有搜索结果")
    print("      - 标记每次搜索的目的 (target/reference)")
    print("      - 可以回溯查找")
    
    print("\n   2. 使用明确的变量名")
    print("      - target_file: 要修改的目标文件")
    print("      - config_file: 配置文件")
    print("      - reference_file: 参考文件")
    print("      - 避免变量覆盖")
    
    print("\n   3. 组合使用")
    print("      - 搜索历史记录所有搜索")
    print("      - 明确变量名标记重要文件")
    print("      - 工作流中明确指定使用哪个变量")


if __name__ == "__main__":
    main()
