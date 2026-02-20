#!/usr/bin/env python3
"""
测试智能token预算调整功能

测试场景：
1. 无chat_files: 应该自动扩大到10000 tokens
2. 有chat_files: 应该保持5000 tokens
3. 禁用auto_scale: 应该保持原始值
"""

import asyncio
from pathlib import Path
from daoyoucode.agents.tools.repomap_tools import RepoMapTool


async def test_no_chat_files():
    """测试无对话文件场景（应该扩大预算）"""
    print("=" * 60)
    print("测试1: 无对话文件（应该自动扩大到6000 tokens）")
    print("=" * 60)
    
    tool = RepoMapTool()
    
    result = await tool.execute(
        repo_path=".",
        chat_files=[],  # 空列表
        mentioned_idents=[],
        max_tokens=3000,  # 默认3000
        auto_scale=True
    )
    
    if result.success:
        metadata = result.metadata
        print(f"\n✓ 生成成功")
        print(f"  - 原始max_tokens: {metadata.get('original_max_tokens')}")
        print(f"  - 实际max_tokens: {metadata.get('max_tokens')}")
        print(f"  - 是否自动调整: {metadata.get('auto_scaled')}")
        print(f"  - chat_files数量: {metadata.get('chat_files_count')}")
        print(f"  - 包含文件数: {metadata.get('file_count')}")
        
        # 验证
        if metadata.get('max_tokens') == 6000:
            print("\n✅ 验证通过: token预算已扩大到6000")
            return True
        else:
            print(f"\n❌ 验证失败: 期望6000，实际{metadata.get('max_tokens')}")
            return False
    else:
        print(f"✗ 生成失败: {result.error}")
        return False


async def test_with_chat_files():
    """测试有对话文件场景（应该保持标准预算）"""
    print("\n" + "=" * 60)
    print("测试2: 有对话文件（应该保持3000 tokens）")
    print("=" * 60)
    
    tool = RepoMapTool()
    
    result = await tool.execute(
        repo_path=".",
        chat_files=["daoyoucode/agents/core/agent.py"],  # 指定文件
        mentioned_idents=["BaseAgent"],
        max_tokens=3000,  # 默认3000
        auto_scale=True
    )
    
    if result.success:
        metadata = result.metadata
        print(f"\n✓ 生成成功")
        print(f"  - 原始max_tokens: {metadata.get('original_max_tokens')}")
        print(f"  - 实际max_tokens: {metadata.get('max_tokens')}")
        print(f"  - 是否自动调整: {metadata.get('auto_scaled')}")
        print(f"  - chat_files数量: {metadata.get('chat_files_count')}")
        print(f"  - 包含文件数: {metadata.get('file_count')}")
        
        # 验证
        if metadata.get('max_tokens') == 3000:
            print("\n✅ 验证通过: token预算保持3000")
            return True
        else:
            print(f"\n❌ 验证失败: 期望3000，实际{metadata.get('max_tokens')}")
            return False
    else:
        print(f"✗ 生成失败: {result.error}")
        return False


async def test_auto_scale_disabled():
    """测试禁用自动调整（应该保持原始值）"""
    print("\n" + "=" * 60)
    print("测试3: 禁用auto_scale（应该保持原始值）")
    print("=" * 60)
    
    tool = RepoMapTool()
    
    result = await tool.execute(
        repo_path=".",
        chat_files=[],  # 空列表
        mentioned_idents=[],
        max_tokens=3000,  # 默认3000
        auto_scale=False  # 禁用自动调整
    )
    
    if result.success:
        metadata = result.metadata
        print(f"\n✓ 生成成功")
        print(f"  - 原始max_tokens: {metadata.get('original_max_tokens')}")
        print(f"  - 实际max_tokens: {metadata.get('max_tokens')}")
        print(f"  - 是否自动调整: {metadata.get('auto_scaled')}")
        print(f"  - chat_files数量: {metadata.get('chat_files_count')}")
        print(f"  - 包含文件数: {metadata.get('file_count')}")
        
        # 验证
        if metadata.get('max_tokens') == 3000:
            print("\n✅ 验证通过: token预算保持3000（未调整）")
            return True
        else:
            print(f"\n❌ 验证失败: 期望3000，实际{metadata.get('max_tokens')}")
            return False
    else:
        print(f"✗ 生成失败: {result.error}")
        return False


async def test_custom_max_tokens():
    """测试自定义max_tokens（应该按比例扩大）"""
    print("\n" + "=" * 60)
    print("测试4: 自定义max_tokens=2000（应该扩大到4000）")
    print("=" * 60)
    
    tool = RepoMapTool()
    
    result = await tool.execute(
        repo_path=".",
        chat_files=[],  # 空列表
        mentioned_idents=[],
        max_tokens=2000,  # 自定义值
        auto_scale=True
    )
    
    if result.success:
        metadata = result.metadata
        print(f"\n✓ 生成成功")
        print(f"  - 原始max_tokens: {metadata.get('original_max_tokens')}")
        print(f"  - 实际max_tokens: {metadata.get('max_tokens')}")
        print(f"  - 是否自动调整: {metadata.get('auto_scaled')}")
        print(f"  - chat_files数量: {metadata.get('chat_files_count')}")
        print(f"  - 包含文件数: {metadata.get('file_count')}")
        
        # 验证
        if metadata.get('max_tokens') == 4000:
            print("\n✅ 验证通过: token预算扩大到4000（2倍）")
            return True
        else:
            print(f"\n❌ 验证失败: 期望4000，实际{metadata.get('max_tokens')}")
            return False
    else:
        print(f"✗ 生成失败: {result.error}")
        return False


async def test_max_limit():
    """测试最大限制（应该不超过6000）"""
    print("\n" + "=" * 60)
    print("测试5: 超大max_tokens=5000（应该限制在6000）")
    print("=" * 60)
    
    tool = RepoMapTool()
    
    result = await tool.execute(
        repo_path=".",
        chat_files=[],  # 空列表
        mentioned_idents=[],
        max_tokens=5000,  # 很大的值
        auto_scale=True
    )
    
    if result.success:
        metadata = result.metadata
        print(f"\n✓ 生成成功")
        print(f"  - 原始max_tokens: {metadata.get('original_max_tokens')}")
        print(f"  - 实际max_tokens: {metadata.get('max_tokens')}")
        print(f"  - 是否自动调整: {metadata.get('auto_scaled')}")
        print(f"  - chat_files数量: {metadata.get('chat_files_count')}")
        print(f"  - 包含文件数: {metadata.get('file_count')}")
        
        # 验证
        if metadata.get('max_tokens') == 6000:
            print("\n✅ 验证通过: token预算限制在6000（未超过上限）")
            return True
        else:
            print(f"\n❌ 验证失败: 期望6000，实际{metadata.get('max_tokens')}")
            return False
    else:
        print(f"✗ 生成失败: {result.error}")
        return False


async def main():
    print("测试智能token预算调整功能\n")
    
    results = []
    
    # 测试1: 无chat_files
    try:
        results.append(("无对话文件", await test_no_chat_files()))
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("无对话文件", False))
    
    # 测试2: 有chat_files
    try:
        results.append(("有对话文件", await test_with_chat_files()))
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        results.append(("有对话文件", False))
    
    # 测试3: 禁用auto_scale
    try:
        results.append(("禁用auto_scale", await test_auto_scale_disabled()))
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        results.append(("禁用auto_scale", False))
    
    # 测试4: 自定义max_tokens
    try:
        results.append(("自定义max_tokens", await test_custom_max_tokens()))
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        results.append(("自定义max_tokens", False))
    
    # 测试5: 最大限制
    try:
        results.append(("最大限制", await test_max_limit()))
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        results.append(("最大限制", False))
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{status}: {name}")
    
    all_passed = all(r[1] for r in results)
    
    if all_passed:
        print("\n🎉 所有测试通过！智能token预算调整功能正常")
        print("\n功能说明：")
        print("- 默认3000 tokens（标准预算）")
        print("- 无对话文件时，自动扩大到6000 tokens（2倍）")
        print("- 有对话文件时，保持3000 tokens")
        print("- 可以通过auto_scale=False禁用")
        print("- 采用智能策略，更经济实用")
        return 0
    else:
        print("\n❌ 部分测试失败")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
