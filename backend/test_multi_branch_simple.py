"""
测试多路分支ConditionalOrchestrator - 简化版
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dataclasses import dataclass
from daoyoucode.agents.orchestrators.conditional import ConditionalOrchestrator
from daoyoucode.agents.core.agent import BaseAgent, AgentConfig, AgentResult, register_agent


# 模拟SkillConfig
@dataclass
class SkillConfig:
    name: str
    orchestrator: str
    conditions: list = None
    condition: str = None
    if_path: dict = None
    else_path: dict = None
    middleware: list = None
    tools: list = None


# 创建Mock Agent
class MockAgent(BaseAgent):
    async def execute(self, prompt_source, user_input, context, llm_config=None, tools=None, max_tool_iterations=5):
        return AgentResult(
            success=True,
            content=f'{self.name} 处理: {user_input}',
            metadata={'agent': self.name}
        )


# 注册Agents
for name in ['python_expert', 'js_expert', 'java_expert', 'general_editor']:
    config = AgentConfig(name=name, description=f"Mock {name}", model="mock")
    agent = MockAgent(config)
    register_agent(agent)


async def test_simple_branch():
    """测试简单分支"""
    print("\n=== 测试1: 简单分支（if/else）===")
    
    skill = SkillConfig(
        name='simple-edit',
        orchestrator='conditional',
        condition='${language} == "python"',
        if_path={'agent': 'python_expert'},
        else_path={'agent': 'general_editor'}
    )
    
    orchestrator = ConditionalOrchestrator()
    
    # Python文件
    print("\n测试1.1: Python文件")
    result = await orchestrator.execute(skill, '修改文件', {'language': 'python'})
    print(f"结果: {result['content']}")
    print(f"路径: {result['metadata']['path_executed']}")
    assert 'python_expert' in result['content']
    
    # JavaScript文件
    print("\n测试1.2: JavaScript文件")
    result = await orchestrator.execute(skill, '修改文件', {'language': 'javascript'})
    print(f"结果: {result['content']}")
    print(f"路径: {result['metadata']['path_executed']}")
    assert 'general_editor' in result['content']
    
    print("✅ 简单分支测试通过")


async def test_multi_branch():
    """测试多路分支"""
    print("\n=== 测试2: 多路分支 ===")
    
    skill = SkillConfig(
        name='smart-edit',
        orchestrator='conditional',
        conditions=[
            {'condition': '${language} == "python"', 'path': {'agent': 'python_expert'}},
            {'condition': '${language} == "javascript"', 'path': {'agent': 'js_expert'}},
            {'condition': '${language} == "java"', 'path': {'agent': 'java_expert'}},
            {'default': True, 'path': {'agent': 'general_editor'}}
        ]
    )
    
    orchestrator = ConditionalOrchestrator()
    
    # Python
    print("\n测试2.1: Python")
    result = await orchestrator.execute(skill, '修改文件', {'language': 'python'})
    print(f"结果: {result['content']}")
    print(f"分支: {result['metadata']['branch_index']}")
    assert 'python_expert' in result['content']
    assert result['metadata']['branch_index'] == 0
    
    # JavaScript
    print("\n测试2.2: JavaScript")
    result = await orchestrator.execute(skill, '修改文件', {'language': 'javascript'})
    print(f"结果: {result['content']}")
    print(f"分支: {result['metadata']['branch_index']}")
    assert 'js_expert' in result['content']
    assert result['metadata']['branch_index'] == 1
    
    # Java
    print("\n测试2.3: Java")
    result = await orchestrator.execute(skill, '修改文件', {'language': 'java'})
    print(f"结果: {result['content']}")
    print(f"分支: {result['metadata']['branch_index']}")
    assert 'java_expert' in result['content']
    assert result['metadata']['branch_index'] == 2
    
    # 其他（default）
    print("\n测试2.4: Rust (default)")
    result = await orchestrator.execute(skill, '修改文件', {'language': 'rust'})
    print(f"结果: {result['content']}")
    print(f"条件: {result['metadata']['matched_condition']}")
    assert 'general_editor' in result['content']
    assert result['metadata']['matched_condition'] == 'default'
    
    print("✅ 多路分支测试通过")


async def test_complex_conditions():
    """测试复杂条件"""
    print("\n=== 测试3: 复杂条件 ===")
    
    skill = SkillConfig(
        name='smart-analysis',
        orchestrator='conditional',
        conditions=[
            {'condition': '${file_size} < 1000 and ${language} == "python"', 'path': {'agent': 'python_expert'}},
            {'condition': '${file_size} >= 1000', 'path': {'agent': 'general_editor'}},
            {'default': True, 'path': {'agent': 'general_editor'}}
        ]
    )
    
    orchestrator = ConditionalOrchestrator()
    
    # 小Python文件
    print("\n测试3.1: 小Python文件")
    result = await orchestrator.execute(skill, '分析', {'language': 'python', 'file_size': 500})
    print(f"结果: {result['content']}")
    assert 'python_expert' in result['content']
    
    # 大Python文件
    print("\n测试3.2: 大Python文件")
    result = await orchestrator.execute(skill, '分析', {'language': 'python', 'file_size': 5000})
    print(f"结果: {result['content']}")
    assert 'general_editor' in result['content']
    
    print("✅ 复杂条件测试通过")


async def main():
    print("=" * 60)
    print("多路分支ConditionalOrchestrator测试")
    print("=" * 60)
    
    try:
        await test_simple_branch()
        await test_multi_branch()
        await test_complex_conditions()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())
