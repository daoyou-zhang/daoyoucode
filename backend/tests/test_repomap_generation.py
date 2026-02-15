#!/usr/bin/env python3
"""
测试 RepoMap 生成功能

测试点：
1. 基本生成（默认5000 tokens）
2. 生成速度
3. 输出内容质量
4. 缓存机制
"""

import asyncio
import time
from pathlib import Path
from daoyoucode.agents.tools.repomap_tools import RepoMapTool


async def test_basic_generation():
    """测试基本生成"""
    print("=" * 60)
    print("测试1: 基本生成（默认max_tokens=5000）")
    print("=" * 60)
    
    tool = RepoMapTool()
    
    # 第一次生成（无缓存）
    print("\n第一次生成（无缓存）...")
    start_time = time.time()
    
    result = await tool.execute(
        repo_path=".",
        chat_files=[],
        mentioned_idents=[]
    )
    
    elapsed = time.time() - start_time
    
    if result.success:
        print(f"✓ 生成成功")
        print(f"✓ 耗时: {elapsed:.2f}秒")
        
        # 检查内容
        content = result.content
        lines = content.split('\n')
        print(f"✓ 输出行数: {len(lines)}")
        
        # 统计文件数
        file_count = len([l for l in lines if l.strip() and not l.startswith(' ') and ':' in l])
        print(f"✓ 包含文件数: {file_count}")
        
        # 统计定义数
        def_count = len([l for l in lines if l.strip().startswith('class ') or 
                         l.strip().startswith('def ') or 
                         l.strip().startswith('function ') or
                         l.strip().startswith('method ')])
        print(f"✓ 包含定义数: {def_count}")
        
        # 显示前20行
        print("\n前20行预览:")
        print("-" * 60)
        for line in lines[:20]:
            print(line)
        print("-" * 60)
        
        # 检查metadata
        if result.metadata:
            print(f"\nMetadata:")
            print(f"  - repo_path: {result.metadata.get('repo_path')}")
            print(f"  - file_count: {result.metadata.get('file_count')}")
            print(f"  - definition_count: {result.metadata.get('definition_count')}")
        
        return True
    else:
        print(f"✗ 生成失败: {result.error}")
        return False


async def test_cached_generation():
    """测试缓存生成"""
    print("\n" + "=" * 60)
    print("测试2: 缓存生成（第二次应该更快）")
    print("=" * 60)
    
    tool = RepoMapTool()
    
    print("\n第二次生成（有缓存）...")
    start_time = time.time()
    
    result = await tool.execute(
        repo_path=".",
        chat_files=[],
        mentioned_idents=[]
    )
    
    elapsed = time.time() - start_time
    
    if result.success:
        print(f"✓ 生成成功")
        print(f"✓ 耗时: {elapsed:.2f}秒（应该比第一次快）")
        return True
    else:
        print(f"✗ 生成失败: {result.error}")
        return False


async def test_with_personalization():
    """测试个性化权重"""
    print("\n" + "=" * 60)
    print("测试3: 个性化权重（提到BaseAgent）")
    print("=" * 60)
    
    tool = RepoMapTool()
    
    print("\n生成时提到 'BaseAgent'...")
    start_time = time.time()
    
    result = await tool.execute(
        repo_path=".",
        chat_files=["daoyoucode/agents/core/agent.py"],
        mentioned_idents=["BaseAgent", "execute"]
    )
    
    elapsed = time.time() - start_time
    
    if result.success:
        print(f"✓ 生成成功")
        print(f"✓ 耗时: {elapsed:.2f}秒")
        
        content = result.content
        lines = content.split('\n')
        
        # 检查agent.py是否在前面
        agent_line = None
        for i, line in enumerate(lines):
            if 'agent.py' in line.lower():
                agent_line = i
                break
        
        if agent_line is not None and agent_line < 10:
            print(f"✓ agent.py 在第 {agent_line} 行（权重生效）")
        else:
            print(f"⚠ agent.py 在第 {agent_line} 行（可能权重未生效）")
        
        # 显示前15行
        print("\n前15行预览:")
        print("-" * 60)
        for line in lines[:15]:
            print(line)
        print("-" * 60)
        
        return True
    else:
        print(f"✗ 生成失败: {result.error}")
        return False


async def test_different_token_limits():
    """测试不同token限制"""
    print("\n" + "=" * 60)
    print("测试4: 不同token限制")
    print("=" * 60)
    
    tool = RepoMapTool()
    
    for max_tokens in [1000, 3000, 5000, 8000]:
        print(f"\n生成 max_tokens={max_tokens}...")
        start_time = time.time()
        
        result = await tool.execute(
            repo_path=".",
            max_tokens=max_tokens
        )
        
        elapsed = time.time() - start_time
        
        if result.success:
            lines = result.content.split('\n')
            file_count = len([l for l in lines if l.strip() and not l.startswith(' ') and ':' in l])
            print(f"  ✓ 耗时: {elapsed:.2f}秒, 文件数: {file_count}, 行数: {len(lines)}")
        else:
            print(f"  ✗ 失败: {result.error}")


async def test_cache_file():
    """测试缓存文件"""
    print("\n" + "=" * 60)
    print("测试5: 缓存文件检查")
    print("=" * 60)
    
    cache_file = Path(".daoyoucode/cache/repomap.db")
    
    if cache_file.exists():
        size = cache_file.stat().st_size
        print(f"✓ 缓存文件存在: {cache_file}")
        print(f"✓ 文件大小: {size / 1024:.2f} KB")
        
        # 检查缓存内容
        import sqlite3
        conn = sqlite3.connect(str(cache_file))
        cursor = conn.execute("SELECT COUNT(*) FROM definitions")
        count = cursor.fetchone()[0]
        conn.close()
        
        print(f"✓ 缓存条目数: {count}")
        return True
    else:
        print(f"✗ 缓存文件不存在: {cache_file}")
        return False


async def main():
    print("测试 RepoMap 生成功能\n")
    
    results = []
    
    # 测试1: 基本生成
    try:
        results.append(("基本生成", await test_basic_generation()))
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("基本生成", False))
    
    # 测试2: 缓存生成
    try:
        results.append(("缓存生成", await test_cached_generation()))
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        results.append(("缓存生成", False))
    
    # 测试3: 个性化权重
    try:
        results.append(("个性化权重", await test_with_personalization()))
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        results.append(("个性化权重", False))
    
    # 测试4: 不同token限制
    try:
        await test_different_token_limits()
    except Exception as e:
        print(f"✗ 测试失败: {e}")
    
    # 测试5: 缓存文件
    try:
        results.append(("缓存文件", await test_cache_file()))
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        results.append(("缓存文件", False))
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{status}: {name}")
    
    all_passed = all(r[1] for r in results)
    
    if all_passed:
        print("\n🎉 所有测试通过！RepoMap生成正常")
        return 0
    else:
        print("\n❌ 部分测试失败")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
