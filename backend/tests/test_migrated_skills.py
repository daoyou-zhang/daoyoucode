"""
测试迁移后的 Skills

验证：
1. Skills 是否正确加载
2. CoreOrchestrator 是否正确初始化
3. 基本功能是否正常
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


async def test_skill_loading(skill_name: str):
    """测试 Skill 加载"""
    logger.info(f"=" * 60)
    logger.info(f"测试 Skill 加载: {skill_name}")
    logger.info(f"=" * 60)
    
    from daoyoucode.agents.core.skill import get_skill_loader
    
    skill_loader = get_skill_loader()
    skill = skill_loader.get_skill(skill_name)
    
    if not skill:
        logger.error(f"❌ {skill_name} 未找到")
        return False
    
    logger.info(f"✅ Skill 加载成功")
    logger.info(f"   - 名称: {skill.name}")
    logger.info(f"   - 版本: {skill.version}")
    logger.info(f"   - 编排器: {skill.orchestrator}")
    logger.info(f"   - 工具数量: {len(skill.tools) if skill.tools else 0}")
    
    # 检查是否使用 core 编排器
    if skill.orchestrator != 'core':
        logger.error(f"❌ {skill_name} 未使用 core 编排器: {skill.orchestrator}")
        return False
    
    return True


async def test_orchestrator_initialization(skill_name: str):
    """测试 CoreOrchestrator 初始化"""
    logger.info(f"\n" + "=" * 60)
    logger.info(f"测试 CoreOrchestrator 初始化: {skill_name}")
    logger.info(f"=" * 60)
    
    from daoyoucode.agents.core.skill import get_skill_loader
    from daoyoucode.agents.core.core_orchestrator import CoreOrchestrator
    
    skill_loader = get_skill_loader()
    skill = skill_loader.get_skill(skill_name)
    
    try:
        # 创建 CoreOrchestrator
        orchestrator = CoreOrchestrator(skill)
        
        logger.info(f"✅ CoreOrchestrator 创建成功")
        logger.info(f"   - Skill: {orchestrator.skill.name}")
        logger.info(f"   - 工作流管理器: {'✅' if orchestrator.workflow_manager else '❌'}")
        logger.info(f"   - Prompt 构建器: {'✅' if orchestrator.prompt_builder else '❌'}")
        
        if orchestrator.workflow_manager:
            logger.info(f"   - 工作流数量: {len(orchestrator.workflow_manager.workflows)}")
        
        return True
    
    except Exception as e:
        logger.error(f"❌ CoreOrchestrator 初始化失败: {e}", exc_info=True)
        return False


async def test_intent_recognition(skill_name: str, user_input: str):
    """测试意图识别"""
    logger.info(f"\n" + "=" * 60)
    logger.info(f"测试意图识别: {skill_name}")
    logger.info(f"=" * 60)
    
    from daoyoucode.agents.core.skill import get_skill_loader
    from daoyoucode.agents.core.intent import should_prefetch_project_understanding
    
    skill_loader = get_skill_loader()
    skill = skill_loader.get_skill(skill_name)
    
    context = {
        'session_id': 'test-session',
        'user_id': 'test-user',
    }
    
    try:
        need_prefetch, intents, prefetch_level = await should_prefetch_project_understanding(
            skill,
            user_input,
            context
        )
        
        logger.info(f"✅ 意图识别完成")
        logger.info(f"   - 用户输入: {user_input}")
        logger.info(f"   - 检测到的意图: {intents}")
        logger.info(f"   - 预取级别: {prefetch_level}")
        logger.info(f"   - 需要预取: {need_prefetch}")
        
        return True
    
    except Exception as e:
        logger.error(f"❌ 意图识别失败: {e}", exc_info=True)
        return False


async def test_skill(skill_name: str, user_input: str = "你好"):
    """测试单个 Skill"""
    logger.info(f"\n" + "=" * 80)
    logger.info(f"开始测试 Skill: {skill_name}")
    logger.info(f"=" * 80)
    
    results = []
    
    # 测试 1: Skill 加载
    results.append(("Skill 加载", await test_skill_loading(skill_name)))
    
    # 测试 2: CoreOrchestrator 初始化
    results.append(("CoreOrchestrator 初始化", await test_orchestrator_initialization(skill_name)))
    
    # 测试 3: 意图识别
    results.append(("意图识别", await test_intent_recognition(skill_name, user_input)))
    
    # 输出总结
    logger.info(f"\n" + "-" * 60)
    logger.info(f"{skill_name} 测试总结")
    logger.info(f"-" * 60)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{name}: {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    logger.info(f"\n总计: {passed}/{total} 测试通过")
    
    return passed == total


async def main():
    """运行所有测试"""
    logger.info("开始测试迁移后的 Skills")
    logger.info("=" * 80)
    
    # 初始化系统
    from daoyoucode.agents.init import initialize_agent_system
    initialize_agent_system()
    
    # 要测试的 Skills（选择几个代表性的）
    test_skills = [
        ("chat-assistant", "你好"),
        ("oracle", "帮我分析这个项目的架构"),
        ("programming", "帮我写一个 Python 函数"),
        ("testing", "帮我写测试用例"),
        ("refactoring", "帮我重构这段代码"),
    ]
    
    all_results = []
    
    # 运行测试
    for skill_name, user_input in test_skills:
        result = await test_skill(skill_name, user_input)
        all_results.append((skill_name, result))
    
    # 输出总结
    logger.info("\n" + "=" * 80)
    logger.info("所有 Skills 测试总结")
    logger.info("=" * 80)
    
    for skill_name, result in all_results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{skill_name}: {status}")
    
    passed = sum(1 for _, result in all_results if result)
    total = len(all_results)
    
    logger.info(f"\n总计: {passed}/{total} Skills 测试通过")
    
    if passed == total:
        logger.info("🎉 所有 Skills 测试通过！")
        return 0
    else:
        logger.warning("⚠️ 部分 Skills 测试失败")
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
