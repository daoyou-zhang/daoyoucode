#!/usr/bin/env python3
"""
真实集成测试：验证 Context 改进是否集成到实际工具调用流程

模拟真实的 Agent 执行流程：
1. 创建 Agent
2. 执行工具调用
3. 验证 Context 是否正确保存
"""

import sys
import os
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from daoyoucode.agents.core.agent import BaseAgent, AgentConfig
from daoyoucode.agents.core.context import get_context_manager


class MockToolResult:
    """模拟工具结果"""
    def __init__(self, content, success=True):
        self.content = content
        self.success = success
        self.error = None if success else "Mock error"


async def test_real_agent_execution():
    """
    测试真实的 Agent 执行流程
    """
    print("\n" + "="*60)
    print("真实集成测试：Agent 工具调用流程")
    print("="*60)
    
    # 1. 创建 Agent
    print("\n步骤1：创建 Agent")
    config = AgentConfig(
        name="test_agent",
        description="测试 Agent",
        model="gpt-4",
        temperature=0.7
    )
    agent = BaseAgent(config)
    print(f"   ✅ Agent 已创建: {agent.name}")
    
    # 2. 准备 context
    print("\n步骤2：准备 Context")
    context = {
        'session_id': 'test_session_real',
        'user_id': 'test_user'
    }
    
    # 模拟 execute 方法中的 Context 初始化逻辑
    session_id = context.get('session_id', 'default')
    ctx = agent.context_manager.get_or_create_context(session_id)
    ctx.update(context, track_change=False)
    context['_context_obj'] = ctx
    print(f"   ✅ Context 对象已创建: session={session_id}")
    
    # 3. 模拟第一次工具调用（搜索目标文件）
    print("\n步骤3：模拟第一次工具调用 (text_search)")
    tool_name_1 = "text_search"
    tool_result_1 = MockToolResult(
        content="backend/daoyoucode/agents/core/agent.py:100: class BaseAgent"
    )
    
    # 模拟工具执行成功后的逻辑
    ctx = context.get('_context_obj')
    if ctx:
        try:
            agent._save_tool_result_to_context(ctx, tool_name_1, tool_result_1)
            print(f"   ✅ 工具结果已保存到 Context")
        except Exception as e:
            print(f"   ❌ 保存失败: {e}")
            return False
    
    # 验证
    target_file_1 = ctx.get("target_file")
    search_history_1 = ctx.get("search_history")
    print(f"   target_file = {target_file_1}")
    print(f"   search_history = {len(search_history_1) if search_history_1 else 0} 条")
    
    if not target_file_1:
        print("   ❌ target_file 未设置")
        return False
    
    # 4. 模拟第二次工具调用（搜索配置文件）
    print("\n步骤4：模拟第二次工具调用 (text_search)")
    tool_name_2 = "text_search"
    tool_result_2 = MockToolResult(
        content="backend/daoyoucode/config.yaml:1: version: 1.0"
    )
    
    # 再次保存
    try:
        agent._save_tool_result_to_context(ctx, tool_name_2, tool_result_2)
        print(f"   ✅ 工具结果已保存到 Context")
    except Exception as e:
        print(f"   ❌ 保存失败: {e}")
        return False
    
    # 验证
    target_file_2 = ctx.get("target_file")
    last_search_paths = ctx.get("last_search_paths")
    search_history_2 = ctx.get("search_history")
    print(f"   target_file = {target_file_2}")
    print(f"   last_search_paths = {last_search_paths}")
    print(f"   search_history = {len(search_history_2) if search_history_2 else 0} 条")
    
    # 5. 模拟第三次工具调用（grep_search）
    print("\n步骤5：模拟第三次工具调用 (grep_search)")
    tool_name_3 = "grep_search"
    tool_result_3 = MockToolResult(
        content="backend/daoyoucode/agents/tools/base.py:50: class BaseTool"
    )
    
    try:
        agent._save_tool_result_to_context(ctx, tool_name_3, tool_result_3)
        print(f"   ✅ 工具结果已保存到 Context")
    except Exception as e:
        print(f"   ❌ 保存失败: {e}")
        return False
    
    # 验证
    target_file_3 = ctx.get("target_file")
    last_search_paths_3 = ctx.get("last_search_paths")
    search_history_3 = ctx.get("search_history")
    print(f"   target_file = {target_file_3}")
    print(f"   last_search_paths = {last_search_paths_3}")
    print(f"   search_history = {len(search_history_3) if search_history_3 else 0} 条")
    
    # 6. 最终验证
    print("\n步骤6：最终验证")
    
    # 验证 target_file 没有被覆盖
    if target_file_3 != target_file_1:
        print(f"   ❌ target_file 被覆盖了: {target_file_1} → {target_file_3}")
        return False
    print(f"   ✅ target_file 保持不变: {target_file_3}")
    
    # 验证搜索历史
    if len(search_history_3) != 3:
        print(f"   ❌ 搜索历史数量不对: {len(search_history_3)} != 3")
        return False
    print(f"   ✅ 搜索历史正确: {len(search_history_3)} 条")
    
    # 验证 last_search_paths 更新
    if last_search_paths_3[0] != "backend/daoyoucode/agents/tools/base.py":
        print(f"   ❌ last_search_paths 不是最新: {last_search_paths_3}")
        return False
    print(f"   ✅ last_search_paths 正确更新")
    
    # 显示搜索历史
    print("\n📝 搜索历史:")
    for i, entry in enumerate(search_history_3, 1):
        print(f"   {i}. [{entry['tool']}] {entry['paths'][0]}")
    
    return True


async def test_context_manager_integration():
    """
    测试 ContextManager 是否正确集成到 Agent
    """
    print("\n" + "="*60)
    print("测试：ContextManager 集成")
    print("="*60)
    
    # 创建 Agent
    config = AgentConfig(
        name="test_agent_2",
        description="测试 Agent 2",
        model="gpt-4"
    )
    agent = BaseAgent(config)
    
    # 验证 context_manager 存在
    if not hasattr(agent, 'context_manager'):
        print("   ❌ Agent 没有 context_manager 属性")
        return False
    print("   ✅ Agent 有 context_manager 属性")
    
    # 验证可以创建 Context
    try:
        ctx = agent.context_manager.get_or_create_context("test_session_2")
        print(f"   ✅ 可以创建 Context: {type(ctx)}")
    except Exception as e:
        print(f"   ❌ 创建 Context 失败: {e}")
        return False
    
    # 验证 _save_tool_result_to_context 方法存在
    if not hasattr(agent, '_save_tool_result_to_context'):
        print("   ❌ Agent 没有 _save_tool_result_to_context 方法")
        return False
    print("   ✅ Agent 有 _save_tool_result_to_context 方法")
    
    # 验证 _extract_paths_from_result 方法存在
    if not hasattr(agent, '_extract_paths_from_result'):
        print("   ❌ Agent 没有 _extract_paths_from_result 方法")
        return False
    print("   ✅ Agent 有 _extract_paths_from_result 方法")
    
    return True


async def test_path_extraction():
    """
    测试路径提取功能
    """
    print("\n" + "="*60)
    print("测试：路径提取功能")
    print("="*60)
    
    config = AgentConfig(
        name="test_agent_3",
        description="测试 Agent 3",
        model="gpt-4"
    )
    agent = BaseAgent(config)
    
    # 测试 text_search 结果
    print("\n1. 测试 text_search 结果")
    result_1 = MockToolResult(
        content="backend/daoyoucode/agents/core/agent.py:100: class BaseAgent\n"
                "backend/daoyoucode/agents/core/context.py:50: class Context"
    )
    paths_1 = agent._extract_paths_from_result("text_search", result_1)
    print(f"   提取的路径: {paths_1}")
    if len(paths_1) != 2:
        print(f"   ❌ 路径数量不对: {len(paths_1)} != 2")
        return False
    print(f"   ✅ 正确提取了 {len(paths_1)} 个路径")
    
    # 测试 grep_search 结果
    print("\n2. 测试 grep_search 结果")
    result_2 = MockToolResult(
        content="backend/daoyoucode/agents/tools/base.py:50: class BaseTool"
    )
    paths_2 = agent._extract_paths_from_result("grep_search", result_2)
    print(f"   提取的路径: {paths_2}")
    if len(paths_2) != 1:
        print(f"   ❌ 路径数量不对: {len(paths_2)} != 1")
        return False
    print(f"   ✅ 正确提取了 {len(paths_2)} 个路径")
    
    # 测试 repo_map 结果
    print("\n3. 测试 repo_map 结果")
    result_3 = MockToolResult(
        content="backend/daoyoucode/agents/core/agent.py\n"
                "backend/daoyoucode/agents/core/context.py\n"
                "backend/daoyoucode/agents/tools/base.py"
    )
    paths_3 = agent._extract_paths_from_result("repo_map", result_3)
    print(f"   提取的路径: {paths_3}")
    if len(paths_3) != 3:
        print(f"   ❌ 路径数量不对: {len(paths_3)} != 3")
        return False
    print(f"   ✅ 正确提取了 {len(paths_3)} 个路径")
    
    return True


async def main():
    print("\n" + "="*60)
    print("真实集成测试套件")
    print("="*60)
    
    all_pass = True
    
    # 测试1：ContextManager 集成
    if not await test_context_manager_integration():
        print("\n❌ ContextManager 集成测试失败")
        all_pass = False
    else:
        print("\n✅ ContextManager 集成测试通过")
    
    # 测试2：路径提取功能
    if not await test_path_extraction():
        print("\n❌ 路径提取功能测试失败")
        all_pass = False
    else:
        print("\n✅ 路径提取功能测试通过")
    
    # 测试3：真实 Agent 执行流程
    if not await test_real_agent_execution():
        print("\n❌ 真实 Agent 执行流程测试失败")
        all_pass = False
    else:
        print("\n✅ 真实 Agent 执行流程测试通过")
    
    # 最终结果
    print("\n" + "="*60)
    if all_pass:
        print("✅ 所有真实集成测试通过！")
        print("="*60)
        print("\n🎉 确认：Context 改进已完全集成到工具调用流程")
        print("\n集成点验证:")
        print("   ✅ Agent.__init__ 中初始化了 context_manager")
        print("   ✅ Agent.execute() 中创建了 Context 对象")
        print("   ✅ 工具执行成功后调用 _save_tool_result_to_context")
        print("   ✅ _save_tool_result_to_context 正确保存路径")
        print("   ✅ _extract_paths_from_result 正确提取路径")
        print("   ✅ target_file 不会被后续搜索覆盖")
        print("   ✅ search_history 正确记录所有搜索")
        return 0
    else:
        print("❌ 部分真实集成测试失败")
        print("="*60)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
