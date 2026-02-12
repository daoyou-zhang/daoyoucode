"""
测试智能化功能：模型选择、上下文选择、委托、行为指南等
"""

import pytest
import asyncio
from pathlib import Path
from daoyoucode.agents.core.model_selector import ModelSelector, get_model_selector
from daoyoucode.agents.core.context_selector import ContextSelector
from daoyoucode.agents.core.delegation import DelegationPrompt, DelegationManager, create_delegation_prompt
from daoyoucode.agents.core.behavior_guide import BehaviorGuide, Phase, RequestType, CodebaseState
from daoyoucode.agents.core.codebase_assessor import CodebaseAssessor
from daoyoucode.agents.core.parallel_executor import ParallelExecutor, get_parallel_executor
from daoyoucode.agents.core.session import SessionManager, get_session_manager


# ==================== 模型选择器测试 ====================

def test_model_selector_singleton():
    """测试模型选择器单例"""
    selector1 = ModelSelector()
    selector2 = ModelSelector()
    assert selector1 is selector2


def test_model_selector_configure():
    """测试模型配置"""
    selector = get_model_selector()
    selector.configure(
        main_model='gpt-4',
        weak_model='gpt-3.5-turbo',
        editor_model='gpt-4-turbo'
    )
    
    assert selector.main_model == 'gpt-4'
    assert selector.weak_model == 'gpt-3.5-turbo'
    assert selector.editor_model == 'gpt-4-turbo'


def test_model_selector_simple_task():
    """测试简单任务选择"""
    selector = get_model_selector()
    selector.configure('gpt-4', 'gpt-3.5-turbo', 'gpt-4-turbo')
    
    model, task_type = selector.select_model('添加注释', context_size=5000)
    assert task_type == 'weak'
    assert model == 'gpt-3.5-turbo'


def test_model_selector_complex_task():
    """测试复杂任务选择"""
    selector = get_model_selector()
    selector.configure('gpt-4', 'gpt-3.5-turbo', 'gpt-4-turbo')
    
    model, task_type = selector.select_model('重构整个系统架构', context_size=100000)
    assert task_type == 'main'
    assert model == 'gpt-4'


def test_model_selector_edit_task():
    """测试编辑任务选择"""
    selector = get_model_selector()
    selector.configure('gpt-4', 'gpt-3.5-turbo', 'gpt-4-turbo')
    
    model, task_type = selector.select_model('修改代码实现', context_size=20000)
    assert task_type == 'editor'
    assert model == 'gpt-4-turbo'


# ==================== 上下文选择器测试 ====================

def test_context_selector_extract_files():
    """测试提取文件路径"""
    selector = ContextSelector(Path('.'))
    
    instruction = "修改 `src/main.py` 和 'tests/test_main.py' 文件"
    references = selector._extract_references(instruction)
    
    assert 'src/main.py' in references['files']
    assert 'tests/test_main.py' in references['files']


def test_context_selector_extract_functions():
    """测试提取函数名"""
    selector = ContextSelector(Path('.'))
    
    instruction = "修改函数 `calculate_total` 和方法 process_data"
    references = selector._extract_references(instruction)
    
    assert 'calculate_total' in references['functions']
    assert 'process_data' in references['functions']


def test_context_selector_extract_classes():
    """测试提取类名"""
    selector = ContextSelector(Path('.'))
    
    instruction = "修改类 `UserManager` 和 DataProcessor"
    references = selector._extract_references(instruction)
    
    assert 'UserManager' in references['classes']
    assert 'DataProcessor' in references['classes']


# ==================== 委托系统测试 ====================

def test_delegation_prompt_creation():
    """测试委托提示创建"""
    prompt = DelegationPrompt(
        task="实现用户认证功能",
        expected_outcome="完整的认证系统，包括登录、注册、密码重置",
        required_skills=["authentication", "security"],
        required_tools=["read_file", "write_file"],
        must_do=["使用bcrypt加密密码", "实现JWT token"],
        must_not_do=["明文存储密码", "使用弱加密算法"],
        context={'framework': 'FastAPI', 'database': 'PostgreSQL'}
    )
    
    assert prompt.task == "实现用户认证功能"
    assert len(prompt.required_skills) == 2
    assert len(prompt.must_do) == 2


def test_delegation_prompt_to_prompt():
    """测试委托提示转换"""
    prompt = create_delegation_prompt(
        task="测试任务",
        expected_outcome="测试结果",
        required_skills=["skill1"],
        must_do=["do this"],
        must_not_do=["don't do that"]
    )
    
    prompt_text = prompt.to_prompt()
    
    assert "## TASK" in prompt_text
    assert "## EXPECTED OUTCOME" in prompt_text
    assert "## REQUIRED SKILLS" in prompt_text
    assert "## MUST DO" in prompt_text
    assert "## MUST NOT DO" in prompt_text


def test_delegation_prompt_validate():
    """测试委托提示验证"""
    # 完整提示
    valid_prompt = DelegationPrompt(
        task="任务",
        expected_outcome="结果"
    )
    assert valid_prompt.validate() is True
    
    # 缺少任务
    invalid_prompt = DelegationPrompt(
        task="",
        expected_outcome="结果"
    )
    assert invalid_prompt.validate() is False


# ==================== 行为指南测试 ====================

def test_behavior_guide_classify_request():
    """测试请求分类"""
    # 测试闲聊
    assert BehaviorGuide.classify_request("你好") == RequestType.CHAT
    assert BehaviorGuide.classify_request("Hello") == RequestType.CHAT
    assert BehaviorGuide.classify_request("How are you?") == RequestType.CHAT
    assert BehaviorGuide.classify_request("谢谢") == RequestType.CHAT
    assert BehaviorGuide.classify_request("今天天气怎么样？") == RequestType.CHAT
    
    # 测试代码相关
    assert BehaviorGuide.classify_request("添加注释") == RequestType.TRIVIAL
    assert BehaviorGuide.classify_request("如何实现认证功能") == RequestType.EXPLORATORY
    assert BehaviorGuide.classify_request("重构整个系统") == RequestType.OPEN_ENDED
    assert BehaviorGuide.classify_request("look into this bug and create PR") == RequestType.GITHUB_WORK


def test_behavior_guide_get_action():
    """测试获取行动"""
    # 测试闲聊
    action = BehaviorGuide.get_action(RequestType.CHAT)
    assert action['action'] == 'respond_directly'
    assert action['use_simple_flow'] is True
    assert '代码库评估' in action['skip_steps']
    
    # 测试代码任务
    action = BehaviorGuide.get_action_for_request(RequestType.TRIVIAL)
    assert action == 'use_direct_tools'
    
    action = BehaviorGuide.get_action_for_request(RequestType.EXPLORATORY)
    assert action == 'fire_explore_parallel'


def test_behavior_guide_should_ask_clarification():
    """测试是否需要澄清"""
    # 缺少关键信息
    assert BehaviorGuide.should_ask_clarification(
        "做点什么",
        missing_critical_info=True
    ) is True
    
    # 工作量差异大
    assert BehaviorGuide.should_ask_clarification(
        "实现功能",
        multiple_interpretations=True,
        effort_difference=3.0
    ) is True
    
    # 正常情况
    assert BehaviorGuide.should_ask_clarification(
        "添加注释到main.py",
        multiple_interpretations=False
    ) is False


# ==================== 代码库评估器测试 ====================

def test_codebase_assessor_creation():
    """测试代码库评估器创建"""
    assessor = CodebaseAssessor(Path('.'))
    assert assessor.repo_path == Path('.')


def test_codebase_assessor_get_behavior_guide():
    """测试获取行为指南"""
    assessor = CodebaseAssessor(Path('.'))
    
    guide = assessor.get_behavior_guide(CodebaseState.DISCIPLINED)
    assert guide['approach'] == 'follow_existing_patterns'
    
    guide = assessor.get_behavior_guide(CodebaseState.CHAOTIC)
    assert guide['approach'] == 'propose_standards'


# ==================== 并行执行器测试 ====================

def test_parallel_executor_singleton():
    """测试并行执行器单例"""
    executor1 = ParallelExecutor()
    executor2 = ParallelExecutor()
    assert executor1 is executor2


@pytest.mark.asyncio
async def test_parallel_executor_submit():
    """测试提交任务"""
    executor = get_parallel_executor()
    
    async def dummy_task():
        await asyncio.sleep(0.1)
        return {'status': 'success', 'data': 'test'}
    
    task_id = await executor.submit('test_task', dummy_task())
    assert task_id == 'test_task'
    assert executor.get_status('test_task') == 'running'


@pytest.mark.asyncio
async def test_parallel_executor_get_result():
    """测试获取结果"""
    executor = get_parallel_executor()
    
    async def dummy_task():
        await asyncio.sleep(0.1)
        return {'status': 'success', 'data': 'test'}
    
    task_id = await executor.submit('test_task_2', dummy_task())
    result = await executor.get_result(task_id)
    
    assert result['status'] == 'success'
    assert result['data'] == 'test'


@pytest.mark.asyncio
async def test_parallel_executor_cancel():
    """测试取消任务"""
    executor = get_parallel_executor()
    
    async def long_task():
        await asyncio.sleep(10)
        return {'status': 'success'}
    
    task_id = await executor.submit('test_task_3', long_task())
    success = executor.cancel(task_id)
    
    assert success is True
    assert executor.get_status(task_id) == 'cancelled'


# ==================== 会话管理器测试 ====================

def test_session_manager_singleton():
    """测试会话管理器单例"""
    manager1 = SessionManager()
    manager2 = SessionManager()
    assert manager1 is manager2


def test_session_manager_create_session():
    """测试创建会话"""
    manager = get_session_manager()
    
    class DummyAgent:
        async def execute(self, instruction, **kwargs):
            return {'status': 'success'}
    
    agent = DummyAgent()
    session_id = manager.create_session(agent)
    
    assert session_id.startswith('ses_')
    assert manager.get_session(session_id) is not None


@pytest.mark.asyncio
async def test_session_manager_execute():
    """测试会话执行"""
    manager = get_session_manager()
    
    class DummyAgent:
        async def execute(self, instruction, **kwargs):
            return {'status': 'success', 'instruction': instruction}
    
    agent = DummyAgent()
    session_id = manager.create_session(agent, 'test_session')
    
    result = await manager.execute(session_id, 'test instruction')
    
    assert result['status'] == 'success'
    assert result['instruction'] == 'test instruction'


def test_session_manager_delete_session():
    """测试删除会话"""
    manager = get_session_manager()
    
    class DummyAgent:
        async def execute(self, instruction, **kwargs):
            return {'status': 'success'}
    
    agent = DummyAgent()
    session_id = manager.create_session(agent, 'test_session_delete')
    
    success = manager.delete_session(session_id)
    assert success is True
    assert manager.get_session(session_id) is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
