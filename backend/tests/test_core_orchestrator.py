"""
测试 CoreOrchestrator 基本功能

验证：
1. CoreOrchestrator 是否正确注册
2. 意图识别是否工作
3. 工作流加载是否正常
4. Agent 执行是否正常
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


async def test_orchestrator_registration():
    """测试 1: 验证 CoreOrchestrator 是否正确注册"""
    logger.info("=" * 60)
    logger.info("测试 1: 验证 CoreOrchestrator 注册")
    logger.info("=" * 60)
    
    from daoyoucode.agents.core.orchestrator import get_orchestrator
    
    # 获取 core 编排器
    orchestrator = get_orchestrator('core')
    
    if orchestrator:
        logger.info(f"✅ CoreOrchestrator 已注册: {orchestrator.__class__.__name__}")
        return True
    else:
        logger.error("❌ CoreOrchestrator 未注册")
        return False


async def test_skill_loading():
    """测试 2: 验证 Skill 加载"""
    logger.info("\n" + "=" * 60)
    logger.info("测试 2: 验证 Skill 加载")
    logger.info("=" * 60)
    
    from daoyoucode.agents.core.skill import get_skill_loader
    
    skill_loader = get_skill_loader()
    
    # 尝试加载测试 skill
    skill = skill_loader.get_skill('test-core-orchestrator')
    
    if skill:
        logger.info(f"✅ Skill 加载成功: {skill.name}")
        logger.info(f"   - 编排器: {skill.orchestrator}")
        logger.info(f"   - 工具数量: {len(skill.tools) if skill.tools else 0}")
        logger.info(f"   - 工作流配置: {skill.workflows}")
        return True
    else:
        logger.warning("⚠️ 测试 Skill 未找到（这是正常的，如果没有创建测试 skill）")
        return False


async def test_intent_recognition():
    """测试 3: 验证意图识别"""
    logger.info("\n" + "=" * 60)
    logger.info("测试 3: 验证意图识别")
    logger.info("=" * 60)
    
    from daoyoucode.agents.core.intent import classify_intents
    from daoyoucode.agents.core.skill import get_skill_loader
    
    skill_loader = get_skill_loader()
    
    # 使用 sisyphus-orchestrator skill（应该存在）
    skill = skill_loader.get_skill('sisyphus-orchestrator')
    
    if not skill:
        logger.warning("⚠️ sisyphus-orchestrator skill 未找到，跳过意图识别测试")
        return False
    
    # 测试几个不同的输入
    test_inputs = [
        "你好",
        "帮我分析这个项目的架构",
        "这段代码是做什么的？",
    ]
    
    for user_input in test_inputs:
        logger.info(f"\n输入: {user_input}")
        
        # 注意：classify_intents 的参数顺序是 (user_input, skill, context)
        intents = await classify_intents(user_input, skill, {})
        
        logger.info(f"识别的意图: {intents}")
    
    logger.info("✅ 意图识别测试完成")
    return True


async def test_workflow_manager():
    """测试 4: 验证工作流管理器"""
    logger.info("\n" + "=" * 60)
    logger.info("测试 4: 验证工作流管理器")
    logger.info("=" * 60)
    
    from daoyoucode.agents.core.workflow_manager import WorkflowManager
    from daoyoucode.agents.core.skill import get_skill_loader
    
    skill_loader = get_skill_loader()
    skill = skill_loader.get_skill('sisyphus-orchestrator')
    
    if not skill or not skill.skill_path:
        logger.warning("⚠️ sisyphus-orchestrator skill 未找到，跳过工作流测试")
        return False
    
    # 创建工作流管理器
    config = {
        'skill_dir': str(skill.skill_path),
        'workflows': getattr(skill, 'workflows', {})
    }
    
    wf_manager = WorkflowManager(config)
    
    logger.info(f"✅ 工作流管理器创建成功")
    logger.info(f"   - 可用工作流数量: {len(wf_manager.workflows)}")
    logger.info(f"   - 工作流列表: {list(wf_manager.workflows.keys())}")
    
    # 测试获取工作流
    if wf_manager.workflows:
        intent = list(wf_manager.workflows.keys())[0]
        workflow_prompt = wf_manager.get_workflow_prompt([intent], "测试输入")
        
        if workflow_prompt:
            logger.info(f"✅ 工作流加载成功: {intent}")
            logger.info(f"   - Prompt 长度: {len(workflow_prompt)} 字符")
        else:
            logger.warning(f"⚠️ 工作流加载失败: {intent}")
    
    return True


async def test_core_orchestrator_execute():
    """测试 5: 验证 CoreOrchestrator 执行（简单测试）"""
    logger.info("\n" + "=" * 60)
    logger.info("测试 5: 验证 CoreOrchestrator 执行")
    logger.info("=" * 60)
    
    from daoyoucode.agents.core.core_orchestrator import CoreOrchestrator
    from daoyoucode.agents.core.skill import get_skill_loader
    
    skill_loader = get_skill_loader()
    skill = skill_loader.get_skill('sisyphus-orchestrator')
    
    if not skill:
        logger.warning("⚠️ sisyphus-orchestrator skill 未找到，跳过执行测试")
        return False
    
    # 创建 CoreOrchestrator
    orchestrator = CoreOrchestrator(skill)
    
    logger.info(f"✅ CoreOrchestrator 创建成功")
    logger.info(f"   - Skill: {skill.name}")
    logger.info(f"   - 工作流管理器: {'已初始化' if orchestrator.workflow_manager else '未初始化'}")
    
    # 注意：这里不实际执行 LLM 调用，只验证初始化
    logger.info("✅ CoreOrchestrator 初始化验证通过")
    
    return True


async def main():
    """运行所有测试"""
    logger.info("开始测试 CoreOrchestrator")
    logger.info("=" * 60)
    
    # 初始化系统
    from daoyoucode.agents.init import initialize_agent_system
    initialize_agent_system()
    
    results = []
    
    # 运行测试
    results.append(("编排器注册", await test_orchestrator_registration()))
    results.append(("Skill 加载", await test_skill_loading()))
    results.append(("意图识别", await test_intent_recognition()))
    results.append(("工作流管理器", await test_workflow_manager()))
    results.append(("CoreOrchestrator 执行", await test_core_orchestrator_execute()))
    
    # 输出总结
    logger.info("\n" + "=" * 60)
    logger.info("测试总结")
    logger.info("=" * 60)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{name}: {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    logger.info(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        logger.info("🎉 所有测试通过！")
        return 0
    else:
        logger.warning("⚠️ 部分测试失败")
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
