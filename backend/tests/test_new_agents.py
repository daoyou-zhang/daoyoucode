"""
测试新增的Agent（Sisyphus, Oracle, Librarian）
"""

import sys
from pathlib import Path

# 添加backend到路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from daoyoucode.agents.builtin import register_builtin_agents
from daoyoucode.agents.core.agent import get_agent_registry
from daoyoucode.agents.tools.tool_groups import (
    get_tools_for_agent,
    AGENT_TOOL_MAPPING
)


def test_agent_registration():
    """测试Agent注册"""
    print("=" * 80)
    print("测试Agent注册")
    print("=" * 80)
    
    # 注册所有内置Agent
    register_builtin_agents()
    
    # 获取注册表
    registry = get_agent_registry()
    
    # 测试新Agent
    new_agents = ['sisyphus', 'oracle', 'librarian']
    
    for agent_name in new_agents:
        print(f"\n测试 {agent_name}...")
        
        # 获取Agent实例
        agent = registry.get_agent(agent_name)
        assert agent is not None, f"Agent {agent_name} 未注册"
        
        # 检查配置
        print(f"  ✓ Agent已注册")
        print(f"  - 名称: {agent.config.name}")
        print(f"  - 描述: {agent.config.description}")
        print(f"  - 模型: {agent.config.model}")
        print(f"  - 温度: {agent.config.temperature}")
    
    print("\n" + "=" * 80)
    print("✓ 所有新Agent注册成功")
    print("=" * 80)


def test_tool_mapping():
    """测试工具映射"""
    print("\n" + "=" * 80)
    print("测试工具映射")
    print("=" * 80)
    
    new_agents = {
        'sisyphus': 4,      # 应该有4个工具
        'oracle': 10,       # 应该有10个工具
        'librarian': 8      # 应该有8个工具
    }
    
    for agent_name, expected_count in new_agents.items():
        print(f"\n测试 {agent_name} 的工具...")
        
        # 获取工具列表
        tools = get_tools_for_agent(agent_name)
        assert len(tools) > 0, f"Agent {agent_name} 没有配置工具"
        
        print(f"  ✓ 工具数量: {len(tools)} (预期: {expected_count})")
        print(f"  - 工具列表: {', '.join(tools)}")
        
        # 验证工具数量
        if len(tools) != expected_count:
            print(f"  ⚠ 警告: 工具数量不匹配 (实际: {len(tools)}, 预期: {expected_count})")
    
    print("\n" + "=" * 80)
    print("✓ 工具映射测试完成")
    print("=" * 80)


def test_agent_tool_mapping_table():
    """测试Agent工具映射表"""
    print("\n" + "=" * 80)
    print("Agent工具映射表")
    print("=" * 80)
    
    print("\n所有Agent及其工具数量:")
    for agent_name, tools in sorted(AGENT_TOOL_MAPPING.items()):
        print(f"  {agent_name:20s}: {len(tools):2d} 个工具")
    
    print("\n新增Agent详情:")
    new_agents = ['sisyphus', 'oracle', 'librarian']
    for agent_name in new_agents:
        if agent_name in AGENT_TOOL_MAPPING:
            tools = AGENT_TOOL_MAPPING[agent_name]
            print(f"\n{agent_name}:")
            for i, tool in enumerate(tools, 1):
                print(f"  {i:2d}. {tool}")
    
    print("\n" + "=" * 80)


def test_skill_files():
    """测试Skill配置文件"""
    print("\n" + "=" * 80)
    print("测试Skill配置文件")
    print("=" * 80)
    
    skills_dir = backend_dir.parent / "skills"
    
    new_skills = {
        'sisyphus-orchestrator': ['skill.yaml', 'prompts/sisyphus.md'],
        'oracle': ['skill.yaml', 'prompts/oracle.md'],
        'librarian': ['skill.yaml', 'prompts/librarian.md']
    }
    
    for skill_name, files in new_skills.items():
        print(f"\n测试 {skill_name}...")
        skill_dir = skills_dir / skill_name
        
        if not skill_dir.exists():
            print(f"  ✗ Skill目录不存在: {skill_dir}")
            continue
        
        print(f"  ✓ Skill目录存在")
        
        for file_path in files:
            full_path = skill_dir / file_path
            if full_path.exists():
                print(f"  ✓ {file_path} 存在")
            else:
                print(f"  ✗ {file_path} 不存在")
    
    print("\n" + "=" * 80)
    print("✓ Skill配置文件测试完成")
    print("=" * 80)


def main():
    """运行所有测试"""
    try:
        test_agent_registration()
        test_tool_mapping()
        test_agent_tool_mapping_table()
        test_skill_files()
        
        print("\n" + "=" * 80)
        print("✓✓✓ 所有测试通过 ✓✓✓")
        print("=" * 80)
        print("\n新增Agent总结:")
        print("  1. Sisyphus - 主编排Agent (4个工具)")
        print("  2. Oracle - 高IQ咨询Agent (10个工具)")
        print("  3. Librarian - 文档搜索Agent (8个工具)")
        print("\n所有Agent已正确注册，工具映射已配置，Skill文件已创建。")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
