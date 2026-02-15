"""
Diff工具测试

测试基于opencode的9种Replacer策略
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from daoyoucode.agents.tools.diff_tools import (
    levenshtein,
    SimpleReplacer,
    LineTrimmedReplacer,
    BlockAnchorReplacer,
    WhitespaceNormalizedReplacer,
    IndentationFlexibleReplacer,
    replace,
    SearchReplaceTool
)


# ========== Levenshtein距离测试 ==========

def test_levenshtein_identical():
    """测试相同字符串"""
    assert levenshtein("hello", "hello") == 0


def test_levenshtein_empty():
    """测试空字符串"""
    assert levenshtein("", "hello") == 5
    assert levenshtein("hello", "") == 5


def test_levenshtein_one_char_diff():
    """测试单字符差异"""
    assert levenshtein("hello", "hallo") == 1


def test_levenshtein_multiple_diff():
    """测试多字符差异"""
    assert levenshtein("kitten", "sitting") == 3


# ========== Replacer策略测试 ==========

def test_simple_replacer():
    """测试策略1: 精确匹配"""
    content = "Hello World\nThis is a test\n"
    find = "Hello World"
    
    matches = list(SimpleReplacer.find_matches(content, find))
    assert len(matches) == 1
    assert matches[0] == "Hello World"


def test_line_trimmed_replacer():
    """测试策略2: 忽略行首尾空白"""
    content = "  Hello World  \n  This is a test  \n"
    find = "Hello World\nThis is a test"
    
    matches = list(LineTrimmedReplacer.find_matches(content, find))
    assert len(matches) == 1
    assert "Hello World" in matches[0]


def test_block_anchor_replacer_single_candidate():
    """测试策略3: 首尾行锚定（单候选）"""
    content = """def hello():
    print("Hello")
    return True
"""
    find = """def hello():
    print("Hello")
    return True"""
    
    matches = list(BlockAnchorReplacer.find_matches(content, find))
    assert len(matches) == 1


def test_block_anchor_replacer_multiple_candidates():
    """测试策略3: 首尾行锚定（多候选）"""
    content = """def func1():
    print("A")
    return 1

def func2():
    print("B")
    return 2
"""
    find = """def func1():
    print("A")
    return 1"""
    
    matches = list(BlockAnchorReplacer.find_matches(content, find))
    assert len(matches) == 1
    assert "func1" in matches[0]


def test_whitespace_normalized_replacer():
    """测试策略4: 空白归一化"""
    content = "Hello    World\n"
    find = "Hello World"
    
    matches = list(WhitespaceNormalizedReplacer.find_matches(content, find))
    assert len(matches) == 1


def test_indentation_flexible_replacer():
    """测试策略5: 缩进灵活匹配"""
    content = """    def hello():
        print("Hello")
"""
    find = """def hello():
    print("Hello")"""
    
    matches = list(IndentationFlexibleReplacer.find_matches(content, find))
    assert len(matches) == 1


# ========== 核心replace函数测试 ==========

def test_replace_simple():
    """测试简单替换"""
    content = "Hello World"
    result = replace(content, "Hello", "Hi")
    assert result == "Hi World"


def test_replace_with_whitespace():
    """测试带空白的替换"""
    content = "  Hello World  "
    result = replace(content, "Hello World", "Hi")
    assert "Hi" in result


def test_replace_multiline():
    """测试多行替换"""
    content = """def hello():
    print("Hello")
    return True
"""
    find = """def hello():
    print("Hello")
    return True"""
    new = """def hello():
    print("Hi")
    return False"""
    
    result = replace(content, find, new)
    assert "Hi" in result
    assert "False" in result


def test_replace_with_indentation():
    """测试缩进灵活替换"""
    content = """    def hello():
        print("Hello")
"""
    find = """def hello():
    print("Hello")"""
    new = """def hello():
    print("Hi")"""
    
    result = replace(content, find, new)
    assert "Hi" in result


def test_replace_not_found():
    """测试找不到匹配"""
    content = "Hello World"
    with pytest.raises(ValueError, match="not found"):
        replace(content, "Goodbye", "Hi")


def test_replace_multiple_matches():
    """测试多个匹配（应该失败）"""
    content = "Hello Hello"
    with pytest.raises(ValueError, match="multiple matches"):
        replace(content, "Hello", "Hi")


def test_replace_all():
    """测试替换所有"""
    content = "Hello Hello"
    result = replace(content, "Hello", "Hi", replace_all=True)
    assert result == "Hi Hi"


# ========== SearchReplaceTool测试 ==========

@pytest.fixture
def temp_dir():
    """创建临时目录"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    if temp_path.exists():
        shutil.rmtree(temp_path)


@pytest.mark.asyncio
async def test_search_replace_tool(temp_dir):
    """测试SearchReplaceTool"""
    # 创建测试文件
    test_file = temp_dir / "test.py"
    test_file.write_text("""def hello():
    print("Hello")
    return True
""")
    
    # 执行替换
    tool = SearchReplaceTool()
    result = await tool.execute(
        file_path=str(test_file),
        search='print("Hello")',
        replace='print("Hi")'
    )
    
    if not result.success:
        print(f"Error: {result.error}")
        import traceback
        traceback.print_exc()
    
    assert result.success
    
    # 验证文件内容
    new_content = test_file.read_text()
    assert "Hi" in new_content
    assert "Hello" not in new_content


@pytest.mark.asyncio
async def test_search_replace_tool_not_found(temp_dir):
    """测试文件不存在"""
    tool = SearchReplaceTool()
    result = await tool.execute(
        file_path=str(temp_dir / "nonexistent.py"),
        search="test",
        replace="new"
    )
    
    assert not result.success
    assert "not found" in result.error.lower()


@pytest.mark.asyncio
async def test_search_replace_tool_with_indentation(temp_dir):
    """测试缩进灵活替换"""
    test_file = temp_dir / "test.py"
    test_file.write_text("""    def hello():
        print("Hello")
""")
    
    tool = SearchReplaceTool()
    result = await tool.execute(
        file_path=str(test_file),
        search="""def hello():
    print("Hello")""",
        replace="""def hello():
    print("Hi")"""
    )
    
    assert result.success
    new_content = test_file.read_text()
    assert "Hi" in new_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
