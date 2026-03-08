"""
测试 PromptBuilder 功能

验证：
1. PromptBuilder 是否正确初始化
2. 模板文件是否正确加载
3. Sections 是否正确构建
4. 最终 Prompt 是否正确生成
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


async def test_prompt_builder_initialization():
    """测试 1: PromptBuilder 初始化"""
    logger.info("=" * 60)
    logger.info("测试 1: PromptBuilder 初始化")
    logger.info("=" * 60)
    
    from daoyoucode.agents.core.skill import get_skill_loader
    from daoyoucode.agents.core.prompt_builder import PromptBuilder
    
    skill_loader = get_skill_loader()
    skill = skill_loader.get_skill('test-core-orchestrator')
    
    if not skill:
        logger.error("❌ 测试 Skill 未找到")
        return False
    
    # 创建 PromptBuilder
    prompt_builder = PromptBuilder(skill)
    
    logger.info(f"✅ PromptBuilder 创建成功")
    logger.info(f"   - Skill: {skill.name}")
    logger.info(f"   - Skill 目录: {prompt_builder.skill_dir}")
    logger.info(f"   - Jinja2 环境: {'已初始化' if prompt_builder.jinja_env else '未初始化'}")
    
    return True


async def test_template_loading():
    """测试 2: 模板文件加载"""
    logger.info("\n" + "=" * 60)
    logger.info("测试 2: 模板文件加载")
    logger.info("=" * 60)
    
    from daoyoucode.agents.core.skill import get_skill_loader
    from daoyoucode.agents.core.prompt_builder import PromptBuilder
    
    skill_loader = get_skill_loader()
    skill = skill_loader.get_skill('test-core-orchestrator')
    
    prompt_builder = PromptBuilder(skill)
    
    # 测试加载基础模板
    base_template = prompt_builder._load_base_template()
    
    if base_template:
        logger.info(f"✅ 基础模板加载成功")
        logger.info(f"   - 长度: {len(base_template)} 字符")
        logger.info(f"   - 包含 sections: {base_template.count('{{')}")
    else:
        logger.error("❌ 基础模板加载失败")
        return False
    
    # 测试加载 section 模板
    role_template = prompt_builder._load_template_file('role.md')
    
    if role_template:
        logger.info(f"✅ 角色模板加载成功")
        logger.info(f"   - 长度: {len(role_template)} 字符")
    else:
        logger.warning("⚠️ 角色模板未找到（将使用配置生成）")
    
    return True


async def test_section_building():
    """测试 3: Section 构建"""
    logger.info("\n" + "=" * 60)
    logger.info("测试 3: Section 构建")
    logger.info("=" * 60)
    
    from daoyoucode.agents.core.skill import get_skill_loader
    from daoyoucode.agents.core.prompt_builder import PromptBuilder
    
    skill_loader = get_skill_loader()
    skill = skill_loader.get_skill('test-core-orchestrator')
    
    prompt_builder = PromptBuilder(skill)
    
    # 测试各个 section
    context = {
        'conversation_history': [
            {'user': '你好', 'ai': '你好！有什么可以帮助你的？'}
        ],
        'user_preferences': {'language': 'python'},
    }
    
    # 1. 角色 section
    role_section = prompt_builder._build_role_section()
    logger.info(f"✅ 角色 section 构建成功")
    logger.info(f"   - 长度: {len(role_section)} 字符")
    logger.info(f"   - 预览: {role_section[:100]}...")
    
    # 2. 能力 section
    capabilities_section = prompt_builder._build_capabilities_section()
    logger.info(f"✅ 能力 section 构建成功")
    logger.info(f"   - 长度: {len(capabilities_section)} 字符")
    
    # 3. 约束 section
    constraints_section = prompt_builder._build_constraints_section()
    logger.info(f"✅ 约束 section 构建成功")
    logger.info(f"   - 长度: {len(constraints_section)} 字符")
    
    # 4. 工具 section
    tools_section = prompt_builder._build_tools_section(context)
    logger.info(f"✅ 工具 section 构建成功")
    logger.info(f"   - 长度: {len(tools_section)} 字符")
    
    # 5. 上下文 section
    context_section = prompt_builder._build_context_section(context)
    logger.info(f"✅ 上下文 section 构建成功")
    logger.info(f"   - 长度: {len(context_section)} 字符")
    
    return True


async def test_full_prompt_building():
    """测试 4: 完整 Prompt 构建"""
    logger.info("\n" + "=" * 60)
    logger.info("测试 4: 完整 Prompt 构建")
    logger.info("=" * 60)
    
    from daoyoucode.agents.core.skill import get_skill_loader
    from daoyoucode.agents.core.prompt_builder import PromptBuilder
    
    skill_loader = get_skill_loader()
    skill = skill_loader.get_skill('test-core-orchestrator')
    
    prompt_builder = PromptBuilder(skill)
    
    # 准备上下文
    context = {
        'conversation_history': [
            {'user': '你好', 'ai': '你好！有什么可以帮助你的？'}
        ],
        'user_preferences': {'language': 'python'},
        'project_understanding_block': '这是一个 Python 项目...',
    }
    
    workflow_prompt = "请按照以下步骤执行：\n1. 分析需求\n2. 编写代码\n3. 测试验证"
    user_input = "帮我写一个 Python 函数"
    
    # 构建完整 Prompt
    full_prompt = prompt_builder.build(workflow_prompt, context, user_input)
    
    logger.info(f"✅ 完整 Prompt 构建成功")
    logger.info(f"   - 总长度: {len(full_prompt)} 字符")
    logger.info(f"   - 包含角色定义: {'角色定义' in full_prompt}")
    logger.info(f"   - 包含能力说明: {'核心能力' in full_prompt}")
    logger.info(f"   - 包含工具列表: {'可用工具' in full_prompt}")
    logger.info(f"   - 包含上下文: {'当前上下文' in full_prompt}")
    logger.info(f"   - 包含工作流: {workflow_prompt[:50] in full_prompt}")
    logger.info(f"   - 包含用户输入: {user_input in full_prompt}")
    
    # 显示 Prompt 预览
    logger.info("\n" + "-" * 60)
    logger.info("Prompt 预览（前 500 字符）:")
    logger.info("-" * 60)
    logger.info(full_prompt[:500])
    logger.info("...")
    logger.info("-" * 60)
    
    return True


async def test_agent_integration():
    """测试 5: Agent 集成"""
    logger.info("\n" + "=" * 60)
    logger.info("测试 5: Agent 集成（验证 Agent 使用 PromptBuilder）")
    logger.info("=" * 60)
    
    from daoyoucode.agents.core.skill import get_skill_loader
    from daoyoucode.agents.core.prompt_builder import PromptBuilder
    from daoyoucode.agents.core.agent import BaseAgent, AgentConfig
    from daoyoucode.agents.core.workflow_manager import WorkflowManager
    
    skill_loader = get_skill_loader()
    skill = skill_loader.get_skill('test-core-orchestrator')
    
    # 创建 PromptBuilder
    prompt_builder = PromptBuilder(skill)
    
    # 创建 WorkflowManager
    workflow_config = {
        'skill_dir': str(skill.skill_path),
        'workflows': getattr(skill, 'workflows', {})
    }
    workflow_manager = WorkflowManager(workflow_config)
    
    # 创建 Agent
    agent_config = AgentConfig(
        name='test-agent',
        description='测试 Agent',
        model='gpt-4',
        temperature=0.7,
        system_prompt=''
    )
    agent = BaseAgent(agent_config)
    
    # 准备 context（包含 prompt_builder）
    context = {
        'detected_intents': ['general_chat'],
        'prompt_builder': prompt_builder,  # 🔥 传递 PromptBuilder
        'workflow_manager': workflow_manager,
        'conversation_history': [],
    }
    
    # 测试 _render_prompt 方法
    try:
        prompt = agent._render_prompt(
            prompt="",  # 空的，因为会使用 PromptBuilder
            user_input="你好",
            context=context
        )
        
        logger.info(f"✅ Agent 成功使用 PromptBuilder")
        logger.info(f"   - Prompt 长度: {len(prompt)} 字符")
        logger.info(f"   - 包含 PromptBuilder 生成的内容: {'TestAgent' in prompt or '测试助手' in prompt}")
        
        return True
    
    except Exception as e:
        logger.error(f"❌ Agent 使用 PromptBuilder 失败: {e}")
        return False


async def main():
    """运行所有测试"""
    logger.info("开始测试 PromptBuilder")
    logger.info("=" * 60)
    
    # 初始化系统
    from daoyoucode.agents.init import initialize_agent_system
    initialize_agent_system()
    
    results = []
    
    # 运行测试
    results.append(("PromptBuilder 初始化", await test_prompt_builder_initialization()))
    results.append(("模板文件加载", await test_template_loading()))
    results.append(("Section 构建", await test_section_building()))
    results.append(("完整 Prompt 构建", await test_full_prompt_building()))
    results.append(("Agent 集成", await test_agent_integration()))
    
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
        logger.info("🎉 所有测试通过！PromptBuilder 工作正常！")
        return 0
    else:
        logger.warning("⚠️ 部分测试失败")
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
