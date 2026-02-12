"""
测试高级功能：Hook系统、权限系统、ReAct循环
"""

import pytest
import asyncio
from daoyoucode.agents.core.hooks import (
    HookManager, HookEvent, HookContext, Hook, FunctionHook,
    get_hook_manager, hook
)
from daoyoucode.agents.core.permission import (
    PermissionManager, PermissionRule, PermissionCategory,
    get_permission_manager, check_permission, require_permission
)
from daoyoucode.agents.orchestrators.react import ReActOrchestrator, ReActPlan
from daoyoucode.agents.core.context import Context


# ==================== Hook系统测试 ====================

def test_hook_manager_singleton():
    """测试Hook管理器单例"""
    manager1 = HookManager()
    manager2 = HookManager()
    assert manager1 is manager2


def test_hook_registration():
    """测试Hook注册"""
    manager = HookManager()
    manager.clear()  # 清空
    
    # 创建Hook
    class TestHook(Hook):
        def __init__(self):
            super().__init__("test_hook", priority=100)
        
        async def execute(self, context: HookContext):
            context.set('executed', True)
            return context
    
    # 注册Hook
    hook_instance = TestHook()
    manager.register(HookEvent.PRE_EXECUTE, hook_instance)
    
    # 验证
    hooks = manager.list_hooks(HookEvent.PRE_EXECUTE)
    assert HookEvent.PRE_EXECUTE.value in hooks
    assert 'test_hook' in hooks[HookEvent.PRE_EXECUTE.value]


@pytest.mark.asyncio
async def test_hook_trigger():
    """测试Hook触发"""
    manager = HookManager()
    manager.clear()
    
    # 注册Hook
    executed = []
    
    def test_hook(context: HookContext):
        executed.append(context.event.value)
        context.set('hook_executed', True)
        return context
    
    manager.register_function(HookEvent.PRE_EXECUTE, test_hook)
    
    # 触发Hook
    context = await manager.trigger(
        HookEvent.PRE_EXECUTE,
        data={'test': 'data'}
    )
    
    # 验证
    assert len(executed) == 1
    assert executed[0] == 'pre_execute'
    assert context.get('hook_executed') is True


@pytest.mark.asyncio
async def test_hook_priority():
    """测试Hook优先级"""
    manager = HookManager()
    manager.clear()
    
    execution_order = []
    
    def hook1(context: HookContext):
        execution_order.append('hook1')
        return context
    
    def hook2(context: HookContext):
        execution_order.append('hook2')
        return context
    
    def hook3(context: HookContext):
        execution_order.append('hook3')
        return context
    
    # 注册Hook（不同优先级）
    manager.register_function(HookEvent.PRE_EXECUTE, hook1, priority=100)
    manager.register_function(HookEvent.PRE_EXECUTE, hook2, priority=50)   # 优先
    manager.register_function(HookEvent.PRE_EXECUTE, hook3, priority=200)  # 最后
    
    # 触发Hook
    await manager.trigger(HookEvent.PRE_EXECUTE)
    
    # 验证执行顺序
    assert execution_order == ['hook2', 'hook1', 'hook3']


@pytest.mark.asyncio
async def test_hook_interruption():
    """测试Hook中断"""
    manager = HookManager()
    manager.clear()
    
    executed = []
    
    def hook1(context: HookContext):
        executed.append('hook1')
        return context
    
    def hook2(context: HookContext):
        executed.append('hook2')
        return None  # 中断执行
    
    def hook3(context: HookContext):
        executed.append('hook3')
        return context
    
    manager.register_function(HookEvent.PRE_EXECUTE, hook1, priority=10)
    manager.register_function(HookEvent.PRE_EXECUTE, hook2, priority=20)
    manager.register_function(HookEvent.PRE_EXECUTE, hook3, priority=30)
    
    # 触发Hook
    context = await manager.trigger(HookEvent.PRE_EXECUTE)
    
    # 验证：hook2返回None后应该中断
    # 使用context.get()方法访问数据
    assert context.get('_interrupted') is True
    assert context.get('_interrupted_by') == 'hook2'


def test_hook_decorator():
    """测试Hook装饰器"""
    manager = HookManager()
    manager.clear()
    
    @hook(HookEvent.PRE_EXECUTE, priority=50)
    def my_hook(context: HookContext):
        context.set('decorator_hook', True)
        return context
    
    # 验证Hook已注册
    hooks = manager.list_hooks(HookEvent.PRE_EXECUTE)
    assert 'my_hook' in hooks[HookEvent.PRE_EXECUTE.value]


# ==================== 权限系统测试 ====================

def test_permission_manager_singleton():
    """测试权限管理器单例"""
    manager1 = PermissionManager()
    manager2 = PermissionManager()
    assert manager1 is manager2


def test_permission_default_rules():
    """测试默认权限规则"""
    manager = PermissionManager()
    
    # 测试读取权限
    assert manager.check_permission('read', 'test.py') == 'allow'
    assert manager.check_permission('read', '.env') == 'ask'
    assert manager.check_permission('read', '.env.example') == 'allow'
    assert manager.check_permission('read', 'secret.key') == 'ask'
    
    # 测试写入权限
    assert manager.check_permission('write', 'test.py') == 'allow'
    assert manager.check_permission('write', '.env') == 'deny'
    assert manager.check_permission('write', 'private.key') == 'deny'
    
    # 测试删除权限
    assert manager.check_permission('delete', 'test.pyc') == 'allow'
    assert manager.check_permission('delete', '.env') == 'deny'
    
    # 测试执行权限
    assert manager.check_permission('execute', 'git status') == 'allow'
    assert manager.check_permission('execute', 'rm -rf /') == 'deny'
    assert manager.check_permission('execute', 'sudo apt install') == 'ask'


def test_permission_rule_matching():
    """测试权限规则匹配"""
    rule = PermissionRule('*.py', 'allow')
    
    assert rule.matches('test.py') is True
    assert rule.matches('test.js') is False
    
    # 测试通配符（fnmatch支持路径匹配）
    rule2 = PermissionRule('**/*.py', 'allow')
    assert rule2.matches('src/test.py') is True
    assert rule2.matches('src/utils/helper.py') is True


def test_permission_priority():
    """测试权限优先级"""
    manager = PermissionManager()
    category = PermissionCategory('test', default_action='ask')
    
    # 添加规则（不同优先级）
    category.add_rule('*.txt', 'allow', priority=100)
    category.add_rule('secret.txt', 'deny', priority=10)  # 更高优先级
    
    # 验证：高优先级规则应该先匹配
    assert category.check('secret.txt') == 'deny'
    assert category.check('normal.txt') == 'allow'


def test_permission_add_rule():
    """测试添加权限规则"""
    manager = PermissionManager()
    manager.clear('test_category')
    
    # 添加规则
    manager.add_rule('test_category', '*.test', 'deny', priority=50)
    
    # 验证
    assert manager.check_permission('test_category', 'file.test') == 'deny'


def test_permission_load_config():
    """测试从配置加载权限"""
    manager = PermissionManager()
    
    config = {
        'custom_read': {
            '*.secret': 'deny',
            '*.public': 'allow'
        },
        'custom_write': {
            '*.lock': 'deny'
        }
    }
    
    manager.load_config(config)
    
    # 验证
    assert manager.check_permission('custom_read', 'data.secret') == 'deny'
    assert manager.check_permission('custom_read', 'data.public') == 'allow'
    assert manager.check_permission('custom_write', 'file.lock') == 'deny'


def test_permission_decorator():
    """测试权限装饰器"""
    manager = PermissionManager()
    
    # 添加拒绝规则
    manager.add_rule('write', 'forbidden.txt', 'deny', priority=1)
    
    @require_permission('write')
    def write_file(path: str, content: str):
        return f"写入 {path}: {content}"
    
    # 测试允许的文件
    result = write_file('allowed.txt', 'content')
    assert 'allowed.txt' in result
    
    # 测试拒绝的文件
    with pytest.raises(PermissionError):
        write_file('forbidden.txt', 'content')


# ==================== ReAct循环测试 ====================

@pytest.mark.asyncio
async def test_react_orchestrator_creation():
    """测试ReAct编排器创建"""
    orchestrator = ReActOrchestrator(
        max_reflections=3,
        require_approval=False,
        auto_verify=True
    )
    
    assert orchestrator.max_reflections == 3
    assert orchestrator.require_approval is False
    assert orchestrator.auto_verify is True
    assert orchestrator.get_name() == 'react'


@pytest.mark.asyncio
async def test_react_plan_generation():
    """测试ReAct计划生成"""
    orchestrator = ReActOrchestrator()
    context = Context(session_id='test')
    
    plan = await orchestrator._plan(
        instruction='实现一个简单的功能',
        context=context
    )
    
    assert plan is not None
    assert isinstance(plan, ReActPlan)
    assert len(plan.steps) > 0
    assert plan.complexity > 0


@pytest.mark.asyncio
async def test_react_step_execution():
    """测试ReAct步骤执行"""
    orchestrator = ReActOrchestrator()
    context = Context(session_id='test')
    
    step = {
        'action': 'analyze',
        'description': '分析任务'
    }
    
    result = await orchestrator._execute_step(step, context, None)
    
    assert result is not None
    assert 'analysis' in result


@pytest.mark.asyncio
async def test_react_observation():
    """测试ReAct观察"""
    orchestrator = ReActOrchestrator(auto_verify=False)
    context = Context(session_id='test')
    
    # 测试成功结果
    success_result = {
        'steps': [
            {'step': 1, 'success': True},
            {'step': 2, 'success': True}
        ],
        'completed': 2,
        'total': 2
    }
    
    observation = await orchestrator._observe(success_result, context)
    assert observation['success'] is True
    
    # 测试失败结果
    failure_result = {
        'steps': [
            {'step': 1, 'success': True},
            {'step': 2, 'success': False, 'error': '测试错误'}
        ],
        'completed': 1,
        'total': 2
    }
    
    observation = await orchestrator._observe(failure_result, context)
    assert observation['success'] is False
    assert '测试错误' in observation['error']


@pytest.mark.asyncio
async def test_react_reflection():
    """测试ReAct反思"""
    orchestrator = ReActOrchestrator()
    context = Context(session_id='test')
    
    plan = ReActPlan(
        steps=[{'action': 'test', 'description': '测试'}],
        estimated_time=100.0,
        complexity=2,
        risks=[]
    )
    
    new_instruction = await orchestrator._reflect(
        original_instruction='原始任务',
        current_instruction='当前任务',
        error='测试错误',
        plan=plan,
        context=context,
        attempt=1
    )
    
    assert new_instruction is not None
    assert isinstance(new_instruction, str)
    assert len(new_instruction) > 0


def test_react_orchestrator_info():
    """测试ReAct编排器信息"""
    orchestrator = ReActOrchestrator()
    
    assert orchestrator.get_name() == 'react'
    assert 'ReAct' in orchestrator.get_description()
    assert '规划-执行-反思-重试' in orchestrator.get_description()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
