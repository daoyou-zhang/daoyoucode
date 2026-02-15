"""
Memory系统实战调试脚本

用于在实际使用中追踪Memory系统的行为
"""

import asyncio
import logging
from daoyoucode.agents.memory import get_memory_manager

# 配置日志 - 可以调整级别
logging.basicConfig(
    level=logging.INFO,  # 改为 DEBUG 可以看到更详细的信息
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def simulate_conversation():
    """模拟一个完整的对话流程"""
    print("\n" + "="*60)
    print("Memory系统实战调试")
    print("="*60)
    
    memory = get_memory_manager()
    session_id = "debug-session"
    user_id = "debug-user"
    
    # 模拟对话场景
    conversations = [
        ("这个项目是做什么的？", "这是一个AI代码助手项目，名为DaoyouCode..."),
        ("有哪些核心功能？", "核心功能包括：代码编辑、重构、测试生成、文档生成..."),
        ("Agent系统是怎么工作的？", "Agent系统使用可插拔架构，包含编排器、工具、记忆等模块..."),
        ("能详细说说编排器吗？", "编排器有三种类型：Simple、ReAct、Parallel..."),
        ("工具系统有哪些工具？", "工具系统有25个工具，包括文件操作、代码分析、测试执行等..."),
        ("Memory系统有什么特点？", "Memory系统支持智能加载、摘要生成、用户画像等功能..."),
        ("能再详细说说智能加载吗？", "智能加载有5种策略，可以节省50-70%的token成本..."),
    ]
    
    for idx, (user_msg, ai_msg) in enumerate(conversations, 1):
        print(f"\n{'='*60}")
        print(f"第{idx}轮对话")
        print(f"{'='*60}")
        print(f"👤 用户: {user_msg}")
        
        # 判断追问
        if idx > 1:
            is_followup, confidence, reason = await memory.is_followup(
                session_id, user_msg
            )
            print(f"\n🔍 追问判断:")
            print(f"   结果: {'是追问' if is_followup else '新话题'}")
            print(f"   置信度: {confidence:.2f}")
            print(f"   原因: {reason}")
        else:
            is_followup, confidence = False, 0.0
            print(f"\n🔍 追问判断: 首轮对话，无需判断")
        
        # 智能加载
        print(f"\n📚 智能加载:")
        context = await memory.load_context_smart(
            session_id=session_id,
            user_id=user_id,
            user_input=user_msg,
            is_followup=is_followup,
            confidence=confidence
        )
        
        print(f"   策略: {context['strategy']}")
        print(f"   历史轮数: {len(context['history'])}")
        print(f"   成本: {context['cost']}")
        print(f"   智能筛选: {'是' if context.get('filtered') else '否'}")
        
        if context['history']:
            print(f"   加载的对话:")
            for h_idx, h in enumerate(context['history'], 1):
                print(f"     {h_idx}. {h['user'][:50]}...")
        
        if context.get('summary'):
            print(f"   摘要: {context['summary'][:100]}...")
        
        # 模拟AI响应
        print(f"\n🤖 AI: {ai_msg[:80]}...")
        
        # 添加到记忆
        memory.add_conversation(session_id, user_msg, ai_msg)
        
        # 检查摘要触发
        history = memory.get_conversation_history(session_id)
        if memory.long_term_memory.should_generate_summary(session_id, len(history)):
            print(f"\n🔄 触发摘要生成条件（当前{len(history)}轮）")
            print(f"   💡 在实际使用中，Agent会自动调用LLM生成摘要")
        
        # 暂停一下，方便观察
        await asyncio.sleep(0.1)
    
    # 最终统计
    print(f"\n{'='*60}")
    print("最终统计")
    print(f"{'='*60}")
    
    # 智能加载统计
    loader_stats = memory.smart_loader.get_stats()
    print(f"\n📊 智能加载统计:")
    print(f"   总加载次数: {loader_stats['total_loads']}")
    print(f"   平均成本: {loader_stats['average_cost']:.2f}")
    print(f"   策略分布:")
    for strategy in ['new_conversation', 'simple_followup', 'medium_followup', 
                     'complex_followup', 'cross_session']:
        count = loader_stats.get(strategy, 0)
        if count > 0:
            percentage = count / loader_stats['total_loads'] * 100
            print(f"     - {strategy}: {count} ({percentage:.1f}%)")
    
    # 存储统计
    storage_stats = memory.storage.get_stats()
    print(f"\n📦 存储统计:")
    print(f"   总会话数: {storage_stats['total_sessions']}")
    print(f"   总对话数: {storage_stats['total_conversations']}")
    print(f"   摘要数: {storage_stats['summaries']}")
    print(f"   用户画像数: {storage_stats['user_profiles']}")
    
    print(f"\n✅ 调试完成！")


async def test_specific_scenario():
    """测试特定场景"""
    print("\n" + "="*60)
    print("测试特定场景：关键词筛选")
    print("="*60)
    
    memory = get_memory_manager()
    session_id = "test-filter"
    user_id = "test-user"
    
    # 添加多样化的历史
    conversations = [
        ("这个项目的结构是什么？", "项目包含backend、frontend、ai等模块..."),
        ("Agent系统在哪里？", "Agent系统在backend/daoyoucode/agents/..."),
        ("今天天气怎么样？", "抱歉，我是代码助手，不能查询天气..."),
        ("Memory系统有什么功能？", "Memory系统支持智能加载、摘要生成..."),
        ("工具注册表怎么工作的？", "工具注册表使用单例模式..."),
    ]
    
    for user_msg, ai_msg in conversations:
        memory.add_conversation(session_id, user_msg, ai_msg)
    
    print(f"✅ 添加了 {len(conversations)} 轮对话")
    
    # 测试不同的查询
    test_queries = [
        "Memory系统的智能加载是怎么工作的？",
        "Agent系统有哪些组件？",
        "今天吃什么？",
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"查询: {query}")
        print(f"{'='*60}")
        
        context = await memory.load_context_smart(
            session_id=session_id,
            user_id=user_id,
            user_input=query,
            is_followup=False
        )
        
        print(f"策略: {context['strategy']}")
        print(f"加载轮数: {len(context['history'])}")
        print(f"智能筛选: {'是' if context.get('filtered') else '否'}")
        
        if context['history']:
            print(f"加载的对话:")
            for idx, h in enumerate(context['history'], 1):
                print(f"  {idx}. {h['user']}")


async def test_token_savings():
    """测试Token节省效果"""
    print("\n" + "="*60)
    print("测试Token节省效果")
    print("="*60)
    
    memory = get_memory_manager()
    session_id = "test-tokens"
    user_id = "test-user"
    
    # 添加10轮对话
    for i in range(10):
        memory.add_conversation(
            session_id,
            f"问题{i+1}: 这是一个测试问题，用于计算token使用情况...",
            f"回答{i+1}: 这是一个测试回答，包含了详细的解释和代码示例..."
        )
    
    # 获取完整历史
    full_history = memory.get_conversation_history(session_id)
    
    # 计算完整历史的token数（粗略估算：4字符=1token）
    full_tokens = sum(
        len(h['user']) + len(h['ai'])
        for h in full_history
    ) // 4
    
    print(f"\n完整历史:")
    print(f"  轮数: {len(full_history)}")
    print(f"  估算tokens: {full_tokens}")
    
    # 使用智能加载
    context = await memory.load_context_smart(
        session_id=session_id,
        user_id=user_id,
        user_input="能详细说说吗？",
        is_followup=True,
        confidence=0.9
    )
    
    # 计算智能加载的token数
    smart_tokens = sum(
        len(h['user']) + len(h['ai'])
        for h in context['history']
    ) // 4
    
    print(f"\n智能加载:")
    print(f"  策略: {context['strategy']}")
    print(f"  轮数: {len(context['history'])}")
    print(f"  估算tokens: {smart_tokens}")
    
    # 计算节省
    saved_tokens = full_tokens - smart_tokens
    saved_percentage = (saved_tokens / full_tokens * 100) if full_tokens > 0 else 0
    
    print(f"\n💰 节省效果:")
    print(f"  节省tokens: {saved_tokens}")
    print(f"  节省比例: {saved_percentage:.1f}%")


async def main():
    """主函数"""
    print("\n" + "="*60)
    print("Memory系统实战调试工具")
    print("="*60)
    print("\n选择测试场景:")
    print("1. 完整对话流程（推荐）")
    print("2. 关键词筛选测试")
    print("3. Token节省效果测试")
    print("4. 运行所有测试")
    
    # 默认运行完整流程
    choice = "1"
    
    # 如果需要交互式选择，取消下面的注释
    # choice = input("\n请选择 (1-4): ").strip()
    
    if choice == "1":
        await simulate_conversation()
    elif choice == "2":
        await test_specific_scenario()
    elif choice == "3":
        await test_token_savings()
    elif choice == "4":
        await simulate_conversation()
        await test_specific_scenario()
        await test_token_savings()
    else:
        print("默认运行完整对话流程...")
        await simulate_conversation()


if __name__ == "__main__":
    asyncio.run(main())
