"""
测试多路分支ConditionalOrchestrator
"""

import asyncio
from dataclasses import dataclass
from typing import Dict, Any, Optional


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


# 导入ConditionalOrchestrator
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from daoyoucode.agents.orchestrators.conditional import ConditionalOrchestrator
from daoyoucode.agents.core.agent import BaseAgent, AgentConfig
from daoyoucode.agents.registry import register_agent


# 创建Mock Agents并注册
class MockAgent(BaseAgent):
    def __init__(self, name: str):
        config = AgentConfig(
            name=name,
            description=f"Mock {name}",
            model="mock-model"
        )
        super().__init__(config)
    
    async def execute(self, prompt_source, user_input, context, llm_config=None, tools=None, max_tool_iterations=5):
        from daoyoucode.agents.core.agent import AgentResult
        return AgentResult(
            success=True,
            content=f'{self.name} 处理: {user_input}',
            metadata={'agent': self.name}
        )


# 注册Mock Agents
register_agent(MockAgent('python_expert'))
register_agent(MockAgent('js_expert'))
register_agent(MockAgent('java_expert'))
register_agent(MockAgent('general_editor'))


async def test_simple_branch():
    """测试简单的if/else分支（向后兼容）"""
    print("\n=== 测试1: 简单分支（if/else）===")
    
    # 创建Skill配置
    skill = SkillConfig(
        name='simple-edit',
        orchestrator='conditional',
        condition='${language} == "python"',  # 直接引用context中的key
        if_path={
            'agent': 'python_expert'
        },
        else_path={
            'agent': 'general_editor'
        }
    )
    
    # 创建编排器
    orchestrator = ConditionalOrchestrator()
    orchestrator._agent_registry = MockAgentRegistry()
    
    # 测试1: Python文件
    print("\n测试1.1: Python文件")
    context = {'language': 'python'}
    result = await orchestrator.execute(skill, '修改文件', context)
    print(f"结果: {result['content']}")
    print(f"元数据: {result['metadata']}")
    assert 'python_expert' in result['content']
    
    # 测试2: JavaScript文件
    print("\n测试1.2: JavaScript文件")
    context = {'language': 'javascript'}
    result = await orchestrator.execute(skill, '修改文件', context)
    print(f"结果: {result['content']}")
    print(f"元数据: {result['metadata']}")
    assert 'general_editor' in result['content']
    
    print("\n✅ 简单分支测试通过")


async def test_multi_branch():
    """测试多路分支"""
    print("\n=== 测试2: 多路分支 ===")
    
    # 创建Skill配置
    skill = SkillConfig(
        name='smart-edit',
        orchestrator='conditional',
        conditions=[
            {
                'condition': '${language} == "python"',
                'path': {
                    'agent': 'python_expert'
                }
            },
            {
                'condition': '${language} == "javascript"',
                'path': {
                    'agent': 'js_expert'
                }
            },
            {
                'condition': '${language} == "java"',
                'path': {
                    'agent': 'java_expert'
                }
            },
            {
                'default': True,
                'path': {
                    'agent': 'general_editor'
                }
            }
        ]
    )
    
    # 创建编排器
    orchestrator = ConditionalOrchestrator()
    orchestrator._agent_registry = MockAgentRegistry()
    
    # 测试1: Python
    print("\n测试2.1: Python文件")
    context = {'language': 'python'}
    result = await orchestrator.execute(skill, '修改文件', context)
    print(f"结果: {result['content']}")
    print(f"元数据: {result['metadata']}")
    assert 'python_expert' in result['content']
    assert result['metadata']['branch_index'] == 0
    
    # 测试2: JavaScript
    print("\n测试2.2: JavaScript文件")
    context = {'language': 'javascript'}
    result = await orchestrator.execute(skill, '修改文件', context)
    print(f"结果: {result['content']}")
    print(f"元数据: {result['metadata']}")
    assert 'js_expert' in result['content']
    assert result['metadata']['branch_index'] == 1
    
    # 测试3: Java
    print("\n测试2.3: Java文件")
    context = {'language': 'java'}
    result = await orchestrator.execute(skill, '修改文件', context)
    print(f"结果: {result['content']}")
    print(f"元数据: {result['metadata']}")
    assert 'java_expert' in result['content']
    assert result['metadata']['branch_index'] == 2
    
    # 测试4: 其他语言（default）
    print("\n测试2.4: 其他语言（default）")
    context = {'language': 'rust'}
    result = await orchestrator.execute(skill, '修改文件', context)
    print(f"结果: {result['content']}")
    print(f"元数据: {result['metadata']}")
    assert 'general_editor' in result['content']
    assert result['metadata']['matched_condition'] == 'default'
    
    print("\n✅ 多路分支测试通过")


async def test_complex_conditions():
    """测试复杂条件"""
    print("\n=== 测试3: 复杂条件 ===")
    
    # 创建Skill配置
    skill = SkillConfig(
        name='smart-analysis',
        orchestrator='conditional',
        conditions=[
            {
                'condition': '${file_size} < 1000 and ${language} == "python"',
                'path': {
                    'agent': 'python_expert'
                }
            },
            {
                'condition': '${file_size} >= 1000',
                'path': {
                    'agent': 'general_editor'
                }
            },
            {
                'default': True,
                'path': {
                    'agent': 'general_editor'
                }
            }
        ]
    )
    
    # 创建编排器
    orchestrator = ConditionalOrchestrator()
    orchestrator._agent_registry = MockAgentRegistry()
    
    # 测试1: 小Python文件
    print("\n测试3.1: 小Python文件")
    context = {'language': 'python', 'file_size': 500}
    result = await orchestrator.execute(skill, '分析文件', context)
    print(f"结果: {result['content']}")
    print(f"元数据: {result['metadata']}")
    assert 'python_expert' in result['content']
    
    # 测试2: 大Python文件
    print("\n测试3.2: 大Python文件")
    context = {'language': 'python', 'file_size': 5000}
    result = await orchestrator.execute(skill, '分析文件', context)
    print(f"结果: {result['content']}")
    print(f"元数据: {result['metadata']}")
    assert 'general_editor' in result['content']
    
    print("\n✅ 复杂条件测试通过")


async def main():
    """运行所有测试"""
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
