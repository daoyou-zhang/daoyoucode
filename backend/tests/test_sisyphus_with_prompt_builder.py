"""
测试 sisyphus-orchestrator 使用 PromptBuilder

验证：
1. sisyphus-orchestrator 是否正确加载
2. CoreOrchestrator 是否正确初始化
3. PromptBuilder 是否正确使用
4. 完整的执行流程是否正常
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


async def test_sisyphus_loading():
    """测试 1: sisyphus-orchestrator 加载"""
    logger.info("=" * 60)
    logger.info("测试 1: sisyphus-orchestrator 加载")
    logger.info("=" * 60)
    
    from daoyoucode.agents.core.skill import get_skill_loader
    
    skill_loader = get_skill_loader()
    skill = skill_loader.get_skill('sisyphus-orchestrator')
    
    if not skill:
        logger.error("❌ sisyphus-orchestrator 未找到")
        return False
    
    logger.info(f"✅ Skill 加载成功")
    logger.info(f"   - 名称: {skill.name}")
    logger.info(f"   - 版本: {skill.version}")
    logger.info(f"   - 编排器: {skill.orchestrator}")
    logger.info(f"   - 工具数量: {len(skill.tools) if skill.tools else 0}")
    
    # 检查 prompt_template 配置
    prompt_template = getattr(skill, 'prompt_template', None)
    if prompt_template:
        logger.info(f"   - Prompt 模板配置: ✅")
        logger.info(f"     - base: {prompt_template.get('base')}")
        logger.info(f"     - sections: {list(prompt_template.get('sections', {}).keys())}")
    else:
        logger.warning(f"   - Prompt 模板配置: ⚠️ 未配置")
    
    return True


async def test_core_orchestrator_initialization():
    """测试 2: CoreOrchestrator 初始化"""
    logger.info("\n" + "=" * 60)
    logger.info("测试 2: CoreOrchestrator 初始化")
    logger.info("=" * 60)
    
    from daoyoucode.agents.core.skill import get_skill_loader
    from daoyoucode.agents.core.core_orchestrator import CoreOrchestrator
    
    skill_loader = get_skill_loader()
    skill = skill_loader.get_skill('sisyphus-orchestrator')
    
    # 创建 CoreOrchestrator
    orchestrator = CoreOrchestrator(skill)
    
    logger.info(f"✅ CoreOrchestrator 创建成功")
    logger.info(f"   - Skill: {orchestrator.skill.name}")
    logger.info(f"   - 工作流管理器: {'✅' if orchestrator.workflow_manager else '❌'}")
    logger.info(f"   - Prompt 构建器: {'✅' if orchestrator.prompt_builder else '❌'}")
    
    if orchestrator.workflow_manager:
        logger.info(f"   - 工作流数量: {len(orchestrator.workflow_manager.workflows)}")
    
    return True


async def test_prompt_builder_integration():
    """测试 3: PromptBuilder 集成"""
    logger.info("\n" + "=" * 60)
    logger.info("测试 3: PromptBuilder 集成")
    logger.info("=" * 60)
    
    from daoyoucode.agents.core.skill import get_skill_loader
    from daoyoucode.agents.core.core_orchestrator import CoreOrchestrator
    
    skill_loader = get_skill_loader()
    skill = skill_loader.get_skill('sisyphus-orchestrator')
    
    orchestrator = CoreOrchestrator(skill)
    
    # 检查 PromptBuilder
    if not orchestrator.prompt_builder:
        logger.error("❌ PromptBuilder 未初始化")
        return False
    
    # 测试构建 Prompt
    context = {
        'conversation_history': [],
        'user_preferences': {},
    }
    
    workflow_prompt = "这是一个测试工作流"
    user_input = "你好"
    
    try:
        full_prompt = orchestrator.prompt_builder.build(
            workflow_prompt,
            context,
            user_input
        )
        
        logger.info(f"✅ Prompt 构建成功")
        logger.info(f"   - 长度: {len(full_prompt)} 字符")
        logger.info(f"   - 包含角色定义: {'角色定义' in full_prompt}")
        logger.info(f"   - 包含能力说明: {'核心能力' in full_prompt}")
        logger.info(f"   - 包含工作流: {workflow_prompt in full_prompt}")
        logger.info(f"   - 包含用户输入: {user_input in full_prompt}")
        
        return True
    
    except Exception as e:
        logger.error(f"❌ Prompt 构建失败: {e}")
        return False


async def test_simple_execution():
    """测试 4: 简单执行（不调用 LLM）"""
    logger.info("\n" + "=" * 60)
    logger.info("测试 4: 简单执行流程（模拟）")
    logger.info("=" * 60)
    
    from daoyoucode.agents.core.skill import get_skill_loader
    from daoyoucode.agents.core.core_orchestrator import CoreOrchestrator
    
    skill_loader = get_skill_loader()
    skill = skill_loader.get_skill('sisyphus-orchestrator')
    
    orchestrator = CoreOrchestrator(skill)
    
    # 准备 context
    context = {
        'session_id': 'test-session',
        'user_id': 'test-user',
    }
    
    user_input = "你好"
    
    logger.info(f"准备执行:")
    logger.info(f"   - 用户输入: {user_input}")
    logger.info(f"   - Session ID: {context['session_id']}")
    
    # 测试意图识别（不调用 LLM，只测试流程）
    try:
        # 只测试到意图识别阶段
        from daoyoucode.agents.core.intent import should_prefetch_project_understanding
        
        need_prefetch, intents, prefetch_level = await should_prefetch_project_understanding(
            skill,
            user_input,
            context
        )
        
        logger.info(f"✅ 意图识别完成")
        logger.info(f"   - 检测到的意图: {intents}")
        logger.info(f"   - 预取级别: {prefetch_level}")
        logger.info(f"   - 需要预取: {need_prefetch}")
        
        return True
    
    except Exception as e:
        logger.error(f"❌ 执行失败: {e}", exc_info=True)
        return False


async def main():
    """运行所有测试"""
    logger.info("开始测试 sisyphus-orchestrator + PromptBuilder")
    logger.info("=" * 60)
    
    # 初始化系统
    from daoyoucode.agents.init import initialize_agent_system
    initialize_agent_system()
    
    results = []
    
    # 运行测试
    results.append(("sisyphus-orchestrator 加载", await test_sisyphus_loading()))
    results.append(("CoreOrchestrator 初始化", await test_core_orchestrator_initialization()))
    results.append(("PromptBuilder 集成", await test_prompt_builder_integration()))
    results.append(("简单执行流程", await test_simple_execution()))
    
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
        logger.info("🎉 所有测试通过！sisyphus-orchestrator + PromptBuilder 工作正常！")
        return 0
    else:
        logger.warning("⚠️ 部分测试失败")
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
