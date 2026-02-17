"""
测试 Git 增强功能

验证：
1. subtree_only 过滤在 repo_map 中生效
2. git_status 工具正常工作
3. 路径处理一致性
"""

import sys
from pathlib import Path
import asyncio

# 添加 backend 到路径
sys.path.insert(0, str(Path(__file__).parent))


async def test_subtree_only_filtering():
    """测试 subtree_only 过滤"""
    from daoyoucode.agents.tools.base import ToolContext
    from daoyoucode.agents.tools.repomap_tools import RepoMapTool
    
    print("=" * 60)
    print("测试 subtree_only 过滤")
    print("=" * 60)
    
    # 创建工具
    tool = RepoMapTool()
    
    # 测试 1：不使用 subtree_only
    print("\n测试 1：不使用 subtree_only（扫描整个项目）")
    context1 = ToolContext(
        repo_path=Path.cwd().parent,  # 项目根目录
        subtree_only=False
    )
    tool.set_context(context1)
    
    result1 = await tool.execute(
        repo_path=".",
        max_tokens=1000
    )
    
    if result1.success:
        file_count1 = result1.metadata.get('file_count', 0)
        print(f"✓ 扫描了 {file_count1} 个文件")
        # 显示前几个文件
        lines = result1.content.split('\n')[:10]
        print("  前几个文件:")
        for line in lines:
            if line.strip():
                print(f"    {line}")
    else:
        print(f"✗ 失败: {result1.error}")
    
    # 测试 2：使用 subtree_only
    print("\n测试 2：使用 subtree_only（只扫描 backend/）")
    context2 = ToolContext(
        repo_path=Path.cwd().parent,  # 项目根目录
        subtree_only=True,
        cwd=Path.cwd()  # backend/
    )
    tool.set_context(context2)
    
    result2 = await tool.execute(
        repo_path=".",
        max_tokens=1000
    )
    
    if result2.success:
        file_count2 = result2.metadata.get('file_count', 0)
        print(f"✓ 扫描了 {file_count2} 个文件")
        # 显示前几个文件
        lines = result2.content.split('\n')[:10]
        print("  前几个文件:")
        for line in lines:
            if line.strip():
                print(f"    {line}")
        
        # 验证：subtree_only 应该扫描更少的文件
        if file_count2 < file_count1:
            print(f"\n✓ subtree_only 生效: {file_count1} → {file_count2} 文件")
        else:
            print(f"\n⚠ subtree_only 可能未生效: {file_count1} → {file_count2} 文件")
    else:
        print(f"✗ 失败: {result2.error}")


async def test_git_status_tool():
    """测试 git_status 工具"""
    from daoyoucode.agents.tools.base import ToolContext
    from daoyoucode.agents.tools.git_tools import GitStatusTool
    
    print("\n" + "=" * 60)
    print("测试 git_status 工具")
    print("=" * 60)
    
    # 创建工具
    tool = GitStatusTool()
    context = ToolContext(repo_path=Path.cwd().parent)
    tool.set_context(context)
    
    # 执行
    result = await tool.execute(repo_path=".")
    
    if result.success:
        print("\n✓ git_status 执行成功")
        print("\n输出:")
        print(result.content)
        
        # 显示元数据
        metadata = result.metadata
        print("\n元数据:")
        print(f"  分支: {metadata.get('branch')}")
        print(f"  仓库根目录: {metadata.get('repo_root')}")
        print(f"  已修改文件数: {len(metadata.get('modified_files', []))}")
        print(f"  已暂存文件数: {len(metadata.get('staged_files', []))}")
        print(f"  未跟踪文件数: {len(metadata.get('untracked_files', []))}")
        print(f"  是否有未提交更改: {metadata.get('is_dirty')}")
    else:
        print(f"\n✗ 失败: {result.error}")


async def test_path_consistency():
    """测试路径一致性"""
    from daoyoucode.agents.tools.base import ToolContext
    from daoyoucode.agents.tools.repomap_tools import RepoMapTool
    from daoyoucode.agents.tools.file_tools import ReadFileTool
    
    print("\n" + "=" * 60)
    print("测试路径一致性")
    print("=" * 60)
    
    # 创建工具
    repo_map_tool = RepoMapTool()
    read_file_tool = ReadFileTool()
    
    context = ToolContext(repo_path=Path.cwd().parent)
    repo_map_tool.set_context(context)
    read_file_tool.set_context(context)
    
    # 1. 使用 repo_map 获取文件列表
    print("\n步骤 1：使用 repo_map 获取文件列表")
    result1 = await repo_map_tool.execute(
        repo_path=".",
        max_tokens=500
    )
    
    if not result1.success:
        print(f"✗ repo_map 失败: {result1.error}")
        return
    
    # 提取第一个文件路径
    lines = result1.content.split('\n')
    first_file = None
    for line in lines:
        if line.strip() and not line.startswith('#') and '/' in line:
            # 提取文件路径（格式可能是 "path/to/file.py:"）
            parts = line.split(':')
            if parts:
                first_file = parts[0].strip()
                break
    
    if not first_file:
        print("⚠ 未找到文件路径")
        return
    
    print(f"✓ 找到文件: {first_file}")
    
    # 2. 使用 read_file 读取该文件
    print(f"\n步骤 2：使用 read_file 读取 {first_file}")
    result2 = await read_file_tool.execute(file_path=first_file)
    
    if result2.success:
        print(f"✓ 成功读取文件")
        print(f"  文件大小: {len(result2.content)} 字符")
        print(f"  前 3 行:")
        lines = result2.content.split('\n')[:3]
        for line in lines:
            print(f"    {line}")
        print("\n✅ 路径一致性测试通过！")
    else:
        print(f"✗ 读取失败: {result2.error}")
        print("\n❌ 路径一致性测试失败！")


async def main():
    """运行所有测试"""
    try:
        await test_subtree_only_filtering()
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        await test_git_status_tool()
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        await test_path_consistency()
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("所有测试完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
