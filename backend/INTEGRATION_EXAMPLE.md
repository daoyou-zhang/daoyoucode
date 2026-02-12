# 智能化功能集成示例

## 概述

本文档展示如何在Executor中集成使用7个智能化功能，实现一个完整的智能Agent执行流程。

## 完整集成示例

```python
from pathlib import Path
from daoyoucode.agents.core.model_selector import ModelSelector
from daoyoucode.agents.core.context_selector import ContextSelector
from daoyoucode.agents.core.delegation import DelegationPrompt, DelegationManager
from daoyoucode.agents.core.behavior_guide import BehaviorGuide
from daoyoucode.agents.core.codebase_assessor import CodebaseAssessor
from daoyoucode.agents.core.parallel_executor import ParallelExecutor
from daoyoucode.agents.core.session import SessionManager
from daoyoucode.agents.core.router import get_intelligent_router
from daoyoucode.agents.core.planner import get_execution_planner
from daoyoucode.agents.core.feedback import get_feedback_loop

async def intelligent_execute(instruction: str, project_root: Path):
    """
    智能执行流程，集成所有智能化功能
    """
    
    # ==================== 1. 代码库评估 ====================
    print("📊 评估代码库...")
    assessor = CodebaseAssessor(project_root)
    assessment = assessor.assess()
    codebase_guide = assessor.get_behavior_guide()
    
    print(f"  规模: {assessment['size']}")
    print(f"  复杂度: {assessment['complexity']}")
    print(f"  质量: {assessment['quality']}")
    
    # ==================== 2. 行为指南 ====================
    print("\n🎯 获取行为指南...")
    behavior_guide = BehaviorGuide()
    request_type = behavior_guide.classify_request(instruction)
    action_guide = behavior_guide.get_action(request_type)
    
    print(f"  请求类型: {request_type}")
    print(f"  建议行动: {action_guide['description']}")
    
    # 判断是否需要澄清
    if behavior_guide.should_ask_clarification(instruction, context_size=100):
        print("  ⚠️ 建议先澄清需求")
        # 这里可以向用户询问更多信息
    
    # ==================== 3. 智能上下文选择 ====================
    print("\n📁 选择相关上下文...")
    context_selector = ContextSelector(project_root)
    selected_files = context_selector.select_context(
        instruction=instruction,
        max_files=10
    )
    
    print(f"  选择了 {len(selected_files)} 个文件")
    for file in selected_files[:3]:  # 只显示前3个
        print(f"    - {file}")
    
    # ==================== 4. 智能路由 ====================
    print("\n🧭 智能路由...")
    router = get_intelligent_router()
    decision = await router.route(instruction)
    
    print(f"  编排器: {decision.orchestrator}")
    print(f"  Agent: {decision.agent}")
    print(f"  置信度: {decision.confidence:.2f}")
    print(f"  理由: {decision.reason}")
    
    # ==================== 5. 智能模型选择 ====================
    print("\n🤖 选择模型...")
    model_selector = ModelSelector()
    model_selector.configure(
        simple_model="gpt-3.5-turbo",
        complex_model="gpt-4",
        edit_model="claude-3-opus"
    )
    
    # 根据任务类型和上下文大小选择模型
    task_type = "complex" if assessment['complexity'] == "high" else "simple"
    context_size = sum(len(open(f).read()) for f in selected_files if f.exists())
    
    selected_model = model_selector.select_model(
        task_type=task_type,
        context_size=context_size
    )
    
    print(f"  选择模型: {selected_model}")
    
    # ==================== 6. 执行规划 ====================
    print("\n📋 生成执行计划...")
    planner = get_execution_planner()
    plan = await planner.create_plan(instruction)
    
    print(f"  复杂度: {plan.complexity}/5")
    print(f"  预估时间: {plan.total_estimated_time/60:.1f}分钟")
    print(f"  预估成本: {plan.total_estimated_tokens} tokens")
    print(f"  步骤数: {len(plan.steps)}")
    
    if plan.risks:
        print(f"  ⚠️ 风险: {', '.join(plan.risks)}")
    
    # 用户确认（可选）
    # if not user_confirms(plan):
    #     return None
    
    # ==================== 7. 会话管理 ====================
    print("\n💬 创建会话...")
    session_manager = SessionManager()
    session_id = session_manager.create_session(
        agent_name=decision.agent,
        metadata={
            'instruction': instruction,
            'model': selected_model,
            'orchestrator': decision.orchestrator,
        }
    )
    
    print(f"  会话ID: {session_id}")
    
    # ==================== 8. 并行执行（如果有多个独立任务）====================
    if len(selected_files) > 3:
        print("\n⚡ 并行分析文件...")
        parallel_executor = ParallelExecutor(max_workers=4)
        
        # 提交并行任务
        task_ids = []
        for file in selected_files[:5]:  # 只分析前5个文件
            task_id = parallel_executor.submit(analyze_file, file)
            task_ids.append(task_id)
        
        # 获取结果
        analysis_results = []
        for task_id in task_ids:
            try:
                result = parallel_executor.get_result(task_id, timeout=30)
                analysis_results.append(result)
            except TimeoutError:
                print(f"  ⚠️ 任务 {task_id} 超时")
        
        print(f"  完成 {len(analysis_results)} 个文件分析")
    
    # ==================== 9. 结构化委托（如果需要子任务）====================
    if plan.complexity >= 4:  # 复杂任务需要委托
        print("\n📤 创建委托任务...")
        delegation_manager = DelegationManager()
        
        # 为每个步骤创建委托
        for i, step in enumerate(plan.steps[:3]):  # 只显示前3个
            delegation_prompt = DelegationPrompt(
                goal=step['description'],
                context={
                    'files': selected_files,
                    'codebase_guide': codebase_guide,
                    'behavior_guide': action_guide,
                },
                constraints=[
                    "遵循代码库规范",
                    "保持代码风格一致",
                    "添加必要的注释",
                ],
                expected_output=f"步骤{i+1}的执行结果"
            )
            
            # 验证委托
            is_valid, message = delegation_prompt.validate()
            if is_valid:
                formatted_prompt = delegation_prompt.to_prompt()
                print(f"  步骤{i+1}: {step['description'][:50]}...")
                # 这里可以将formatted_prompt发送给子Agent
            else:
                print(f"  ⚠️ 步骤{i+1}委托无效: {message}")
    
    # ==================== 10. 执行任务 ====================
    print("\n🚀 执行任务...")
    # 这里是实际的任务执行逻辑
    # result = await execute_with_orchestrator(
    #     orchestrator=decision.orchestrator,
    #     agent=decision.agent,
    #     instruction=instruction,
    #     context=selected_files,
    #     model=selected_model,
    # )
    
    # 模拟执行结果
    result = {
        'success': True,
        'output': '任务执行成功',
        'files_modified': ['file1.py', 'file2.py'],
    }
    
    # ==================== 11. 保存会话 ====================
    print("\n💾 保存会话...")
    session_manager.save_session(session_id)
    
    # ==================== 12. 反馈评估 ====================
    print("\n📊 评估结果...")
    feedback_loop = get_feedback_loop()
    evaluation = await feedback_loop.evaluate(instruction, result)
    
    print(f"  质量分数: {evaluation.quality_score:.2f}")
    print(f"  优点: {', '.join(evaluation.strengths[:2])}")
    if evaluation.issues:
        print(f"  问题: {', '.join(evaluation.issues[:2])}")
    if evaluation.suggestions:
        print(f"  建议: {', '.join(evaluation.suggestions[:2])}")
    
    # ==================== 13. 学习和改进 ====================
    if evaluation.quality_score < 0.7:
        print("\n📚 学习改进...")
        await feedback_loop.learn_from_failure(instruction, result, evaluation)
    
    print("\n✅ 执行完成！")
    return result


def analyze_file(file_path: Path) -> dict:
    """分析单个文件（示例函数）"""
    # 这里是实际的文件分析逻辑
    return {
        'file': str(file_path),
        'lines': 100,
        'functions': 5,
        'classes': 2,
    }


# ==================== 使用示例 ====================
if __name__ == "__main__":
    import asyncio
    
    project_root = Path(".")
    instruction = "重构 user.py 中的 UserManager 类，提高代码质量"
    
    result = asyncio.run(intelligent_execute(instruction, project_root))
    print(f"\n最终结果: {result}")
```

## 输出示例

```
📊 评估代码库...
  规模: medium
  复杂度: moderate
  质量: good

🎯 获取行为指南...
  请求类型: refactor
  建议行动: 重构代码以提高质量和可维护性

📁 选择相关上下文...
  选择了 3 个文件
    - user.py
    - models/user.py
    - tests/test_user.py

🧭 智能路由...
  编排器: simple
  Agent: CodeAnalyzer
  置信度: 0.85
  理由: 单文件重构任务，使用简单编排器

🤖 选择模型...
  选择模型: gpt-4

📋 生成执行计划...
  复杂度: 3/5
  预估时间: 5.0分钟
  预估成本: 2000 tokens
  步骤数: 3

💬 创建会话...
  会话ID: session_12345

🚀 执行任务...

💾 保存会话...

📊 评估结果...
  质量分数: 0.85
  优点: 代码结构清晰, 遵循最佳实践

✅ 执行完成！

最终结果: {'success': True, 'output': '任务执行成功', 'files_modified': ['file1.py', 'file2.py']}
```

## 关键点

### 1. 可选性
所有智能化功能都是可选的，可以根据需要选择性启用：
- 简单任务可以跳过代码库评估
- 明确的指令可以跳过行为指南
- 单文件任务可以跳过上下文选择
- 简单任务可以跳过执行规划

### 2. 灵活性
每个功能都可以独立使用，也可以组合使用：
```python
# 只使用模型选择
model = ModelSelector().select_model("complex", 5000)

# 只使用上下文选择
files = ContextSelector(root).select_context(instruction)

# 组合使用
model = ModelSelector().select_model("complex", 5000)
files = ContextSelector(root).select_context(instruction)
```

### 3. 性能优化
- 单例模式避免重复初始化
- 并行执行提高效率
- 智能缓存减少重复计算

### 4. 错误处理
```python
try:
    result = parallel_executor.get_result(task_id, timeout=30)
except TimeoutError:
    print("任务超时")
except Exception as e:
    print(f"任务失败: {e}")
```

## 总结

通过集成7个智能化功能，实现了一个完整的智能Agent执行流程：

1. **代码库评估** - 了解项目规模和复杂度
2. **行为指南** - 获取最佳实践建议
3. **上下文选择** - 自动选择相关文件
4. **智能路由** - 自动选择编排器和Agent
5. **模型选择** - 根据任务选择最优模型
6. **执行规划** - 预览执行计划和成本
7. **会话管理** - 管理长期交互
8. **并行执行** - 提高执行效率
9. **结构化委托** - 提高子任务质量
10. **反馈评估** - 评估结果质量
11. **学习改进** - 从失败中学习

这些功能共同构成了一个智能、高效、可靠的Agent系统。
