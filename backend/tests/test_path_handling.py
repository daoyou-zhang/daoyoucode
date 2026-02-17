"""
测试路径处理修复

验证所有工具返回的路径都是相对于 repo_path 的标准路径
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from daoyoucode.agents.tools.base import ToolContext
from daoyoucode.agents.tools.registry import get_tool_registry
from daoyoucode.agents.tools.repomap_tools import RepoMapTool, GetRepoStructureTool
from daoyoucode.agents.tools.file_tools import ListFilesTool, ReadFileTool
from daoyoucode.agents.tools.search_tools import TextSearchTool


async def test_tool_context():
    """测试 ToolContext 基础功能"""
    print("\n=== 测试 ToolContext ===")
    
    # 创建上下文
    repo_path = Path(__file__).parent.parent  # 项目根目录
    context = ToolContext(repo_path=repo_path)
    
    print(f"✓ repo_path: {context.repo_path}")
    
    # 测试 abs_path
    abs_path = context.abs_path("backend/test.py")
    print(f"✓ abs_path('backend/test.py'): {abs_path}")
    assert abs_path == repo_path / "backend/test.py"
    
    # 测试 rel_path
    rel_path = context.rel_path(str(repo_path / "backend/test.py"))
    print(f"✓ rel_path('{repo_path}/backend/test.py'): {rel_path}")
    assert rel_path == "backend/test.py" or rel_path == "backend\\test.py"
    
    # 测试 normalize_path
    norm_path = context.normalize_path(str(repo_path / "backend/test.py"))
    print(f"✓ normalize_path('{repo_path}/backend/test.py'): {norm_path}")
    
    print("✓ ToolContext 测试通过")


async def test_repo_map_paths():
    """测试 repo_map 返回的路径"""
    print("\n=== 测试 repo_map 路径 ===")
    
    # 设置上下文
    repo_path = Path(__file__).parent.parent
    context = ToolContext(repo_path=repo_path)
    
    # 创建工具
    tool = RepoMapTool()
    tool.set_context(context)
    
    # 执行
    result = await tool.execute(
        repo_path=".",
        max_tokens=1000
    )
    
    if not result.success:
        print(f"✗ repo_map 执行失败: {result.error}")
        return False
    
    print(f"✓ repo_map 执行成功")
    
    # 检查返回的路径
    content = result.content
    lines = content.split('\n')
    
    file_paths = []
    for line in lines:
        if line and not line.startswith('#') and not line.startswith(' ') and line.endswith(':'):
            file_path = line.rstrip(':')
            file_paths.append(file_path)
    
    print(f"✓ 找到 {len(file_paths)} 个文件路径")
    
    # 验证路径格式
    for file_path in file_paths[:5]:  # 只检查前5个
        print(f"  • {file_path}")
        
        # 路径应该是相对路径
        if Path(file_path).is_absolute():
            print(f"✗ 路径是绝对路径: {file_path}")
            return False
        
        # 路径应该可以直接用于 read_file
        full_path = repo_path / file_path
        if not full_path.exists():
            print(f"✗ 路径不存在: {file_path} (resolved to {full_path})")
            return False
    
    print("✓ repo_map 路径测试通过")
    return True


async def test_list_files_paths():
    """测试 list_files 返回的路径"""
    print("\n=== 测试 list_files 路径 ===")
    
    # 设置上下文
    repo_path = Path(__file__).parent.parent
    context = ToolContext(repo_path=repo_path)
    
    # 创建工具
    tool = ListFilesTool()
    tool.set_context(context)
    
    # 执行
    result = await tool.execute(
        directory="backend",
        recursive=True,
        pattern="*.py",
        max_depth=2
    )
    
    if not result.success:
        print(f"✗ list_files 执行失败: {result.error}")
        return False
    
    print(f"✓ list_files 执行成功")
    
    # 检查返回的路径
    files = result.content
    print(f"✓ 找到 {len(files)} 个文件")
    
    # 验证路径格式
    for file_info in files[:5]:  # 只检查前5个
        file_path = file_info['path']
        print(f"  • {file_path}")
        
        # 路径应该是相对路径
        if Path(file_path).is_absolute():
            print(f"✗ 路径是绝对路径: {file_path}")
            return False
        
        # 路径应该以 backend 开头
        if not file_path.startswith('backend'):
            print(f"✗ 路径不以 backend 开头: {file_path}")
            return False
        
        # 路径应该可以直接用于 read_file
        full_path = repo_path / file_path
        if not full_path.exists():
            print(f"✗ 路径不存在: {file_path} (resolved to {full_path})")
            return False
    
    print("✓ list_files 路径测试通过")
    return True


async def test_text_search_paths():
    """测试 text_search 返回的路径"""
    print("\n=== 测试 text_search 路径 ===")
    
    # 设置上下文
    repo_path = Path(__file__).parent.parent
    context = ToolContext(repo_path=repo_path)
    
    # 创建工具
    tool = TextSearchTool()
    tool.set_context(context)
    
    # 执行
    result = await tool.execute(
        query="ToolContext",
        directory="backend",
        file_pattern="*.py",
        max_results=10
    )
    
    if not result.success:
        print(f"✗ text_search 执行失败: {result.error}")
        return False
    
    print(f"✓ text_search 执行成功")
    
    # 检查返回的路径
    results = result.content
    print(f"✓ 找到 {len(results)} 个匹配")
    
    # 验证路径格式
    for match in results[:5]:  # 只检查前5个
        file_path = match['file']
        print(f"  • {file_path}:{match['line']}")
        
        # 路径应该是相对路径
        if Path(file_path).is_absolute():
            print(f"✗ 路径是绝对路径: {file_path}")
            return False
        
        # 路径应该以 backend 开头
        if not file_path.startswith('backend'):
            print(f"✗ 路径不以 backend 开头: {file_path}")
            return False
        
        # 路径应该可以直接用于 read_file
        full_path = repo_path / file_path
        if not full_path.exists():
            print(f"✗ 路径不存在: {file_path} (resolved to {full_path})")
            return False
    
    print("✓ text_search 路径测试通过")
    return True


async def test_read_file_with_repo_map_path():
    """测试使用 repo_map 返回的路径读取文件"""
    print("\n=== 测试 repo_map → read_file 工作流 ===")
    
    # 设置上下文
    repo_path = Path(__file__).parent.parent
    context = ToolContext(repo_path=repo_path)
    
    # 1. 执行 repo_map
    repo_map_tool = RepoMapTool()
    repo_map_tool.set_context(context)
    
    result = await repo_map_tool.execute(
        repo_path=".",
        mentioned_idents=["ToolContext"],
        max_tokens=1000
    )
    
    if not result.success:
        print(f"✗ repo_map 执行失败: {result.error}")
        return False
    
    print(f"✓ repo_map 执行成功")
    
    # 2. 提取第一个文件路径
    content = result.content
    lines = content.split('\n')
    
    first_file = None
    for line in lines:
        if line and not line.startswith('#') and not line.startswith(' ') and line.endswith(':'):
            first_file = line.rstrip(':')
            break
    
    if not first_file:
        print("✗ 未找到文件路径")
        return False
    
    print(f"✓ 提取文件路径: {first_file}")
    
    # 3. 使用该路径读取文件
    read_tool = ReadFileTool()
    read_tool.set_context(context)
    
    result = await read_tool.execute(file_path=first_file)
    
    if not result.success:
        print(f"✗ read_file 执行失败: {result.error}")
        print(f"  文件路径: {first_file}")
        return False
    
    print(f"✓ read_file 执行成功")
    print(f"  文件大小: {len(result.content)} 字符")
    
    print("✓ repo_map → read_file 工作流测试通过")
    return True


async def test_tool_registry_context():
    """测试 ToolRegistry 的 ToolContext 传播"""
    print("\n=== 测试 ToolRegistry ToolContext 传播 ===")
    
    # 设置上下文
    repo_path = Path(__file__).parent.parent
    context = ToolContext(repo_path=repo_path)
    
    # 获取注册表
    registry = get_tool_registry()
    registry.set_context(context)
    
    print(f"✓ 设置 ToolRegistry context: {context.repo_path}")
    
    # 注册工具
    tools = [
        RepoMapTool(),
        ListFilesTool(),
        TextSearchTool(),
        ReadFileTool()
    ]
    
    for tool in tools:
        registry.register(tool)
    
    print(f"✓ 注册了 {len(tools)} 个工具")
    
    # 验证每个工具都有正确的 context
    for tool_name in ['repo_map', 'list_files', 'text_search', 'read_file']:
        tool = registry.get_tool(tool_name)
        if not tool:
            print(f"✗ 工具未找到: {tool_name}")
            return False
        
        if not tool._context:
            print(f"✗ 工具没有 context: {tool_name}")
            return False
        
        if tool._context.repo_path != context.repo_path:
            print(f"✗ 工具 context 不匹配: {tool_name}")
            return False
        
        print(f"  ✓ {tool_name}: context.repo_path = {tool._context.repo_path}")
    
    print("✓ ToolRegistry ToolContext 传播测试通过")
    return True


async def main():
    """运行所有测试"""
    print("=" * 60)
    print("路径处理修复测试")
    print("=" * 60)
    
    tests = [
        ("ToolContext 基础功能", test_tool_context),
        ("ToolRegistry ToolContext 传播", test_tool_registry_context),
        ("repo_map 路径", test_repo_map_paths),
        ("list_files 路径", test_list_files_paths),
        ("text_search 路径", test_text_search_paths),
        ("repo_map → read_file 工作流", test_read_file_with_repo_map_path),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            result = await test_func()
            if result is None or result:
                passed += 1
            else:
                failed += 1
                print(f"✗ {name} 失败")
        except Exception as e:
            failed += 1
            print(f"✗ {name} 异常: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
