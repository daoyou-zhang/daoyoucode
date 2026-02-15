#!/usr/bin/env python3
"""
测试3阶段项目理解功能

阶段1: discover_project_docs（文档层）
阶段2: get_repo_structure（结构层）
阶段3: repo_map（代码层）
"""

import asyncio
from pathlib import Path
from daoyoucode.agents.tools import get_tool_registry


async def test_stage1_docs():
    """测试阶段1: 文档层"""
    print("=" * 60)
    print("阶段1: 文档层 - discover_project_docs")
    print("=" * 60)
    
    registry = get_tool_registry()
    
    result = await registry.execute_tool(
        "discover_project_docs",
        repo_path="."
    )
    
    if result.success:
        print(f"\n✓ 文档发现成功")
        print(f"  - 文档数量: {result.metadata.get('doc_count')}")
        print(f"  - 文档类型: {result.metadata.get('doc_types')}")
        
        # 显示前500字符
        content = result.content[:500] if result.content else ""
        print(f"\n内容预览:")
        print("-" * 60)
        print(content)
        print("...")
        print("-" * 60)
        
        return True
    else:
        print(f"✗ 文档发现失败: {result.error}")
        return False


async def test_stage2_structure():
    """测试阶段2: 结构层"""
    print("\n" + "=" * 60)
    print("阶段2: 结构层 - get_repo_structure")
    print("=" * 60)
    
    registry = get_tool_registry()
    
    result = await registry.execute_tool(
        "get_repo_structure",
        repo_path=".",
        annotate=True,
        max_depth=3,
        show_files=False  # 只显示目录
    )
    
    if result.success:
        print(f"\n✓ 结构获取成功")
        print(f"  - 是否添加注释: {result.metadata.get('annotate')}")
        print(f"  - 最大深度: {result.metadata.get('max_depth')}")
        
        # 显示前30行
        lines = result.content.split('\n')[:30]
        print(f"\n目录结构预览:")
        print("-" * 60)
        print('\n'.join(lines))
        print("...")
        print("-" * 60)
        
        return True
    else:
        print(f"✗ 结构获取失败: {result.error}")
        return False


async def test_stage3_code():
    """测试阶段3: 代码层"""
    print("\n" + "=" * 60)
    print("阶段3: 代码层 - repo_map")
    print("=" * 60)
    
    registry = get_tool_registry()
    
    result = await registry.execute_tool(
        "repo_map",
        repo_path=".",
        chat_files=[],  # 无chat_files，自动扩大到6000
        max_tokens=3000
    )
    
    if result.success:
        print(f"\n✓ 代码地图生成成功")
        print(f"  - 原始max_tokens: {result.metadata.get('original_max_tokens')}")
        print(f"  - 实际max_tokens: {result.metadata.get('max_tokens')}")
        print(f"  - 是否自动调整: {result.metadata.get('auto_scaled')}")
        print(f"  - 文件数量: {result.metadata.get('file_count')}")
        
        # 显示前20行
        lines = result.content.split('\n')[:20]
        print(f"\n代码地图预览:")
        print("-" * 60)
        print('\n'.join(lines))
        print("...")
        print("-" * 60)
        
        return True
    else:
        print(f"✗ 代码地图生成失败: {result.error}")
        return False


async def test_full_workflow():
    """测试完整的3阶段工作流"""
    print("\n" + "=" * 60)
    print("完整工作流测试")
    print("=" * 60)
    
    registry = get_tool_registry()
    
    total_tokens = 0
    
    # 阶段1: 文档
    print("\n[1/3] 获取项目文档...")
    result1 = await registry.execute_tool(
        "discover_project_docs",
        repo_path="."
    )
    if result1.success:
        doc_tokens = len(result1.content) // 4  # 粗略估算
        total_tokens += doc_tokens
        print(f"✓ 文档层完成 (~{doc_tokens} tokens)")
    
    # 阶段2: 结构
    print("\n[2/3] 获取目录结构...")
    result2 = await registry.execute_tool(
        "get_repo_structure",
        repo_path=".",
        annotate=True,
        max_depth=3
    )
    if result2.success:
        struct_tokens = len(result2.content) // 4  # 粗略估算
        total_tokens += struct_tokens
        print(f"✓ 结构层完成 (~{struct_tokens} tokens)")
    
    # 阶段3: 代码
    print("\n[3/3] 生成代码地图...")
    result3 = await registry.execute_tool(
        "repo_map",
        repo_path=".",
        chat_files=[],
        max_tokens=3000
    )
    if result3.success:
        code_tokens = result3.metadata.get('max_tokens', 0)
        total_tokens += code_tokens
        print(f"✓ 代码层完成 (~{code_tokens} tokens)")
    
    # 总结
    print("\n" + "=" * 60)
    print("工作流总结")
    print("=" * 60)
    print(f"总token消耗: ~{total_tokens} tokens")
    print(f"阶段1（文档）: ~{doc_tokens} tokens")
    print(f"阶段2（结构）: ~{struct_tokens} tokens")
    print(f"阶段3（代码）: ~{code_tokens} tokens")
    
    if total_tokens < 10000:
        print(f"\n✅ Token消耗合理（< 10000）")
        return True
    else:
        print(f"\n⚠️ Token消耗较高（> 10000）")
        return False


async def main():
    print("测试3阶段项目理解功能\n")
    
    results = []
    
    # 测试阶段1
    try:
        results.append(("阶段1: 文档层", await test_stage1_docs()))
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("阶段1: 文档层", False))
    
    # 测试阶段2
    try:
        results.append(("阶段2: 结构层", await test_stage2_structure()))
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        results.append(("阶段2: 结构层", False))
    
    # 测试阶段3
    try:
        results.append(("阶段3: 代码层", await test_stage3_code()))
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        results.append(("阶段3: 代码层", False))
    
    # 测试完整工作流
    try:
        results.append(("完整工作流", await test_full_workflow()))
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        results.append(("完整工作流", False))
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{status}: {name}")
    
    all_passed = all(r[1] for r in results)
    
    if all_passed:
        print("\n🎉 所有测试通过！3阶段项目理解功能正常")
        print("\n功能说明：")
        print("- 阶段1: 自动发现并读取项目文档（README、架构文档等）")
        print("- 阶段2: 获取带注释的目录结构")
        print("- 阶段3: 生成智能代码地图（自动扩大token预算）")
        print("- 总成本: ~7500 tokens（可控）")
        return 0
    else:
        print("\n❌ 部分测试失败")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
