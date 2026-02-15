"""
测试TaskManager
"""

import asyncio
from daoyoucode.agents.core.task import get_task_manager, TaskStatus


async def test_task_creation():
    """测试任务创建"""
    print("\n=== 测试1: 任务创建 ===")
    
    task_manager = get_task_manager()
    
    # 创建任务
    task = task_manager.create_task(
        description="分析代码结构",
        orchestrator="parallel_explore",
        agent="code_analyzer"
    )
    
    print(f"✓ 创建任务: {task.id}")
    print(f"  描述: {task.description}")
    print(f"  状态: {task.status.value}")
    print(f"  编排器: {task.orchestrator}")
    print(f"  Agent: {task.agent}")
    
    assert task.status == TaskStatus.PENDING
    assert task.orchestrator == "parallel_explore"
    assert task.agent == "code_analyzer"


async def test_task_status_update():
    """测试任务状态更新"""
    print("\n=== 测试2: 任务状态更新 ===")
    
    task_manager = get_task_manager()
    
    # 创建任务
    task = task_manager.create_task(
        description="重构函数",
        orchestrator="workflow"
    )
    
    print(f"✓ 创建任务: {task.id}")
    print(f"  初始状态: {task.status.value}")
    
    # 更新为运行中
    task_manager.update_status(task.id, TaskStatus.RUNNING)
    print(f"  更新状态: {task.status.value}")
    assert task.status == TaskStatus.RUNNING
    assert task.started_at is not None
    
    # 模拟执行
    await asyncio.sleep(0.1)
    
    # 更新为完成
    task_manager.update_status(
        task.id,
        TaskStatus.COMPLETED,
        result="重构完成"
    )
    print(f"  最终状态: {task.status.value}")
    print(f"  结果: {task.result}")
    
    assert task.status == TaskStatus.COMPLETED
    assert task.completed_at is not None
    assert task.result == "重构完成"
    
    # 计算执行时长
    duration = task_manager.get_task_duration(task.id)
    print(f"  执行时长: {duration:.3f}秒")
    assert duration is not None
    assert duration > 0


async def test_task_hierarchy():
    """测试任务层次结构"""
    print("\n=== 测试3: 任务层次结构 ===")
    
    task_manager = get_task_manager()
    
    # 创建父任务
    parent = task_manager.create_task(
        description="完整的代码重构",
        orchestrator="workflow"
    )
    
    print(f"✓ 创建父任务: {parent.id}")
    
    # 创建子任务
    subtask1 = task_manager.create_task(
        description="分析代码",
        orchestrator="simple",
        parent_id=parent.id
    )
    
    subtask2 = task_manager.create_task(
        description="生成重构计划",
        orchestrator="simple",
        parent_id=parent.id
    )
    
    subtask3 = task_manager.create_task(
        description="执行重构",
        orchestrator="simple",
        parent_id=parent.id
    )
    
    print(f"  子任务1: {subtask1.id}")
    print(f"  子任务2: {subtask2.id}")
    print(f"  子任务3: {subtask3.id}")
    
    # 验证父子关系
    assert len(parent.subtasks) == 3
    assert subtask1.parent_id == parent.id
    assert subtask2.parent_id == parent.id
    assert subtask3.parent_id == parent.id
    
    # 获取任务树
    tree = task_manager.get_task_tree(parent.id)
    print(f"\n任务树:")
    print(f"  根任务: {tree['description']}")
    print(f"  子任务数: {len(tree['subtasks'])}")
    
    for i, st in enumerate(tree['subtasks'], 1):
        print(f"    {i}. {st['description']}")
    
    assert len(tree['subtasks']) == 3


async def test_task_queries():
    """测试任务查询"""
    print("\n=== 测试4: 任务查询 ===")
    
    task_manager = get_task_manager()
    
    # 清理之前的任务
    task_manager.clear_completed()
    
    # 创建多个任务
    task1 = task_manager.create_task(
        description="查询测试任务1",
        orchestrator="simple",
        agent="agent1"
    )
    
    task2 = task_manager.create_task(
        description="查询测试任务2",
        orchestrator="workflow",
        agent="agent2"
    )
    
    task3 = task_manager.create_task(
        description="查询测试任务3",
        orchestrator="simple",
        agent="agent1"
    )
    
    # 更新状态
    task_manager.update_status(task1.id, TaskStatus.RUNNING)
    task_manager.update_status(task2.id, TaskStatus.COMPLETED, result="完成")
    
    # 查询活跃任务（只包含这3个任务中的活跃任务）
    active = task_manager.get_active_tasks()
    print(f"✓ 活跃任务数: {len(active)}")
    # task1 (running) + task3 (pending) = 2
    active_test_tasks = [t for t in active if '查询测试任务' in t.description]
    assert len(active_test_tasks) == 2
    
    # 按编排器查询
    simple_tasks = task_manager.get_tasks_by_orchestrator("simple")
    simple_test_tasks = [t for t in simple_tasks if '查询测试任务' in t.description]
    print(f"✓ simple编排器任务数: {len(simple_test_tasks)}")
    assert len(simple_test_tasks) == 2
    
    # 按Agent查询
    agent1_tasks = task_manager.get_tasks_by_agent("agent1")
    agent1_test_tasks = [t for t in agent1_tasks if '查询测试任务' in t.description]
    print(f"✓ agent1任务数: {len(agent1_test_tasks)}")
    assert len(agent1_test_tasks) == 2


async def test_task_stats():
    """测试任务统计"""
    print("\n=== 测试5: 任务统计 ===")
    
    task_manager = get_task_manager()
    
    # 获取统计信息
    stats = task_manager.get_stats()
    
    print(f"✓ 任务统计:")
    print(f"  总任务数: {stats['total_tasks']}")
    print(f"  活跃任务数: {stats['active_tasks']}")
    print(f"  历史任务数: {stats['history_size']}")
    
    print(f"\n  状态分布:")
    for status, count in stats['status_counts'].items():
        if count > 0:
            print(f"    {status}: {count}")
    
    print(f"\n  编排器分布:")
    for orch, count in stats['orchestrator_counts'].items():
        print(f"    {orch}: {count}")
    
    assert stats['total_tasks'] > 0


async def test_singleton():
    """测试单例模式"""
    print("\n=== 测试6: 单例模式 ===")
    
    manager1 = get_task_manager()
    manager2 = get_task_manager()
    
    print(f"✓ manager1 is manager2: {manager1 is manager2}")
    assert manager1 is manager2
    
    # 在manager1创建任务
    task = manager1.create_task(
        description="测试单例",
        orchestrator="simple"
    )
    
    # 在manager2应该能看到
    task2 = manager2.get_task(task.id)
    assert task2 is not None
    assert task2.id == task.id
    print(f"✓ 单例模式工作正常")


async def main():
    """运行所有测试"""
    print("=" * 60)
    print("TaskManager 测试")
    print("=" * 60)
    
    try:
        await test_task_creation()
        await test_task_status_update()
        await test_task_hierarchy()
        await test_task_queries()
        await test_task_stats()
        await test_singleton()
        
        print("\n" + "=" * 60)
        print("✓ 所有测试通过！")
        print("=" * 60)
    
    except AssertionError as e:
        print(f"\n✗ 测试失败: {e}")
        raise
    except Exception as e:
        print(f"\n✗ 测试错误: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
