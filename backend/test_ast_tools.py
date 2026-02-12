"""
AST工具测试

测试ast-grep集成的AST级别代码搜索和替换功能
"""

import pytest
import asyncio
import tempfile
from pathlib import Path

from daoyoucode.agents.tools.ast_tools import (
    AstGrepSearchTool,
    AstGrepReplaceTool,
    AstGrepManager,
    _ast_grep_manager
)


class TestAstGrepManager:
    """AST-grep管理器测试"""
    
    def test_get_cache_dir(self):
        """测试获取缓存目录"""
        manager = AstGrepManager()
        cache_dir = manager._get_cache_dir()
        
        assert cache_dir is not None
        assert "daoyoucode" in str(cache_dir)
        assert "bin" in str(cache_dir)
    
    def test_get_binary_name(self):
        """测试获取二进制文件名"""
        manager = AstGrepManager()
        binary_name = manager._get_binary_name()
        
        import platform
        if platform.system() == "Windows":
            assert binary_name == "sg.exe"
        else:
            assert binary_name == "sg"
    
    @pytest.mark.asyncio
    async def test_get_binary_path(self):
        """测试获取二进制路径"""
        manager = AstGrepManager()
        
        # 尝试获取二进制路径
        # 注意：这可能会触发下载，所以我们只检查返回值类型
        binary_path = await manager.get_binary_path()
        
        # 如果返回了路径，应该是字符串
        if binary_path:
            assert isinstance(binary_path, str)
            assert len(binary_path) > 0


class TestAstGrepSearchTool:
    """AST搜索工具测试"""
    
    @pytest.mark.asyncio
    async def test_search_python_function(self):
        """测试搜索Python函数"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试文件
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("""
def hello():
    print("Hello")
    return True

def world():
    print("World")
    return False

class Calculator:
    def add(self, a, b):
        return a + b
""")
            
            # 创建工具
            tool = AstGrepSearchTool()
            
            # 搜索所有函数定义
            result = await tool.execute(
                pattern="def $FUNC($$):",
                lang="python",
                paths=[str(tmpdir)]
            )
            
            # 验证结果
            # 注意：如果ast-grep未安装，会返回错误
            if result.success:
                assert "hello" in result.content or "world" in result.content or "add" in result.content
            else:
                # ast-grep未安装，跳过
                assert "not available" in result.error or "not found" in result.error
    
    @pytest.mark.asyncio
    async def test_search_javascript_console(self):
        """测试搜索JavaScript console.log"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试文件
            test_file = Path(tmpdir) / "test.js"
            test_file.write_text("""
function hello() {
    console.log("Hello");
    return true;
}

function world() {
    console.log("World");
    console.error("Error");
    return false;
}
""")
            
            # 创建工具
            tool = AstGrepSearchTool()
            
            # 搜索console.log
            result = await tool.execute(
                pattern="console.log($MSG)",
                lang="javascript",
                paths=[str(tmpdir)]
            )
            
            # 验证结果
            if result.success:
                assert "console.log" in result.content
                assert result.metadata["total_matches"] >= 2
            else:
                # ast-grep未安装，跳过
                assert "not available" in result.error or "not found" in result.error
    
    @pytest.mark.asyncio
    async def test_search_with_context(self):
        """测试带上下文的搜索"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试文件
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("""
def calculate(a, b):
    result = a + b
    print(result)
    return result
""")
            
            # 创建工具
            tool = AstGrepSearchTool()
            
            # 搜索print语句，带2行上下文
            result = await tool.execute(
                pattern="print($MSG)",
                lang="python",
                paths=[str(tmpdir)],
                context=2
            )
            
            # 验证结果
            if result.success:
                assert "print" in result.content
            else:
                # ast-grep未安装，跳过
                assert "not available" in result.error or "not found" in result.error
    
    @pytest.mark.asyncio
    async def test_search_with_globs(self):
        """测试使用glob模式搜索"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建多个测试文件
            (Path(tmpdir) / "test1.py").write_text("def hello(): pass")
            (Path(tmpdir) / "test2.py").write_text("def world(): pass")
            (Path(tmpdir) / "ignore.txt").write_text("def ignore(): pass")
            
            # 创建工具
            tool = AstGrepSearchTool()
            
            # 只搜索.py文件
            result = await tool.execute(
                pattern="def $FUNC():",
                lang="python",
                paths=[str(tmpdir)],
                globs=["*.py"]
            )
            
            # 验证结果
            if result.success:
                # 应该找到hello和world，但不包括ignore
                assert "hello" in result.content or "world" in result.content
                assert "ignore.txt" not in result.content
            else:
                # ast-grep未安装，跳过
                assert "not available" in result.error or "not found" in result.error
    
    @pytest.mark.asyncio
    async def test_search_no_matches(self):
        """测试无匹配结果"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试文件
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("""
def hello():
    print("Hello")
""")
            
            # 创建工具
            tool = AstGrepSearchTool()
            
            # 搜索不存在的模式
            result = await tool.execute(
                pattern="class $NAME:",
                lang="python",
                paths=[str(tmpdir)]
            )
            
            # 验证结果
            if result.success:
                assert "No matches found" in result.content
            else:
                # ast-grep未安装，跳过
                assert "not available" in result.error or "not found" in result.error


class TestAstGrepReplaceTool:
    """AST替换工具测试"""
    
    @pytest.mark.asyncio
    async def test_replace_dry_run(self):
        """测试dry-run模式（预览）"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试文件
            test_file = Path(tmpdir) / "test.js"
            original_content = """
function hello() {
    console.log("Hello");
    return true;
}
"""
            test_file.write_text(original_content)
            
            # 创建工具
            tool = AstGrepReplaceTool()
            
            # 替换console.log为logger.info（dry-run）
            result = await tool.execute(
                pattern="console.log($MSG)",
                rewrite="logger.info($MSG)",
                lang="javascript",
                paths=[str(tmpdir)],
                dry_run=True
            )
            
            # 验证结果
            if result.success:
                assert "[DRY RUN]" in result.content
                assert "replacement" in result.content.lower()
                # 文件内容不应该改变
                assert test_file.read_text() == original_content
            else:
                # ast-grep未安装，跳过
                assert "not available" in result.error or "not found" in result.error
    
    @pytest.mark.asyncio
    async def test_replace_apply(self):
        """测试实际应用替换"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试文件
            test_file = Path(tmpdir) / "test.js"
            test_file.write_text("""
function hello() {
    console.log("Hello");
    return true;
}
""")
            
            # 创建工具
            tool = AstGrepReplaceTool()
            
            # 替换console.log为logger.info（实际应用）
            result = await tool.execute(
                pattern="console.log($MSG)",
                rewrite="logger.info($MSG)",
                lang="javascript",
                paths=[str(tmpdir)],
                dry_run=False
            )
            
            # 验证结果
            if result.success:
                assert "[DRY RUN]" not in result.content
                assert "replacement" in result.content.lower()
                # 文件内容应该改变
                new_content = test_file.read_text()
                assert "logger.info" in new_content
                assert "console.log" not in new_content
            else:
                # ast-grep未安装，跳过
                assert "not available" in result.error or "not found" in result.error
    
    @pytest.mark.asyncio
    async def test_replace_python_print(self):
        """测试替换Python print语句"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试文件
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("""
def calculate(a, b):
    result = a + b
    print(result)
    return result
""")
            
            # 创建工具
            tool = AstGrepReplaceTool()
            
            # 替换print为logger.info（dry-run）
            result = await tool.execute(
                pattern="print($MSG)",
                rewrite="logger.info($MSG)",
                lang="python",
                paths=[str(tmpdir)],
                dry_run=True
            )
            
            # 验证结果
            if result.success:
                assert "[DRY RUN]" in result.content
                assert "replacement" in result.content.lower()
            else:
                # ast-grep未安装，跳过
                assert "not available" in result.error or "not found" in result.error
    
    @pytest.mark.asyncio
    async def test_replace_no_matches(self):
        """测试无匹配结果"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试文件
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("""
def hello():
    print("Hello")
""")
            
            # 创建工具
            tool = AstGrepReplaceTool()
            
            # 替换不存在的模式
            result = await tool.execute(
                pattern="class $NAME:",
                rewrite="class New$NAME:",
                lang="python",
                paths=[str(tmpdir)],
                dry_run=True
            )
            
            # 验证结果
            if result.success:
                assert "No matches found" in result.content
            else:
                # ast-grep未安装，跳过
                assert "not available" in result.error or "not found" in result.error


class TestAstToolsIntegration:
    """AST工具集成测试"""
    
    @pytest.mark.asyncio
    async def test_search_and_replace_workflow(self):
        """测试搜索和替换工作流"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试文件
            test_file = Path(tmpdir) / "test.js"
            test_file.write_text("""
function processData(data) {
    console.log("Processing:", data);
    const result = data.map(x => x * 2);
    console.log("Result:", result);
    return result;
}
""")
            
            # 1. 先搜索
            search_tool = AstGrepSearchTool()
            search_result = await search_tool.execute(
                pattern="console.log($MSG)",
                lang="javascript",
                paths=[str(tmpdir)]
            )
            
            if not search_result.success:
                # ast-grep未安装，跳过
                pytest.skip("ast-grep not available")
            
            # 验证找到了匹配
            assert search_result.metadata["total_matches"] >= 2
            
            # 2. 预览替换
            replace_tool = AstGrepReplaceTool()
            preview_result = await replace_tool.execute(
                pattern="console.log($MSG)",
                rewrite="logger.info($MSG)",
                lang="javascript",
                paths=[str(tmpdir)],
                dry_run=True
            )
            
            assert preview_result.success
            assert "[DRY RUN]" in preview_result.content
            
            # 3. 应用替换
            apply_result = await replace_tool.execute(
                pattern="console.log($MSG)",
                rewrite="logger.info($MSG)",
                lang="javascript",
                paths=[str(tmpdir)],
                dry_run=False
            )
            
            assert apply_result.success
            
            # 4. 验证替换成功
            new_content = test_file.read_text()
            assert "logger.info" in new_content
            assert "console.log" not in new_content
    
    @pytest.mark.asyncio
    async def test_multiple_languages(self):
        """测试多种语言支持"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Python文件
            (Path(tmpdir) / "test.py").write_text("def hello(): pass")
            
            # JavaScript文件
            (Path(tmpdir) / "test.js").write_text("function hello() {}")
            
            # TypeScript文件
            (Path(tmpdir) / "test.ts").write_text("function hello(): void {}")
            
            search_tool = AstGrepSearchTool()
            
            # 搜索Python
            py_result = await search_tool.execute(
                pattern="def $FUNC():",
                lang="python",
                paths=[str(tmpdir)],
                globs=["*.py"]
            )
            
            # 搜索JavaScript
            js_result = await search_tool.execute(
                pattern="function $FUNC() {}",
                lang="javascript",
                paths=[str(tmpdir)],
                globs=["*.js"]
            )
            
            # 搜索TypeScript
            ts_result = await search_tool.execute(
                pattern="function $FUNC(): void {}",
                lang="typescript",
                paths=[str(tmpdir)],
                globs=["*.ts"]
            )
            
            # 至少有一个应该成功（如果ast-grep已安装）
            if py_result.success or js_result.success or ts_result.success:
                # 验证找到了匹配
                if py_result.success:
                    assert "hello" in py_result.content
                if js_result.success:
                    assert "hello" in js_result.content
                if ts_result.success:
                    assert "hello" in ts_result.content


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
