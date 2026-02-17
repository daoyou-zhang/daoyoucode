"""
测试 repo_path 确定逻辑

验证 determine_repo_path() 函数的各种场景
"""

import sys
from pathlib import Path
import tempfile
import shutil

# 添加 backend 到路径
sys.path.insert(0, str(Path(__file__).parent))

def test_determine_repo_path():
    """测试 repo_path 确定逻辑"""
    
    # 导入函数（需要模拟 typer 环境）
    import os
    os.chdir(Path(__file__).parent)
    
    # 模拟导入
    from cli.commands.chat import determine_repo_path
    
    print("=" * 60)
    print("测试 repo_path 确定逻辑")
    print("=" * 60)
    
    # 测试 1：没有文件，使用当前目录
    print("\n测试 1：没有文件，使用当前目录")
    try:
        result = determine_repo_path(files=None, repo_arg=Path("."))
        print(f"✓ 结果: {result}")
        print(f"  是否为绝对路径: {result.is_absolute()}")
    except Exception as e:
        print(f"✗ 错误: {e}")
    
    # 测试 2：指定 repo 参数
    print("\n测试 2：指定 repo 参数")
    try:
        test_repo = Path(__file__).parent
        result = determine_repo_path(files=None, repo_arg=test_repo)
        print(f"✓ 结果: {result}")
        print(f"  是否为绝对路径: {result.is_absolute()}")
        print(f"  是否等于指定路径: {result == test_repo.resolve()}")
    except Exception as e:
        print(f"✗ 错误: {e}")
    
    # 测试 3：从文件推断（使用当前文件）
    print("\n测试 3：从文件推断")
    try:
        current_file = Path(__file__)
        result = determine_repo_path(files=[current_file], repo_arg=Path("."))
        print(f"✓ 结果: {result}")
        print(f"  是否为绝对路径: {result.is_absolute()}")
        print(f"  文件是否在 repo 下: {current_file.resolve().is_relative_to(result)}")
    except Exception as e:
        print(f"✗ 错误: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


def test_tool_context():
    """测试 ToolContext 的 subtree_only 功能"""
    from daoyoucode.agents.tools.base import ToolContext
    
    print("\n" + "=" * 60)
    print("测试 ToolContext subtree_only 功能")
    print("=" * 60)
    
    # 创建测试目录结构
    repo_path = Path("/project")
    cwd = Path("/project/backend")
    
    # 测试 1：subtree_only = False
    print("\n测试 1：subtree_only = False（包含所有路径）")
    ctx = ToolContext(repo_path=repo_path, subtree_only=False)
    
    test_paths = [
        "backend/main.py",
        "frontend/app.tsx",
        "README.md"
    ]
    
    for path in test_paths:
        included = ctx.should_include_path(path)
        print(f"  {path}: {'✓ 包含' if included else '✗ 排除'}")
    
    # 测试 2：subtree_only = True
    print("\n测试 2：subtree_only = True（只包含 backend/）")
    ctx = ToolContext(
        repo_path=repo_path,
        subtree_only=True,
        cwd=cwd
    )
    
    for path in test_paths:
        included = ctx.should_include_path(path)
        print(f"  {path}: {'✓ 包含' if included else '✗ 排除'}")
    
    # 测试 3：路径标准化
    print("\n测试 3：路径标准化")
    ctx = ToolContext(repo_path=Path.cwd())
    
    test_cases = [
        ("backend/main.py", "相对路径"),
        (str(Path.cwd() / "backend/main.py"), "绝对路径"),
    ]
    
    for path, desc in test_cases:
        normalized = ctx.normalize_path(path)
        print(f"  {desc}: {path}")
        print(f"    → {normalized}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_determine_repo_path()
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        test_tool_context()
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
