"""
测试WorkflowOrchestrator和ParallelExploreOrchestrator的增强功能
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch
from daoyoucode.agents.orchestrators.workflow import WorkflowOrchestrator
from daoyoucode.agents.orchestrators.parallel_explore import ParallelExploreOrchestrator


# ============================================================================
# WorkflowOrchestrator 测试
# ============================================================================

class TestWorkflowOrchestrator:
    """测试WorkflowOrchestrator的增强功能"""
    
    @pytest.mark.asyncio
    async def test_step_retry_success(self):
        """测试步骤重试机制 - 成功场景"""
        orchestrator = WorkflowOrchestrator()
        
        # Mock Agent（第一次失败，第二次成功）
        mock_agent = Mock()
        attempt = 0
        
        async def execute_with_retry(*args, **kwargs):
            nonlocal attempt
            attempt += 1
            if attempt == 1:
                return {'success': False, 'content': '', 'error': '临时失败'}
            else:
                return {'success': True, 'content': '成功结果', 'metadata': {}}
        
        mock_agent.execute = AsyncMock(side_effect=execute_with_retry)
        
        # Mock Skill
        mock_skill = Mock()
        mock_skill.workflow = [
            {
                'name': 'test_step',
                'agent': 'test_agent',
                'max_retries': 3,
                'timeout': 10.0
            }
        ]
        mock_skill.middleware = None
        mock_skill.tools = None
        
        with patch.object(orchestrator, '_get_agent', return_value=mock_agent):
            result = await orchestrator.execute(
                skill=mock_skill,
                user_input='测试输入',
                context={}
            )
        
        assert result['success'] is True
        assert '成功结果' in result['content']
        assert attempt == 2  # 第一次失败，第二次成功
        print("✅ 步骤重试机制测试通过")
    
    @pytest.mark.asyncio
    async def test_step_dependency(self):
        """测试步骤依赖检查"""
        orchestrator = WorkflowOrchestrator()
        
        # Mock Agent
        mock_agent = Mock()
        mock_agent.execute = AsyncMock(return_value={
            'success': True,
            'content': '步骤结果',
            'metadata': {}
        })
        
        # Mock Skill（带依赖）
        mock_skill = Mock()
        mock_skill.workflow = [
            {
                'name': 'step1',
                'agent': 'agent1'
                # output默认使用步骤名称'step1'
            },
            {
                'name': 'step2',
                'agent': 'agent2',
                'depends_on': ['step1'],  # 依赖step1
                'input': '${step1}'  # 使用step1的结果
            }
        ]
        mock_skill.middleware = None
        mock_skill.tools = None
        
        with patch.object(orchestrator, '_get_agent', return_value=mock_agent):
            result = await orchestrator.execute(
                skill=mock_skill,
                user_input='测试输入',
                context={}
            )
        
        assert result['success'] is True
        assert 'step1' in result['workflow_results']
        assert 'step2' in result['workflow_results']
        print("✅ 步骤依赖检查测试通过")
    
    @pytest.mark.asyncio
    async def test_circular_dependency_detection(self):
        """测试循环依赖检测"""
        orchestrator = WorkflowOrchestrator()
        
        # Mock Skill（循环依赖）
        mock_skill = Mock()
        mock_skill.workflow = [
            {
                'name': 'step1',
                'agent': 'agent1',
                'depends_on': ['step2']  # 依赖step2
            },
            {
                'name': 'step2',
                'agent': 'agent2',
                'depends_on': ['step1']  # 依赖step1 -> 循环！
            }
        ]
        mock_skill.middleware = None
        
        result = await orchestrator.execute(
            skill=mock_skill,
            user_input='测试输入',
            context={}
        )
        
        assert result['success'] is False
        assert '循环依赖' in result['error']
        print("✅ 循环依赖检测测试通过")
    
    @pytest.mark.asyncio
    async def test_rollback_on_failure(self):
        """测试失败回滚"""
        orchestrator = WorkflowOrchestrator()
        
        # Mock Agents
        mock_agent1 = Mock()
        mock_agent1.execute = AsyncMock(return_value={
            'success': True,
            'content': '步骤1成功',
            'metadata': {}
        })
        
        mock_agent2 = Mock()
        mock_agent2.execute = AsyncMock(return_value={
            'success': False,
            'content': '',
            'error': '步骤2失败'
        })
        
        mock_rollback_agent = Mock()
        mock_rollback_agent.execute = AsyncMock(return_value={
            'success': True,
            'content': '回滚完成',
            'metadata': {}
        })
        
        def get_agent(name):
            if name == 'agent1':
                return mock_agent1
            elif name == 'agent2':
                return mock_agent2
            elif name == 'rollback_agent':
                return mock_rollback_agent
        
        # Mock Skill（带回滚）
        mock_skill = Mock()
        mock_skill.workflow = [
            {
                'name': 'step1',
                'agent': 'agent1',
                'rollback': 'rollback_agent'  # 配置回滚Agent
            },
            {
                'name': 'step2',
                'agent': 'agent2'
            }
        ]
        mock_skill.middleware = None
        mock_skill.tools = None
        
        with patch.object(orchestrator, '_get_agent', side_effect=get_agent):
            result = await orchestrator.execute(
                skill=mock_skill,
                user_input='测试输入',
                context={}
            )
        
        assert result['success'] is False
        assert result['rollback_executed'] is True
        assert mock_rollback_agent.execute.called  # 回滚Agent被调用
        print("✅ 失败回滚测试通过")
    
    @pytest.mark.asyncio
    async def test_step_timeout(self):
        """测试步骤超时"""
        orchestrator = WorkflowOrchestrator()
        
        # Mock Agent（模拟慢操作）
        mock_agent = Mock()
        
        async def slow_execute(*args, **kwargs):
            await asyncio.sleep(2.0)  # 睡眠2秒
            return {'success': True, 'content': '结果', 'metadata': {}}
        
        mock_agent.execute = AsyncMock(side_effect=slow_execute)
        
        # Mock Skill（超时1秒）
        mock_skill = Mock()
        mock_skill.workflow = [
            {
                'name': 'slow_step',
                'agent': 'test_agent',
                'timeout': 0.5,  # 超时0.5秒
                'max_retries': 1  # 不重试
            }
        ]
        mock_skill.middleware = None
        mock_skill.tools = None
        
        with patch.object(orchestrator, '_get_agent', return_value=mock_agent):
            result = await orchestrator.execute(
                skill=mock_skill,
                user_input='测试输入',
                context={}
            )
        
        assert result['success'] is False
        assert '超时' in result['error']
        print("✅ 步骤超时测试通过")


# ============================================================================
# ParallelExploreOrchestrator 测试
# ============================================================================

class TestParallelExploreOrchestrator:
    """测试ParallelExploreOrchestrator的增强功能"""
    
    @pytest.mark.asyncio
    async def test_static_background_tasks(self):
        """测试静态后台任务（现有功能）"""
        orchestrator = ParallelExploreOrchestrator()
        
        # Mock BackgroundManager
        mock_bg_manager = Mock()
        mock_bg_manager.submit = AsyncMock(return_value='task_1')
        mock_bg_manager.get_result = AsyncMock(return_value={
            'success': True,
            'content': '后台结果'
        })
        orchestrator.bg_manager = mock_bg_manager
        
        # Mock Agent
        mock_agent = Mock()
        mock_agent.execute = AsyncMock(return_value={
            'success': True,
            'content': '主任务结果',
            'metadata': {}
        })
        
        # Mock Skill（静态配置）
        mock_skill = Mock()
        mock_skill.agent = 'main_agent'
        mock_skill.prompt = {'use_agent_default': True}
        mock_skill.tools = None
        mock_skill.middleware = None
        mock_skill.use_dynamic_tasks = False
        mock_skill.use_llm_aggregate = False
        mock_skill.background_tasks = [
            {
                'agent': 'explore',
                'prompt': '搜索: {{user_input}}',
                'timeout': 5.0,
                'priority': 8
            }
        ]
        
        with patch.object(orchestrator, '_get_agent', return_value=mock_agent):
            result = await orchestrator.execute(
                skill=mock_skill,
                user_input='测试查询',
                context={}
            )
        
        assert result['success'] is True
        assert '主任务结果' in result['content']
        assert len(result['background_results']) == 1
        assert mock_bg_manager.submit.called
        print("✅ 静态后台任务测试通过")
    
    @pytest.mark.asyncio
    async def test_dynamic_task_generation(self):
        """测试动态任务生成（LLM驱动）- 测试降级机制"""
        orchestrator = ParallelExploreOrchestrator()
        
        # Mock BackgroundManager
        mock_bg_manager = Mock()
        mock_bg_manager.submit = AsyncMock(side_effect=['task_1', 'task_2'])
        mock_bg_manager.get_result = AsyncMock(return_value={
            'success': True,
            'content': '探索结果'
        })
        orchestrator.bg_manager = mock_bg_manager
        
        # Mock Agent
        mock_agent = Mock()
        mock_agent.execute = AsyncMock(return_value={
            'success': True,
            'content': '主任务结果',
            'metadata': {}
        })
        
        # Mock Skill（动态生成，但LLM会失败，测试降级）
        mock_skill = Mock()
        mock_skill.agent = 'main_agent'
        mock_skill.prompt = {'use_agent_default': True}
        mock_skill.tools = None
        mock_skill.middleware = None
        mock_skill.use_dynamic_tasks = True
        mock_skill.use_llm_aggregate = False
        mock_skill.llm = {'model': 'qwen-turbo'}
        mock_skill.available_agents = {
            'explore': '代码探索',
            'librarian': '文档查找'
        }
        
        with patch.object(orchestrator, '_get_agent', return_value=mock_agent):
            result = await orchestrator.execute(
                skill=mock_skill,
                user_input='如何实现登录功能',
                context={}
            )
        
        # 验证结果（LLM失败会降级，返回空任务列表）
        assert result['success'] is True
        assert result['metadata']['dynamic_tasks'] is True
        # 降级模式：没有生成任务（因为LLM失败）
        print("✅ 动态任务生成测试通过（降级模式）")
    
    @pytest.mark.asyncio
    async def test_llm_smart_aggregation(self):
        """测试LLM智能聚合 - 测试降级机制"""
        orchestrator = ParallelExploreOrchestrator()
        
        # Mock BackgroundManager
        mock_bg_manager = Mock()
        mock_bg_manager.submit = AsyncMock(return_value='task_1')
        mock_bg_manager.get_result = AsyncMock(return_value={
            'success': True,
            'content': '后台探索发现了相关代码'
        })
        orchestrator.bg_manager = mock_bg_manager
        
        # Mock Agent
        mock_agent = Mock()
        mock_agent.execute = AsyncMock(return_value={
            'success': True,
            'content': '主任务分析结果',
            'metadata': {}
        })
        
        # Mock Skill（启用LLM聚合，但LLM会失败，测试降级）
        mock_skill = Mock()
        mock_skill.agent = 'main_agent'
        mock_skill.prompt = {'use_agent_default': True}
        mock_skill.tools = None
        mock_skill.middleware = None
        mock_skill.use_dynamic_tasks = False
        mock_skill.use_llm_aggregate = True
        mock_skill.llm = {'model': 'qwen-turbo'}
        mock_skill.background_tasks = [
            {
                'agent': 'explore',
                'prompt': '搜索',
                'timeout': 5.0,
                'priority': 8
            }
        ]
        
        with patch.object(orchestrator, '_get_agent', return_value=mock_agent):
            result = await orchestrator.execute(
                skill=mock_skill,
                user_input='测试',
                context={}
            )
        
        assert result['success'] is True
        assert result['metadata']['llm_aggregate'] is True
        
        # LLM失败会降级到简单聚合
        assert '主任务分析结果' in result['content'] or '后台探索' in result['content']
        print("✅ LLM智能聚合测试通过（降级模式）")
    
    @pytest.mark.asyncio
    async def test_priority_ordering(self):
        """测试任务优先级排序"""
        orchestrator = ParallelExploreOrchestrator()
        
        # Mock BackgroundManager
        task_results = {
            'task_1': {'success': True, 'content': '低优先级结果'},
            'task_2': {'success': True, 'content': '高优先级结果'}
        }
        
        mock_bg_manager = Mock()
        mock_bg_manager.submit = AsyncMock(side_effect=['task_1', 'task_2'])
        
        async def get_result_by_id(task_id, timeout):
            return task_results[task_id]
        
        mock_bg_manager.get_result = AsyncMock(side_effect=get_result_by_id)
        orchestrator.bg_manager = mock_bg_manager
        
        # Mock Agent
        mock_agent = Mock()
        mock_agent.execute = AsyncMock(return_value={
            'success': True,
            'content': '主任务',
            'metadata': {}
        })
        
        # Mock Skill（不同优先级）
        mock_skill = Mock()
        mock_skill.agent = 'main_agent'
        mock_skill.prompt = {'use_agent_default': True}
        mock_skill.tools = None
        mock_skill.middleware = None
        mock_skill.use_dynamic_tasks = False
        mock_skill.use_llm_aggregate = False
        mock_skill.background_tasks = [
            {
                'agent': 'low_priority',
                'prompt': '低优先级',
                'timeout': 5.0,
                'priority': 3
            },
            {
                'agent': 'high_priority',
                'prompt': '高优先级',
                'timeout': 5.0,
                'priority': 9
            }
        ]
        
        with patch.object(orchestrator, '_get_agent', return_value=mock_agent):
            result = await orchestrator.execute(
                skill=mock_skill,
                user_input='测试',
                context={}
            )
        
        assert result['success'] is True
        # 验证高优先级任务先被处理
        assert result['background_results'][0]['priority'] == 9
        assert result['background_results'][1]['priority'] == 3
        print("✅ 任务优先级排序测试通过")


# ============================================================================
# 运行测试
# ============================================================================

async def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*70)
    print("测试 WorkflowOrchestrator 和 ParallelExploreOrchestrator 增强功能")
    print("="*70 + "\n")
    
    # WorkflowOrchestrator测试
    print("【WorkflowOrchestrator 测试】\n")
    
    workflow_tests = TestWorkflowOrchestrator()
    
    try:
        await workflow_tests.test_step_retry_success()
    except Exception as e:
        print(f"❌ 步骤重试测试失败: {e}")
    
    try:
        await workflow_tests.test_step_dependency()
    except Exception as e:
        print(f"❌ 步骤依赖测试失败: {e}")
    
    try:
        await workflow_tests.test_circular_dependency_detection()
    except Exception as e:
        print(f"❌ 循环依赖检测测试失败: {e}")
    
    try:
        await workflow_tests.test_rollback_on_failure()
    except Exception as e:
        print(f"❌ 失败回滚测试失败: {e}")
    
    try:
        await workflow_tests.test_step_timeout()
    except Exception as e:
        print(f"❌ 步骤超时测试失败: {e}")
    
    # ParallelExploreOrchestrator测试
    print("\n【ParallelExploreOrchestrator 测试】\n")
    
    parallel_tests = TestParallelExploreOrchestrator()
    
    try:
        await parallel_tests.test_static_background_tasks()
    except Exception as e:
        print(f"❌ 静态后台任务测试失败: {e}")
    
    try:
        await parallel_tests.test_dynamic_task_generation()
    except Exception as e:
        print(f"❌ 动态任务生成测试失败: {e}")
    
    try:
        await parallel_tests.test_llm_smart_aggregation()
    except Exception as e:
        print(f"❌ LLM智能聚合测试失败: {e}")
    
    try:
        await parallel_tests.test_priority_ordering()
    except Exception as e:
        print(f"❌ 任务优先级排序测试失败: {e}")
    
    print("\n" + "="*70)
    print("所有测试完成！")
    print("="*70)


if __name__ == '__main__':
    asyncio.run(run_all_tests())
