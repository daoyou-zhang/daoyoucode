# ReAct编排器预留方法指南

## 概述

ReAct编排器包含一组预留方法，用于未来实现更高级的编排逻辑。这些方法在当前的简化版本中不使用，但保留作为参考实现。

## 当前架构

### 简化版本（当前使用）

当前的 `ReActOrchestrator.execute()` 使用简化的实现：

```python
async def execute(self, skill, user_input, context):
    # 1. 获取Agent
    # 2. 准备prompt
    # 3. 执行Agent（带工具）- LLM自动控制ReAct循环
    # 4. 返回结果
```

**优势**：
- 简单高效：LLM自动控制循环，无需额外的规划步骤
- 成本低：减少不必要的LLM调用
- 灵活性：LLM可以根据实际情况动态调整策略
- 易于使用：对用户透明，无需配置复杂参数

**ReAct循环在Agent层实现**（通过Function Calling）：
- Thought（思考）：LLM分析用户问题，决定是否调用工具
- Action（行动）：执行工具获取信息
- Observation（观察）：处理工具返回的结果
- Reflect（反思）：LLM基于结果决定下一步行动

## 预留方法

### 1. `_plan()` - 生成执行计划

**用途**：显式的规划阶段，生成详细的执行计划

**功能**：
- 分析任务需求
- 生成详细的执行步骤
- 估算时间和复杂度
- 识别潜在风险
- 支持基于失败的重新规划

**测试**：`test_advanced_features.py::test_react_plan_generation`

### 2. `_approve()` - 请求用户批准

**用途**：人工审核阶段，让用户确认执行计划

**功能**：
- 展示执行计划给用户
- 等待用户确认或拒绝
- 支持计划修改建议

**注意**：需要集成用户交互机制（CLI/Web界面）

### 3. `_execute_plan()` - 执行计划

**用途**：按计划执行步骤

**功能**：
- 按顺序执行计划中的步骤
- 为每个步骤创建子任务
- 跟踪执行进度
- 处理步骤失败（中断执行）
- 记录执行结果

### 4. `_execute_step()` - 执行单个步骤

**用途**：执行计划中的单个步骤

**功能**：
- 根据步骤类型选择执行方式
- 调用相应的Agent或工具
- 返回步骤执行结果

**测试**：`test_advanced_features.py::test_react_step_execution`

### 5. `_observe()` - 观察执行结果

**用途**：检查执行结果，决定是否需要反思

**功能**：
- 检查执行结果是否成功
- 识别失败的步骤
- 自动验证结果（如果启用）
- 生成观察报告

**测试**：`test_advanced_features.py::test_react_observation`

### 6. `_verify()` - 验证执行结果

**用途**：自动验证执行结果的正确性

**功能**：
- 运行诊断工具检查代码问题
- 运行测试验证功能
- 检查文件变更是否符合预期
- 生成验证报告

**注意**：需要集成诊断工具和测试框架

### 7. `_reflect()` - 反思失败原因

**用途**：分析失败原因，生成新的执行策略

**功能**：
- 分析失败原因（使用FeedbackLoop）
- 识别错误类型和根因
- 生成恢复建议
- 调整执行策略
- 生成新的指令用于重试

**测试**：`test_advanced_features.py::test_react_reflection`

## 未来扩展：AdvancedReActOrchestrator

### 使用场景

当需要以下功能时，可以实现 `AdvancedReActOrchestrator`：

1. **显式规划**：生成详细的执行计划，让用户了解将要执行的步骤
2. **人工审核**：在执行前让用户批准计划
3. **强错误恢复**：自动分析失败原因并重试
4. **自动验证**：执行后自动运行测试和诊断
5. **多轮反思**：支持多次重试和策略调整

### 实现方式

```python
class AdvancedReActOrchestrator(ReActOrchestrator):
    """高级ReAct编排器，实现完整的Plan-Execute-Observe-Reflect循环"""
    
    async def execute(self, skill, user_input, context):
        """
        完整的ReAct循环：
        1. Plan（规划）：生成执行计划
        2. Approve（批准）：用户确认计划（可选）
        3. Execute（执行）：执行计划
        4. Observe（观察）：检查结果
        5. Reflect（反思）：如果失败，分析原因并重试
        """
        
        instruction = user_input
        attempt = 0
        
        while attempt < self.max_reflections:
            # 1. 规划
            plan = await self._plan(instruction, context)
            
            # 2. 批准（可选）
            if self.require_approval:
                if not await self._approve(plan, context):
                    return {'success': False, 'error': '用户拒绝执行计划'}
            
            # 3. 执行
            result = await self._execute_plan(plan, context, agents, task)
            
            # 4. 观察
            observation = await self._observe(result, context)
            
            if observation['success']:
                return {'success': True, 'result': result}
            
            # 5. 反思
            instruction = await self._reflect(
                original_instruction=user_input,
                current_instruction=instruction,
                error=observation['error'],
                plan=plan,
                context=context,
                attempt=attempt
            )
            
            if not instruction:
                return {'success': False, 'error': '无法恢复'}
            
            attempt += 1
        
        return {'success': False, 'error': '达到最大重试次数'}
```

### 配置选项

```python
orchestrator = AdvancedReActOrchestrator(
    max_reflections=3,        # 最大反思次数
    require_approval=True,    # 是否需要用户批准
    auto_verify=True          # 是否自动验证结果
)
```

## 测试

所有预留方法都有完整的单元测试：

```bash
# 运行所有ReAct测试
python -m pytest backend/test_advanced_features.py -k react -v

# 验证文档完整性
python backend/verify_react_docs.py
```

## 参考

- `backend/daoyoucode/agents/orchestrators/react.py` - 实现代码
- `backend/test_advanced_features.py` - 单元测试
- `backend/AGENT_OPTIMIZATION_PLAN.md` - 优化计划
- `backend/REACT_IMPLEMENTATION_STATUS.md` - 实现状态（如果存在）
- `daoyouCodePilot/OrchestratorCoder` - 原始实现参考

## 总结

预留方法为未来的高级功能提供了清晰的扩展路径，同时保持当前实现的简洁性。当需要更复杂的编排逻辑时，可以基于这些方法实现 `AdvancedReActOrchestrator`，而不需要从头开始。
