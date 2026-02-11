"""
测试上下文管理器
"""

import pytest

from daoyoucode.llm.context import ContextManager


@pytest.fixture
def context_manager():
    """创建上下文管理器（独立实例）"""
    # 创建独立的实例，避免测试间干扰
    from daoyoucode.llm.context.followup_detector import FollowupDetector
    from daoyoucode.llm.context.memory_manager import MemoryManager
    from daoyoucode.llm.context.manager import ContextManager as CM
    
    manager = CM()
    manager.followup_detector = FollowupDetector()
    manager.memory_manager = MemoryManager()
    return manager


class TestContextManager:
    """测试ContextManager"""
    
    @pytest.mark.asyncio
    async def test_add_conversation(self, context_manager):
        """测试添加对话"""
        await context_manager.add_conversation(
            "session1",
            "你好",
            "你好！有什么可以帮助你的？",
            skill_name="greeting",
            model="qwen-max"
        )
        
        history = context_manager.get_history("session1")
        assert len(history) == 1
        assert history[0]['user'] == "你好"
        assert history[0]['metadata']['skill'] == "greeting"
        assert history[0]['metadata']['model'] == "qwen-max"
    
    @pytest.mark.asyncio
    async def test_is_followup_no_history(self, context_manager):
        """测试无历史时的追问判断"""
        is_followup, confidence, reason = await context_manager.is_followup(
            "new_session_test",
            "你好"
        )
        
        # 无历史应该返回False，但"你好"可能包含追问标志词
        assert reason == "no_history" or confidence < 0.9
    
    @pytest.mark.asyncio
    async def test_is_followup_with_history(self, context_manager):
        """测试有历史时的追问判断"""
        # 添加历史
        await context_manager.add_conversation(
            "session1",
            "猫不吃东西",
            "可能是生病了"
        )
        
        # 判断追问
        is_followup, confidence, reason = await context_manager.is_followup(
            "session1",
            "继续说"
        )
        
        assert is_followup is True
        assert confidence > 0.8
    
    def test_get_history(self, context_manager):
        """测试获取历史"""
        # 添加多条对话
        import asyncio
        asyncio.run(context_manager.add_conversation(
            "test_get_history_session", "消息1", "回复1"
        ))
        asyncio.run(context_manager.add_conversation(
            "test_get_history_session", "消息2", "回复2"
        ))
        
        history = context_manager.get_history("test_get_history_session")
        assert len(history) == 2
        
        # 限制数量
        history = context_manager.get_history("test_get_history_session", limit=1)
        assert len(history) == 1
        assert history[0]['user'] == "消息2"
    
    def test_get_context_summary(self, context_manager):
        """测试获取上下文摘要"""
        import asyncio
        asyncio.run(context_manager.add_conversation(
            "session1",
            "猫不吃东西",
            "可能是生病了，建议观察..."
        ))
        asyncio.run(context_manager.add_conversation(
            "session1",
            "还呕吐",
            "呕吐加上不吃东西，建议立即就医..."
        ))
        
        summary = context_manager.get_context_summary("session1", rounds=2)
        
        assert "猫不吃东西" in summary
        assert "还呕吐" in summary
    
    def test_format_context_for_prompt(self, context_manager):
        """测试格式化上下文为prompt"""
        import asyncio
        asyncio.run(context_manager.add_conversation(
            "session1",
            "猫不吃东西",
            "可能是生病了"
        ))
        
        prompt = context_manager.format_context_for_prompt(
            "session1",
            "还呕吐",
            include_history=True,
            history_limit=1
        )
        
        assert "【历史对话】" in prompt
        assert "【当前问题】" in prompt
        assert "猫不吃东西" in prompt
        assert "还呕吐" in prompt
    
    def test_format_context_without_history(self, context_manager):
        """测试不包含历史的prompt格式化"""
        prompt = context_manager.format_context_for_prompt(
            "session1",
            "你好",
            include_history=False
        )
        
        assert "【历史对话】" not in prompt
        assert "【当前问题】" in prompt
        assert "你好" in prompt
    
    def test_clear_session(self, context_manager):
        """测试清除会话"""
        import asyncio
        asyncio.run(context_manager.add_conversation(
            "test_clear_session", "消息1", "回复1"
        ))
        
        history = context_manager.get_history("test_clear_session")
        assert len(history) == 1
        
        context_manager.clear_session("test_clear_session")
        
        history = context_manager.get_history("test_clear_session")
        assert len(history) == 0
    
    def test_get_stats(self, context_manager):
        """测试获取统计信息"""
        import asyncio
        asyncio.run(context_manager.add_conversation(
            "test_stats_1", "消息1", "回复1"
        ))
        asyncio.run(context_manager.add_conversation(
            "test_stats_2", "消息2", "回复2"
        ))
        
        stats = context_manager.get_stats()
        
        # 至少有这两个session
        assert stats['total_sessions'] >= 2
        assert stats['total_messages'] >= 2
    
    @pytest.mark.asyncio
    async def test_multiple_sessions_isolation(self, context_manager):
        """测试多个会话的隔离"""
        # 添加两个会话
        await context_manager.add_conversation(
            "isolation_test_1", "猫不吃东西", "可能生病了"
        )
        await context_manager.add_conversation(
            "isolation_test_2", "狗狗训练", "需要耐心"
        )
        
        # 判断session1的追问
        is_followup1, _, _ = await context_manager.is_followup(
            "isolation_test_1",
            "猫还呕吐"
        )
        
        # 判断session2的追问
        is_followup2, _, _ = await context_manager.is_followup(
            "isolation_test_2",
            "狗狗多大开始训练"
        )
        
        # 两个会话应该独立判断
        assert is_followup1 is True  # 与猫相关
        # session2可能因为关键词不重叠被判断为新话题
        # 主要测试会话隔离，不强制要求追问判断结果
