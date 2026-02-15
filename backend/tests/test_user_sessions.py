"""
测试用户会话映射功能

验证user_id到session_id的映射是否正常工作
"""

import asyncio
import logging
from daoyoucode.agents.memory import get_memory_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_user_sessions():
    """测试用户会话映射"""
    print("\n" + "="*60)
    print("用户会话映射测试")
    print("="*60)
    
    memory = get_memory_manager()
    
    # 模拟多个用户的多个会话
    test_data = [
        ('user-alice', 'session-alice-1', '你好', '你好！'),
        ('user-alice', 'session-alice-1', '这个项目是做什么的？', '这是一个AI助手...'),
        ('user-alice', 'session-alice-2', '如何写Python函数？', '可以这样写...'),
        ('user-bob', 'session-bob-1', 'JavaScript怎么学？', '建议从基础开始...'),
        ('user-bob', 'session-bob-2', 'React有什么特点？', 'React是一个...'),
        ('user-alice', 'session-alice-3', '测试一下', '好的'),
    ]
    
    print("\n第一步：添加对话并建立映射...")
    for user_id, session_id, user_msg, ai_msg in test_data:
        memory.add_conversation(
            session_id=session_id,
            user_message=user_msg,
            ai_response=ai_msg,
            user_id=user_id
        )
        print(f"  ✅ {user_id} -> {session_id}: {user_msg[:20]}...")
    
    # 验证映射
    print("\n第二步：验证用户会话映射...")
    
    # Alice的会话
    alice_sessions = memory.get_user_sessions('user-alice')
    print(f"\nAlice的会话:")
    print(f"  会话数: {len(alice_sessions)}")
    print(f"  会话ID: {alice_sessions}")
    
    expected_alice = ['session-alice-1', 'session-alice-2', 'session-alice-3']
    if set(alice_sessions) == set(expected_alice):
        print("  ✅ Alice的会话映射正确")
    else:
        print(f"  ❌ Alice的会话映射错误，期望: {expected_alice}")
    
    # Bob的会话
    bob_sessions = memory.get_user_sessions('user-bob')
    print(f"\nBob的会话:")
    print(f"  会话数: {len(bob_sessions)}")
    print(f"  会话ID: {bob_sessions}")
    
    expected_bob = ['session-bob-1', 'session-bob-2']
    if set(bob_sessions) == set(expected_bob):
        print("  ✅ Bob的会话映射正确")
    else:
        print(f"  ❌ Bob的会话映射错误，期望: {expected_bob}")
    
    # 反向查询
    print("\n第三步：验证反向查询（session -> user）...")
    
    test_sessions = [
        ('session-alice-1', 'user-alice'),
        ('session-bob-1', 'user-bob'),
        ('session-alice-3', 'user-alice'),
    ]
    
    for session_id, expected_user in test_sessions:
        actual_user = memory.get_session_user(session_id)
        if actual_user == expected_user:
            print(f"  ✅ {session_id} -> {actual_user}")
        else:
            print(f"  ❌ {session_id} -> {actual_user} (期望: {expected_user})")
    
    # 验证持久化
    print("\n第四步：验证持久化...")
    
    # 检查文件是否存在
    storage_dir = memory.storage.storage_dir
    user_sessions_file = storage_dir / 'user_sessions.json'
    
    if user_sessions_file.exists():
        print(f"  ✅ 映射文件已创建: {user_sessions_file}")
        
        # 读取文件内容
        import json
        with open(user_sessions_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"  用户数: {len(data.get('user_sessions', {}))}")
        print(f"  会话数: {len(data.get('session_users', {}))}")
    else:
        print(f"  ❌ 映射文件不存在")
    
    # 模拟程序重启
    print("\n第五步：模拟程序重启...")
    
    # 清除单例
    import daoyoucode.agents.memory.manager as manager_module
    manager_module._memory_manager_instance = None
    print("  ✅ 清除了内存单例")
    
    # 重新创建管理器
    memory2 = get_memory_manager()
    print("  ✅ 重新创建了管理器")
    
    # 验证数据是否恢复
    alice_sessions_2 = memory2.get_user_sessions('user-alice')
    bob_sessions_2 = memory2.get_user_sessions('user-bob')
    
    print(f"\n重启后的数据:")
    print(f"  Alice会话数: {len(alice_sessions_2)}")
    print(f"  Bob会话数: {len(bob_sessions_2)}")
    
    if set(alice_sessions_2) == set(expected_alice):
        print("  ✅ Alice的会话映射已恢复")
    else:
        print(f"  ❌ Alice的会话映射未恢复")
    
    if set(bob_sessions_2) == set(expected_bob):
        print("  ✅ Bob的会话映射已恢复")
    else:
        print(f"  ❌ Bob的会话映射未恢复")
    
    # 测试用户画像生成
    print("\n第六步：测试用户画像生成...")
    
    # 为Alice生成画像
    try:
        profile = await memory2.long_term_memory.build_user_profile(
            user_id='user-alice'
        )
        
        print(f"\nAlice的用户画像:")
        print(f"  会话数: {profile.get('total_sessions')}")
        print(f"  对话数: {profile.get('total_conversations')}")
        print(f"  常见话题: {profile.get('common_topics', [])}")
        print(f"  技能水平: {profile.get('skill_level')}")
        
        if profile.get('total_sessions') == 3:
            print("  ✅ 会话数正确")
        else:
            print(f"  ❌ 会话数错误，期望3，实际{profile.get('total_sessions')}")
    
    except Exception as e:
        print(f"  ❌ 生成画像失败: {e}")
    
    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    all_passed = (
        set(alice_sessions) == set(expected_alice) and
        set(bob_sessions) == set(expected_bob) and
        set(alice_sessions_2) == set(expected_alice) and
        set(bob_sessions_2) == set(expected_bob) and
        user_sessions_file.exists()
    )
    
    if all_passed:
        print("🎉 所有测试通过！用户会话映射功能正常！")
    else:
        print("⚠️ 部分测试失败")
    
    return all_passed


if __name__ == "__main__":
    asyncio.run(test_user_sessions())
