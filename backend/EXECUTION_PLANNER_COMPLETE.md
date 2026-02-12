# ExecutionPlanner 实现完成

> 执行前的智能规划系统

---

## ✅ 完成的工作

### 核心实现

**文件**: `backend/daoyoucode/agents/core/planner.py`

**关键组件**:

#### ExecutionPlanner（执行计划器）

```python
class ExecutionPlanner:
    """执行计划器（可选功能）"""
    
    async def create_plan(task_description, context, orchestrator)
    
    # 内部方法
    def _analyze_complexity(task_description, context) -> int
    def _select_orchestrator(task_description, complexity, context) -> str
    def _generate_steps(task_description, orchestrator, complexity, context) -> List[ExecutionStep]
    def _estimate_cost(steps, orchestrator) -> (tokens, time)
    def _identify_risks(task_description, orchestrator, complexity, steps) -> List[str]
    def _generate_recommendations(task_description, orchestrator, complexity, risks) -> List[str]
```

**功能**:
- ✅ 任务复杂度分析（1-5级）
- ✅ 执行步骤生成
- ✅ 成本预估（tokens、时间）
- ✅ 风险识别
- ✅ 建议生成
- ✅ 与Router集成（可选）
- ✅ 单例模式

---

## 📊 核心特性

### 1. 任务复杂度分析 ✅

```python
planner = get_execution_planner()

plan = await planner.create_plan("设计一个完整的系统架构")

print(plan.complexity)  # 4/5
```

**分析维度**:
- 关键词（简单、中等、复杂、非常复杂）
- 任务长度
- 分句数量
- 上下文依赖

### 2. 执行步骤生成 ✅

```python
plan = await planner.create_plan(
    "先分析代码，然后生成文档，最后进行测试"
)

for step in plan.steps:
    print(f"步骤{step.step_id}: {step.description}")
    print(f"  编排器: {step.orchestrator}")
    print(f"  预估tokens: {step.estimated_tokens}")
    print(f"  预估时间: {step.estimated_time}秒")
    if step.dependencies:
        print(f"  依赖: {step.dependencies}")
```

**输出**:
```
步骤1: 分析和理解任务
  编排器: simple
  预估tokens: 500
  预估时间: 3.0秒
  
步骤2: 生成执行计划
  编排器: simple
  预估tokens: 800
  预估时间: 4.0秒
  依赖: [1]
  
步骤3: 执行任务
  编排器: simple
  预估tokens: 1200
  预估时间: 6.0秒
  依赖: [2]
```

### 3. 成本预估 ✅

```python
plan = await planner.create_plan("重构整个项目")

print(f"预估tokens: {plan.total_estimated_tokens}")
print(f"预估时间: {plan.total_estimated_time:.1f}秒")
```

**预估基于**:
- 步骤数量
- 编排器类型
- 任务复杂度
- 历史数据（经验值）

### 4. 风险识别 ✅

```python
plan = await planner.create_plan("设计完整系统架构")

print("识别的风险:")
for risk in plan.risks:
    print(f"  - {risk}")
```

**输出**:
```
识别的风险:
  - 任务复杂度较高，可能需要多次迭代
  - 执行步骤较多（5步），可能耗时较长
  - 存在步骤依赖，前置步骤失败会影响后续步骤
  - 预估tokens较高（5000），成本较大
```

### 5. 建议生成 ✅

```python
plan = await planner.create_plan("重构整个项目")

print("生成的建议:")
for rec in plan.recommendations:
    print(f"  - {rec}")
```

**输出**:
```
生成的建议:
  - 建议分阶段执行，每阶段验证结果
  - 建议在关键步骤设置检查点
  - 建议优化prompt，减少不必要的上下文
  - 建议启用日志记录，便于调试
```

---

## 🔄 与其他模块的集成

### 1. 与Router集成（可选）

```python
# 启用Router集成
planner = get_execution_planner(use_router=True)

plan = await planner.create_plan("查找所有Python文件")

# Planner会使用Router选择最优编排器
print(plan.steps[0].orchestrator)  # parallel_explore (Router选择)
```

### 2. 与Executor集成（可选）

```python
# Executor可以选择性使用Planner
async def execute_skill_with_planning(skill_name, user_input):
    # 1. 创建执行计划（可选）
    planner = get_execution_planner()
    plan = await planner.create_plan(user_input)
    
    # 2. 显示计划给用户（可选）
    print(f"执行计划:")
    print(f"  步骤数: {len(plan.steps)}")
    print(f"  预估时间: {plan.total_estimated_time:.1f}秒")
    print(f"  预估成本: {plan.total_estimated_tokens} tokens")
    
    # 3. 用户确认后执行
    if user_confirms():
        result = await execute_skill(skill_name, user_input)
        return result
```

---

## 💡 使用场景

### 场景1: 执行前预览

```python
# 用户想知道任务会如何执行
planner = get_execution_planner()
plan = await planner.create_plan("重构整个项目的代码结构")

# 显示计划
print(f"任务复杂度: {plan.complexity}/5")
print(f"执行步骤: {len(plan.steps)}步")
print(f"预估时间: {plan.total_estimated_time/60:.1f}分钟")
print(f"预估成本: {plan.total_estimated_tokens} tokens")

# 用户确认后执行
if user_confirms():
    await execute_task()
```

### 场景2: 成本控制

```python
planner = get_execution_planner()
plan = await planner.create_plan(user_input)

# 检查成本
if plan.total_estimated_tokens > 10000:
    print(f"警告：预估tokens较高（{plan.total_estimated_tokens}）")
    print("建议:")
    for rec in plan.recommendations:
        print(f"  - {rec}")
    
    # 让用户决定是否继续
    if not user_confirms():
        return
```

### 场景3: 风险评估

```python
planner = get_execution_planner()
plan = await planner.create_plan(user_input)

# 评估风险
if plan.risks:
    print("识别到以下风险:")
    for risk in plan.risks:
        print(f"  ⚠️ {risk}")
    
    # 提供建议
    print("\n建议:")
    for rec in plan.recommendations:
        print(f"  💡 {rec}")
```

### 场景4: 自动优化

```python
planner = get_execution_planner()
plan = await planner.create_plan(user_input)

# 如果复杂度太高，自动分解
if plan.complexity >= 4:
    print("任务复杂度较高，建议分阶段执行")
    
    # 分阶段执行
    for step in plan.steps:
        print(f"\n执行步骤{step.step_id}: {step.description}")
        result = await execute_step(step)
        
        # 每步验证
        if not result.success:
            print(f"步骤{step.step_id}失败，停止执行")
            break
```

---

## 🎯 核心优势

### 1. 可选功能 ✅

**不影响原有流程**：
```python
# 原有流程（不使用Planner）
result = await execute_skill("code_analysis", user_input)

# 使用Planner（可选）
planner = get_execution_planner()
plan = await planner.create_plan(user_input)
# 显示计划...
result = await execute_skill("code_analysis", user_input)
```

### 2. 智能规划 ✅

- 自动分析任务复杂度
- 自动选择最优编排器
- 自动生成执行步骤
- 自动识别风险

### 3. 成本透明 ✅

- 预估tokens消耗
- 预估执行时间
- 帮助用户做决策

### 4. 风险预警 ✅

- 识别潜在问题
- 提供改进建议
- 降低执行失败率

---

## 📝 测试结果

**文件**: `backend/test_execution_planner.py`

**测试场景**:
- ✅ 简单任务规划
- ✅ 工作流任务规划
- ✅ 并行任务规划
- ✅ 复杂度分析
- ✅ 成本预估
- ✅ 风险识别
- ✅ 建议生成
- ✅ 与Router集成
- ✅ 计划序列化
- ✅ 指定编排器

**所有测试通过！** ✅

---

## 🔌 保持可插拔设计

### ExecutionPlanner是完全可选的

```python
# 方式1: 不使用Planner（原有流程）
result = await execute_skill(skill_name, user_input)

# 方式2: 使用Planner（新功能）
planner = get_execution_planner()
plan = await planner.create_plan(user_input)
# 显示计划...
result = await execute_skill(skill_name, user_input)

# 方式3: 使用Planner选择编排器
planner = get_execution_planner(use_router=True)
plan = await planner.create_plan(user_input)
# 使用plan.steps[0].orchestrator...
```

### 不破坏现有接口

- ✅ 所有现有代码无需修改
- ✅ Planner是独立模块
- ✅ 可以随时启用/禁用
- ✅ 不影响性能（只在需要时调用）

---

## 🎉 总结

### 完成的功能

1. ✅ **ExecutionPlanner** - 执行计划器
2. ✅ **ExecutionPlan** - 执行计划对象
3. ✅ **ExecutionStep** - 执行步骤对象
4. ✅ **复杂度分析** - 1-5级评估
5. ✅ **步骤生成** - 自动生成执行步骤
6. ✅ **成本预估** - tokens和时间
7. ✅ **风险识别** - 自动识别潜在问题
8. ✅ **建议生成** - 提供改进建议
9. ✅ **Router集成** - 可选集成
10. ✅ **单例模式** - 全局唯一实例

### 核心价值

- **智能规划** - 执行前分析和规划
- **成本透明** - 预估tokens和时间
- **风险预警** - 识别潜在问题
- **可选功能** - 不影响原有流程
- **保持可插拔** - 完全独立的模块

---

**ExecutionPlanner实现完成！** 🎉

现在系统具备了：
- 统一的任务管理（TaskManager）
- 完整的记忆系统（MemorySystem）
- 智能的路由能力（IntelligentRouter）
- 结构化的上下文管理（ContextManager）
- 智能的执行规划（ExecutionPlanner）

还剩最后一个中优先级优化：FeedbackLoop（反馈循环）

