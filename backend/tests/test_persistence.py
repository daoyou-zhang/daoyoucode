"""
测试持久化功能

验证数据在程序重启后是否保留
"""

import asyncio
import logging
from pathlib import Path
from daoyoucode.agents.memory import get_memory_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_persistence():
    """测试持久化功能"""
    print("\n" + "="*60)
    print("持久化功能测试")
    print("="*60)
    
    # 第一次运行：写入数据
    print("\n第一步：写入数据...")
    memory1 = get_memory_manager()
    
    # 添加用户偏好
    memory1.remember_preference('test-user', 'language', 'python')
    memory1.remember_preference('test-user', 'style', 'functional')
    print("✅ 添加了用户偏好")
    
    # 添加任务
    memory1.add_task('test-user', {
        'agent': 'TestAgent',
        'input': '测试任务1',
        'result': '测试结果1',
        'success': True
    })
    memory1.add_task('test-user', {
        'agent': 'TestAgent',
        'input': '测试任务2',
        'result': '测试结果2',
        'success': True
    })
    print("✅ 添加了2个任务")
    
    # 保存摘要
    memory1.long_term_memory.storage.save_summary(
        'test-session',
        '这是一个测试摘要，用于验证持久化功能。'
    )
    print("✅ 保存了摘要")
    
    # 保存用户画像
    memory1.long_term_memory.storage.save_user_profile(
        'test-user',
        {
            'common_topics': ['python', 'testing', 'memory'],
            'total_conversations': 10,
            'preferred_style': 'functional'
        }
    )
    print("✅ 保存了用户画像")
    
    # 获取存储路径
    storage_dir = memory1.storage.storage_dir
    print(f"\n存储位置: {storage_dir}")
    
    # 检查文件是否存在
    files = [
        'preferences.json',
        'tasks.json',
        'summaries.json',
        'profiles.json'
    ]
    
    print("\n检查文件:")
    for filename in files:
        filepath = storage_dir / filename
        if filepath.exists():
            size = filepath.stat().st_size
            print(f"  ✅ {filename} ({size} bytes)")
        else:
            print(f"  ❌ {filename} (不存在)")
    
    # 模拟程序重启：清除内存中的单例
    print("\n第二步：模拟程序重启...")
    import daoyoucode.agents.memory.manager as manager_module
    manager_module._memory_manager_instance = None
    print("✅ 清除了内存中的单例")
    
    # 重新创建管理器（会自动加载持久化数据）
    print("\n第三步：重新加载数据...")
    memory2 = get_memory_manager()
    
    # 验证用户偏好
    prefs = memory2.get_preferences('test-user')
    print(f"\n用户偏好:")
    for key, value in prefs.items():
        print(f"  {key}: {value}")
    
    if prefs.get('language') == 'python' and prefs.get('style') == 'functional':
        print("✅ 用户偏好加载成功")
    else:
        print("❌ 用户偏好加载失败")
    
    # 验证任务历史
    tasks = memory2.get_task_history('test-user')
    print(f"\n任务历史: {len(tasks)} 个任务")
    for idx, task in enumerate(tasks, 1):
        print(f"  {idx}. {task.get('input', 'N/A')}")
    
    if len(tasks) == 2:
        print("✅ 任务历史加载成功")
    else:
        print("❌ 任务历史加载失败")
    
    # 验证摘要
    summary = memory2.long_term_memory.get_summary('test-session')
    print(f"\n摘要: {summary}")
    
    if summary and '测试摘要' in summary:
        print("✅ 摘要加载成功")
    else:
        print("❌ 摘要加载失败")
    
    # 验证用户画像
    profile = memory2.long_term_memory.get_user_profile('test-user')
    print(f"\n用户画像:")
    if profile:
        for key, value in profile.items():
            print(f"  {key}: {value}")
        print("✅ 用户画像加载成功")
    else:
        print("❌ 用户画像加载失败")
    
    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    all_passed = (
        prefs.get('language') == 'python' and
        len(tasks) == 2 and
        summary and '测试摘要' in summary and
        profile is not None
    )
    
    if all_passed:
        print("🎉 所有持久化测试通过！")
        print("\n数据已成功保存到磁盘，程序重启后会自动加载。")
    else:
        print("⚠️ 部分测试失败")
    
    return all_passed


if __name__ == "__main__":
    test_persistence()
