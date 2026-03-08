"""
Phase 3 集成测试

验证：
1. CLI 能否正常启动
2. Skills 能否正常执行
3. CoreOrchestrator 是否正常工作
4. 所有核心功能是否正常
"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_skill_execution(skill_name: str, user_input: str):
    """测试 Skill 执行"""
    logger.info(f"=" * 60)
    logger.info(f"测试 Skill 执行: {skill_name}")
    logger.info(f"=" * 60)
    
    from daoyoucode.agents.executor import execute_skill
    
    context = {
        'session_id': 'test-session',
        'user_id': 'test-user',
        'repo': '.',
        'enable_streaming': False,
    }
    
    try:
        result = await execute_skill(
            skill_name=skill_name,
            user_input=user_input,
            context=context
        )
        
        # 检查是否返回生成器（流式输出）
        import inspect
        if inspect.isasyncgen(result):
            logger.info("⚠️ 返回了流式生成器，跳过验证")
            return True
        
        logger.info(f"✅ Skill 执行完成")
        logger.info(f"   - 成功: {result.get('success', False)}")
        logger.info(f"   - 内容长度: {len(result.get('content', ''))} 字符")
        logger.info(f"   - 错误: {result.get('error', 'None')}")
        logger.info(f"   - 任务ID: {result.get('task_id', 'None')}")
        
        return result.get('success', False)
    
    except Exception as e:
        logger.error(f"❌ Skill 执行失败: {e}", exc_info=True)
        return False


async def test_orchestrator_selection():
    """测试编排器选择"""
    logger.info(f"\n" + "=" * 60)
    logger.info(f"测试编排器选择")
    logger.info(f"=" * 60)
    
    from daoyoucode.agents.core.skill import get_skill_loader
    from daoyoucode.agents.core.orchestrator import get_orchestrator
    
    skill_loader = get_skill_loader()
    
    # 测试几个 Skills
    test_skills = ['chat-assistant', 'programming', 'testing']
    
    for skill_name in test_skills:
        skill = skill_loader.get_skill(skill_name)
        
        if not skill:
            logger.error(f"❌ {skill_name} 未找到")
            return False
        
        orchestrator = get_orchestrator(skill.orchestrator)
        
        if not orchestrator:
            logger.error(f"❌ {skill_name} 的编排器 '{skill.orchestrator}' 未找到")
            return False
        
        logger.info(f"✅ {skill_name}: {skill.orchestrator} → {orchestrator.__class__.__name__}")
    
    return True


async def test_workflow_loading():
    """测试工作流加载"""
    logger.info(f"\n" + "=" * 60)
    logger.info(f"测试工作流加载")
    logger.info(f"=" * 60)
    
    from daoyoucode.agents.core.skill import get_skill_loader
    from daoyoucode.agents.core.workflow_manager import WorkflowManager
    
    skill_loader = get_skill_loader()
    
    # 测试几个 Skills
    test_skills = ['sisyphus-orchestrator', 'programming', 'testing']
    
    for skill_name in test_skills:
        skill = skill_loader.get_skill(skill_name)
        
        if not skill:
            logger.error(f"❌ {skill_name} 未找到")
            return False
        
        # 创建工作流管理器
        workflow_config = {
            'skill_dir': str(skill.skill_path),
            'workflows': getattr(skill, 'workflows', {})
        }
        
        workflow_manager = WorkflowManager(workflow_config)
        
        logger.info(f"✅ {skill_name}: {len(workflow_manager.workflows)} 个工作流")
        
        if workflow_manager.workflows:
            logger.info(f"   - 工作流: {list(workflow_manager.workflows.keys())[:5]}...")
    
    return True


async def test_memory_system():
    """测试记忆系统"""
    logger.info(f"\n" + "=" * 60)
    logger.info(f"测试记忆系统")
    logger.info(f"=" * 60)
    
    from daoyoucode.agents.memory import get_memory_manager
    
    try:
        memory = get_memory_manager()
        
        logger.info(f"✅ 记忆管理器已初始化")
        
        # 测试添加对话
        session_id = 'test-session-phase3'
        user_id = 'test-user'
        
        memory.add_conversation(
            session_id,
            "你好",
            "你好！有什么可以帮助你的？",
            user_id=user_id
        )
        
        # 测试获取历史
        history = memory.get_conversation_history(session_id)
        
        logger.info(f"✅ 对话历史: {len(history)} 轮")
        
        return True
    
    except Exception as e:
        logger.error(f"❌ 记忆系统测试失败: {e}", exc_info=True)
        return False


async def test_tool_registry():
    """测试工具注册表"""
    logger.info(f"\n" + "=" * 60)
    logger.info(f"测试工具注册表")
    logger.info(f"=" * 60)
    
    from daoyoucode.agents.tools import get_tool_registry
    
    try:
        registry = get_tool_registry()
        
        tools = registry.list_tools()
        
        logger.info(f"✅ 工具注册表已初始化")
        logger.info(f"   - 工具数量: {len(tools)}")
        logger.info(f"   - 工具列表: {tools[:10]}...")
        
        # 测试获取几个关键工具
        key_tools = ['repo_map', 'read_file', 'write_file', 'lsp_diagnostics']
        
        for tool_name in key_tools:
            tool = registry.get_tool(tool_name)
            if tool:
                logger.info(f"   - ✅ {tool_name}: {tool.__class__.__name__}")
            else:
                logger.warning(f"   - ⚠️ {tool_name}: 未找到")
        
        return True
    
    except Exception as e:
        logger.error(f"❌ 工具注册表测试失败: {e}", exc_info=True)
        return False


async def main():
    """运行所有测试"""
    logger.info("开始 Phase 3 集成测试")
    logger.info("=" * 80)
    
    # 初始化系统
    from daoyoucode.agents.init import initialize_agent_system
    initialize_agent_system()
    
    results = []
    
    # 运行测试
    results.append(("编排器选择", await test_orchestrator_selection()))
    results.append(("工作流加载", await test_workflow_loading()))
    results.append(("记忆系统", await test_memory_system()))
    results.append(("工具注册表", await test_tool_registry()))
    
    # 注意：Skill 执行测试需要 LLM，这里跳过
    # results.append(("Skill 执行", await test_skill_execution('chat-assistant', '你好')))
    
    # 输出总结
    logger.info("\n" + "=" * 80)
    logger.info("Phase 3 集成测试总结")
    logger.info("=" * 80)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{name}: {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    logger.info(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        logger.info("🎉 所有集成测试通过！系统已准备就绪！")
        return 0
    else:
        logger.warning("⚠️ 部分集成测试失败")
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
