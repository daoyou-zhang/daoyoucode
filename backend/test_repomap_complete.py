#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整测试 RepoMap 缓存优化（包括增量更新和缓存失效）
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


async def test_complete_cache():
    """完整测试缓存和增量更新"""
    
    print("=" * 80)
    print("RepoMap 完整测试（缓存 + 增量更新 + LSP）")
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
    max_tokens = 3000
    
    # ========== 测试1：首次调用 ==========
    print("测试1：首次调用（冷启动）")
    print("-" * 80)
    start = time.time()
    result1 = await tool.execute(repo_path, [], [], max_tokens, enable_lsp=False)
    time1 = time.time() - start
    print(f"✅ 首次调用: {time1:.2f}秒")
    print(f"   文件数: {result1.metadata.get('file_count', 0)}")
    print(f"   定义数: {result1.metadata.get('definition_count', 0)}")
    print(f"   LSP启用: {result1.metadata.get('lsp_enabled', False)}")
    stats = result1.metadata.get('cache_stats', {})
    print(f"   结果级缓存: {stats.get('result_hits', 0)}/{stats.get('result_hits', 0) + stats.get('result_misses', 0)}")
    print()
    
    # ========== 测试2：重复调用（结果级缓存） ==========
    print("测试2：重复调用（应该命中结果级缓存）")
    print("-" * 80)
    start = time.time()
    result2 = await tool.execute(repo_path, [], [], max_tokens, enable_lsp=False)
    time2 = time.time() - start
    print(f"✅ 重复调用: {time2:.4f}秒")
    if time2 > 0:
        print(f"   性能提升: {time1 / time2:.0f}x")
    else:
        print(f"   性能提升: >10000x")
    stats = result2.metadata.get('cache_stats', {})
    print(f"   结果级缓存: {stats.get('result_hits', 0)}/{stats.get('result_hits', 0) + stats.get('result_misses', 0)}")
    print()
    
    # ========== 测试3：模拟文件修改 ==========
    print("测试3：模拟文件修改（触发增量更新）")
    print("-" * 80)
    test_file = Path("backend/test_repomap_cache.py")
    original_content = None
    
    if test_file.exists():
        # 读取原始内容
        original_content = test_file.read_text(encoding='utf-8')
        # 添加注释（触发 mtime 改变）
        modified_content = original_content + "\n# Test modification for incremental update\n"
        test_file.write_text(modified_content, encoding='utf-8')
        print(f"✅ 修改文件: {test_file}")
        time.sleep(0.1)  # 确保 mtime 改变
    else:
        print("⚠️  测试文件不存在")
    print()
    
    # ========== 测试4：增量更新 ==========
    print("测试4：增量更新（应该只重新解析1个文件）")
    print("-" * 80)
    start = time.time()
    result3 = await tool.execute(repo_path, [], [], max_tokens, enable_lsp=False)
    time3 = time.time() - start
    print(f"✅ 增量更新: {time3:.2f}秒")
    print(f"   性能提升: {time1 / time3:.0f}x（相比首次调用）")
    stats = result3.metadata.get('cache_stats', {})
    print(f"   结果级缓存: {stats.get('result_hits', 0)}/{stats.get('result_hits', 0) + stats.get('result_misses', 0)}")
    print(f"   文件级缓存: {stats.get('file_hits', 0)}/{stats.get('file_hits', 0) + stats.get('file_misses', 0)}")
    print()
    
    # ========== 测试5：验证结果级缓存已失效 ==========
    print("测试5：再次调用（验证结果级缓存已失效并重新生成）")
    print("-" * 80)
    start = time.time()
    result4 = await tool.execute(repo_path, [], [], max_tokens, enable_lsp=False)
    time4 = time.time() - start
    print(f"✅ 再次调用: {time4:.4f}秒")
    if time4 > 0:
        print(f"   性能提升: {time1 / time4:.0f}x")
    else:
        print(f"   性能提升: >10000x")
    stats = result4.metadata.get('cache_stats', {})
    print(f"   结果级缓存: {stats.get('result_hits', 0)}/{stats.get('result_hits', 0) + stats.get('result_misses', 0)}")
    print()
    
    # ========== 测试6：恢复文件 ==========
    print("测试6：恢复文件")
    print("-" * 80)
    if test_file.exists() and original_content:
        test_file.write_text(original_content, encoding='utf-8')
        print(f"✅ 恢复文件: {test_file}")
    print()
    
    # ========== 测试7：LSP 增强 ==========
    print("测试7：LSP 增强（验证 LSP 继续工作）")
    print("-" * 80)
    start = time.time()
    result5 = await tool.execute(repo_path, [], [], max_tokens, enable_lsp=True)
    time5 = time.time() - start
    print(f"✅ LSP 增强调用: {time5:.2f}秒")
    print(f"   LSP启用: {result5.metadata.get('lsp_enabled', False)}")
    # 检查输出是否包含 LSP 信息
    if "LSP增强" in result5.content:
        print(f"   ✅ LSP 信息已包含在输出中")
    else:
        print(f"   ⚠️  LSP 信息未包含在输出中")
    print()
    
    # ========== 总结 ==========
    print("=" * 80)
    print("测试总结")
    print("=" * 80)
    print(f"1. 首次调用: {time1:.2f}秒 (全量扫描)")
    print(f"2. 重复调用: {time2:.4f}秒 (结果级缓存)")
    print(f"3. 增量更新: {time3:.2f}秒 (只重新解析1个文件)")
    print(f"4. 再次调用: {time4:.4f}秒 (新的结果级缓存)")
    print(f"5. LSP增强: {time5:.2f}秒 (LSP继续工作)")
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
    
    # 验证
    print("验证结果:")
    
    # 1. 结果级缓存
    if time2 < 0.01:
        print("  ✅ 结果级缓存工作正常")
    else:
        print("  ⚠️  结果级缓存可能未生效")
    
    # 2. 增量更新
    if time3 < time1 * 0.5:
        print("  ✅ 增量更新工作正常（比全量扫描快50%以上）")
    else:
        print("  ⚠️  增量更新可能未生效")
    
    # 3. 缓存失效
    if time4 < 0.01:
        print("  ✅ 结果级缓存失效并重新生成正常")
    else:
        print("  ⚠️  结果级缓存失效可能有问题")
    
    # 4. LSP 增强
    if result5.metadata.get('lsp_enabled', False):
        print("  ✅ LSP 增强继续工作")
    else:
        print("  ⚠️  LSP 增强可能未启用")
    
    # 5. 文件级缓存
    if cache_stats['file_hit_rate'] > 0.9:
        print("  ✅ 文件级缓存工作正常")
    else:
        print("  ⚠️  文件级缓存命中率较低")


if __name__ == "__main__":
    asyncio.run(test_complete_cache())
