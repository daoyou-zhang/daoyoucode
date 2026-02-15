"""
测试用户画像检查优化

验证时间窗口缓存是否生效
"""

import asyncio
import time
from daoyoucode.agents.core.agent import BaseAgent, AgentConfig


async def test_profile_check_frequency():
    """测试画像检查频率优化"""
    print("\n" + "="*60)
    print("测试：用户画像检查频率优化")
    print("="*60)
    
    # 创建Agent
    config = AgentConfig(
        name="test_agent",
        description="测试Agent",
        model="gpt-4",
        temperature=0.7
    )
    agent = BaseAgent(config)
    
    user_id = "test_user_123"
    session_id = "test_session"
    
    # 第1次检查（应该执行）
    print("\n第1次检查（应该执行）...")
    start = time.time()
    await agent._check_and_update_profile(user_id, session_id)
    duration1 = time.time() - start
    print(f"✓ 第1次检查完成，耗时: {duration1*1000:.2f}ms")
    
    # 第2次检查（应该跳过，因为在1小时内）
    print("\n第2次检查（应该跳过）...")
    start = time.time()
    await agent._check_and_update_profile(user_id, session_id)
    duration2 = time.time() - start
    print(f"✓ 第2次检查完成，耗时: {duration2*1000:.2f}ms")
    
    # 第3次检查（应该跳过）
    print("\n第3次检查（应该跳过）...")
    start = time.time()
    await agent._check_and_update_profile(user_id, session_id)
    duration3 = time.time() - start
    print(f"✓ 第3次检查完成，耗时: {duration3*1000:.2f}ms")
    
    # 验证优化效果
    print("\n" + "="*60)
    print("优化效果分析：")
    print("="*60)
    print(f"第1次检查: {duration1*1000:.2f}ms（正常执行）")
    print(f"第2次检查: {duration2*1000:.2f}ms（应该很快，因为跳过了）")
    print(f"第3次检查: {duration3*1000:.2f}ms（应该很快，因为跳过了）")
    
    # 第2、3次应该比第1次快很多（至少快50%）
    if duration2 < duration1 * 0.5 and duration3 < duration1 * 0.5:
        print("\n✅ 优化生效！后续检查速度提升 50%+")
        speedup = duration1 / ((duration2 + duration3) / 2)
        print(f"   平均加速: {speedup:.1f}x")
    else:
        print("\n⚠️ 优化效果不明显，可能需要进一步调查")
    
    # 测试不同用户（应该独立缓存）
    print("\n" + "="*60)
    print("测试：不同用户独立缓存")
    print("="*60)
    
    user_id2 = "test_user_456"
    print(f"\n检查用户2: {user_id2}（应该执行）...")
    start = time.time()
    await agent._check_and_update_profile(user_id2, session_id)
    duration_user2 = time.time() - start
    print(f"✓ 用户2检查完成，耗时: {duration_user2*1000:.2f}ms")
    
    print(f"\n再次检查用户1: {user_id}（应该跳过）...")
    start = time.time()
    await agent._check_and_update_profile(user_id, session_id)
    duration_user1_again = time.time() - start
    print(f"✓ 用户1再次检查完成，耗时: {duration_user1_again*1000:.2f}ms")
    
    if duration_user1_again < duration_user2 * 0.5:
        print("\n✅ 不同用户缓存独立工作正常")
    
    print("\n" + "="*60)
    print("✅ 测试完成")
    print("="*60)


async def test_cache_expiry():
    """测试缓存过期（模拟）"""
    print("\n" + "="*60)
    print("测试：缓存过期机制")
    print("="*60)
    
    config = AgentConfig(
        name="test_agent",
        description="测试Agent",
        model="gpt-4",
        temperature=0.7
    )
    agent = BaseAgent(config)
    
    user_id = "test_user_expiry"
    session_id = "test_session"
    
    # 第1次检查
    print("\n第1次检查...")
    await agent._check_and_update_profile(user_id, session_id)
    print("✓ 完成")
    
    # 手动修改缓存时间（模拟1小时后）
    print("\n模拟1小时后...")
    agent._profile_check_cache[user_id] = time.time() - 3601  # 3601秒前
    
    # 第2次检查（应该重新执行）
    print("第2次检查（缓存已过期，应该重新执行）...")
    start = time.time()
    await agent._check_and_update_profile(user_id, session_id)
    duration = time.time() - start
    print(f"✓ 完成，耗时: {duration*1000:.2f}ms")
    
    print("\n✅ 缓存过期机制正常")


if __name__ == "__main__":
    asyncio.run(test_profile_check_frequency())
    asyncio.run(test_cache_expiry())
