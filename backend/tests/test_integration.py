"""
集成测试 - 验证所有组件正确连接

测试范围：
1. Agent + 工具系统
2. Agent + 记忆系统
3. Agent + 上下文管理
4. Agent + RepoMap
5. Agent + LSP工具
6. 完整工作流
"""

import pytest
import asyncio
from pathlib import Path
import tempfile
import shutil

from daoyoucode.agents.core.agent import BaseAgent, AgentConfig, AgentResult
from daoyoucode.agents.tools import get_tool_registry
from daoyoucode.agents.memory import get_memory_manager
from daoyoucode.agents.core.context import ContextManager


class TestIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_agent_with_tools(self):
        """测试Agent + 工具系统集成"""
        # 创建Agent
        config = AgentConfig(
            name="test_agent",
            description="测试Agent",
            model="gpt-3.5-turbo",
            system_prompt="你是一个测试助手"
        )
        agent = BaseAgent(config)
        
        # 获取工具注册表
        registry = get_tool_registry()
        tools = registry.list_tools()
        
        # 验证工具已注册
        assert len(tools) == 25  # 6文件+2搜索+4Git+2命令+1Diff+2RepoMap+6LSP+2AST
        assert "read_file" in tools
        assert "write_file" in tools
        assert "repo_map" in tools
        assert "lsp_diagnostics" in tools
        assert "ast_grep_search" in tools
        assert "ast_grep_replace" in tools
        
        print(f"\n✅ 工具系统集成成功: {len(tools)}个工具已注册")
    
    @pytest.mark.asyncio
    async def test_agent_with_memory(self):
        """测试Agent + 记忆系统集成"""
        # 创建Agent
        config = AgentConfig(
            name="test_agent",
            description="测试Agent",
            model="gpt-3.5-turbo",
            system_prompt="你是一个测试助手"
        )
        agent = BaseAgent(config)
        
        # 验证记忆系统已连接
        assert agent.memory is not None
        
        # 测试记忆功能
        session_id = "test_session"
        agent.memory.add_conversation(session_id, "你好", "你好！有什么可以帮助你的？")
        
        history = agent.memory.get_conversation_history(session_id)
        assert len(history) > 0
        
        print(f"\n✅ 记忆系统集成成功: 对话历史已保存")
    
    @pytest.mark.asyncio
    async def test_agent_with_context(self):
        """测试Agent + 上下文管理集成"""
        # 创建上下文管理器
        context_manager = ContextManager()
        
        session_id = "test_session"
        context = context_manager.create_context(session_id)
        
        # 设置变量
        context.set("user_name", "Alice")
        context.set("task", "代码审查")
        
        # 获取变量
        user_name = context.get("user_name")
        assert user_name == "Alice"
        
        # 创建快照
        snapshot_id = context.create_snapshot("初始状态")
        assert snapshot_id is not None
        
        print(f"\n✅ 上下文管理集成成功: 变量和快照功能正常")
    
    @pytest.mark.asyncio
    async def test_repomap_integration(self):
        """测试RepoMap集成"""
        # 创建临时仓库
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            
            # 创建测试文件
            (repo_path / "test.py").write_text("""
class Calculator:
    def add(self, a, b):
        return a + b
    
    def subtract(self, a, b):
        return a - b

def main():
    calc = Calculator()
    print(calc.add(1, 2))
""")
            
            # 获取工具注册表
            registry = get_tool_registry()
            
            # 执行RepoMap
            result = await registry.execute_tool(
                "repo_map",
                repo_path=str(repo_path),
                max_tokens=500
            )
            
            assert result.success
            # RepoMap可能返回空（如果没有引用关系），这是正常的
            print(f"\n✅ RepoMap集成成功:")
            print(f"   内容: {result.content[:200] if result.content else '(空)'}")
    
    @pytest.mark.asyncio
    async def test_context_with_repomap(self):
        """测试上下文管理器 + RepoMap集成"""
        # 创建临时仓库
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            
            # 创建测试文件
            (repo_path / "utils.py").write_text("""
def format_date(date):
    return date.strftime("%Y-%m-%d")

def parse_date(date_str):
    from datetime import datetime
    return datetime.strptime(date_str, "%Y-%m-%d")
""")
            
            # 创建上下文管理器
            context_manager = ContextManager()
            session_id = "test_session"
            context = context_manager.create_context(session_id)
            
            # 添加RepoMap到上下文
            await context_manager.add_repo_map(
                session_id,
                repo_path=str(repo_path),
                chat_files=[],
                mentioned_idents=["format_date"],
                max_tokens=500
            )
            
            # 验证RepoMap已添加
            repo_map = context.get("repo_map")
            assert repo_map is not None
            
            print(f"\n✅ 上下文+RepoMap集成成功:")
            print(f"   RepoMap: {repo_map[:200] if repo_map else '(空)'}...")
    
    @pytest.mark.asyncio
    async def test_token_budget_control(self):
        """测试Token预算控制"""
        context_manager = ContextManager()
        session_id = "test_session"
        context = context_manager.create_context(session_id)
        
        # 添加大量内容（确保超出预算）
        for i in range(20):
            context.set(f"file_{i}", "x" * 2000)  # 每个文件2000字符
        
        # 执行Token预算控制（设置较小的预算确保会剪枝）
        result = context_manager.enforce_token_budget(
            session_id,
            token_budget=5000,  # 5000 tokens ≈ 20000字符，但我们有40000字符
            priority_keys=[]
        )
        
        assert result['success']
        assert result['pruned']  # 应该发生剪枝
        assert result['final_tokens'] <= result['budget']
        
        print(f"\n✅ Token预算控制成功: {result['original_tokens']} -> {result['final_tokens']} tokens")
    
    @pytest.mark.skip(reason="Requires real LLM client")
    @pytest.mark.asyncio
    async def test_intelligent_summary(self):
        """测试智能摘要"""
        context_manager = ContextManager()
        session_id = "test_session"
        context = context_manager.create_context(session_id)
        
        # 添加长文本
        long_text = """
        这是一个很长的文本，包含了很多信息。
        第一部分讲述了项目的背景和目标。
        第二部分介绍了技术架构和实现细节。
        第三部分讨论了测试策略和质量保证。
        第四部分展望了未来的发展方向。
        """ * 10
        
        context.set("long_doc", long_text)
        
        # 执行智能摘要（需要真实LLM）
        success = await context_manager.summarize_content(
            session_id,
            "long_doc",
            target_ratio=0.33,
            model="gpt-4o-mini"
        )
        
        assert success
        
        # 获取摘要后的内容
        summarized = context.get("long_doc")
        assert summarized
        assert len(summarized) < len(long_text)
        
        print(f"\n✅ 智能摘要成功: {len(long_text)} -> {len(summarized)} 字符")
    
    @pytest.mark.asyncio
    async def test_file_tools_integration(self):
        """测试文件工具集成"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            
            registry = get_tool_registry()
            
            # 测试write_file
            result = await registry.execute_tool(
                "write_file",
                file_path=str(test_file),
                content="Hello, World!"
            )
            assert result.success
            
            # 测试read_file
            result = await registry.execute_tool(
                "read_file",
                file_path=str(test_file)
            )
            assert result.success
            assert result.content == "Hello, World!"
            
            # 测试list_files
            result = await registry.execute_tool(
                "list_files",
                directory=str(tmpdir)
            )
            assert result.success
            assert len(result.content) > 0
            
            print(f"\n✅ 文件工具集成成功: write/read/list 功能正常")
    
    @pytest.mark.asyncio
    async def test_search_tools_integration(self):
        """测试搜索工具集成"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试文件
            (Path(tmpdir) / "file1.py").write_text("def hello(): pass")
            (Path(tmpdir) / "file2.py").write_text("def world(): pass")
            
            registry = get_tool_registry()
            
            # 测试text_search
            result = await registry.execute_tool(
                "text_search",
                query="hello",
                directory=str(tmpdir)
            )
            assert result.success
            assert len(result.content) > 0
            
            # 测试regex_search
            result = await registry.execute_tool(
                "regex_search",
                pattern=r"def \w+\(\)",
                directory=str(tmpdir)
            )
            assert result.success
            assert len(result.content) > 0
            
            print(f"\n✅ 搜索工具集成成功: text/regex 搜索功能正常")
    
    @pytest.mark.asyncio
    async def test_diff_tool_integration(self):
        """测试Diff工具集成"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("""
def hello():
    print("Hello")
    return True
""")
            
            registry = get_tool_registry()
            
            # 测试search_replace
            result = await registry.execute_tool(
                "search_replace",
                file_path=str(test_file),
                search='print("Hello")',
                replace='print("Hi there!")'
            )
            assert result.success
            
            # 验证替换成功
            content = test_file.read_text()
            assert "Hi there!" in content
            
            print(f"\n✅ Diff工具集成成功: search_replace 功能正常")
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """测试完整工作流：Agent + 所有系统"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 1. 创建测试环境
            repo_path = Path(tmpdir)
            (repo_path / "main.py").write_text("""
def calculate(a, b):
    return a + b

def main():
    result = calculate(1, 2)
    print(result)
""")
            
            # 2. 创建Agent
            config = AgentConfig(
                name="code_assistant",
                description="代码助手",
                model="gpt-3.5-turbo",
                system_prompt="你是一个代码助手，帮助用户分析和修改代码"
            )
            agent = BaseAgent(config)
            
            # 3. 创建上下文
            context_manager = ContextManager()
            session_id = "workflow_test"
            context_manager.create_context(session_id)
            
            # 4. 添加RepoMap到上下文
            await context_manager.add_repo_map(
                session_id,
                repo_path=str(repo_path),
                chat_files=[],
                mentioned_idents=["calculate"],
                max_tokens=1000
            )
            
            # 5. 获取上下文
            context = context_manager.get_context(session_id)
            
            # 6. 验证集成
            assert agent.memory is not None  # 记忆系统
            assert context.get("repo_map") is not None  # RepoMap
            assert len(get_tool_registry().list_tools()) == 25  # 工具系统
            
            print(f"\n✅ 完整工作流集成成功:")
            print(f"   - Agent: {agent.name}")
            print(f"   - 记忆系统: 已连接")
            print(f"   - 上下文管理: 已创建")
            print(f"   - RepoMap: 已添加")
            print(f"   - 工具系统: {len(get_tool_registry().list_tools())}个工具")


class TestToolRegistry:
    """工具注册表测试"""
    
    def test_all_tools_registered(self):
        """测试所有工具已注册"""
        registry = get_tool_registry()
        tools = registry.list_tools()
        
        # 验证工具数量
        assert len(tools) == 25
        
        # 验证文件工具（6个）
        assert "read_file" in tools
        assert "write_file" in tools
        assert "list_files" in tools
        assert "get_file_info" in tools
        assert "create_directory" in tools
        assert "delete_file" in tools
        
        # 验证搜索工具（2个）
        assert "text_search" in tools
        assert "regex_search" in tools
        
        # 验证Git工具（4个）
        assert "git_status" in tools
        assert "git_diff" in tools
        assert "git_commit" in tools
        assert "git_log" in tools
        
        # 验证命令工具（2个）
        assert "run_command" in tools
        assert "run_test" in tools
        
        # 验证Diff工具（1个）
        assert "search_replace" in tools
        
        # 验证RepoMap工具（2个）
        assert "repo_map" in tools
        assert "get_repo_structure" in tools
        
        # 验证LSP工具（6个）
        assert "lsp_diagnostics" in tools
        assert "lsp_goto_definition" in tools
        assert "lsp_find_references" in tools
        assert "lsp_symbols" in tools
        assert "lsp_rename" in tools
        assert "lsp_code_actions" in tools
        
        # 验证AST工具（2个）
        assert "ast_grep_search" in tools
        assert "ast_grep_replace" in tools
        
        print(f"\n✅ 所有25个工具已正确注册")
    
    def test_get_function_schemas(self):
        """测试获取Function schemas"""
        registry = get_tool_registry()
        
        # 获取部分工具的schemas
        schemas = registry.get_function_schemas([
            "read_file",
            "write_file",
            "repo_map"
        ])
        
        assert len(schemas) == 3
        
        # 验证schema格式
        for schema in schemas:
            assert "name" in schema
            assert "description" in schema
            assert "parameters" in schema
        
        print(f"\n✅ Function schemas 格式正确")


class TestMemoryIntegration:
    """记忆系统集成测试"""
    
    def test_memory_singleton(self):
        """测试记忆系统单例"""
        from daoyoucode.agents.memory import get_memory_manager
        
        manager1 = get_memory_manager()
        manager2 = get_memory_manager()
        
        assert manager1 is manager2
        
        print(f"\n✅ 记忆系统单例模式正常")
    
    def test_conversation_memory(self):
        """测试对话记忆"""
        from daoyoucode.agents.memory import get_memory_manager
        
        manager = get_memory_manager()
        session_id = "test_conv"
        
        # 添加对话
        manager.add_conversation(session_id, "你好", "你好！")
        manager.add_conversation(session_id, "天气如何", "今天天气不错")
        
        # 获取历史
        history = manager.get_conversation_history(session_id)
        assert len(history) >= 2
        
        print(f"\n✅ 对话记忆功能正常: {len(history)}轮对话")
    
    def test_task_memory(self):
        """测试任务记忆"""
        from daoyoucode.agents.memory import get_memory_manager
        
        manager = get_memory_manager()
        user_id = "test_user"
        
        # 添加任务
        manager.add_task(user_id, {
            'agent': 'test_agent',
            'input': '分析代码',
            'result': '分析完成',
            'success': True
        })
        
        # 获取历史
        history = manager.get_task_history(user_id)
        assert len(history) > 0
        
        print(f"\n✅ 任务记忆功能正常: {len(history)}个任务")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
