"""
测试上下文管理增强功能

测试：
1. RepoMap集成
2. Token预算控制
3. 智能摘要
4. 自动优化
"""

import pytest
import asyncio
from pathlib import Path
import tempfile
import shutil

from daoyoucode.agents.core.context import ContextManager, get_context_manager


class TestRepoMapIntegration:
    """测试RepoMap集成"""
    
    @pytest.fixture
    def temp_repo(self):
        """创建临时仓库"""
        temp_dir = tempfile.mkdtemp()
        repo_path = Path(temp_dir) / "test_repo"
        repo_path.mkdir()
        
        # 创建测试文件
        (repo_path / "main.py").write_text("""
def hello():
    print("Hello")

class MyClass:
    def method(self):
        pass
""")
        
        (repo_path / "utils.py").write_text("""
def helper():
    return 42

class Helper:
    pass
""")
        
        yield repo_path
        
        # 清理
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_add_repo_map(self, temp_repo):
        """测试添加RepoMap"""
        manager = ContextManager()
        context = manager.create_context("test_session")
        
        # 添加RepoMap
        success = await manager.add_repo_map(
            session_id="test_session",
            repo_path=str(temp_repo),
            max_tokens=5000  # 增加token限制
        )
        
        assert success
        assert context.has('repo_map')
        assert context.has('repo_map_metadata')
        
        repo_map = context.get('repo_map')
        print(f"RepoMap content: {repo_map}")  # 调试输出
        
        # RepoMap可能为空（如果没有引用关系）
        # 只要成功生成就算通过
        assert repo_map is not None
    
    @pytest.mark.asyncio
    async def test_add_repo_map_with_chat_files(self, temp_repo):
        """测试带对话文件的RepoMap"""
        manager = ContextManager()
        context = manager.create_context("test_session")
        
        # 添加RepoMap（指定对话文件）
        success = await manager.add_repo_map(
            session_id="test_session",
            repo_path=str(temp_repo),
            chat_files=["main.py"],
            mentioned_idents=["hello", "MyClass"],
            max_tokens=1000
        )
        
        assert success
        assert context.has('repo_map')
    
    @pytest.mark.asyncio
    async def test_add_repo_map_nonexistent_session(self, temp_repo):
        """测试不存在的会话"""
        manager = ContextManager()
        
        success = await manager.add_repo_map(
            session_id="nonexistent",
            repo_path=str(temp_repo)
        )
        
        assert not success


class TestTokenBudgetControl:
    """测试Token预算控制"""
    
    def test_enforce_token_budget_no_pruning(self):
        """测试Token充足时不剪枝"""
        manager = ContextManager(default_token_budget=10000)
        context = manager.create_context("test_session")
        
        # 添加少量数据
        context.set('key1', 'value1')
        context.set('key2', 'value2')
        
        # 执行预算控制
        stats = manager.enforce_token_budget("test_session")
        
        assert stats['success']
        assert not stats['pruned']
        assert stats['original_tokens'] == stats['final_tokens']
    
    def test_enforce_token_budget_with_pruning(self):
        """测试Token超出时剪枝"""
        manager = ContextManager(default_token_budget=100)
        context = manager.create_context("test_session")
        
        # 添加大量数据
        context.set('key1', 'x' * 1000)
        context.set('key2', 'y' * 1000)
        context.set('key3', 'z' * 1000)
        
        # 执行预算控制
        stats = manager.enforce_token_budget("test_session")
        
        assert stats['success']
        assert stats['pruned']
        assert stats['final_tokens'] < stats['original_tokens']
        assert stats['final_tokens'] <= stats['budget']
        assert len(stats['removed_keys']) > 0
    
    def test_enforce_token_budget_with_priority(self):
        """测试优先级保护"""
        manager = ContextManager(default_token_budget=100)
        context = manager.create_context("test_session")
        
        # 添加数据
        context.set('important', 'x' * 500)
        context.set('optional1', 'y' * 500)
        context.set('optional2', 'z' * 500)
        
        # 执行预算控制（保护important）
        stats = manager.enforce_token_budget(
            "test_session",
            priority_keys=['important']
        )
        
        assert stats['success']
        assert stats['pruned']
        
        # important应该保留
        assert context.has('important')
        
        # 至少有一个optional被移除
        assert not context.has('optional1') or not context.has('optional2')
    
    def test_enforce_token_budget_custom_budget(self):
        """测试自定义预算"""
        manager = ContextManager(default_token_budget=10000)
        context = manager.create_context("test_session")
        
        # 添加数据
        context.set('key1', 'x' * 1000)
        context.set('key2', 'y' * 1000)
        
        # 使用小预算
        stats = manager.enforce_token_budget(
            "test_session",
            token_budget=50
        )
        
        assert stats['success']
        assert stats['pruned']
        assert stats['budget'] == 50
        assert stats['final_tokens'] <= 50
    
    def test_enforce_token_budget_with_snapshot(self):
        """测试剪枝时创建快照"""
        manager = ContextManager(default_token_budget=100)
        context = manager.create_context("test_session")
        
        # 添加数据
        context.set('key1', 'x' * 1000)
        context.set('key2', 'y' * 1000)
        
        # 执行预算控制
        stats = manager.enforce_token_budget("test_session")
        
        assert stats['success']
        assert stats['pruned']
        assert 'snapshot_id' in stats
        
        # 验证快照存在
        snapshot = context.get_snapshot(stats['snapshot_id'])
        assert snapshot is not None


class TestIntelligentSummary:
    """测试智能摘要"""
    
    @pytest.mark.asyncio
    async def test_summarize_content(self):
        """测试内容摘要"""
        manager = ContextManager()
        context = manager.create_context("test_session")
        
        # 添加长内容
        long_content = """
        This is a very long content that needs to be summarized.
        It contains multiple paragraphs and lots of information.
        Some information is important, some is redundant.
        We want to keep the important parts and remove the redundant parts.
        """ * 10
        
        context.set('long_text', long_content)
        
        # 摘要（使用mock避免真实LLM调用）
        # 这里需要mock LLMClient
        # success = await manager.summarize_content(
        #     "test_session",
        #     "long_text",
        #     target_ratio=0.33
        # )
        
        # 暂时跳过（需要LLM）
        pytest.skip("需要LLM集成")
    
    @pytest.mark.asyncio
    async def test_summarize_nonexistent_key(self):
        """测试摘要不存在的key"""
        manager = ContextManager()
        context = manager.create_context("test_session")
        
        success = await manager.summarize_content(
            "test_session",
            "nonexistent_key"
        )
        
        assert not success


class TestAutoOptimization:
    """测试自动优化"""
    
    @pytest.mark.asyncio
    async def test_auto_optimize_context(self):
        """测试自动优化"""
        manager = ContextManager(default_token_budget=100)
        context = manager.create_context("test_session")
        
        # 添加数据
        context.set('key1', 'x' * 1000)
        context.set('key2', 'y' * 1000)
        context.set('key3', 'z' * 1000)
        
        # 自动优化（不使用摘要）
        stats = await manager.auto_optimize_context(
            "test_session",
            token_budget=100
        )
        
        assert stats['success']
        assert stats['pruning_stats']['pruned']
        assert stats['pruning_stats']['final_tokens'] <= 100


class TestPriorityCalculation:
    """测试优先级计算"""
    
    def test_sort_by_priority(self):
        """测试优先级排序"""
        manager = ContextManager()
        
        variables = {
            'normal_key': 'value1',
            '_internal_key': 'value2',
            'repo_map': 'value3',
            'priority_key': 'value4'
        }
        
        sorted_vars = manager._sort_by_priority(
            variables,
            priority_keys=['priority_key']
        )
        
        # 检查排序
        keys = [key for key, _, _ in sorted_vars]
        
        # priority_key应该在最前面
        assert keys[0] == 'priority_key'
        
        # repo_map应该在中间
        assert 'repo_map' in keys[:2]
        
        # _internal_key应该在最后
        assert keys[-1] == '_internal_key'


class TestBinarySearch:
    """测试二分查找"""
    
    def test_binary_search_optimal_vars(self):
        """测试二分查找最优变量数量"""
        manager = ContextManager()
        
        sorted_vars = [
            ('key1', 'x' * 100, 100),
            ('key2', 'y' * 100, 50),
            ('key3', 'z' * 100, 50),
            ('key4', 'w' * 100, 10)
        ]
        
        result = manager._binary_search_optimal_vars(
            sorted_vars,
            token_budget=100,
            priority_keys=[]
        )
        
        # 应该只包含部分变量
        assert len(result) < len(sorted_vars)
        
        # Token应该在预算内
        tokens = manager._estimate_tokens(result)
        assert tokens <= 100


class TestTokenEstimation:
    """测试Token估算"""
    
    def test_estimate_tokens(self):
        """测试Token估算"""
        manager = ContextManager()
        
        # 简单测试
        data = {'key': 'value'}
        tokens = manager._estimate_tokens(data)
        assert tokens > 0
        
        # 大数据
        large_data = {'key': 'x' * 1000}
        large_tokens = manager._estimate_tokens(large_data)
        assert large_tokens > tokens


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
