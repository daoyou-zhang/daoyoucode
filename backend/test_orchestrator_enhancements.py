"""
测试编排器增强功能
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dataclasses import dataclass
from daoyoucode.agents.orchestrators.simple import SimpleOrchestrator
from daoyoucode.agents.orchestrators.multi_agent import MultiAgentOrchestrator
from daoyoucode.agents.core.agent import BaseAgent, AgentConfig, AgentResult, register_agent


# 模拟SkillConfig
@dataclass
class SkillConfig:
    name: str
    orchestrator: str
    agent: str = None
    agents: list = None
    collaboration_mode: str = None
    max_retries: int = 3
    retry_delay: float = 0.1
    middleware: list = None
    tools: list = None
    llm: dict = None
    prompt: dict = None


# 创建Mock Agent
class MockAgent(BaseAgent):
    def __init__(self, name: str, fail_count: int = 0):
        config = AgentConfig(name=name, description=f"Mock {name}", model="mock")
        super().__init__(config)
        self.fail_count = fail_count
        self.call_count = 0
    
    async def execute(self, prompt_source, user_input, context, llm_config=None, tools=None, max_tool_iterations=5):
        self.call_count += 1
        
        # 模拟前N次失败
        if self.call_count <= self.fail_count:
            return AgentResult(
                success=False,
                content="",
                error=f"模拟失败 {self.call_count}",
                metadata={'agent': self.name}
            )
        
        # 成功
        return AgentResult(
            success=True,
            content=f'{self.name} 处理: {user_input}',
            metadata={'agent': self.name},
            tokens_used=100
        )


# 注册Agents
register_agent(MockAgent('agent1'))
register_agent(MockAgent('agent2'))
register_agent(MockAgent('agent3'))
register_agent(MockAgent('failing_agent', fail_count=2))  # 前2次失败


async def test_simple_retry():
    """测试SimpleOrchestrator的重试机制"""
    print("\n=== 测试1: SimpleOrchestrator重试机制 ===")
    
    # 测试1.1: 正常执行（无需重试）
    print("\n测试1.1: 正常执行")
    skill = SkillConfig(
        name='test-skill',
        orchestrator='simple',
        agent='agent1'
    )
    
    orchestrator = SimpleOrchestrator()
    result = await orchestrator.execute(skill, '测试输入', {})
    
    print(f"成功: {result['success']}")
    print(f"内容: {result['content']}")
    print(f"重试次数: {result['metadata']['retries']}")
    print(f"耗时: {result['metadata']['duration']:.3f}s")
    
    assert result['success']
    assert result['metadata']['retries'] == 0
    
    # 测试1.2: 失败后重试成功
    print("\n测试1.2: 失败后重试成功")
    skill = SkillConfig(
        name='test-skill',
        orchestrator='simple',
        agent='failing_agent',
        max_retries=3
    )
    
    # 重置failing_agent的计数
    from daoyoucode.agents.core.agent import get_agent_registry
    registry = get_agent_registry()
    failing_agent = registry.get_agent('failing_agent')
    failing_agent.call_count = 0
    
    orchestrator = SimpleOrchestrator()
    result = await orchestrator.execute(skill, '测试输入', {})
    
    print(f"成功: {result['success']}")
    print(f"内容: {result['content']}")
    print(f"重试次数: {result['metadata']['retries']}")
    print(f"调用次数: {failing_agent.call_count}")
    
    assert result['success']
    assert result['metadata']['retries'] == 2  # 前2次失败，第3次成功
    assert failing_agent.call_count == 3
    
    print("\n✅ SimpleOrchestrator重试测试通过")


async def test_multi_agent_sequential():
    """测试MultiAgentOrchestrator的顺序执行模式"""
    print("\n=== 测试2: MultiAgentOrchestrator顺序执行 ===")
    
    skill = SkillConfig(
        name='multi-agent-skill',
        orchestrator='multi_agent',
        agents=['agent1', 'agent2', 'agent3'],
        collaboration_mode='sequential'
    )
    
    orchestrator = MultiAgentOrchestrator()
    result = await orchestrator.execute(skill, '初始输入', {})
    
    print(f"成功: {result['success']}")
    print(f"协作模式: {result['metadata']['collaboration_mode']}")
    print(f"Agent数量: {result['metadata']['agents_count']}")
    print(f"顺序结果数: {len(result['sequential_results'])}")
    
    # 验证顺序执行
    for i, r in enumerate(result['sequential_results']):
        print(f"  Agent {i+1}: {r['agent']} - {r['content'][:50]}")
    
    assert result['success']
    assert len(result['sequential_results']) == 3
    assert result['metadata']['collaboration_mode'] == 'sequential'
    
    print("\n✅ 顺序执行测试通过")


async def test_multi_agent_parallel():
    """测试MultiAgentOrchestrator的并行执行模式"""
    print("\n=== 测试3: MultiAgentOrchestrator并行执行 ===")
    
    skill = SkillConfig(
        name='multi-agent-skill',
        orchestrator='multi_agent',
        agents=['agent1', 'agent2', 'agent3'],
        collaboration_mode='parallel'
    )
    
    orchestrator = MultiAgentOrchestrator()
    result = await orchestrator.execute(skill, '测试输入', {})
    
    print(f"成功: {result['success']}")
    print(f"协作模式: {result['metadata']['collaboration_mode']}")
    print(f"并行结果数: {len(result['parallel_results'])}")
    
    # 验证并行执行
    for r in result['parallel_results']:
        print(f"  {r['agent']}: {r['content'][:50]}")
    
    assert result['success']
    assert len(result['parallel_results']) == 3
    assert result['metadata']['collaboration_mode'] == 'parallel'
    
    print("\n✅ 并行执行测试通过")


async def test_multi_agent_debate():
    """测试MultiAgentOrchestrator的辩论模式"""
    print("\n=== 测试4: MultiAgentOrchestrator辩论模式 ===")
    
    skill = SkillConfig(
        name='multi-agent-skill',
        orchestrator='multi_agent',
        agents=['agent1', 'agent2'],
        collaboration_mode='debate'
    )
    
    orchestrator = MultiAgentOrchestrator()
    result = await orchestrator.execute(skill, '讨论这个问题', {})
    
    print(f"成功: {result['success']}")
    print(f"协作模式: {result['metadata']['collaboration_mode']}")
    print(f"辩论轮数: {result['metadata']['rounds']}")
    print(f"辩论历史: {len(result['debate_history'])} 轮")
    
    # 验证辩论
    for round_data in result['debate_history']:
        print(f"\n  第 {round_data['round']} 轮:")
        for opinion in round_data['opinions']:
            print(f"    {opinion['agent']}: {opinion['opinion'][:50]}...")
    
    assert result['success']
    assert len(result['debate_history']) == 3  # 默认3轮
    
    print("\n✅ 辩论模式测试通过")


async def test_multi_agent_main_with_helpers():
    """测试MultiAgentOrchestrator的主Agent+辅助Agent模式"""
    print("\n=== 测试5: MultiAgentOrchestrator主Agent+辅助Agent ===")
    
    skill = SkillConfig(
        name='multi-agent-skill',
        orchestrator='multi_agent',
        agents=['agent1', 'agent2', 'agent3'],
        collaboration_mode='main_with_helpers'
    )
    
    orchestrator = MultiAgentOrchestrator()
    result = await orchestrator.execute(skill, '测试输入', {})
    
    print(f"成功: {result['success']}")
    print(f"主Agent: {result['metadata']['main_agent']}")
    print(f"辅助Agent: {result['metadata']['helper_agents']}")
    print(f"辅助结果数: {len(result['helper_results'])}")
    
    assert result['success']
    assert result['metadata']['main_agent'] == 'agent1'
    assert len(result['metadata']['helper_agents']) == 2
    assert len(result['helper_results']) == 2
    
    print("\n✅ 主Agent+辅助Agent测试通过")


async def main():
    print("=" * 60)
    print("编排器增强功能测试")
    print("=" * 60)
    
    try:
        await test_simple_retry()
        await test_multi_agent_sequential()
        await test_multi_agent_parallel()
        await test_multi_agent_debate()
        await test_multi_agent_main_with_helpers()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())
