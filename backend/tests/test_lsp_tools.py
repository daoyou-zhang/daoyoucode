"""
测试LSP工具

测试：
1. LSP诊断工具
2. LSP跳转定义工具
3. LSP查找引用工具
4. LSP符号工具
5. LSP重命名工具
6. LSP代码操作工具
7. 工具注册
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from daoyoucode.agents.tools.lsp_tools import (
    LSPDiagnosticsTool,
    LSPGotoDefinitionTool,
    LSPFindReferencesTool,
    LSPSymbolsTool,
    LSPRenameTool,
    LSPCodeActionsTool,
    get_lsp_manager
)


class TestLSPDiagnosticsTool:
    """测试LSP诊断工具"""
    
    @pytest.fixture
    def temp_file(self):
        """创建临时文件"""
        temp_dir = tempfile.mkdtemp()
        file_path = Path(temp_dir) / "test.py"
        file_path.write_text("def hello():\n    print('Hello')\n")
        
        yield file_path
        
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_diagnostics_basic(self, temp_file):
        """测试基础诊断"""
        tool = LSPDiagnosticsTool()
        
        result = await tool.execute(
            file_path=str(temp_file)
        )
        
        assert result.success
        assert result.content is not None
        assert 'LSP diagnostics' in result.content
    
    @pytest.mark.asyncio
    async def test_diagnostics_with_severity(self, temp_file):
        """测试带严重性过滤的诊断"""
        tool = LSPDiagnosticsTool()
        
        result = await tool.execute(
            file_path=str(temp_file),
            severity="error"
        )
        
        assert result.success
        assert result.metadata['severity'] == 'error'
    
    @pytest.mark.asyncio
    async def test_diagnostics_nonexistent_file(self):
        """测试不存在的文件"""
        tool = LSPDiagnosticsTool()
        
        result = await tool.execute(
            file_path="/nonexistent/file.py"
        )
        
        assert not result.success
        assert 'not found' in result.error.lower()


class TestLSPGotoDefinitionTool:
    """测试LSP跳转定义工具"""
    
    @pytest.fixture
    def temp_file(self):
        """创建临时文件"""
        temp_dir = tempfile.mkdtemp()
        file_path = Path(temp_dir) / "test.py"
        file_path.write_text("def hello():\n    print('Hello')\n")
        
        yield file_path
        
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_goto_definition_basic(self, temp_file):
        """测试基础跳转定义"""
        tool = LSPGotoDefinitionTool()
        
        result = await tool.execute(
            file_path=str(temp_file),
            line=1,
            character=4
        )
        
        assert result.success
        assert result.content is not None
        assert 'goto definition' in result.content.lower()
    
    @pytest.mark.asyncio
    async def test_goto_definition_metadata(self, temp_file):
        """测试元数据"""
        tool = LSPGotoDefinitionTool()
        
        result = await tool.execute(
            file_path=str(temp_file),
            line=1,
            character=4
        )
        
        assert result.metadata['line'] == 1
        assert result.metadata['character'] == 4


class TestLSPFindReferencesTool:
    """测试LSP查找引用工具"""
    
    @pytest.fixture
    def temp_file(self):
        """创建临时文件"""
        temp_dir = tempfile.mkdtemp()
        file_path = Path(temp_dir) / "test.py"
        file_path.write_text("def hello():\n    print('Hello')\n")
        
        yield file_path
        
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_find_references_basic(self, temp_file):
        """测试基础查找引用"""
        tool = LSPFindReferencesTool()
        
        result = await tool.execute(
            file_path=str(temp_file),
            line=1,
            character=4
        )
        
        assert result.success
        assert result.content is not None
        assert 'find references' in result.content.lower()
    
    @pytest.mark.asyncio
    async def test_find_references_with_declaration(self, temp_file):
        """测试包含声明的查找引用"""
        tool = LSPFindReferencesTool()
        
        result = await tool.execute(
            file_path=str(temp_file),
            line=1,
            character=4,
            include_declaration=False
        )
        
        assert result.success
        assert result.metadata['include_declaration'] == False


class TestLSPSymbolsTool:
    """测试LSP符号工具"""
    
    @pytest.fixture
    def temp_file(self):
        """创建临时文件"""
        temp_dir = tempfile.mkdtemp()
        file_path = Path(temp_dir) / "test.py"
        file_path.write_text("def hello():\n    print('Hello')\n")
        
        yield file_path
        
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_symbols_document_scope(self, temp_file):
        """测试文档范围符号"""
        tool = LSPSymbolsTool()
        
        result = await tool.execute(
            file_path=str(temp_file),
            scope="document"
        )
        
        assert result.success
        assert result.content is not None
        assert 'document' in result.content.lower()
    
    @pytest.mark.asyncio
    async def test_symbols_workspace_scope(self, temp_file):
        """测试工作区范围符号"""
        tool = LSPSymbolsTool()
        
        result = await tool.execute(
            file_path=str(temp_file),
            scope="workspace",
            query="hello"
        )
        
        assert result.success
        assert result.metadata['query'] == 'hello'
    
    @pytest.mark.asyncio
    async def test_symbols_workspace_without_query(self, temp_file):
        """测试工作区范围但没有查询"""
        tool = LSPSymbolsTool()
        
        result = await tool.execute(
            file_path=str(temp_file),
            scope="workspace"
        )
        
        assert not result.success
        assert 'required' in result.error.lower()


class TestLSPRenameTool:
    """测试LSP重命名工具"""
    
    @pytest.fixture
    def temp_file(self):
        """创建临时文件"""
        temp_dir = tempfile.mkdtemp()
        file_path = Path(temp_dir) / "test.py"
        file_path.write_text("def hello():\n    print('Hello')\n")
        
        yield file_path
        
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_rename_basic(self, temp_file):
        """测试基础重命名"""
        tool = LSPRenameTool()
        
        result = await tool.execute(
            file_path=str(temp_file),
            line=1,
            character=4,
            new_name="greet"
        )
        
        assert result.success
        assert result.content is not None
        assert 'rename' in result.content.lower()
        assert result.metadata['new_name'] == 'greet'


class TestLSPCodeActionsTool:
    """测试LSP代码操作工具"""
    
    @pytest.fixture
    def temp_file(self):
        """创建临时文件"""
        temp_dir = tempfile.mkdtemp()
        file_path = Path(temp_dir) / "test.py"
        file_path.write_text("def hello():\n    print('Hello')\n")
        
        yield file_path
        
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_code_actions_basic(self, temp_file):
        """测试基础代码操作"""
        tool = LSPCodeActionsTool()
        
        result = await tool.execute(
            file_path=str(temp_file),
            line=1,
            character=4
        )
        
        assert result.success
        assert result.content is not None
        assert 'code actions' in result.content.lower()


class TestLSPManager:
    """测试LSP管理器"""
    
    def test_manager_singleton(self):
        """测试管理器单例"""
        manager1 = get_lsp_manager()
        manager2 = get_lsp_manager()
        
        assert manager1 is manager2
    
    def test_find_server_for_python(self):
        """测试查找Python服务器"""
        manager = get_lsp_manager()
        
        server = manager.find_server_for_extension(".py")
        
        # 可能找到也可能找不到（取决于是否安装）
        if server:
            assert server.id in ["pyright", "pylsp"]
            assert ".py" in server.extensions
    
    def test_find_server_for_javascript(self):
        """测试查找JavaScript服务器"""
        manager = get_lsp_manager()
        
        server = manager.find_server_for_extension(".js")
        
        if server:
            assert server.id == "typescript-language-server"
            assert ".js" in server.extensions


class TestToolIntegration:
    """测试工具集成"""
    
    def test_tool_registry(self):
        """测试工具注册"""
        from daoyoucode.agents.tools import get_tool_registry
        
        registry = get_tool_registry()
        tools = registry.list_tools()
        
        # 检查LSP工具是否已注册
        lsp_tools = [
            'lsp_diagnostics',
            'lsp_goto_definition',
            'lsp_find_references',
            'lsp_symbols',
            'lsp_rename',
            'lsp_code_actions'
        ]
        
        for tool_name in lsp_tools:
            assert tool_name in tools
    
    def test_function_schemas(self):
        """测试Function schemas"""
        from daoyoucode.agents.tools import get_tool_registry
        
        registry = get_tool_registry()
        
        lsp_tools = [
            'lsp_diagnostics',
            'lsp_goto_definition',
            'lsp_find_references',
            'lsp_symbols',
            'lsp_rename',
            'lsp_code_actions'
        ]
        
        schemas = registry.get_function_schemas(lsp_tools)
        
        assert len(schemas) == 6
        
        for schema in schemas:
            assert 'name' in schema
            assert 'description' in schema
            assert 'parameters' in schema


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
