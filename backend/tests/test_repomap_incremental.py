#!/usr/bin/env python3
"""
测试 RepoMap 增量更新功能
"""

import asyncio
import time
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from daoyoucode.agents.tools.repomap_tools import RepoMapTool
from daoyoucode.agents.tools.base import ToolContext


async def test_incremental_update():
    """测试增量更新"""
    
    print("=" * 80)
    print("RepoMap 增量更新测试")
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
    
    print("步骤1：首次调用（冷启动）")
    print("-" * 80)
    start = time.time()
    result1 = await tool.execute(repo_path, [], [], max_tokens, enable_lsp=False)
    time1 = time.time() - start
    print(f"✅ 首次调用完成: {time1:.2f}秒")
    print(f"   文件数: {result1.metadata.get('file_count', 0)}")
    print(f"   定义数: {result1.metadata.get('definition_count', 0)}")
    if 'cache_stats' in result1.metadata:
        stats = result1.metadata['cache_stats']
        print(f"   文件级缓存: {stats['file_hits']}/{stats['file_hits'] + stats['file_misses']} "
              f"({stats['file_hits'] / (stats['file_hits'] + stats['file_misses']):.0%})")
    print()
    
    print("步骤2：模拟文件修改（修改测试文件）")
    print("-" * 80)
    test_file = Path("backend/test_repomap_cache.py")
    if test_file.exists():
        # 读取文件
        content = test_file.read_text(encoding='utf-8')
        # 添加一个注释（触发 mtime 改变）
        test_file.write_text(content + "\n# Test modification\n", encoding='utf-8')
        print(f"✅ 修改文件: {test_file}")
        
        # 等待一下确保 mtime 改变
        time.sleep(0.1)
    else:
        print("⚠️  测试文件不存在，跳过修改")
    print()
    
    print("步骤3：再次调用（应该触发增量更新）")
    print("-" * 80)
    start = time.time()
    result2 = await tool.execute(repo_path, [], [], max_tokens, enable_lsp=False)
    time2 = time.time() - start
    print(f"✅ 增量更新完成: {time2:.2f}秒")
    print(f"   文件数: {result2.metadata.get('file_count', 0)}")
    if 'cache_stats' in result2.metadata:
        stats = result2.metadata['cache_stats']
        print(f"   文件级缓存: {stats['file_hits']}/{stats['file_hits'] + stats['file_misses']} "
              f"({stats['file_hits'] / (stats['file_hits'] + stats['file_misses']):.0%})")
    print()
    
    print("步骤4：恢复文件（撤销修改）")
    print("-" * 80)
    if test_file.exists():
        # 恢复文件
        test_file.write_text(content, encoding='utf-8')
        print(f"✅ 恢复文件: {test_file}")
    print()
    
    print("步骤5：第三次调用（验证缓存）")
    print("-" * 80)
    start = time.time()
    result3 = await tool.execute(repo_path, [], [], max_tokens, enable_lsp=False)
    time3 = time.time() - start
    print(f"✅ 第三次调用完成: {time3:.4f}秒")
    if 'cache_stats' in result3.metadata:
        stats = result3.metadata['cache_stats']
        print(f"   文件级缓存: {stats['file_hits']}/{stats['file_hits'] + stats['file_misses']} "
              f"({stats['file_hits'] / (stats['file_hits'] + stats['file_misses']):.0%})")
    print()
    
    # 总结
    print("=" * 80)
    print("测试总结")
    print("=" * 80)
    print(f"首次调用: {time1:.2f}秒 (全量扫描)")
    print(f"增量更新: {time2:.2f}秒 (只重新解析1个文件)")
    print(f"缓存命中: {time3:.4f}秒 (全部命中缓存)")
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
    print("验证增量更新:")
    if time2 < time1 * 0.5:
        print("  🎉 增量更新工作正常！（比全量扫描快50%以上）")
    else:
        print("  ⚠️  增量更新可能未生效")
    
    if time3 < 0.01:
        print("  🎉 缓存工作正常！")
    else:
        print("  ⚠️  缓存可能未生效")


if __name__ == "__main__":
    asyncio.run(test_incremental_update())
