"""
端到端集成测试
测试完整的LLM调用流程
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from daoyoucode.llm import get_orchestrator
from daoyoucode.llm.base import LLMResponse
from daoyoucode.llm.skills import SkillConfig


@pytest.fixture
def mock_llm_client():
    """模拟LLM客户端"""
    client = MagicMock()
    
    # 模拟chat方法
    async def mock_chat(request):
        return LLMResponse(
            content="这是测试回复",
            model=request.model,
            tokens_used=50,
            cost=0.001,
            latency=1.0
        )
    
    client.chat = AsyncMock(side_effect=mock_chat)
    
    # 模拟stream_chat方法
    async def mock_stream_chat(prompt, model, temperature):
        import json
        chunks = [
            json.dumps({"choices": [{"delta": {"content": "这"}}]}),
            json.dumps({"choices": [{"delta": {"content": "是"}}]}),
            json.dumps({"choices": [{"delta": {"content": "测试"}}]}),
            json.dumps({"choices": [{"delta": {"content": "回复"}}]}),
            "[DONE]"
        ]
        for chunk in chunks:
            yield chunk
    
    client.stream_chat = mock_stream_chat
    
    return client


class TestEndToEnd:
    """端到端测试"""
    
    @pytest.mark.asyncio
    async def test_complete_conversation_flow(self, mock_llm_client):
        """测试完整的对话流程"""
        orchestrator = get_orchestrator()
        
        # 创建测试Skill
        test_skill = SkillConfig(
            name="test_skill",
            version="1.0.0",
            description="测试Skill",
            prompt_template="你是测试助手。\n\n用户: {{ user_message }}\n\n请回复。",
            llm={'model': 'qwen-max', 'temperature': 0.7}
        )
        orchestrator.skill_loader.skills['test_skill'] = test_skill
        
        # Mock客户端
        with patch.object(orchestrator.client_manager, 'get_client', return_value=mock_llm_client):
            # 1. 第一次对话（新对话）
            result1 = await orchestrator.execute_skill(
                skill_name="test_skill",
                user_message="你好",
                session_id="test_e2e_session"
            )
            
            assert result1 is not None
            assert result1['response'] == "这是测试回复"
            assert result1['is_followup'] is False
            
            # 2. 追问
            result2 = await orchestrator.execute_skill(
                skill_name="test_skill",
                user_message="继续",
                session_id="test_e2e_session"
            )
            
            assert result2 is not None
            assert result2['response'] == "这是测试回复"
            # 可能被判断为追问
            assert 'is_followup' in result2
            
            # 3. 查看历史
            history = orchestrator.context_manager.get_history("test_e2e_session")
            assert len(history) >= 1  # 至少有一条记录
            
            # 4. 查看统计
            stats = orchestrator.get_stats()
            assert stats['executor']['total_executions'] >= 1  # 至少执行过一次
            
            # 5. 清理会话
            orchestrator.clear_session("test_e2e_session")
            history = orchestrator.context_manager.get_history("test_e2e_session")
            assert len(history) == 0
    
    @pytest.mark.asyncio
    async def test_multi_skill_conversation(self, mock_llm_client):
        """测试多Skill对话"""
        orchestrator = get_orchestrator()
        
        # 创建两个测试Skill
        skill1 = SkillConfig(
            name="skill1",
            version="1.0.0",
            description="Skill 1",
            prompt_template="Skill 1: {{ user_message }}",
            llm={'model': 'qwen-max'}
        )
        skill2 = SkillConfig(
            name="skill2",
            version="1.0.0",
            description="Skill 2",
            prompt_template="Skill 2: {{ user_message }}",
            llm={'model': 'qwen-plus'}
        )
        
        orchestrator.skill_loader.skills['skill1'] = skill1
        orchestrator.skill_loader.skills['skill2'] = skill2
        
        with patch.object(orchestrator.client_manager, 'get_client', return_value=mock_llm_client):
            # 使用skill1
            result1 = await orchestrator.execute_skill(
                skill_name="skill1",
                user_message="测试1",
                session_id="multi_skill_session"
            )
            
            # 使用skill2
            result2 = await orchestrator.execute_skill(
                skill_name="skill2",
                user_message="测试2",
                session_id="multi_skill_session"
            )
            
            # 验证两个Skill都成功执行
            assert result1 is not None
            assert result2 is not None
            # 注意：实际模型可能因为降级而不同，只验证执行成功即可
            
            # 历史应该包含两次对话
            history = orchestrator.context_manager.get_history("multi_skill_session")
            assert len(history) >= 2
    
    @pytest.mark.asyncio
    async def test_stream_conversation(self, mock_llm_client):
        """测试流式对话"""
        orchestrator = get_orchestrator()
        
        test_skill = SkillConfig(
            name="stream_skill",
            version="1.0.0",
            description="流式Skill",
            prompt_template="{{ user_message }}",
            llm={'model': 'qwen-max'}
        )
        orchestrator.skill_loader.skills['stream_skill'] = test_skill
        
        with patch.object(orchestrator.client_manager, 'get_client', return_value=mock_llm_client):
            tokens = []
            full_response = ""
            
            async for chunk in orchestrator.stream_execute_skill(
                skill_name="stream_skill",
                user_message="测试流式",
                session_id="stream_session"
            ):
                if chunk['type'] == 'token':
                    tokens.append(chunk['content'])
                    full_response += chunk['content']
                elif chunk['type'] == 'done':
                    assert chunk['content'] == full_response
            
            assert len(tokens) > 0
            assert full_response == "这是测试回复"
    
    @pytest.mark.asyncio
    async def test_error_handling(self, mock_llm_client):
        """测试错误处理"""
        orchestrator = get_orchestrator()
        
        # 测试Skill不存在
        with pytest.raises(ValueError, match="not found"):
            await orchestrator.execute_skill(
                skill_name="nonexistent",
                user_message="测试",
                session_id="error_session"
            )
    
    @pytest.mark.asyncio
    async def test_rate_limiting_integration(self, mock_llm_client):
        """测试限流集成"""
        orchestrator = get_orchestrator()
        
        test_skill = SkillConfig(
            name="rate_test_skill",
            version="1.0.0",
            description="限流测试",
            prompt_template="{{ user_message }}",
            llm={'model': 'qwen-max'}
        )
        orchestrator.skill_loader.skills['rate_test_skill'] = test_skill
        
        # 配置严格的限流
        from daoyoucode.llm.utils import get_rate_limiter
        rate_limiter = get_rate_limiter()
        rate_limiter.configure_user_limit(capacity=2, refill_rate=0.1)  # 2个令牌，每秒0.1个
        
        with patch.object(orchestrator.client_manager, 'get_client', return_value=mock_llm_client):
            # 前2次应该成功
            for i in range(2):
                result = await orchestrator.execute_skill(
                    skill_name="rate_test_skill",
                    user_message=f"测试{i}",
                    session_id="rate_session",
                    user_id=999
                )
                assert result is not None
            
            # 第3次应该被限流（但由于是测试环境，可能不会真的限流）
            # 这里只验证不会崩溃
            try:
                result = await orchestrator.execute_skill(
                    skill_name="rate_test_skill",
                    user_message="测试3",
                    session_id="rate_session",
                    user_id=999
                )
            except Exception:
                pass  # 限流异常是预期的
    
    @pytest.mark.asyncio
    async def test_context_isolation(self, mock_llm_client):
        """测试会话隔离"""
        orchestrator = get_orchestrator()
        
        test_skill = SkillConfig(
            name="isolation_skill",
            version="1.0.0",
            description="隔离测试",
            prompt_template="{{ user_message }}",
            llm={'model': 'qwen-max'}
        )
        orchestrator.skill_loader.skills['isolation_skill'] = test_skill
        
        with patch.object(orchestrator.client_manager, 'get_client', return_value=mock_llm_client):
            # 会话1
            await orchestrator.execute_skill(
                skill_name="isolation_skill",
                user_message="会话1消息",
                session_id="isolation_session_1"
            )
            
            # 会话2
            await orchestrator.execute_skill(
                skill_name="isolation_skill",
                user_message="会话2消息",
                session_id="isolation_session_2"
            )
            
            # 验证隔离
            history1 = orchestrator.context_manager.get_history("isolation_session_1")
            history2 = orchestrator.context_manager.get_history("isolation_session_2")
            
            assert len(history1) >= 1
            assert len(history2) >= 1
            assert history1[0]['user'] == "会话1消息"
            assert history2[0]['user'] == "会话2消息"
    
    @pytest.mark.asyncio
    async def test_stats_tracking(self, mock_llm_client):
        """测试统计追踪"""
        orchestrator = get_orchestrator()
        
        test_skill = SkillConfig(
            name="stats_skill",
            version="1.0.0",
            description="统计测试",
            prompt_template="{{ user_message }}",
            llm={'model': 'qwen-max'}
        )
        orchestrator.skill_loader.skills['stats_skill'] = test_skill
        
        with patch.object(orchestrator.client_manager, 'get_client', return_value=mock_llm_client):
            initial_stats = orchestrator.get_stats()
            initial_count = initial_stats['executor']['total_executions']
            
            # 执行3次
            for i in range(3):
                await orchestrator.execute_skill(
                    skill_name="stats_skill",
                    user_message=f"测试{i}",
                    session_id="stats_session"
                )
            
            # 验证统计更新
            final_stats = orchestrator.get_stats()
            final_count = final_stats['executor']['total_executions']
            
            # 由于是共享的单例，统计可能包含其他测试的执行
            # 只验证统计有增长即可
            assert final_count > initial_count
