"""
Agent系统端到端使用示例

展示如何使用Agent系统完成实际任务
"""

import asyncio
from pathlib import Path

from daoyoucode.agents.core.agent import BaseAgent, AgentConfig
from daoyoucode.agents.tools import get_tool_registry
from daoyoucode.agents.core.context import ContextManager


async def example_1_code_review():
    """
    示例1: 代码审查
    
    任务：审查一个Python文件，找出潜在问题
    """
    print("\n" + "="*60)
    print("示例1: 代码审查")
    print("="*60)
    
    # 1. 创建Agent
    config = AgentConfig(
        name="code_reviewer",
        description="代码审查助手",
        model="gpt-4",
        system_prompt="你是一个专业的代码审查助手，帮助发现代码中的问题"
    )
    agent = BaseAgent(config)
    
    # 2. 获取工具
    registry = get_tool_registry()
    
    # 3. 读取代码文件
    print("\n📖 读取代码文件...")
    read_result = await registry.execute_tool(
        "read_file",
        file_path="backend/daoyoucode/agents/tools/file_tools.py"
    )
    
    if read_result.success:
        print(f"✅ 成功读取文件（{len(read_result.content)} 字符）")
    
    # 4. 使用LSP检查错误
    print("\n🔍 使用LSP检查代码错误...")
    lsp_result = await registry.execute_tool(
        "lsp_diagnostics",
        file_path="backend/daoyoucode/agents/tools/file_tools.py"
    )
    
    if lsp_result.success:
        if lsp_result.content:
            print(f"⚠️ 发现问题:\n{lsp_result.content}")
        else:
            print("✅ 没有发现错误")
    
    # 5. 搜索TODO注释
    print("\n📝 搜索TODO注释...")
    search_result = await registry.execute_tool(
        "text_search",
        query="TODO",
        directory="backend/daoyoucode/agents/tools"
    )
    
    if search_result.success and search_result.content:
        print(f"📋 找到TODO:\n{search_result.content[:500]}...")
    else:
        print("✅ 没有TODO注释")
    
    print("\n✅ 代码审查完成！")


async def example_2_refactoring():
    """
    示例2: 代码重构
    
    任务：将所有print语句改为logger.info
    """
    print("\n" + "="*60)
    print("示例2: 代码重构")
    print("="*60)
    
    registry = get_tool_registry()
    
    # 1. 使用AST搜索所有print语句
    print("\n🔍 搜索所有print语句...")
    search_result = await registry.execute_tool(
        "ast_grep_search",
        pattern="print($MSG)",
        lang="python",
        paths=["backend/daoyoucode/agents/tools"]
    )
    
    if search_result.success:
        if "No matches found" in search_result.content:
            print("✅ 没有找到print语句")
        else:
            print(f"📋 找到print语句:\n{search_result.content[:500]}...")
            
            # 2. 预览替换
            print("\n👀 预览替换...")
            preview_result = await registry.execute_tool(
                "ast_grep_replace",
                pattern="print($MSG)",
                rewrite="logger.info($MSG)",
                lang="python",
                paths=["backend/daoyoucode/agents/tools"],
                dry_run=True
            )
            
            if preview_result.success:
                print(f"📋 预览:\n{preview_result.content[:500]}...")
                print("\n💡 提示: 设置dry_run=False可以实际应用修改")
    
    print("\n✅ 重构预览完成！")


async def example_3_understand_project():
    """
    示例3: 理解项目结构
    
    任务：快速了解一个陌生项目
    """
    print("\n" + "="*60)
    print("示例3: 理解项目结构")
    print("="*60)
    
    registry = get_tool_registry()
    
    # 1. 查看目录结构
    print("\n📁 查看目录结构...")
    structure_result = await registry.execute_tool(
        "get_repo_structure",
        repo_path="backend/daoyoucode/agents"
    )
    
    if structure_result.success:
        print(f"📋 目录结构:\n{structure_result.content[:800]}...")
    
    # 2. 生成代码地图
    print("\n🗺️ 生成代码地图...")
    repomap_result = await registry.execute_tool(
        "repo_map",
        repo_path="backend/daoyoucode/agents",
        mentioned_idents=["BaseAgent", "execute"],
        max_tokens=1000
    )
    
    if repomap_result.success:
        if repomap_result.content:
            print(f"📋 代码地图:\n{repomap_result.content[:800]}...")
        else:
            print("ℹ️ 代码地图为空（可能没有引用关系）")
    
    # 3. 查看主要文件的符号
    print("\n🔍 查看主要文件的符号...")
    symbols_result = await registry.execute_tool(
        "lsp_symbols",
        file_path="backend/daoyoucode/agents/core/agent.py"
    )
    
    if symbols_result.success:
        print(f"📋 符号列表:\n{symbols_result.content[:500]}...")
    
    print("\n✅ 项目结构分析完成！")


async def example_4_fix_bug():
    """
    示例4: 修复Bug
    
    任务：找到并修复一个bug
    """
    print("\n" + "="*60)
    print("示例4: 修复Bug")
    print("="*60)
    
    registry = get_tool_registry()
    
    # 1. 搜索错误信息
    print("\n🔍 搜索可能的错误...")
    search_result = await registry.execute_tool(
        "text_search",
        query="FIXME",
        directory="backend/daoyoucode/agents"
    )
    
    if search_result.success and search_result.content:
        print(f"📋 找到FIXME:\n{search_result.content[:500]}...")
    else:
        print("✅ 没有找到FIXME标记")
    
    # 2. 使用LSP查找引用
    print("\n🔍 查找函数引用...")
    # 这里需要具体的文件和位置
    print("💡 提示: 使用lsp_find_references可以查找函数的所有调用位置")
    
    # 3. 使用Diff工具修复
    print("\n🔧 使用Diff工具修复代码...")
    print("💡 提示: 使用search_replace可以精确修改代码")
    
    # 4. 运行测试验证
    print("\n🧪 运行测试验证修复...")
    test_result = await registry.execute_tool(
        "run_test",
        test_path="backend/test_tools.py",
        framework="pytest"
    )
    
    if test_result.success:
        print(f"📋 测试结果:\n{test_result.content[:500]}...")
    
    print("\n✅ Bug修复流程演示完成！")


async def example_5_context_management():
    """
    示例5: 智能上下文管理
    
    任务：演示如何使用上下文管理器
    """
    print("\n" + "="*60)
    print("示例5: 智能上下文管理")
    print("="*60)
    
    # 1. 创建上下文管理器
    context_manager = ContextManager()
    session_id = "demo_session"
    
    # 2. 创建上下文
    print("\n📝 创建上下文...")
    context = context_manager.create_context(session_id)
    
    # 3. 设置变量
    print("\n💾 设置上下文变量...")
    context.set("project_name", "daoyoucode")
    context.set("task", "代码审查")
    context.set("priority", "high")
    
    print(f"✅ 已设置 {len(context.keys())} 个变量")
    
    # 4. 创建快照
    print("\n📸 创建快照...")
    snapshot_id = context.create_snapshot("初始状态")
    print(f"✅ 快照ID: {snapshot_id[:8]}...")
    
    # 5. 添加RepoMap到上下文
    print("\n🗺️ 添加RepoMap到上下文...")
    success = await context_manager.add_repo_map(
        session_id,
        repo_path="backend/daoyoucode/agents",
        mentioned_idents=["BaseAgent"],
        max_tokens=500
    )
    
    if success:
        print("✅ RepoMap已添加到上下文")
    
    # 6. Token预算控制
    print("\n⚖️ 执行Token预算控制...")
    result = context_manager.enforce_token_budget(
        session_id,
        token_budget=1000,
        priority_keys=["project_name", "task"]
    )
    
    if result['success']:
        print(f"✅ Token控制完成: {result['original_tokens']} → {result['final_tokens']}")
        if result['pruned']:
            print(f"   剪枝了 {len(result.get('removed_keys', []))} 个变量")
    
    # 7. 查看上下文统计
    print("\n📊 上下文统计...")
    stats = context_manager.get_stats()
    print(f"   总上下文数: {stats['total_contexts']}")
    print(f"   总变量数: {stats['total_variables']}")
    print(f"   总快照数: {stats['total_snapshots']}")
    
    print("\n✅ 上下文管理演示完成！")


async def example_6_git_workflow():
    """
    示例6: Git工作流
    
    任务：演示Git工具的使用
    """
    print("\n" + "="*60)
    print("示例6: Git工作流")
    print("="*60)
    
    registry = get_tool_registry()
    
    # 1. 查看Git状态
    print("\n📊 查看Git状态...")
    status_result = await registry.execute_tool(
        "git_status",
        repo_path="."
    )
    
    if status_result.success:
        print(f"📋 状态:\n{status_result.content[:500]}...")
    
    # 2. 查看改动
    print("\n🔍 查看改动...")
    diff_result = await registry.execute_tool(
        "git_diff",
        repo_path="."
    )
    
    if diff_result.success:
        if diff_result.content:
            print(f"📋 改动:\n{diff_result.content[:500]}...")
        else:
            print("✅ 没有改动")
    
    # 3. 查看提交历史
    print("\n📜 查看提交历史...")
    log_result = await registry.execute_tool(
        "git_log",
        repo_path=".",
        max_count=3
    )
    
    if log_result.success:
        print(f"📋 最近3次提交:\n{log_result.content[:500]}...")
    
    print("\n✅ Git工作流演示完成！")


async def main():
    """主函数：运行所有示例"""
    print("\n" + "="*60)
    print("🚀 Agent系统端到端使用示例")
    print("="*60)
    print("\n这些示例展示了如何使用Agent系统完成实际任务")
    print("包括：代码审查、重构、理解项目、修复Bug、上下文管理、Git工作流")
    
    try:
        # 运行所有示例
        await example_1_code_review()
        await example_2_refactoring()
        await example_3_understand_project()
        await example_4_fix_bug()
        await example_5_context_management()
        await example_6_git_workflow()
        
        print("\n" + "="*60)
        print("🎉 所有示例运行完成！")
        print("="*60)
        print("\n💡 提示:")
        print("   - 这些示例展示了工具的基本用法")
        print("   - 实际使用时可以组合多个工具")
        print("   - 查看TOOLS_USER_GUIDE.md了解更多")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
