"""
测试LLM编排器
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from daoyoucode.llm.orchestrator import LLMOrchestrator
from daoyoucode.llm.base import LLMResponse
from daoyoucode.llm.skills import SkillConfig


@pytest.fixture
def orchestrator():
    """创建编排器（独立实例）"""
    # 创建独立实例，避免单例干扰
    from daoyoucode.llm.skills.loader import SkillLoader
    from daoyoucode.llm.skills.executor import SkillExecutor
    from daoyoucode.llm.context.manager import ContextManager
    from daoyoucode.llm.client_manager import LLMClientManager
    
    orch = LLMOrchestrator()
    orch.skill_loader = SkillLoader()
    orch.skill_executor = SkillExecutor()
    orch.context_manager = ContextManager()
    orch.client_manager = LLMClientManager()
    
    return orch


@pytest.fixture
def sample_skill():
    """创建示例Skill"""
    return SkillConfig(
        name="test_skill",
        version="1.0.0",
        description="测试Skill",
        prompt_template="你是测试助手。\n\n用户: {{ user_message }}\n\n请回复。",
        llm={
            'model': 'qwen-max',
            'temperature': 0.7,
            'max_tokens': 1000
        }
    )


@pytest.fixture
def mock_llm_response():
    """模拟LLM响应"""
    return LLMResponse(
        content="这是测试回复",
        model="qwen-max",
        tokens_used=50,
        cost=0.001,
        latency=1.0
    )


class TestLLMOrchestrator:
    """测试LLMOrchestrator"""
    
    def test_init(self, orchestrator):
        """测试初始化"""
        assert orchestrator is not None
        assert orchestrator.skill_loader is not None
        assert orchestrator.skill_executor is not None
        assert orchestrator.context_manager is not None
        assert orchestrator.client_manager is not None
    
    @pytest.mark.asyncio
    async def test_execute_skill_new_conversation(
        self,
        orchestrator,
        sample_skill,
        mock_llm_response
    ):
        """测试执行Skill（新对话）"""
        # 添加Skill
        orchestrator.skill_loader.skills['test_skill'] = sample_skill
        
        # Mock依赖
        with patch.object(orchestrator.skill_executor, 'execute', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = {
                'response': '测试回复',
                '_metadata': {
                    'skill': 'test_skill',
                    'model': 'qwen-max',
                    'tokens_used': 50,
                    'cost': 0.001,
                    'mode': 'full'
                }
            }
            
            result = await orchestrator.execute_skill(
                skill_name="test_skill",
                user_message="你好",
                session_id="test_session"
            )
            
            assert result is not None
            assert result['response'] == '测试回复'
            assert result['is_followup'] is False
            assert '_metadata' in result
            
            # 验证调用了完整模式
            mock_execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_skill_followup(
        self,
        orchestrator,
        sample_skill,
        mock_llm_response
    ):
        """测试执行Skill（追问）"""
        # 添加Skill
        orchestrator.skill_loader.skills['test_skill'] = sample_skill
        
        # 添加历史对话
        await orchestrator.context_manager.add_conversation(
            "test_session",
            "第一个问题",
            "第一个回复"
        )
        
        # Mock依赖
        with patch.object(orchestrator.skill_executor, 'execute_followup', new_callable=AsyncMock) as mock_followup:
            mock_followup.return_value = {
                'response': '追问回复',
                '_metadata': {
                    'skill': 'test_skill',
                    'model': 'qwen-max',
                    'tokens_used': 30,
                    'cost': 0.0006,
                    'mode': 'followup'
                }
            }
            
            result = await orchestrator.execute_skill(
                skill_name="test_skill",
                user_message="继续",
                session_id="test_session"
            )
            
            assert result is not None
            assert result['response'] == '追问回复'
            # 可能被判断为追问
            assert 'is_followup' in result
    
    @pytest.mark.asyncio
    async def test_execute_skill_not_found(self, orchestrator):
        """测试执行不存在的Skill"""
        with pytest.raises(ValueError, match="not found"):
            await orchestrator.execute_skill(
                skill_name="nonexistent",
                user_message="你好",
                session_id="test_session"
            )
    
    @pytest.mark.asyncio
    async def test_chat(self, orchestrator, mock_llm_response):
        """测试普通对话"""
        # Mock客户端
        mock_client = MagicMock()
        mock_client.chat = AsyncMock(return_value=mock_llm_response)
        
        with patch.object(orchestrator.client_manager, 'get_client', return_value=mock_client):
            result = await orchestrator.chat(
                user_message="你好",
                session_id="test_session",
                model="qwen-turbo"
            )
            
            assert result is not None
            assert result['response'] == "这是测试回复"
            assert result['model'] == "qwen-turbo"
            assert result['tokens_used'] == 50
            assert 'is_followup' in result
    
    def test_list_skills(self, orchestrator, sample_skill):
        """测试列出Skill"""
        orchestrator.skill_loader.skills['test_skill'] = sample_skill
        
        skills = orchestrator.list_skills()
        
        assert 'test_skill' in skills
        assert skills['test_skill'] == "测试Skill"
    
    def test_get_skill_info(self, orchestrator, sample_skill):
        """测试获取Skill信息"""
        orchestrator.skill_loader.skills['test_skill'] = sample_skill
        
        info = orchestrator.get_skill_info('test_skill')
        
        assert info is not None
        assert info['name'] == 'test_skill'
        assert info['version'] == '1.0.0'
        assert info['description'] == '测试Skill'
        assert 'llm' in info
    
    def test_get_skill_info_not_found(self, orchestrator):
        """测试获取不存在的Skill信息"""
        info = orchestrator.get_skill_info('nonexistent')
        assert info is None
    
    def test_search_skills(self, orchestrator, sample_skill):
        """测试搜索Skill"""
        orchestrator.skill_loader.skills['test_skill'] = sample_skill
        
        results = orchestrator.search_skills('测试')
        
        assert len(results) > 0
        assert any(r['name'] == 'test_skill' for r in results)
    
    def test_get_stats(self, orchestrator):
        """测试获取统计信息"""
        stats = orchestrator.get_stats()
        
        assert 'skills' in stats
        assert 'executor' in stats
        assert 'context' in stats
        assert 'client' in stats
        
        assert 'total' in stats['skills']
        assert 'loaded' in stats['skills']
    
    def test_clear_session(self, orchestrator):
        """测试清除会话"""
        import asyncio
        
        # 添加对话
        asyncio.run(orchestrator.context_manager.add_conversation(
            "test_clear",
            "消息1",
            "回复1"
        ))
        
        # 清除
        orchestrator.clear_session("test_clear")
        
        # 验证已清除
        history = orchestrator.context_manager.get_history("test_clear")
        assert len(history) == 0
    
    @pytest.mark.asyncio
    async def test_force_full_mode(
        self,
        orchestrator,
        sample_skill,
        mock_llm_response
    ):
        """测试强制完整模式"""
        orchestrator.skill_loader.skills['test_skill'] = sample_skill
        
        # 添加历史（模拟追问场景）
        await orchestrator.context_manager.add_conversation(
            "test_session",
            "第一个问题",
            "第一个回复"
        )
        
        # Mock依赖
        with patch.object(orchestrator.skill_executor, 'execute', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = {
                'response': '完整模式回复',
                '_metadata': {
                    'skill': 'test_skill',
                    'model': 'qwen-max',
                    'tokens_used': 50,
                    'cost': 0.001,
                    'mode': 'full'
                }
            }
            
            result = await orchestrator.execute_skill(
                skill_name="test_skill",
                user_message="继续",
                session_id="test_session",
                force_full_mode=True  # 强制完整模式
            )
            
            # 应该调用完整模式
            mock_execute.assert_called_once()
