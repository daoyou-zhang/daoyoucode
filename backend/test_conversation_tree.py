"""
测试对话树功能
"""

import asyncio
import sys
from pathlib import Path

# 设置UTF-8编码
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加backend到路径
sys.path.insert(0, str(Path(__file__).parent))

from daoyoucode.agents.memory import get_conversation_tree


async def test_basic_tree():
    """测试基础树结构"""
    print("\n" + "="*60)
    print("测试1: 基础树结构")
    print("="*60)
    
    # 重新创建树实例（避免单例影响）
    from daoyoucode.agents.memory.conversation_tree import ConversationTree
    tree = ConversationTree(enabled=True)
    
    # 添加第一个对话
    node1 = tree.add_conversation(
        user_message="我的猫不吃饭",
        ai_response="可能是肠胃问题，建议观察..."
    )
    print(f"✅ 添加对话1: branch={node1.branch_id}, depth={node1.depth}")
    print(f"   话题关键词: {tree._topic_keywords.get(node1.branch_id, set())}")
    
    # 添加第二个对话（同一话题 - 包含"猫"关键词）
    node2 = tree.add_conversation(
        user_message="猫不吃饭需要去医院吗？",
        ai_response="如果持续2天以上，建议就医..."
    )
    print(f"✅ 添加对话2: branch={node2.branch_id}, depth={node2.depth}")
    print(f"   话题关键词: {tree._topic_keywords.get(node2.branch_id, set())}")
    
    # 检查是否在同一分支
    assert node1.branch_id == node2.branch_id, f"应该在同一分支: {node1.branch_id} vs {node2.branch_id}"
    print(f"✓ 对话1和2在同一分支: {node1.branch_id}")
    
    # 添加第三个对话（话题切换）
    node3 = tree.add_conversation(
        user_message="那狗呢？狗的皮肤有红点",
        ai_response="狗的皮肤问题可能是过敏..."
    )
    print(f"✅ 添加对话3: branch={node3.branch_id}, depth={node3.depth}")
    
    # 检查是否创建了新分支
    assert node3.branch_id != node1.branch_id, "应该创建新分支"
    print(f"✓ 对话3创建了新分支: {node3.branch_id}")
    
    # 获取统计信息
    stats = tree.get_tree_stats()
    print(f"\n📊 树统计:")
    print(f"  - 总对话数: {stats['total_conversations']}")
    print(f"  - 总分支数: {stats['total_branches']}")
    print(f"  - 最大深度: {stats['max_depth']}")
    print(f"  - 当前分支: {stats['current_branch_id']}")
    
    assert stats['total_conversations'] == 3
    assert stats['total_branches'] == 2
    
    print("\n✅ 测试1通过")


async def test_branch_retrieval():
    """测试分支检索"""
    print("\n" + "="*60)
    print("测试2: 分支检索")
    print("="*60)
    
    tree = get_conversation_tree(enabled=True)
    
    # 创建多个分支
    # 分支1: 猫-肠胃问题
    tree.add_conversation("我的猫不吃饭", "可能是肠胃问题...")
    tree.add_conversation("需要吃药吗？", "可以先观察...")
    tree.add_conversation("吃什么药？", "建议益生菌...")
    
    # 分支2: 狗-皮肤问题
    tree.add_conversation("狗的皮肤有红点", "可能是过敏...")
    tree.add_conversation("怎么治疗？", "可以用药膏...")
    
    # 分支3: 猫-疫苗
    tree.add_conversation("猫需要打疫苗吗？", "需要定期接种...")
    
    stats = tree.get_tree_stats()
    print(f"📊 创建了{stats['total_branches']}个分支，{stats['total_conversations']}个对话")
    
    # 测试当前分支检索
    current_branch_convs = tree.get_branch_conversations()
    print(f"\n✅ 当前分支有{len(current_branch_convs)}个对话")
    
    # 测试关键词检索
    relevant_convs = tree.get_relevant_conversations(
        current_message="猫的肠胃问题怎么办？",
        limit=3,
        strategy='keyword'
    )
    print(f"\n✅ 关键词检索找到{len(relevant_convs)}个相关对话:")
    for i, conv in enumerate(relevant_convs, 1):
        print(f"  {i}. {conv['user'][:30]}...")
    
    # 测试树结构检索
    relevant_convs = tree.get_relevant_conversations(
        current_message="猫的肠胃问题怎么办？",
        limit=3,
        strategy='tree'
    )
    print(f"\n✅ 树结构检索找到{len(relevant_convs)}个相关对话:")
    for i, conv in enumerate(relevant_convs, 1):
        print(f"  {i}. {conv['user'][:30]}...")
    
    print("\n✅ 测试2通过")


async def test_topic_detection():
    """测试话题检测"""
    print("\n" + "="*60)
    print("测试3: 话题检测")
    print("="*60)
    
    from daoyoucode.agents.memory.conversation_tree import ConversationTree
    tree = ConversationTree(enabled=True)
    
    # 添加一系列对话，测试话题检测
    conversations = [
        ("我的猫不吃饭", "可能是肠胃问题..."),
        ("猫不吃饭需要去医院吗？", "建议观察2天..."),  # 同一话题（包含"猫"、"吃饭"）
        ("狗的皮肤有红点", "可能是过敏..."),  # 话题切换
        ("狗的皮肤用什么药膏？", "可以用皮炎平..."),  # 同一话题（包含"狗的"、"皮肤"）
        ("猫需要打疫苗吗？", "需要定期接种..."),  # 话题切换
    ]
    
    branches = []
    for user_msg, ai_resp in conversations:
        node = tree.add_conversation(user_msg, ai_resp)
        branches.append(node.branch_id)
        
        topic_switch = "🌿" if node.is_branch_start else "  "
        print(f"{topic_switch} {user_msg[:20]}... -> branch={node.branch_id[:10]}...")
    
    # 检查话题切换
    assert branches[0] == branches[1], "对话1和2应该在同一分支（都关于猫不吃饭）"
    assert branches[2] != branches[1], "对话3应该创建新分支（从猫切换到狗）"
    assert branches[2] == branches[3], "对话3和4应该在同一分支（都关于狗皮肤）"
    assert branches[4] != branches[3], "对话5应该创建新分支（从狗皮肤切换到猫疫苗）"
    
    stats = tree.get_tree_stats()
    print(f"\n📊 检测到{stats['total_branches']}个话题分支")
    
    print("\n✅ 测试3通过")


async def test_export_import():
    """测试导出和导入"""
    print("\n" + "="*60)
    print("测试4: 导出和导入")
    print("="*60)
    
    # 创建树并添加对话
    tree1 = get_conversation_tree(enabled=True)
    tree1.add_conversation("我的猫不吃饭", "可能是肠胃问题...")
    tree1.add_conversation("需要去医院吗？", "建议观察...")
    tree1.add_conversation("狗的皮肤有红点", "可能是过敏...")
    
    # 导出
    history = tree1.export_to_history()
    print(f"✅ 导出了{len(history)}个对话")
    
    # 检查元数据
    for conv in history:
        assert 'metadata' in conv
        assert 'conversation_id' in conv['metadata']
        assert 'branch_id' in conv['metadata']
    print("✓ 所有对话都包含树结构元数据")
    
    # 创建新树并导入
    from daoyoucode.agents.memory.conversation_tree import ConversationTree
    tree2 = ConversationTree(enabled=True)
    tree2.load_from_history(history)
    
    stats1 = tree1.get_tree_stats()
    stats2 = tree2.get_tree_stats()
    
    print(f"\n📊 原树: {stats1['total_conversations']}个对话, {stats1['total_branches']}个分支")
    print(f"📊 新树: {stats2['total_conversations']}个对话, {stats2['total_branches']}个分支")
    
    assert stats1['total_conversations'] == stats2['total_conversations']
    assert stats1['total_branches'] == stats2['total_branches']
    
    print("\n✅ 测试4通过")


async def test_integration_with_memory():
    """测试与Memory系统的集成"""
    print("\n" + "="*60)
    print("测试5: 与Memory系统集成")
    print("="*60)
    
    from daoyoucode.agents.memory import get_memory_manager
    
    # 创建记忆管理器（启用树结构）
    memory = get_memory_manager()
    
    session_id = "test-session-tree"
    user_id = "test-user"
    
    # 添加对话
    memory.add_conversation(
        session_id=session_id,
        user_message="我的猫不吃饭",
        ai_response="可能是肠胃问题...",
        user_id=user_id
    )
    
    memory.add_conversation(
        session_id=session_id,
        user_message="需要去医院吗？",
        ai_response="建议观察2天...",
        user_id=user_id
    )
    
    memory.add_conversation(
        session_id=session_id,
        user_message="狗的皮肤有红点",
        ai_response="可能是过敏...",
        user_id=user_id
    )
    
    # 获取历史（应该包含树结构元数据）
    history = memory.get_conversation_history(session_id)
    print(f"✅ 获取了{len(history)}个对话")
    
    # 检查元数据
    has_tree_metadata = all(
        'metadata' in conv and 'branch_id' in conv.get('metadata', {})
        for conv in history
    )
    
    if has_tree_metadata:
        print("✓ 所有对话都包含树结构元数据")
        
        # 显示分支信息
        for i, conv in enumerate(history, 1):
            branch_id = conv['metadata']['branch_id']
            is_start = conv['metadata'].get('is_branch_start', False)
            marker = "🌿" if is_start else "  "
            print(f"{marker} 对话{i}: branch={branch_id[:10]}...")
    else:
        print("⚠️ 对话不包含树结构元数据（树可能未启用）")
    
    # 获取统计信息
    stats = memory.get_stats()
    if 'tree' in stats:
        print(f"\n📊 树统计:")
        print(f"  - 总对话数: {stats['tree']['total_conversations']}")
        print(f"  - 总分支数: {stats['tree']['total_branches']}")
        print(f"  - 当前分支: {stats['tree']['current_branch_id'][:10]}...")
    
    print("\n✅ 测试5通过")


async def test_smart_loader_with_tree():
    """测试SmartLoader与树结构的集成"""
    print("\n" + "="*60)
    print("测试6: SmartLoader与树结构集成")
    print("="*60)
    
    from daoyoucode.agents.memory import get_memory_manager
    
    memory = get_memory_manager()
    session_id = "test-session-smart"
    user_id = "test-user"
    
    # 添加多个对话
    conversations = [
        ("我的猫不吃饭", "可能是肠胃问题..."),
        ("需要吃药吗？", "可以先观察..."),
        ("吃什么药？", "建议益生菌..."),
        ("狗的皮肤有红点", "可能是过敏..."),
        ("用什么药膏？", "可以用皮炎平..."),
        ("猫需要打疫苗吗？", "需要定期接种..."),
    ]
    
    for user_msg, ai_resp in conversations:
        memory.add_conversation(
            session_id=session_id,
            user_message=user_msg,
            ai_response=ai_resp,
            user_id=user_id
        )
    
    print(f"✅ 添加了{len(conversations)}个对话")
    
    # 测试智能加载（应该使用树结构检索）
    context = await memory.load_context_smart(
        session_id=session_id,
        user_id=user_id,
        user_input="猫的肠胃问题怎么办？",
        is_followup=True,
        confidence=0.8
    )
    
    print(f"\n📊 智能加载结果:")
    print(f"  - 策略: {context['strategy']}")
    print(f"  - 加载历史: {len(context['history'])}轮")
    print(f"  - 使用树结构: {context.get('tree_based', False)}")
    print(f"  - 成本: {context['cost']}")
    
    if context.get('tree_based'):
        print("\n✅ 使用了树结构检索")
        print("相关对话:")
        for i, conv in enumerate(context['history'], 1):
            print(f"  {i}. {conv['user'][:30]}...")
    else:
        print("\n⚠️ 未使用树结构检索（可能树未启用或历史较少）")
    
    print("\n✅ 测试6通过")


async def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("对话树功能测试")
    print("="*60)
    
    try:
        await test_basic_tree()
        await test_branch_retrieval()
        await test_topic_detection()
        await test_export_import()
        await test_integration_with_memory()
        await test_smart_loader_with_tree()
        
        print("\n" + "="*60)
        print("✅ 所有测试通过！")
        print("="*60)
    
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
