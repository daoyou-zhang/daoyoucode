"""
Memory系统集成测试

测试智能加载、摘要生成、用户画像等功能
"""

import asyncio
import logging
from daoyoucode.agents.memory import get_memory_manager
from daoyoucode.agents.core.agent import BaseAgent, AgentConfig, AgentResult
from daoyoucode.agents.llm import get_client_manager
from daoyoucode.agents.llm.config_loader import auto_configure

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_basic_memory():
    """测试1：基础记忆功能"""
    print("\n" + "="*60)
    print("测试1：基础记忆功能")
    print("="*60)
    
    memory = get_memory_manager()
    
    # 添加对话
    memory.add_conversation(
        session_id="test-1",
        user_message="你好",
        ai_response="你好！我是DaoyouCode。"
    )
    
    memory.add_conversation(
        session_id="test-1",
        user_message="这个项目的结构是什么？",
        ai_response="项目包含以下模块..."
    )
    
    # 获取历史
    history = memory.get_conversation_history("test-1")
    
    print(f"✅ 添加了 {len(history)} 轮对话")
    for idx, h in enumerate(history, 1):
        print(f"  第{idx}轮: {h['user'][:30]}...")
    
    return True


async def test_smart_loading():
    """测试2：智能加载策略"""
    print("\n" + "="*60)
    print("测试2：智能加载策略")
    print("="*60)
    
    memory = get_memory_manager()
    
    # 准备测试数据
    session_id = "test-smart-loading"
    user_id = "user-123"
    
    # 添加多轮对话
    conversations = [
        ("这个项目的结构是什么？", "项目包含以下模块..."),
        ("有哪些核心组件？", "核心组件包括..."),
        ("Agent系统在哪里？", "Agent系统在backend/daoyoucode/agents/..."),
        ("工具注册表怎么工作的？", "工具注册表使用单例模式..."),
        ("编排器有哪些类型？", "编排器有Simple、ReAct、Parallel..."),
        ("Memory系统在哪里？", "Memory系统在backend/daoyoucode/agents/memory/..."),
    ]
    
    for user_msg, ai_msg in conversations:
        memory.add_conversation(session_id, user_msg, ai_msg)
    
    print(f"✅ 添加了 {len(conversations)} 轮对话")
    
    # 测试不同的加载策略
    test_cases = [
        ("新对话", "完全不相关的问题：今天天气怎么样？", False, 0.0),
        ("简单追问", "能详细说说吗？", True, 0.9),
        ("相关问题", "Memory系统有哪些功能？", True, 0.7),
    ]
    
    for test_name, user_input, is_followup, confidence in test_cases:
        print(f"\n--- {test_name} ---")
        print(f"用户输入: {user_input}")
        print(f"追问判断: {is_followup} (置信度: {confidence})")
        
        # 智能加载
        context = await memory.load_context_smart(
            session_id=session_id,
            user_id=user_id,
            user_input=user_input,
            is_followup=is_followup,
            confidence=confidence
        )
        
        print(f"✅ 加载策略: {context['strategy']}")
        print(f"   历史轮数: {len(context['history'])}")
        print(f"   成本: {context['cost']}")
        print(f"   智能筛选: {'是' if context.get('filtered') else '否'}")
        
        if context['history']:
            print(f"   加载的对话:")
            for idx, h in enumerate(context['history'], 1):
                print(f"     {idx}. {h['user'][:40]}...")
    
    return True


async def test_summary_generation():
    """测试3：摘要生成"""
    print("\n" + "="*60)
    print("测试3：摘要生成")
    print("="*60)
    
    memory = get_memory_manager()
    
    # 准备测试数据
    session_id = "test-summary"
    
    # 添加5轮对话（触发摘要）
    conversations = [
        ("这个项目是做什么的？", "这是一个AI代码助手项目..."),
        ("有哪些核心功能？", "核心功能包括代码编辑、重构、测试..."),
        ("Agent系统是怎么工作的？", "Agent系统使用可插拔架构..."),
        ("工具系统有哪些工具？", "工具系统有25个工具..."),
        ("Memory系统有什么特点？", "Memory系统支持智能加载..."),
    ]
    
    for user_msg, ai_msg in conversations:
        memory.add_conversation(session_id, user_msg, ai_msg)
    
    print(f"✅ 添加了 {len(conversations)} 轮对话")
    
    # 检查是否应该生成摘要
    history = memory.get_conversation_history(session_id)
    should_generate = memory.long_term_memory.should_generate_summary(
        session_id, len(history)
    )
    
    print(f"是否应该生成摘要: {should_generate}")
    
    if should_generate:
        print("⚠️ 需要LLM客户端才能生成摘要")
        print("💡 在实际使用中，Agent会自动调用LLM生成摘要")
    
    return True


async def test_user_profile():
    """测试4：用户画像"""
    print("\n" + "="*60)
    print("测试4：用户画像")
    print("="*60)
    
    memory = get_memory_manager()
    
    user_id = "user-456"
    
    # 添加用户偏好
    memory.remember_preference(user_id, 'preferred_language', 'python')
    memory.remember_preference(user_id, 'code_style', 'functional')
    
    # 获取偏好
    prefs = memory.get_preferences(user_id)
    
    print(f"✅ 用户偏好:")
    for key, value in prefs.items():
        print(f"   {key}: {value}")
    
    # 添加任务历史
    for i in range(3):
        memory.add_task(user_id, {
            'agent': 'MainAgent',
            'input': f'任务{i+1}',
            'result': f'结果{i+1}',
            'success': True
        })
    
    # 获取任务历史
    tasks = memory.get_task_history(user_id)
    
    print(f"✅ 任务历史: {len(tasks)} 个任务")
    for idx, task in enumerate(tasks, 1):
        print(f"   {idx}. {task.get('input', 'N/A')}")
    
    return True


async def test_agent_integration():
    """测试5：Agent集成"""
    print("\n" + "="*60)
    print("测试5：Agent集成（模拟）")
    print("="*60)
    
    # 创建测试Agent
    config = AgentConfig(
        name="TestAgent",
        description="测试Agent",
        model="qwen-plus",
        temperature=0.7,
        system_prompt="你是一个测试Agent"
    )
    
    agent = BaseAgent(config)
    
    print(f"✅ Agent已创建: {agent.name}")
    print(f"   Memory管理器: {agent.memory}")
    print(f"   工具注册表: {agent._tool_registry}")
    
    # 测试记忆加载（不实际调用LLM）
    session_id = "test-agent-session"
    user_id = "test-user"
    
    # 添加一些历史
    agent.memory.add_conversation(
        session_id,
        "测试问题1",
        "测试回答1"
    )
    
    agent.memory.add_conversation(
        session_id,
        "测试问题2",
        "测试回答2"
    )
    
    # 模拟智能加载
    context = await agent.memory.load_context_smart(
        session_id=session_id,
        user_id=user_id,
        user_input="测试问题3",
        is_followup=True,
        confidence=0.8
    )
    
    print(f"✅ 智能加载成功:")
    print(f"   策略: {context['strategy']}")
    print(f"   历史: {len(context['history'])}轮")
    print(f"   成本: {context['cost']}")
    
    return True


async def test_statistics():
    """测试6：统计信息"""
    print("\n" + "="*60)
    print("测试6：统计信息")
    print("="*60)
    
    memory = get_memory_manager()
    
    # 获取存储统计
    storage_stats = memory.storage.get_stats()
    
    print("✅ 存储统计:")
    for key, value in storage_stats.items():
        print(f"   {key}: {value}")
    
    # 获取智能加载统计
    loader_stats = memory.smart_loader.get_stats()
    
    print("\n✅ 智能加载统计:")
    for key, value in loader_stats.items():
        print(f"   {key}: {value}")
    
    return True


async def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("Memory系统集成测试")
    print("="*60)
    
    tests = [
        ("基础记忆功能", test_basic_memory),
        ("智能加载策略", test_smart_loading),
        ("摘要生成", test_summary_generation),
        ("用户画像", test_user_profile),
        ("Agent集成", test_agent_integration),
        ("统计信息", test_statistics),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result, None))
        except Exception as e:
            logger.error(f"测试失败: {test_name}", exc_info=True)
            results.append((test_name, False, str(e)))
    
    # 打印总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    passed = sum(1 for _, result, _ in results if result)
    total = len(results)
    
    for test_name, result, error in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {test_name}")
        if error:
            print(f"   错误: {error}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！Memory系统集成成功！")
    else:
        print(f"\n⚠️ {total - passed} 个测试失败")


if __name__ == "__main__":
    asyncio.run(main())
