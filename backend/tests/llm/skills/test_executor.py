"""
测试Skill执行器
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from daoyoucode.llm.skills import SkillExecutor, SkillConfig
from daoyoucode.llm.base import LLMResponse
from daoyoucode.llm.exceptions import SkillExecutionError


@pytest.fixture
def sample_skill():
    """创建示例Skill"""
    return SkillConfig(
        name="test_skill",
        version="1.0.0",
        description="测试Skill",
        prompt_template="Hello {{ name }}!",
        llm={
            'model': 'qwen-max',
            'temperature': 0.7,
            'max_tokens': 1000
        },
        inputs=[
            {'name': 'name', 'type': 'string', 'required': True}
        ],
        outputs=[
            {'name': 'response', 'type': 'string'}
        ]
    )


@pytest.fixture
def mock_llm_response():
    """模拟LLM响应"""
    return LLMResponse(
        content='{"response": "Hello World!"}',
        model="qwen-max",
        tokens_used=50,
        cost=0.001,
        latency=1.0
    )


class TestSkillExecutor:
    """测试SkillExecutor"""
    
    def test_init(self):
        """测试初始化"""
        executor = SkillExecutor()
        assert executor is not None
        assert executor.stats['total_executions'] == 0
    
    @pytest.mark.asyncio
    async def test_execute_success(self, sample_skill, mock_llm_response):
        """测试成功执行Skill"""
        executor = SkillExecutor()
        
        # Mock依赖
        with patch.object(executor.client_manager, 'get_client') as mock_get_client, \
             patch.object(executor.rate_limiter, 'acquire', new_callable=AsyncMock) as mock_acquire, \
             patch.object(executor.circuit_breaker, 'call', new_callable=AsyncMock) as mock_call, \
             patch.object(executor.fallback_strategy, 'execute_with_fallback', new_callable=AsyncMock) as mock_fallback:
            
            # 配置mock
            mock_client = MagicMock()
            mock_client.chat = AsyncMock(return_value=mock_llm_response)
            mock_get_client.return_value = mock_client
            
            mock_call.return_value = mock_llm_response
            mock_fallback.return_value = (mock_llm_response, 'qwen-max')
            
            # 执行
            context = {'name': 'World'}
            result = await executor.execute(sample_skill, context)
            
            # 验证
            assert result is not None
            assert 'response' in result
            assert result['_metadata']['skill'] == 'test_skill'
            assert result['_metadata']['mode'] == 'full'
            
            # 验证调用
            mock_acquire.assert_called_once()
            mock_fallback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_missing_required_input(self, sample_skill):
        """测试缺少必需输入"""
        executor = SkillExecutor()
        
        context = {}  # 缺少 'name'
        
        with pytest.raises(SkillExecutionError, match="Required input"):
            await executor.execute(sample_skill, context)
    
    @pytest.mark.asyncio
    async def test_execute_timeout(self, sample_skill):
        """测试执行超时"""
        executor = SkillExecutor()
        
        with patch.object(executor.fallback_strategy, 'execute_with_fallback', new_callable=AsyncMock) as mock_fallback:
            # 模拟超时
            import asyncio
            mock_fallback.side_effect = asyncio.TimeoutError()
            
            context = {'name': 'World'}
            
            with pytest.raises(SkillExecutionError, match="超时"):
                await executor.execute(sample_skill, context, timeout=0.1)
    
    @pytest.mark.asyncio
    async def test_execute_followup(self, sample_skill, mock_llm_response):
        """测试追问模式执行"""
        executor = SkillExecutor()
        
        with patch.object(executor.client_manager, 'get_client') as mock_get_client, \
             patch.object(executor.rate_limiter, 'acquire', new_callable=AsyncMock), \
             patch.object(executor.circuit_breaker, 'call', new_callable=AsyncMock) as mock_call, \
             patch.object(executor.fallback_strategy, 'execute_with_fallback', new_callable=AsyncMock) as mock_fallback:
            
            mock_client = MagicMock()
            mock_client.chat = AsyncMock(return_value=mock_llm_response)
            mock_get_client.return_value = mock_client
            
            mock_call.return_value = mock_llm_response
            mock_fallback.return_value = (mock_llm_response, 'qwen-plus')
            
            context = {'user_message': '继续'}
            history_context = {'summary': '之前讨论了天气'}
            
            result = await executor.execute_followup(
                sample_skill,
                context,
                history_context
            )
            
            assert result is not None
            assert 'response' in result
            assert result['_metadata']['mode'] == 'followup'
            assert result['_metadata']['model'] == 'qwen-plus'
    
    def test_validate_inputs(self, sample_skill):
        """测试输入验证"""
        executor = SkillExecutor()
        
        # 有效输入
        context = {'name': 'World'}
        executor._validate_inputs(sample_skill, context)
        
        # 缺少必需输入
        context = {}
        with pytest.raises(ValueError):
            executor._validate_inputs(sample_skill, context)
    
    def test_render_prompt(self, sample_skill):
        """测试Prompt渲染"""
        executor = SkillExecutor()
        
        context = {'name': 'World'}
        prompt = executor._render_prompt(sample_skill, context)
        
        assert prompt == "Hello World!"
    
    def test_parse_output_json(self):
        """测试解析JSON输出"""
        executor = SkillExecutor()
        skill = SkillConfig(
            name="test",
            version="1.0.0",
            description="Test",
            prompt_template=""
        )
        
        # JSON格式
        response = '{"response": "Hello", "status": "ok"}'
        result = executor._parse_output(skill, response)
        
        assert result['response'] == "Hello"
        assert result['status'] == "ok"
    
    def test_parse_output_text(self):
        """测试解析文本输出"""
        executor = SkillExecutor()
        skill = SkillConfig(
            name="test",
            version="1.0.0",
            description="Test",
            prompt_template=""
        )
        
        # 纯文本
        response = "Hello World"
        result = executor._parse_output(skill, response)
        
        assert result['response'] == "Hello World"
    
    @pytest.mark.asyncio
    async def test_post_process(self):
        """测试后处理"""
        executor = SkillExecutor()
        
        skill = SkillConfig(
            name="test",
            version="1.0.0",
            description="Test",
            prompt_template="",
            outputs=[
                {'name': 'status', 'type': 'enum', 'values': ['ok', 'error']}
            ],
            post_process=['validate_output']
        )
        
        result = {'status': 'invalid'}
        context = {}
        
        processed = await executor._post_process(skill, result, context)
        
        # 应该被修正为默认值
        assert processed['status'] == 'ok'
    
    def test_get_stats(self):
        """测试获取统计信息"""
        executor = SkillExecutor()
        
        # 全局统计
        stats = executor.get_stats()
        assert 'total_executions' in stats
        
        # 特定Skill统计
        stats = executor.get_stats('test_skill')
        assert isinstance(stats, dict)
    
    @pytest.mark.asyncio
    async def test_stats_update(self, sample_skill, mock_llm_response):
        """测试统计信息更新"""
        executor = SkillExecutor()
        
        initial_count = executor.stats['total_executions']
        
        with patch.object(executor.client_manager, 'get_client') as mock_get_client, \
             patch.object(executor.rate_limiter, 'acquire', new_callable=AsyncMock), \
             patch.object(executor.circuit_breaker, 'call', new_callable=AsyncMock), \
             patch.object(executor.fallback_strategy, 'execute_with_fallback', new_callable=AsyncMock) as mock_fallback:
            
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            mock_fallback.return_value = (mock_llm_response, 'qwen-max')
            
            context = {'name': 'World'}
            await executor.execute(sample_skill, context)
            
            # 验证统计更新
            assert executor.stats['total_executions'] == initial_count + 1
            assert executor.stats['successful_executions'] > 0
            assert 'test_skill' in executor.stats['by_skill']
