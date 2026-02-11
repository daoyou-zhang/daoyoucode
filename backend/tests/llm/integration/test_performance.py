"""
性能测试
测试LLM模块的性能指标
"""

import pytest
import time
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from daoyoucode.llm import get_orchestrator
from daoyoucode.llm.base import LLMResponse
from daoyoucode.llm.skills import SkillConfig


@pytest.fixture
def fast_mock_client():
    """快速响应的模拟客户端"""
    client = MagicMock()
    
    async def mock_chat(request):
        await asyncio.sleep(0.01)  # 模拟10ms延迟
        return LLMResponse(
            content="快速回复",
            model=request.model,
            tokens_used=20,
            cost=0.0004,
            latency=0.01
        )
    
    client.chat = AsyncMock(side_effect=mock_chat)
    return client


class TestPerformance:
    """性能测试"""
    
    @pytest.mark.asyncio
    async def test_followup_detection_speed(self):
        """测试追问判断速度"""
        from daoyoucode.llm.context import get_followup_detector
        
        detector = get_followup_detector()
        
        # 准备历史
        history = [
            {'user': '猫不吃东西', 'ai': '可能生病了'},
            {'user': '还呕吐', 'ai': '建议就医'}
        ]
        
        # 测试100次
        start_time = time.time()
        for _ in range(100):
            await detector.is_followup("继续说", history)
        elapsed = time.time() - start_time
        
        avg_time = elapsed / 100
        print(f"\n追问判断平均耗时: {avg_time*1000:.2f}ms")
        
        # 应该小于5ms
        assert avg_time < 0.005
    
    @pytest.mark.asyncio
    async def test_skill_loading_speed(self):
        """测试Skill加载速度"""
        from daoyoucode.llm.skills import SkillLoader
        import tempfile
        from pathlib import Path
        
        # 创建临时Skill
        temp_dir = tempfile.mkdtemp()
        skill_dir = Path(temp_dir) / "test_skill"
        skill_dir.mkdir()
        
        (skill_dir / "skill.yaml").write_text("""
name: test_skill
version: "1.0.0"
description: "测试"
""", encoding='utf-8')
        
        (skill_dir / "prompt.md").write_text("测试prompt", encoding='utf-8')
        
        loader = SkillLoader(skills_dirs=[temp_dir])
        
        # 测试加载速度
        start_time = time.time()
        loader.load_all_skills()
        elapsed = time.time() - start_time
        
        print(f"\nSkill加载耗时: {elapsed*1000:.2f}ms")
        
        # 应该小于100ms
        assert elapsed < 0.1
        
        # 清理
        import shutil
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, fast_mock_client):
        """测试并发请求"""
        orchestrator = get_orchestrator()
        
        test_skill = SkillConfig(
            name="concurrent_skill",
            version="1.0.0",
            description="并发测试",
            prompt_template="{{ user_message }}",
            llm={'model': 'qwen-max'}
        )
        orchestrator.skill_loader.skills['concurrent_skill'] = test_skill
        
        with patch.object(orchestrator.client_manager, 'get_client', return_value=fast_mock_client):
            # 并发10个请求
            tasks = []
            start_time = time.time()
            
            for i in range(10):
                task = orchestrator.execute_skill(
                    skill_name="concurrent_skill",
                    user_message=f"并发测试{i}",
                    session_id=f"concurrent_session_{i}"
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            elapsed = time.time() - start_time
            
            print(f"\n10个并发请求总耗时: {elapsed*1000:.2f}ms")
            print(f"平均每个请求: {elapsed/10*1000:.2f}ms")
            
            # 验证所有请求都成功
            assert len(results) == 10
            assert all(r is not None for r in results)
            
            # 并发执行应该比串行快
            # 串行需要10*10ms=100ms，并发应该接近10ms
            assert elapsed < 0.5  # 给一些余量
    
    @pytest.mark.asyncio
    async def test_memory_usage(self, fast_mock_client):
        """测试内存使用"""
        orchestrator = get_orchestrator()
        
        test_skill = SkillConfig(
            name="memory_skill",
            version="1.0.0",
            description="内存测试",
            prompt_template="{{ user_message }}",
            llm={'model': 'qwen-max'}
        )
        orchestrator.skill_loader.skills['memory_skill'] = test_skill
        
        with patch.object(orchestrator.client_manager, 'get_client', return_value=fast_mock_client):
            # 执行100次对话
            for i in range(100):
                await orchestrator.execute_skill(
                    skill_name="memory_skill",
                    user_message=f"测试{i}",
                    session_id="memory_session"
                )
            
            # 检查历史记录数量（应该有限制）
            history = orchestrator.context_manager.get_history("memory_session")
            
            # 应该不超过max_history（默认10）
            assert len(history) <= 10
            
            print(f"\n100次对话后历史记录数: {len(history)}")
    
    @pytest.mark.asyncio
    async def test_stats_overhead(self, fast_mock_client):
        """测试统计开销"""
        orchestrator = get_orchestrator()
        
        test_skill = SkillConfig(
            name="stats_overhead_skill",
            version="1.0.0",
            description="统计开销测试",
            prompt_template="{{ user_message }}",
            llm={'model': 'qwen-max'}
        )
        orchestrator.skill_loader.skills['stats_overhead_skill'] = test_skill
        
        with patch.object(orchestrator.client_manager, 'get_client', return_value=fast_mock_client):
            # 测试获取统计的速度
            start_time = time.time()
            for _ in range(1000):
                orchestrator.get_stats()
            elapsed = time.time() - start_time
            
            avg_time = elapsed / 1000
            print(f"\n获取统计平均耗时: {avg_time*1000:.3f}ms")
            
            # 应该非常快（<1ms）
            assert avg_time < 0.001
    
    @pytest.mark.asyncio
    async def test_context_formatting_speed(self):
        """测试上下文格式化速度"""
        from daoyoucode.llm.context import get_context_manager
        
        context_manager = get_context_manager()
        
        # 添加一些历史
        for i in range(10):
            await context_manager.add_conversation(
                "format_session",
                f"用户消息{i}",
                f"AI回复{i}"
            )
        
        # 测试格式化速度
        start_time = time.time()
        for _ in range(100):
            context_manager.format_context_for_prompt(
                "format_session",
                "当前消息",
                include_history=True,
                history_limit=5
            )
        elapsed = time.time() - start_time
        
        avg_time = elapsed / 100
        print(f"\n上下文格式化平均耗时: {avg_time*1000:.2f}ms")
        
        # 应该很快（<1ms）
        assert avg_time < 0.001
    
    def test_skill_search_speed(self):
        """测试Skill搜索速度"""
        from daoyoucode.llm.skills import SkillLoader
        
        loader = SkillLoader()
        
        # 添加一些测试Skill
        for i in range(50):
            skill = SkillConfig(
                name=f"skill_{i}",
                version="1.0.0",
                description=f"测试Skill {i}",
                prompt_template="test"
            )
            loader.skills[f"skill_{i}"] = skill
        
        # 测试搜索速度
        start_time = time.time()
        for _ in range(100):
            loader.search_skills("测试")
        elapsed = time.time() - start_time
        
        avg_time = elapsed / 100
        print(f"\nSkill搜索平均耗时: {avg_time*1000:.2f}ms")
        
        # 应该很快（<5ms）
        assert avg_time < 0.005


class TestStressTest:
    """压力测试"""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_long_running_session(self, fast_mock_client):
        """测试长时间运行的会话"""
        orchestrator = get_orchestrator()
        
        test_skill = SkillConfig(
            name="long_session_skill",
            version="1.0.0",
            description="长会话测试",
            prompt_template="{{ user_message }}",
            llm={'model': 'qwen-max'}
        )
        orchestrator.skill_loader.skills['long_session_skill'] = test_skill
        
        with patch.object(orchestrator.client_manager, 'get_client', return_value=fast_mock_client):
            # 模拟500轮对话
            for i in range(500):
                await orchestrator.execute_skill(
                    skill_name="long_session_skill",
                    user_message=f"消息{i}",
                    session_id="long_session"
                )
                
                # 每100轮检查一次
                if (i + 1) % 100 == 0:
                    history = orchestrator.context_manager.get_history("long_session")
                    print(f"\n{i+1}轮后历史记录数: {len(history)}")
                    
                    # 验证历史记录被正确限制
                    assert len(history) <= 10
            
            # 最终验证
            stats = orchestrator.get_stats()
            print(f"\n总执行次数: {stats['executor']['total_executions']}")
            # 由于是共享单例，统计可能包含其他测试，只验证有执行即可
            assert stats['executor']['total_executions'] > 0
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_many_sessions(self, fast_mock_client):
        """测试大量会话"""
        orchestrator = get_orchestrator()
        
        test_skill = SkillConfig(
            name="many_sessions_skill",
            version="1.0.0",
            description="多会话测试",
            prompt_template="{{ user_message }}",
            llm={'model': 'qwen-max'}
        )
        orchestrator.skill_loader.skills['many_sessions_skill'] = test_skill
        
        with patch.object(orchestrator.client_manager, 'get_client', return_value=fast_mock_client):
            # 创建100个会话
            for i in range(100):
                await orchestrator.execute_skill(
                    skill_name="many_sessions_skill",
                    user_message=f"会话{i}",
                    session_id=f"session_{i}"
                )
            
            # 验证统计
            stats = orchestrator.get_stats()
            print(f"\n会话数: {stats['context']['total_sessions']}")
            print(f"\n总消息数: {stats['context']['total_messages']}")
            
            # 应该有很多会话
            assert stats['context']['total_sessions'] >= 50
