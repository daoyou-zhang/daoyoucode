"""
测试超时恢复集成到 executor
"""

import asyncio
import logging
from unittest.mock import AsyncMock, patch, MagicMock
from daoyoucode.agents.executor import execute_skill
from daoyoucode.agents.llm.exceptions import LLMTimeoutError

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_timeout_recovery_integration():
    """测试超时恢复集成"""
    print("\n" + "="*60)
    print("测试: 超时恢复集成到 executor")
    print("="*60)
    
    # Mock skill loader
    mock_skill = MagicMock()
    mock_skill.name = "test-skill"
    mock_skill.orchestrator = "react"
    mock_skill.agent = "test-agent"
    
    # Mock orchestrator
    mock_orchestrator = MagicMock()
    
    # 模拟第一次超时，第二次成功
    call_count = [0]
    
    async def mock_execute(skill, user_input, context):
        call_count[0] += 1
        if call_count[0] == 1:
            raise LLMTimeoutError("模拟超时")
        return {
            'success': True,
            'content': '成功响应',
            'error': None
        }
    
    mock_orchestrator.execute = mock_execute
    
    with patch('daoyoucode.agents.executor.get_skill_loader') as mock_get_skill_loader, \
         patch('daoyoucode.agents.executor.get_orchestrator') as mock_get_orchestrator, \
         patch('daoyoucode.agents.executor.get_hook_manager') as mock_get_hook_manager, \
         patch('daoyoucode.agents.executor.get_task_manager') as mock_get_task_manager:
        
        # 设置 mocks
        mock_skill_loader = MagicMock()
        mock_skill_loader.get_skill.return_value = mock_skill
        mock_get_skill_loader.return_value = mock_skill_loader
        
        mock_get_orchestrator.return_value = mock_orchestrator
        
        # Mock hook manager - 添加所有需要的方法
        mock_hook_mgr = MagicMock()
        
        async def mock_run_before_hooks(ctx):
            return ctx
        
        async def mock_run_after_hooks(ctx, result):
            return result
        
        async def mock_run_error_hooks(ctx, error):
            return None
        
        mock_hook_mgr.run_before_hooks = mock_run_before_hooks
        mock_hook_mgr.run_after_hooks = mock_run_after_hooks
        mock_hook_mgr.run_error_hooks = mock_run_error_hooks
        mock_get_hook_manager.return_value = mock_hook_mgr
        
        # Mock task manager
        mock_task_mgr = MagicMock()
        mock_task = MagicMock()
        mock_task.id = "test-task-123"
        mock_task_mgr.create_task.return_value = mock_task
        mock_get_task_manager.return_value = mock_task_mgr
        
        # 执行测试
        result = await execute_skill(
            skill_name="test-skill",
            user_input="测试输入",
            context={'test': True},
            enable_timeout_recovery=True
        )
        
        print(f"\n执行结果:")
        print(f"  成功: {result.get('success')}")
        print(f"  内容: {result.get('content')}")
        print(f"  错误: {result.get('error')}")
        print(f"  调用次数: {call_count[0]}")
        
        if result.get('success') and call_count[0] == 2:
            print("\n✅ 测试通过：超时恢复成功")
            return True
        else:
            print("\n❌ 测试失败")
            return False


async def test_timeout_recovery_disabled():
    """测试禁用超时恢复"""
    print("\n" + "="*60)
    print("测试: 禁用超时恢复")
    print("="*60)
    
    # Mock skill loader
    mock_skill = MagicMock()
    mock_skill.name = "test-skill"
    mock_skill.orchestrator = "react"
    mock_skill.agent = "test-agent"
    
    # Mock orchestrator - 总是超时
    mock_orchestrator = MagicMock()
    
    async def mock_execute(skill, user_input, context):
        raise LLMTimeoutError("模拟超时")
    
    mock_orchestrator.execute = mock_execute
    
    with patch('daoyoucode.agents.executor.get_skill_loader') as mock_get_skill_loader, \
         patch('daoyoucode.agents.executor.get_orchestrator') as mock_get_orchestrator, \
         patch('daoyoucode.agents.executor.get_hook_manager') as mock_get_hook_manager, \
         patch('daoyoucode.agents.executor.get_task_manager') as mock_get_task_manager:
        
        # 设置 mocks
        mock_skill_loader = MagicMock()
        mock_skill_loader.get_skill.return_value = mock_skill
        mock_get_skill_loader.return_value = mock_skill_loader
        
        mock_get_orchestrator.return_value = mock_orchestrator
        
        # Mock hook manager
        mock_hook_mgr = MagicMock()
        
        async def mock_run_before_hooks(ctx):
            return ctx
        
        async def mock_run_error_hooks(ctx, error):
            return None
        
        mock_hook_mgr.run_before_hooks = mock_run_before_hooks
        mock_hook_mgr.run_error_hooks = mock_run_error_hooks
        mock_get_hook_manager.return_value = mock_hook_mgr
        
        # Mock task manager
        mock_task_mgr = MagicMock()
        mock_task = MagicMock()
        mock_task.id = "test-task-123"
        mock_task_mgr.create_task.return_value = mock_task
        mock_get_task_manager.return_value = mock_task_mgr
        
        # 执行测试 - 禁用超时恢复
        result = await execute_skill(
            skill_name="test-skill",
            user_input="测试输入",
            context={'test': True},
            enable_timeout_recovery=False
        )
        
        print(f"\n执行结果:")
        print(f"  成功: {result.get('success')}")
        print(f"  错误: {result.get('error')}")
        
        if not result.get('success') and 'timeout' in str(result.get('error')).lower():
            print("\n✅ 测试通过：禁用超时恢复时直接返回错误")
            return True
        else:
            print("\n❌ 测试失败")
            return False


async def test_timeout_recovery_context_flag():
    """测试通过 context 控制超时恢复"""
    print("\n" + "="*60)
    print("测试: 通过 context 控制超时恢复")
    print("="*60)
    
    # Mock skill loader
    mock_skill = MagicMock()
    mock_skill.name = "test-skill"
    mock_skill.orchestrator = "react"
    mock_skill.agent = "test-agent"
    
    # Mock orchestrator
    mock_orchestrator = MagicMock()
    
    async def mock_execute(skill, user_input, context):
        return {
            'success': True,
            'content': '成功',
            'error': None
        }
    
    mock_orchestrator.execute = mock_execute
    
    with patch('daoyoucode.agents.executor.get_skill_loader') as mock_get_skill_loader, \
         patch('daoyoucode.agents.executor.get_orchestrator') as mock_get_orchestrator, \
         patch('daoyoucode.agents.executor.get_hook_manager') as mock_get_hook_manager, \
         patch('daoyoucode.agents.executor.get_task_manager') as mock_get_task_manager:
        
        # 设置 mocks
        mock_skill_loader = MagicMock()
        mock_skill_loader.get_skill.return_value = mock_skill
        mock_get_skill_loader.return_value = mock_skill_loader
        
        mock_get_orchestrator.return_value = mock_orchestrator
        
        # Mock hook manager - 添加所有需要的方法
        mock_hook_mgr = MagicMock()
        
        async def mock_run_before_hooks(ctx):
            return ctx
        
        async def mock_run_after_hooks(ctx, result):
            return result
        
        async def mock_run_error_hooks(ctx, error):
            return None
        
        mock_hook_mgr.run_before_hooks = mock_run_before_hooks
        mock_hook_mgr.run_after_hooks = mock_run_after_hooks
        mock_hook_mgr.run_error_hooks = mock_run_error_hooks
        mock_get_hook_manager.return_value = mock_hook_mgr
        
        # Mock task manager
        mock_task_mgr = MagicMock()
        mock_task = MagicMock()
        mock_task.id = "test-task-123"
        mock_task_mgr.create_task.return_value = mock_task
        mock_get_task_manager.return_value = mock_task_mgr
        
        # 测试1: 通过 context 禁用
        result1 = await execute_skill(
            skill_name="test-skill",
            user_input="测试输入",
            context={'disable_timeout_recovery': True}
        )
        
        print(f"\n测试1 - 通过 context 禁用:")
        print(f"  成功: {result1.get('success')}")
        
        # 测试2: 测试模式禁用
        result2 = await execute_skill(
            skill_name="test-skill",
            user_input="测试输入",
            context={'test_mode': True}
        )
        
        print(f"\n测试2 - 测试模式禁用:")
        print(f"  成功: {result2.get('success')}")
        
        if result1.get('success') and result2.get('success'):
            print("\n✅ 测试通过：context 控制超时恢复正常工作")
            return True
        else:
            print("\n❌ 测试失败")
            return False


async def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("超时恢复集成测试")
    print("="*60)
    
    results = []
    results.append(await test_timeout_recovery_integration())
    results.append(await test_timeout_recovery_disabled())
    results.append(await test_timeout_recovery_context_flag())
    
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    print(f"通过: {sum(results)}/{len(results)}")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
