"""
工具系统测试

测试所有内置工具的功能
"""

import pytest
import asyncio
from pathlib import Path
import tempfile
import shutil
import os

from daoyoucode.agents.tools import get_tool_registry


@pytest.fixture
def tool_registry():
    """获取工具注册表"""
    return get_tool_registry()


@pytest.fixture
def temp_dir():
    """创建临时目录"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # 清理
    if temp_path.exists():
        shutil.rmtree(temp_path)


# ========== 文件操作工具测试 ==========

@pytest.mark.asyncio
async def test_read_file_tool(tool_registry, temp_dir):
    """测试读取文件工具"""
    # 创建测试文件
    test_file = temp_dir / "test.txt"
    test_content = "Hello, World!"
    test_file.write_text(test_content)
    
    # 执行工具
    result = await tool_registry.execute_tool(
        "read_file",
        file_path=str(test_file)
    )
    
    assert result.success
    assert result.content == test_content
    assert result.metadata['lines'] == 1


@pytest.mark.asyncio
async def test_write_file_tool(tool_registry, temp_dir):
    """测试写入文件工具"""
    test_file = temp_dir / "subdir" / "test.txt"
    test_content = "Hello, World!"
    
    # 执行工具（自动创建目录）
    result = await tool_registry.execute_tool(
        "write_file",
        file_path=str(test_file),
        content=test_content
    )
    
    assert result.success
    assert test_file.exists()
    assert test_file.read_text() == test_content


@pytest.mark.asyncio
async def test_list_files_tool(tool_registry, temp_dir):
    """测试列出文件工具"""
    # 创建测试文件
    (temp_dir / "file1.txt").write_text("test")
    (temp_dir / "file2.py").write_text("test")
    (temp_dir / "subdir").mkdir()
    (temp_dir / "subdir" / "file3.txt").write_text("test")
    
    # 非递归列出
    result = await tool_registry.execute_tool(
        "list_files",
        directory=str(temp_dir),
        recursive=False
    )
    
    assert result.success
    assert len(result.content) == 3  # 2个文件 + 1个目录
    
    # 递归列出
    result = await tool_registry.execute_tool(
        "list_files",
        directory=str(temp_dir),
        recursive=True
    )
    
    assert result.success
    assert len(result.content) == 4  # 3个文件 + 1个目录
    
    # 模式匹配
    result = await tool_registry.execute_tool(
        "list_files",
        directory=str(temp_dir),
        pattern="*.txt",
        recursive=True
    )
    
    assert result.success
    # 应该包含2个.txt文件 + 1个subdir目录（因为递归会包含目录）
    txt_files = [f for f in result.content if f['type'] == 'file']
    assert len(txt_files) == 2  # 只有.txt文件


@pytest.mark.asyncio
async def test_get_file_info_tool(tool_registry, temp_dir):
    """测试获取文件信息工具"""
    test_file = temp_dir / "test.txt"
    test_file.write_text("Hello")
    
    result = await tool_registry.execute_tool(
        "get_file_info",
        path=str(test_file)
    )
    
    assert result.success
    assert result.content['name'] == "test.txt"
    assert result.content['type'] == "file"
    assert result.content['size'] == 5


@pytest.mark.asyncio
async def test_create_directory_tool(tool_registry, temp_dir):
    """测试创建目录工具"""
    new_dir = temp_dir / "a" / "b" / "c"
    
    result = await tool_registry.execute_tool(
        "create_directory",
        directory=str(new_dir),
        parents=True
    )
    
    assert result.success
    assert new_dir.exists()
    assert new_dir.is_dir()


@pytest.mark.asyncio
async def test_delete_file_tool(tool_registry, temp_dir):
    """测试删除文件工具"""
    # 删除文件
    test_file = temp_dir / "test.txt"
    test_file.write_text("test")
    
    result = await tool_registry.execute_tool(
        "delete_file",
        path=str(test_file)
    )
    
    assert result.success
    assert not test_file.exists()
    
    # 删除目录
    test_dir = temp_dir / "testdir"
    test_dir.mkdir()
    (test_dir / "file.txt").write_text("test")
    
    result = await tool_registry.execute_tool(
        "delete_file",
        path=str(test_dir),
        recursive=True
    )
    
    assert result.success
    assert not test_dir.exists()


# ========== 搜索工具测试 ==========

@pytest.mark.asyncio
async def test_text_search_tool(tool_registry, temp_dir):
    """测试文本搜索工具"""
    # 创建测试文件
    (temp_dir / "file1.py").write_text("def hello():\n    print('Hello')\n")
    (temp_dir / "file2.py").write_text("def world():\n    print('World')\n")
    (temp_dir / "file3.txt").write_text("Hello World\n")
    
    # 搜索 "Hello"
    result = await tool_registry.execute_tool(
        "text_search",
        query="Hello",
        directory=str(temp_dir)
    )
    
    assert result.success
    # 应该找到3个匹配（file1.py有2行，file3.txt有1行）
    assert len(result.content) >= 2  # 至少2个匹配
    # 检查文件
    files = set(r['file'] for r in result.content)
    assert len(files) == 2  # 来自2个文件
    
    # 区分大小写搜索
    result = await tool_registry.execute_tool(
        "text_search",
        query="hello",
        directory=str(temp_dir),
        case_sensitive=True
    )
    
    assert result.success
    assert len(result.content) == 1  # 只有 file1.py
    
    # 文件模式匹配
    result = await tool_registry.execute_tool(
        "text_search",
        query="Hello",
        directory=str(temp_dir),
        file_pattern="*.py"
    )
    
    assert result.success
    # file1.py有2行包含Hello
    assert len(result.content) >= 1  # 至少1个匹配
    # 检查所有结果都来自.py文件
    for r in result.content:
        assert r['file'].endswith('.py')


@pytest.mark.asyncio
async def test_regex_search_tool(tool_registry, temp_dir):
    """测试正则搜索工具"""
    # 创建测试文件
    (temp_dir / "file1.py").write_text("def func1():\n    pass\n")
    (temp_dir / "file2.py").write_text("def func2():\n    pass\n")
    (temp_dir / "file3.py").write_text("class MyClass:\n    pass\n")
    
    # 搜索函数定义
    result = await tool_registry.execute_tool(
        "regex_search",
        pattern=r"def \w+\(",
        directory=str(temp_dir)
    )
    
    assert result.success
    assert len(result.content) == 2  # func1 和 func2
    
    # 搜索类定义
    result = await tool_registry.execute_tool(
        "regex_search",
        pattern=r"class \w+:",
        directory=str(temp_dir)
    )
    
    assert result.success
    assert len(result.content) == 1  # MyClass


# ========== 命令执行工具测试 ==========

@pytest.mark.asyncio
async def test_run_command_tool(tool_registry, temp_dir):
    """测试运行命令工具"""
    # 简单命令
    result = await tool_registry.execute_tool(
        "run_command",
        command="echo Hello",
        cwd=str(temp_dir)
    )
    
    assert result.success
    assert "Hello" in result.content['stdout']
    assert result.content['returncode'] == 0


@pytest.mark.asyncio
async def test_run_command_tool_failure(tool_registry, temp_dir):
    """测试运行命令工具（失败情况）"""
    result = await tool_registry.execute_tool(
        "run_command",
        command="exit 1",
        cwd=str(temp_dir)
    )
    
    assert not result.success
    assert result.content['returncode'] == 1


# ========== 工具注册表测试 ==========

def test_tool_registry_list(tool_registry):
    """测试工具列表"""
    tools = tool_registry.list_tools()
    
    # 应该有14个工具
    assert len(tools) == 14
    
    # 检查关键工具
    assert "read_file" in tools
    assert "write_file" in tools
    assert "text_search" in tools
    assert "git_status" in tools
    assert "run_command" in tools


def test_tool_registry_get_schemas(tool_registry):
    """测试获取Function schemas"""
    schemas = tool_registry.get_function_schemas()
    
    assert len(schemas) == 14
    
    # 检查schema结构
    for schema in schemas:
        assert "name" in schema
        assert "description" in schema
        assert "parameters" in schema
        assert "type" in schema["parameters"]
        assert "properties" in schema["parameters"]


def test_tool_registry_get_specific_schemas(tool_registry):
    """测试获取特定工具的schemas"""
    schemas = tool_registry.get_function_schemas(["read_file", "write_file"])
    
    assert len(schemas) == 2
    assert schemas[0]["name"] == "read_file"
    assert schemas[1]["name"] == "write_file"


@pytest.mark.asyncio
async def test_tool_not_found(tool_registry):
    """测试工具不存在"""
    result = await tool_registry.execute_tool("non_existent_tool")
    
    assert not result.success
    assert "not found" in result.error.lower()


# ========== 集成测试 ==========

@pytest.mark.asyncio
async def test_tool_integration(tool_registry, temp_dir):
    """测试工具集成（完整流程）"""
    # 1. 创建目录
    result = await tool_registry.execute_tool(
        "create_directory",
        directory=str(temp_dir / "project")
    )
    assert result.success
    
    # 2. 写入文件
    result = await tool_registry.execute_tool(
        "write_file",
        file_path=str(temp_dir / "project" / "main.py"),
        content="def main():\n    print('Hello')\n"
    )
    assert result.success
    
    # 3. 读取文件
    result = await tool_registry.execute_tool(
        "read_file",
        file_path=str(temp_dir / "project" / "main.py")
    )
    assert result.success
    assert "def main()" in result.content
    
    # 4. 搜索文件
    result = await tool_registry.execute_tool(
        "text_search",
        query="main",
        directory=str(temp_dir / "project")
    )
    assert result.success
    assert len(result.content) >= 1
    
    # 5. 列出文件
    result = await tool_registry.execute_tool(
        "list_files",
        directory=str(temp_dir / "project")
    )
    assert result.success
    assert len(result.content) == 1
    
    # 6. 获取文件信息
    result = await tool_registry.execute_tool(
        "get_file_info",
        path=str(temp_dir / "project" / "main.py")
    )
    assert result.success
    assert result.content['name'] == "main.py"
    
    # 7. 删除文件
    result = await tool_registry.execute_tool(
        "delete_file",
        path=str(temp_dir / "project" / "main.py")
    )
    assert result.success


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
