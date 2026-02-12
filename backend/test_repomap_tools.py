"""
RepoMap工具测试

测试场景：
1. 基本RepoMap生成
2. 个性化权重（对话文件、提到的标识符）
3. Token预算控制
4. 缓存机制
5. 仓库结构获取
"""

import pytest
import asyncio
from pathlib import Path
import tempfile
import shutil

from daoyoucode.agents.tools.repomap_tools import RepoMapTool, GetRepoStructureTool


@pytest.fixture
def temp_repo():
    """创建临时测试仓库"""
    temp_dir = tempfile.mkdtemp()
    repo_path = Path(temp_dir)
    
    # 创建测试文件
    # file1.py
    (repo_path / "file1.py").write_text("""
class UserManager:
    def create_user(self, name):
        pass
    
    def delete_user(self, user_id):
        pass

def get_user(user_id):
    return UserManager().get_user(user_id)
""")
    
    # file2.py
    (repo_path / "file2.py").write_text("""
from file1 import UserManager

class AuthService:
    def __init__(self):
        self.user_manager = UserManager()
    
    def login(self, username, password):
        user = self.user_manager.get_user(username)
        return user
""")
    
    # subdir/file3.js
    subdir = repo_path / "subdir"
    subdir.mkdir()
    (subdir / "file3.js").write_text("""
class ApiClient {
    constructor() {}
    
    fetchUser(userId) {
        return fetch(`/api/users/${userId}`)
    }
}

function getUserData(userId) {
    const client = new ApiClient()
    return client.fetchUser(userId)
}
""")
    
    yield repo_path
    
    # 清理
    shutil.rmtree(temp_dir)


class TestRepoMapTool:
    """RepoMap工具测试"""
    
    @pytest.mark.asyncio
    async def test_basic_repomap(self, temp_repo):
        """测试基本RepoMap生成"""
        tool = RepoMapTool()
        result = await tool.execute(
            repo_path=str(temp_repo),
            max_tokens=1000
        )
        
        print("\n=== 基本RepoMap ===")
        print(f"Success: {result.success}")
        print(f"Content:\n{result.content}")
        
        assert result.success
        assert "代码地图" in result.content
        assert "file1.py" in result.content or "file2.py" in result.content
        assert "class" in result.content or "function" in result.content
    
    @pytest.mark.asyncio
    async def test_chat_files_weight(self, temp_repo):
        """测试对话文件权重（×50）"""
        tool = RepoMapTool()
        
        # 不指定chat_files
        result1 = await tool.execute(
            repo_path=str(temp_repo),
            max_tokens=1000
        )
        
        # 指定chat_files
        result2 = await tool.execute(
            repo_path=str(temp_repo),
            chat_files=["file2.py"],
            max_tokens=1000
        )
        
        print("\n=== 无chat_files ===")
        print(result1.content)
        print("\n=== 有chat_files (file2.py) ===")
        print(result2.content)
        
        # file2.py应该排在前面
        assert result2.success
        assert "file2.py" in result2.content
    
    @pytest.mark.asyncio
    async def test_mentioned_idents_weight(self, temp_repo):
        """测试提到的标识符权重（×10）"""
        tool = RepoMapTool()
        
        result = await tool.execute(
            repo_path=str(temp_repo),
            mentioned_idents=["UserManager", "AuthService"],
            max_tokens=1000
        )
        
        print("\n=== 提到标识符 (UserManager, AuthService) ===")
        print(result.content)
        
        # 应该包含相关文件
        assert result.success
        assert "file1.py" in result.content or "file2.py" in result.content
    
    @pytest.mark.asyncio
    async def test_token_budget(self, temp_repo):
        """测试Token预算控制"""
        tool = RepoMapTool()
        
        # 小预算
        result_small = await tool.execute(
            repo_path=str(temp_repo),
            max_tokens=50
        )
        
        # 大预算
        result_large = await tool.execute(
            repo_path=str(temp_repo),
            max_tokens=1000
        )
        
        print("\n=== 小预算 (50 tokens) ===")
        print(result_small.content)
        print(f"长度: {len(result_small.content)}")
        
        print("\n=== 大预算 (1000 tokens) ===")
        print(result_large.content)
        print(f"长度: {len(result_large.content)}")
        
        # 两个都应该成功
        assert result_small.success
        assert result_large.success
        # 小预算应该不超过大预算（测试仓库太小，可能相等）
        assert len(result_small.content) <= len(result_large.content)
    
    @pytest.mark.asyncio
    async def test_cache_mechanism(self, temp_repo):
        """测试缓存机制"""
        tool = RepoMapTool()
        
        # 第一次调用（无缓存）
        import time
        start1 = time.time()
        result1 = await tool.execute(
            repo_path=str(temp_repo),
            max_tokens=1000
        )
        time1 = time.time() - start1
        
        # 第二次调用（有缓存）
        start2 = time.time()
        result2 = await tool.execute(
            repo_path=str(temp_repo),
            max_tokens=1000
        )
        time2 = time.time() - start2
        
        print(f"\n=== 缓存测试 ===")
        print(f"第一次: {time1:.4f}s")
        print(f"第二次: {time2:.4f}s")
        print(f"加速: {time1/time2:.2f}x" if time2 > 0 else "N/A")
        
        # 结果应该相同
        assert result1.success
        assert result2.success
        assert result1.content == result2.content
    
    @pytest.mark.asyncio
    async def test_nonexistent_repo(self):
        """测试不存在的仓库"""
        tool = RepoMapTool()
        result = await tool.execute(
            repo_path="/nonexistent/path"
        )
        
        print("\n=== 不存在的仓库 ===")
        print(f"Success: {result.success}")
        print(f"Error: {result.error}")
        
        assert not result.success
        assert result.error is not None


class TestGetRepoStructureTool:
    """仓库结构工具测试"""
    
    @pytest.mark.asyncio
    async def test_basic_structure(self, temp_repo):
        """测试基本结构获取"""
        tool = GetRepoStructureTool()
        result = await tool.execute(
            repo_path=str(temp_repo)
        )
        
        print("\n=== 仓库结构 ===")
        print(result.content)
        
        assert result.success
        assert "file1.py" in result.content
        assert "file2.py" in result.content
        assert "subdir" in result.content
        assert "file3.js" in result.content
    
    @pytest.mark.asyncio
    async def test_max_depth(self, temp_repo):
        """测试最大深度限制"""
        tool = GetRepoStructureTool()
        
        # 深度1（只显示根目录）
        result1 = await tool.execute(
            repo_path=str(temp_repo),
            max_depth=1
        )
        
        # 深度2（显示子目录）
        result2 = await tool.execute(
            repo_path=str(temp_repo),
            max_depth=2
        )
        
        print("\n=== 深度1 ===")
        print(result1.content)
        
        print("\n=== 深度2 ===")
        print(result2.content)
        
        # 深度1应该更短
        assert result1.success
        assert result2.success
        assert len(result1.content) < len(result2.content)
        # 深度2应该包含子目录文件
        assert "file3.js" in result2.content
    
    @pytest.mark.asyncio
    async def test_show_files_false(self, temp_repo):
        """测试只显示目录"""
        tool = GetRepoStructureTool()
        result = await tool.execute(
            repo_path=str(temp_repo),
            show_files=False
        )
        
        print("\n=== 只显示目录 ===")
        print(result.content)
        
        # 应该包含目录
        assert result.success
        assert "subdir" in result.content
        # 不应该包含文件
        assert "file1.py" not in result.content
        assert "file2.py" not in result.content


class TestToolIntegration:
    """工具集成测试"""
    
    @pytest.mark.asyncio
    async def test_tool_registry(self):
        """测试工具注册"""
        from daoyoucode.agents.tools import get_tool_registry
        
        registry = get_tool_registry()
        tools = registry.list_tools()
        
        print(f"\n=== 已注册工具 ({len(tools)}个) ===")
        for tool_name in tools:
            print(f"  - {tool_name}")
        
        # 应该包含RepoMap工具
        assert "repo_map" in tools
        assert "get_repo_structure" in tools
        
        # 总共23个工具（包括6个LSP工具）
        assert len(tools) == 23
    
    @pytest.mark.asyncio
    async def test_function_schemas(self):
        """测试Function schemas"""
        from daoyoucode.agents.tools import get_tool_registry
        
        registry = get_tool_registry()
        schemas = registry.get_function_schemas()
        
        print(f"\n=== Function Schemas ({len(schemas)}个) ===")
        
        # 找到repo_map的schema
        repo_map_schema = None
        for schema in schemas:
            if schema["name"] == "repo_map":
                repo_map_schema = schema
                break
        
        assert repo_map_schema is not None
        print("\n=== repo_map schema ===")
        import json
        print(json.dumps(repo_map_schema, indent=2, ensure_ascii=False))
        
        # 检查schema结构
        assert "name" in repo_map_schema
        assert "description" in repo_map_schema
        assert "parameters" in repo_map_schema
        assert "repo_path" in repo_map_schema["parameters"]["properties"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
