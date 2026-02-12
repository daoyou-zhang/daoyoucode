# ContextManager 实现完成

> 结构化的上下文管理系统

---

## ✅ 完成的工作

### 核心实现

**文件**: `backend/daoyoucode/agents/core/context.py`

**关键组件**:

#### 1. Context（上下文）

```python
class Context:
    """结构化上下文"""
    
    # 变量管理
    def set(key, value)
    def get(key, default=None)
    def delete(key)
    def has(key)
    def update(variables)
    def clear()
    
    # 快照和回滚
    def create_snapshot(description) -> snapshot_id
    def rollback_to_snapshot(snapshot_id)
    def list_snapshots()
    
    # 变更历史
    def get_history(limit)
    def get_changes_for_key(key)
    
    # 嵌套上下文
    def create_child() -> Context
```

**功能**:
- ✅ 变量管理（set/get/delete/has）
- ✅ 批量操作（update/clear）
- ✅ 快照和回滚（错误恢复）
- ✅ 变更历史追踪（调试用）
- ✅ 嵌套上下文（子任务继承父任务）
- ✅ 父子上下文变量查找

#### 2. ContextManager（上下文管理器）

```python
class ContextManager:
    """上下文管理器（单例）"""
    
    def create_context(session_id, parent_session_id)
    def get_context(session_id)
    def get_or_create_context(session_id)
    def delete_context(session_id)
    def list_contexts()
    def get_stats()
```

**功能**:
- ✅ 多会话管理
- ✅ 上下文创建和销毁
- ✅ 自动清理旧上下文
- ✅ 统计信息
- ✅ 单例模式

---

## 📊 核心特性

### 1. 变量管理 ✅

```python
ctx = context_manager.create_context('session1')

# 设置变量
ctx.set('user_name', 'Alice')
ctx.set('user_age', 25)

# 获取变量
name = ctx.get('user_name')  # 'Alice'
age = ctx.get('user_age')    # 25

# 检查存在
ctx.has('user_name')  # True

# 更新变量
ctx.set('user_age', 26)

# 删除变量
ctx.delete('user_name')

# 批量更新
ctx.update({
    'var1': 'value1',
    'var2': 'value2'
})

# 清空
ctx.clear()
```

### 2. 快照和回滚 ✅

```python
ctx = context_manager.create_context('session1')

# 初始状态
ctx.set('counter', 0)
ctx.set('status', 'init')

# 创建快照
snapshot1 = ctx.create_snapshot('初始状态')

# 修改状态
ctx.set('counter', 10)
ctx.set('status', 'running')

# 创建另一个快照
snapshot2 = ctx.create_snapshot('运行状态')

# 继续修改
ctx.set('counter', 20)

# 回滚到快照1
ctx.rollback_to_snapshot(snapshot1)
# 现在 counter=0, status='init'

# 列出所有快照
snapshots = ctx.list_snapshots()
```

**用途**：
- 错误恢复
- 试错性任务
- 多步骤工作流的回滚

### 3. 变更历史 ✅

```python
ctx = context_manager.create_context('session1')

# 执行操作
ctx.set('x', 1)      # set
ctx.set('x', 10)     # update
ctx.delete('x')      # delete

# 获取历史
history = ctx.get_history()
# [
#   {'key': 'x', 'operation': 'set', 'old_value': None, 'new_value': 1},
#   {'key': 'x', 'operation': 'update', 'old_value': 1, 'new_value': 10},
#   {'key': 'x', 'operation': 'delete', 'old_value': 10, 'new_value': None}
# ]

# 获取特定变量的历史
x_history = ctx.get_changes_for_key('x')
```

**用途**：
- 调试
- 审计
- 理解状态变化

### 4. 嵌套上下文 ✅

```python
# 创建父上下文
parent = context_manager.create_context('parent')
parent.set('global_var', 'global_value')
parent.set('parent_var', 'parent_value')

# 创建子上下文
child = parent.create_child()
child.set('child_var', 'child_value')
child.set('parent_var', 'overridden')  # 覆盖父变量

# 子上下文可以访问父变量
child.get('global_var')  # 'global_value'

# 子上下文覆盖父变量
child.get('parent_var')   # 'overridden'
parent.get('parent_var')  # 'parent_value' (不受影响)

# 子变量不影响父上下文
parent.has('child_var')  # False
```

**用途**：
- 子任务继承父任务状态
- 并行任务隔离
- 作用域管理

---

## 🔄 与Memory的协作

### Context vs Memory

| 维度 | Context | Memory |
|------|---------|--------|
| 职责 | 任务执行期间的临时状态 | 长期存储的历史信息 |
| 生命周期 | 单次任务 | 跨任务、跨会话 |
| 可回滚 | ✅ 支持 | ❌ 不支持 |

### 协作模式

```python
# 1. 创建Context
ctx = context_manager.create_context(session_id)

# 2. 从Memory加载历史
memory = get_memory_manager()
history = memory.get_conversation_history(session_id)
prefs = memory.get_preferences(user_id)

# 3. 将Memory数据放入Context
ctx.set('conversation_history', history)
ctx.set('user_preferences', prefs)

# 4. Agent从Context读取
result = await agent.execute(user_input, ctx.to_dict())

# 5. 保存到Memory
memory.add_conversation(session_id, user_input, result)

# 6. Context可以丢弃
del ctx
```

详见：`CONTEXT_VS_MEMORY.md`

---

## 💡 使用场景

### 场景1: 多步骤工作流

```python
# 工作流：分析 -> 规划 -> 执行

ctx = context_manager.create_context('workflow_session')

# 步骤1：分析
ctx.set('current_step', 'analyze')
ctx.create_snapshot('分析开始')

result1 = await analyzer.execute(input, ctx.to_dict())
ctx.set('analysis_result', result1)

# 步骤2：规划
ctx.set('current_step', 'plan')
ctx.create_snapshot('规划开始')

result2 = await planner.execute(input, ctx.to_dict())
ctx.set('plan', result2)

# 步骤3：执行
ctx.set('current_step', 'execute')
result3 = await executor.execute(input, ctx.to_dict())

# 如果失败，回滚到规划阶段
if not result3.success:
    ctx.rollback_to_snapshot('规划开始')
    # 重新规划...
```

### 场景2: 并行任务隔离

```python
# 父上下文
parent = context_manager.create_context('parallel_session')
parent.set('global_config', config)

# 创建多个子上下文（隔离）
tasks = []
for i in range(5):
    child = parent.create_child()
    child.set('task_id', i)
    tasks.append(execute_task(child))

# 并行执行（互不干扰）
results = await asyncio.gather(*tasks)
```

### 场景3: 试错性任务

```python
ctx = context_manager.create_context('trial_session')

strategies = ['strategy_a', 'strategy_b', 'strategy_c']

for strategy in strategies:
    # 创建快照
    snapshot = ctx.create_snapshot(f'尝试{strategy}')
    
    # 尝试策略
    ctx.set('current_strategy', strategy)
    result = await try_strategy(strategy, ctx)
    
    if result.success:
        break  # 成功，保留当前状态
    else:
        # 失败，回滚
        ctx.rollback_to_snapshot(snapshot)
```

### 场景4: 调试和审计

```python
ctx = context_manager.create_context('debug_session')

# 执行任务
await execute_complex_task(ctx)

# 查看变更历史
history = ctx.get_history()
for change in history:
    print(f"{change['operation']}: {change['key']} = {change['new_value']}")

# 查看特定变量的变化
status_changes = ctx.get_changes_for_key('status')
```

---

## 📝 测试结果

**文件**: `backend/test_context_manager.py`

**测试场景**:
- ✅ 基本上下文操作（set/get/delete/has）
- ✅ 快照和回滚
- ✅ 变更历史
- ✅ 嵌套上下文
- ✅ 批量操作
- ✅ 上下文管理器
- ✅ 快照数量限制
- ✅ 单例模式

**所有测试通过！** ✅

---

## 🎯 核心优势

### 1. 结构化管理 ✅

不再是简单的Dict，而是有生命周期管理的结构化对象：
- 变量追踪
- 历史记录
- 快照回滚

### 2. 错误恢复 ✅

支持快照和回滚，适合：
- 多步骤工作流
- 试错性任务
- 需要撤销的场景

### 3. 嵌套隔离 ✅

支持父子上下文：
- 子任务继承父任务状态
- 子任务修改不影响父任务
- 并行任务隔离

### 4. 调试友好 ✅

完整的变更历史：
- 追踪每个变量的变化
- 了解状态演变过程
- 审计和调试

---

## 🔄 与其他模块的集成

### 1. 与Executor集成

```python
# Executor可以使用Context管理执行状态
async def execute_skill(skill_name, user_input, session_id):
    # 创建Context
    ctx_manager = get_context_manager()
    ctx = ctx_manager.get_or_create_context(session_id)
    
    # 设置执行参数
    ctx.set('skill_name', skill_name)
    ctx.set('user_input', user_input)
    
    # 从Memory加载
    memory = get_memory_manager()
    history = memory.get_conversation_history(session_id)
    ctx.set('conversation_history', history)
    
    # 执行
    result = await orchestrator.execute(skill, user_input, ctx.to_dict())
    
    return result
```

### 2. 与Orchestrator集成

```python
# Orchestrator使用Context传递状态
class WorkflowOrchestrator:
    async def execute(self, skill, user_input, context):
        # 获取Context对象
        ctx_manager = get_context_manager()
        session_id = context.get('session_id')
        ctx = ctx_manager.get_or_create_context(session_id)
        
        # 更新Context
        ctx.update(context)
        
        # 多步骤执行
        for step in workflow_steps:
            ctx.create_snapshot(f'步骤{step}')
            result = await execute_step(step, ctx.to_dict())
            
            if not result.success:
                ctx.rollback_to_snapshot(f'步骤{step}')
                # 重试...
        
        return result
```

---

## 🎉 总结

### 完成的功能

1. ✅ **Context** - 结构化上下文对象
2. ✅ **ContextManager** - 上下文管理器
3. ✅ **快照和回滚** - 错误恢复机制
4. ✅ **变更历史** - 调试和审计
5. ✅ **嵌套上下文** - 父子关系和隔离
6. ✅ **单例模式** - 全局唯一实例

### 核心价值

- **结构化** - 不再是简单Dict
- **可回滚** - 支持错误恢复
- **可追踪** - 完整变更历史
- **可嵌套** - 支持复杂场景

### 与Memory的关系

- **Context** - 任务执行的"工作台"（临时）
- **Memory** - Agent的"大脑"（长期）
- **协作** - Memory数据通过Context传递给Agent

---

**ContextManager实现完成！** 🎉

现在系统具备了：
- 统一的任务管理（TaskManager）
- 完整的记忆系统（MemorySystem）
- 智能的路由能力（IntelligentRouter）
- 结构化的上下文管理（ContextManager）

可以继续实施下一个中优先级优化！

