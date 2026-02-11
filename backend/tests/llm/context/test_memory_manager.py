"""
测试记忆管理器
"""

import pytest
from datetime import datetime

from daoyoucode.llm.context import MemoryManager


@pytest.fixture
def memory_manager():
    """创建记忆管理器"""
    return MemoryManager(max_history=5, max_sessions=10)


class TestMemoryManager:
    """测试MemoryManager"""
    
    def test_init(self):
        """测试初始化"""
        manager = MemoryManager()
        assert manager.max_history == 10
        assert manager.max_sessions == 1000
        assert manager.get_session_count() == 0
    
    def test_add_message(self, memory_manager):
        """测试添加消息"""
        memory_manager.add_message(
            "session1",
            "你好",
            "你好！有什么可以帮助你的？"
        )
        
        history = memory_manager.get_history("session1")
        assert len(history) == 1
        assert history[0]['user'] == "你好"
        assert history[0]['ai'] == "你好！有什么可以帮助你的？"
    
    def test_add_multiple_messages(self, memory_manager):
        """测试添加多条消息"""
        for i in range(3):
            memory_manager.add_message(
                "session1",
                f"消息{i}",
                f"回复{i}"
            )
        
        history = memory_manager.get_history("session1")
        assert len(history) == 3
    
    def test_max_history_limit(self, memory_manager):
        """测试历史记录限制"""
        # 添加超过max_history的消息
        for i in range(10):
            memory_manager.add_message(
                "session1",
                f"消息{i}",
                f"回复{i}"
            )
        
        history = memory_manager.get_history("session1")
        # 应该只保留最近5条
        assert len(history) == 5
        # 最后一条应该是消息9
        assert history[-1]['user'] == "消息9"
    
    def test_get_history_with_limit(self, memory_manager):
        """测试获取限制数量的历史"""
        for i in range(5):
            memory_manager.add_message(
                "session1",
                f"消息{i}",
                f"回复{i}"
            )
        
        # 只获取最近2条
        history = memory_manager.get_history("session1", limit=2)
        assert len(history) == 2
        assert history[0]['user'] == "消息3"
        assert history[1]['user'] == "消息4"
    
    def test_get_recent_context(self, memory_manager):
        """测试获取最近上下文"""
        memory_manager.add_message(
            "session1",
            "猫不吃东西",
            "可能是生病了，建议观察..."
        )
        memory_manager.add_message(
            "session1",
            "还呕吐",
            "呕吐加上不吃东西，建议立即就医..."
        )
        
        context = memory_manager.get_recent_context("session1", rounds=2)
        
        assert "猫不吃东西" in context
        assert "还呕吐" in context
        assert "[第1轮]" in context
        assert "[第2轮]" in context
    
    def test_multiple_sessions(self, memory_manager):
        """测试多个会话"""
        memory_manager.add_message("session1", "消息1", "回复1")
        memory_manager.add_message("session2", "消息2", "回复2")
        
        assert memory_manager.get_session_count() == 2
        
        history1 = memory_manager.get_history("session1")
        history2 = memory_manager.get_history("session2")
        
        assert len(history1) == 1
        assert len(history2) == 1
        assert history1[0]['user'] == "消息1"
        assert history2[0]['user'] == "消息2"
    
    def test_clear_session(self, memory_manager):
        """测试清除会话"""
        memory_manager.add_message("session1", "消息1", "回复1")
        assert memory_manager.get_session_count() == 1
        
        memory_manager.clear_session("session1")
        assert memory_manager.get_session_count() == 0
        
        history = memory_manager.get_history("session1")
        assert len(history) == 0
    
    def test_max_sessions_cleanup(self, memory_manager):
        """测试最大会话数清理"""
        # 添加超过max_sessions的会话
        for i in range(15):
            memory_manager.add_message(f"session{i}", f"消息{i}", f"回复{i}")
        
        # 应该只保留最近10个
        assert memory_manager.get_session_count() == 10
    
    def test_get_stats(self, memory_manager):
        """测试获取统计信息"""
        memory_manager.add_message("session1", "消息1", "回复1")
        memory_manager.add_message("session1", "消息2", "回复2")
        memory_manager.add_message("session2", "消息3", "回复3")
        
        stats = memory_manager.get_stats()
        
        assert stats['total_sessions'] == 2
        assert stats['total_messages'] == 3
        assert stats['max_history'] == 5
        assert stats['max_sessions'] == 10
    
    def test_metadata(self, memory_manager):
        """测试元数据"""
        memory_manager.add_message(
            "session1",
            "消息1",
            "回复1",
            metadata={'skill': 'test_skill', 'model': 'qwen-max'}
        )
        
        history = memory_manager.get_history("session1")
        assert history[0]['metadata']['skill'] == 'test_skill'
        assert history[0]['metadata']['model'] == 'qwen-max'
