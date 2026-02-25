#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 RepoMap 缓存优化效果
"""

import asyncio
import time
import sys
import io
from pathlib import Path

# 设置标准输出编码为 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from daoyoucode.agents.tools.repomap_tools import RepoMapTool
from daoyoucode.agents.tools.base import ToolContext


async def test_repomap_cache():
    """测试 RepoMap 缓存"""
    
    print("=" * 80)
    print("RepoMap 缓存优化测试")
    print("=" * 80)
    print()
    
    # 创建工具实例
    tool = RepoMapTool()
    
    # 设置上下文
    context = ToolContext(
        repo_path=Path(".").resolve(),
        session_id="test",
        subtree_only=None
    )
    tool.set_context(context)
    
    # 测试参数
    repo_path = "."
    chat_files = []
    mentioned_idents = []
    max_tokens = 3000
    
    print("测试场景1：首次调用（冷启动）")
    print("-" * 80)
    start = time.time()
    result1 = await tool.execute(repo_path, chat_files, mentioned_idents, max_tokens, enable_lsp=False)
    time1 = time.time() - start
    print(f"✅ 首次调用完成: {time1:.2f}秒")
    print(f"   文件数: {result1.metadata.get('file_count', 0)}")
    print(f"   定义数: {result1.metadata.get('definition_count', 0)}")
    if 'cache_stats' in result1.metadata:
        stats = result1.metadata['cache_stats']
        print(f"   缓存统计: {stats}")
    print()
    
    print("测试场景2：重复调用（相同参数）")
    print("-" * 80)
    start = time.time()
    result2 = await tool.execute(repo_path, chat_files, mentioned_idents, max_tokens, enable_lsp=False)
    time2 = time.time() - start
    print(f"✅ 重复调用完成: {time2:.4f}秒")
    if time2 > 0:
        print(f"   性能提升: {time1 / time2:.0f}x")
    else:
        print(f"   性能提升: >10000x (太快了！)")
    if 'cache_stats' in result2.metadata:
        stats = result2.metadata['cache_stats']
        print(f"   缓存统计: {stats}")
    print()
    
    print("测试场景3：不同参数调用")
    print("-" * 80)
    start = time.time()
    result3 = await tool.execute(repo_path, ["backend/daoyoucode/agents/core/agent.py"], [], max_tokens, enable_lsp=False)
    time3 = time.time() - start
    print(f"✅ 不同参数调用完成: {time3:.4f}秒")
    if time3 > 0:
        print(f"   性能提升: {time1 / time3:.0f}x")
    else:
        print(f"   性能提升: >10000x (太快了！)")
    if 'cache_stats' in result3.metadata:
        stats = result3.metadata['cache_stats']
        print(f"   缓存统计: {stats}")
    print()
    
    print("测试场景4：再次重复调用（验证结果级缓存）")
    print("-" * 80)
    start = time.time()
    result4 = await tool.execute(repo_path, chat_files, mentioned_idents, max_tokens, enable_lsp=False)
    time4 = time.time() - start
    print(f"✅ 再次重复调用完成: {time4:.4f}秒")
    if time4 > 0:
        print(f"   性能提升: {time1 / time4:.0f}x")
    else:
        print(f"   性能提升: >10000x (太快了！)")
    if 'cache_stats' in result4.metadata:
        stats = result4.metadata['cache_stats']
        print(f"   缓存统计: {stats}")
    print()
    
    # 验证结果一致性
    print("验证结果一致性")
    print("-" * 80)
    if result1.content == result2.content:
        print("✅ 场景1和场景2结果一致")
    else:
        print("❌ 场景1和场景2结果不一致")
    
    if result2.content == result4.content:
        print("✅ 场景2和场景4结果一致")
    else:
        print("❌ 场景2和场景4结果不一致")
    print()
    
    # 总结
    print("=" * 80)
    print("测试总结")
    print("=" * 80)
    print(f"首次调用: {time1:.2f}秒")
    print(f"重复调用: {time2:.4f}秒 (提升 {time1 / time2:.0f}x)" if time2 > 0 else f"重复调用: {time2:.4f}秒 (提升 >10000x)")
    print(f"不同参数: {time3:.4f}秒 (提升 {time1 / time3:.0f}x)" if time3 > 0 else f"不同参数: {time3:.4f}秒 (提升 >10000x)")
    print(f"再次重复: {time4:.4f}秒 (提升 {time1 / time4:.0f}x)" if time4 > 0 else f"再次重复: {time4:.4f}秒 (提升 >10000x)")
    print()
    
    # 缓存统计
    cache_stats = tool.get_cache_stats()
    print("最终缓存统计:")
    print(f"  结果级缓存: {cache_stats['result_hits']}/{cache_stats['result_hits'] + cache_stats['result_misses']} "
          f"({cache_stats['result_hit_rate']:.0%})")
    print(f"  内存级缓存: {cache_stats['memory_hits']}/{cache_stats['memory_hits'] + cache_stats['memory_misses']} "
          f"({cache_stats['memory_hit_rate']:.0%})")
    print(f"  文件级缓存: {cache_stats['file_hits']}/{cache_stats['file_hits'] + cache_stats['file_misses']} "
          f"({cache_stats['file_hit_rate']:.0%})")
    print()
    
    # 预期效果
    print("预期效果:")
    print("  ✅ 重复调用应该 < 0.01秒 (结果级缓存)")
    print("  ✅ 不同参数应该 < 0.5秒 (内存级缓存)")
    print("  ✅ 文件级缓存命中率应该 > 90%")
    print()
    
    if time2 < 0.01:
        print("🎉 结果级缓存工作正常！")
    else:
        print("⚠️  结果级缓存可能未生效")
    
    if time3 < 0.5:
        print("🎉 内存级缓存工作正常！")
    else:
        print("⚠️  内存级缓存可能未生效")
    
    if cache_stats['file_hit_rate'] > 0.9:
        print("🎉 文件级缓存工作正常！")
    else:
        print("⚠️  文件级缓存命中率较低")


if __name__ == "__main__":
    asyncio.run(test_repomap_cache())
