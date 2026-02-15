"""
测试ParallelOrchestrator的LLM增强功能
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dataclasses import dataclass
from daoyoucode.agents.orchestrators.parallel import ParallelOrchestrator
from daoyoucode.agents.core.agent import BaseAgent, AgentConfig, AgentResult, register_agent


# 模拟SkillConfig
@dataclass
class SkillConfig:
    name: str
    orchestrator: str
    agents: list = None
    use_llm_split: bool = False
    use_llm_aggregate: bool = False
    middleware: list = None
    tools: list = None
    llm: dict = None


# 创建Mock Agent
class MockAgent(BaseAgent):
    async def execute(self, prompt_source, user_input, context, llm_config=None, tools=None, max_tool_iterations=5):
        return AgentResult(
            success=True,
            content=f'{self.name} 分析: {user_input[:50]}...',
            metadata={'agent': self.name},
            tokens_used=100
        )


# 注册多个Agents
for name in ['code_explorer', 'translator', 'code_analyzer', 'test_expert']:
    config = AgentConfig(name=name, description=f"Mock {name}", model="mock")
    agent = MockAgent(config)
    register_agent(agent)


async def test_config_mode():
    """测试配置模式（不使用LLM）"""
    print("\n=== 测试1: 配置模式 ===")
    
    skill = SkillConfig(
        name='parallel-skill',
        orchestrator='parallel',
        agents=[
            {'name': 'search', 'agent': 'code_explorer', 'task': '搜索代码', 'priority': 8},
            {'name': 'analyze', 'agent': 'code_analyzer', 'task': '分析代码', 'priority': 5},
            {'name': 'test', 'agent': 'test_expert', 'task': '测试代码', 'priority': 3}
        ]
    )
    
    orchestrator = ParallelOrchestrator(batch_size=2)
    result = await orchestrator.execute(skill, '处理代码', {})
    
    print(f"成功: {result['success']}")
    print(f"总任务: {result['metadata']['total_tasks']}")
    print(f"成功任务: {result['metadata']['successful_tasks']}")
    print(f"批量大小: {result['metadata']['batch_size']}")
    print(f"使用LLM拆分: {result['metadata']['use_llm_split']}")
    
    assert result['success']
    assert result['metadata']['total_tasks'] == 3
    assert result['metadata']['successful_tasks'] == 3
    
    print("✅ 配置模式测试通过")


async def test_keyword_split():
    """测试关键词拆分模式"""
    print("\n=== 测试2: 关键词拆分 ===")
    
    skill = SkillConfig(
        name='parallel-skill',
        orchestrator='parallel',
        use_llm_split=False  # 不使用LLM
    )
    
    orchestrator = ParallelOrchestrator()
    result = await orchestrator.execute(skill, '查找和搜索相关代码文档', {})
    
    print(f"成功: {result['success']}")
    print(f"总任务: {result['metadata']['total_tasks']}")
    print(f"任务列表:")
    for r in result['parallel_results']:
        if not isinstance(r, Exception):
            print(f"  - {r.get('task_name')}: {r.get('agent_name')}")
    
    assert result['success']
    assert result['metadata']['total_tasks'] >= 1
    
    print("✅ 关键词拆分测试通过")


async def test_priority_scheduling():
    """测试优先级调度"""
    print("\n=== 测试3: 优先级调度 ===")
    
    skill = SkillConfig(
        name='parallel-skill',
        orchestrator='parallel',
        agents=[
            {'name': 'low', 'agent': 'translator', 'task': '低优先级', 'priority': 2},
            {'name': 'high', 'agent': 'code_explorer', 'task': '高优先级', 'priority': 9},
            {'name': 'medium', 'agent': 'code_analyzer', 'task': '中优先级', 'priority': 5}
        ]
    )
    
    orchestrator = ParallelOrchestrator(batch_size=2)
    result = await orchestrator.execute(skill, '测试', {})
    
    print(f"成功: {result['success']}")
    print(f"执行顺序（按优先级）:")
    for i, r in enumerate(result['parallel_results']):
        if not isinstance(r, Exception):
            print(f"  {i+1}. {r.get('task_name')} (Agent: {r.get('agent_name')})")
    
    # 验证高优先级任务先执行（在前2个批次中）
    first_two = result['parallel_results'][:2]
    task_names = [r.get('task_name') for r in first_two if not isinstance(r, Exception)]
    
    assert 'high' in task_names  # 高优先级应该在前面
    
    print("✅ 优先级调度测试通过")


async def test_batch_execution():
    """测试批量执行"""
    print("\n=== 测试4: 批量执行 ===")
    
    # 创建5个任务，批量大小为2
    skill = SkillConfig(
        name='parallel-skill',
        orchestrator='parallel',
        agents=[
            {'name': f'task{i}', 'agent': 'translator', 'task': f'任务{i}'}
            for i in range(5)
        ]
    )
    
    orchestrator = ParallelOrchestrator(batch_size=2)
    result = await orchestrator.execute(skill, '测试', {})
    
    print(f"成功: {result['success']}")
    print(f"总任务: {result['metadata']['total_tasks']}")
    print(f"批量大小: {result['metadata']['batch_size']}")
    print(f"预期批次数: {(5 + 2 - 1) // 2} = 3")
    
    assert result['success']
    assert result['metadata']['total_tasks'] == 5
    assert result['metadata']['batch_size'] == 2
    
    print("✅ 批量执行测试通过")


async def main():
    print("=" * 60)
    print("ParallelOrchestrator LLM增强功能测试")
    print("=" * 60)
    
    try:
        await test_config_mode()
        await test_keyword_split()
        await test_priority_scheduling()
        await test_batch_execution()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        print("\n注意: LLM拆分和聚合功能需要真实的LLM才能测试")
        print("当前测试覆盖了配置模式、关键词拆分、优先级调度和批量执行")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())
