# Context vs Memory：区别与协作

> 两个系统职责不同，互相配合

---

## 📊 核心区别

| 维度 | Context（上下文） | Memory（记忆） |
|------|------------------|---------------|
| **职责** | 任务执行期间的临时状态 | 长期存储的历史信息 |
| **生命周期** | 单次任务执行 | 跨任务、跨会话 |
| **数据类型** | 执行参数、中间结果、临时变量 | 对话历史、用户偏好、任务历史 |
| **可变性** | 频繁变化（每步都可能改） | 相对稳定（只在关键点保存） |
| **用途** | 传递执行状态 | 学习和回忆 |
| **快照** | 支持回滚（用于错误恢复） | 不支持回滚（历史记录） |

---

## 🎯 具体对比

### Context（上下文管理器）

**定位**：任务执行的"工作台"

**存储内容**：
```python
context = {
    # 执行参数
    'session_id': 'user123',
    'task_id': 'task456',
    'skill_name': 'code_analysis',
    
    # 中间结果
    'current_file': 'main.py',
    'analysis_result': {...},
    'step_counter': 3,
    
    # 临时变量
    'temp_data': [...],
    'processing_status': 'running',
    
    # 工具状态
    'last_tool_used': 'file_reader',
    'tool_results': [...]
}
```

**特点**：
- ✅ 支持快照和回滚（错误恢复）
- ✅ 支持嵌套（子任务继承父任务上下文）
- ✅ 追踪变更历史（调试用）
- ✅ 任务结束后可以丢弃

**使用场景**：
```python
# 1. 工作流编排器使用Context传递状态
orchestrator = WorkflowOrchestrator()

# 创建上下文
ctx = context_manager.create_context(session_id)
ctx.set('current_step', 1)
ctx.set('input_file', 'main.py')

# 步骤1：分析
ctx.create_snapshot('步骤1开始')
result1 = await agent1.execute(user_input, ctx.to_dict())
ctx.set('analysis_result', result1)

# 步骤2：规划（使用步骤1的结果）
ctx.set('current_step', 2)
result2 = await agent2.execute(user_input, ctx.to_dict())

# 如果步骤2失败，回滚到步骤1
if not result2.success:
    ctx.rollback_to_snapshot('步骤1开始')
```

---

### Memory（记忆系统）

**定位**：Agent的"大脑"

**存储内容**：
```python
memory = {
    # 对话历史（LLM层）
    'conversations': [
        {'user': '如何修复bug？', 'ai': '...', 'timestamp': '...'},
        {'user': '那如果是性能问题呢？', 'ai': '...', 'timestamp': '...'}
    ],
    
    # 用户偏好（Agent层）
    'preferences': {
        'preferred_language': 'python',
        'detail_level': 'high',
        'code_style': 'pep8'
    },
    
    # 任务历史（Agent层）
    'tasks': [
        {'description': '修复bug', 'success': True, 'timestamp': '...'},
        {'description': '优化性能', 'success': True, 'timestamp': '...'}
    ]
}
```

**特点**：
- ✅ 持久化存储（跨会话）
- ✅ 自动学习用户偏好
- ✅ 支持追问判断
- ✅ 多智能体共享
- ❌ 不支持回滚（历史是历史）

**使用场景**：
```python
# Agent自动使用Memory
class BaseAgent:
    def __init__(self):
        self.memory = get_memory_manager()  # 单例
    
    async def execute(self, user_input, context):
        session_id = context.get('session_id')
        user_id = context.get('user_id')
        
        # 1. 从记忆加载
        history = self.memory.get_conversation_history(session_id)
        prefs = self.memory.get_preferences(user_id)
        tasks = self.memory.get_task_history(user_id)
        
        # 2. 增强context（注意：这里是把Memory的数据放到Context中）
        context['conversation_history'] = history
        context['user_preferences'] = prefs
        context['recent_tasks'] = tasks
        
        # 3. 执行任务
        result = await self._call_llm(prompt, context)
        
        # 4. 保存到记忆
        self.memory.add_conversation(session_id, user_input, result)
        self.memory.add_task(user_id, task_data)
        self.memory.remember_preference(user_id, 'language', 'python')
        
        return result
```

---

## 🔄 协作关系

### 数据流向

```
┌─────────────────────────────────────────────────┐
│  用户请求                                        │
└────────────────┬────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────┐
│  Executor                                       │
│  1. 创建Context（临时工作台）                    │
│  2. 从Memory加载历史信息                         │
│  3. 将Memory数据放入Context                      │
└────────────────┬────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────┐
│  Orchestrator                                   │
│  - 使用Context传递状态                           │
│  - 创建快照（用于回滚）                          │
│  - 更新Context变量                               │
└────────────────┬────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────┐
│  Agent                                          │
│  - 从Context读取执行参数                         │
│  - 从Context读取Memory数据（历史、偏好）          │
│  - 执行任务                                      │
│  - 更新Context（中间结果）                        │
└────────────────┬────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────┐
│  执行完成                                        │
│  1. 将结果保存到Memory（对话、任务、偏好）        │
│  2. Context可以丢弃（或保留用于调试）             │
└─────────────────────────────────────────────────┘
```

### 典型协作场景

#### 场景1: 用户追问

```python
# 第1次请求
user_input_1 = "如何修复Python的bug？"

# 1. 创建Context
ctx = context_manager.create_context('session123')
ctx.set('session_id', 'session123')
ctx.set('user_id', 'user456')

# 2. Memory为空（首次对话）
history = memory.get_conversation_history('session123')  # []

# 3. Agent执行
result_1 = await agent.execute(user_input_1, ctx.to_dict())

# 4. 保存到Memory
memory.add_conversation('session123', user_input_1, result_1)
memory.remember_preference('user456', 'language', 'python')

# 5. Context丢弃
del ctx

# ========== 第2次请求（追问）==========

user_input_2 = "那如果是JavaScript呢？"

# 1. 创建新Context
ctx = context_manager.create_context('session123')
ctx.set('session_id', 'session123')
ctx.set('user_id', 'user456')

# 2. 从Memory加载历史
history = memory.get_conversation_history('session123')  # 有1轮对话
prefs = memory.get_preferences('user456')  # {'language': 'python'}

# 3. 判断追问
is_followup = await memory.is_followup('session123', user_input_2)  # True

# 4. 将Memory数据放入Context
ctx.set('conversation_history', history)
ctx.set('user_preferences', prefs)
ctx.set('is_followup', is_followup)

# 5. Agent执行（知道这是追问）
result_2 = await agent.execute(user_input_2, ctx.to_dict())

# 6. 保存到Memory
memory.add_conversation('session123', user_input_2, result_2)
memory.remember_preference('user456', 'language', 'javascript')  # 更新偏好
```

#### 场景2: 多步骤工作流

```python
# 工作流：分析 -> 规划 -> 执行

# 1. 创建Context（工作台）
ctx = context_manager.create_context('workflow_session')
ctx.set('session_id', 'session123')
ctx.set('user_id', 'user456')

# 2. 从Memory加载用户偏好
prefs = memory.get_preferences('user456')
ctx.set('user_preferences', prefs)

# 3. 步骤1：分析
ctx.set('current_step', 'analyze')
ctx.create_snapshot('分析开始')

result1 = await analyzer_agent.execute(user_input, ctx.to_dict())
ctx.set('analysis_result', result1)

# 4. 步骤2：规划（使用步骤1的结果）
ctx.set('current_step', 'plan')
ctx.create_snapshot('规划开始')

result2 = await planner_agent.execute(user_input, ctx.to_dict())
ctx.set('plan', result2)

# 5. 步骤3：执行（使用步骤1和2的结果）
ctx.set('current_step', 'execute')
ctx.create_snapshot('执行开始')

result3 = await executor_agent.execute(user_input, ctx.to_dict())

# 如果执行失败，可以回滚
if not result3.success:
    ctx.rollback_to_snapshot('规划开始')
    # 重新规划...

# 6. 保存到Memory（整个工作流的结果）
memory.add_conversation('session123', user_input, result3)
memory.add_task('user456', {
    'description': user_input,
    'steps': ['analyze', 'plan', 'execute'],
    'success': result3.success
})

# 7. Context可以丢弃
del ctx
```

---

## 🎯 使用原则

### 什么时候用Context？

✅ **任务执行期间的临时状态**
- 当前处理的文件
- 中间计算结果
- 步骤计数器
- 工具调用结果

✅ **需要回滚的场景**
- 多步骤工作流
- 试错性任务
- 需要错误恢复

✅ **需要嵌套的场景**
- 子任务继承父任务状态
- 并行任务隔离

### 什么时候用Memory？

✅ **需要跨任务记住的信息**
- 对话历史
- 用户偏好
- 任务历史

✅ **需要学习的信息**
- 用户习惯
- 常用工具
- 成功经验

✅ **需要共享的信息**
- 多智能体协作
- 跨会话信息

---

## 💡 最佳实践

### 1. Context传递Memory数据

```python
# ✅ 正确：Memory数据通过Context传递给Agent
ctx = context_manager.create_context(session_id)

# 从Memory加载
history = memory.get_conversation_history(session_id)
prefs = memory.get_preferences(user_id)

# 放入Context
ctx.set('conversation_history', history)
ctx.set('user_preferences', prefs)

# Agent从Context读取
result = await agent.execute(user_input, ctx.to_dict())
```

### 2. 任务结束后保存到Memory

```python
# ✅ 正确：执行完成后保存到Memory
result = await agent.execute(user_input, context)

# 保存对话
memory.add_conversation(session_id, user_input, result.content)

# 保存任务
memory.add_task(user_id, {
    'description': user_input,
    'success': result.success
})

# Context可以丢弃
```

### 3. 工作流使用Context快照

```python
# ✅ 正确：多步骤工作流使用Context快照
ctx = context_manager.create_context(session_id)

for step in workflow_steps:
    # 创建快照
    snapshot_id = ctx.create_snapshot(f'步骤{step}开始')
    
    # 执行步骤
    result = await execute_step(step, ctx)
    
    # 如果失败，回滚
    if not result.success:
        ctx.rollback_to_snapshot(snapshot_id)
        # 重试或跳过
```

---

## 🎉 总结

### Context（上下文）
- **定位**：任务执行的"工作台"
- **生命周期**：单次任务
- **特点**：临时、可变、可回滚
- **用途**：传递执行状态、错误恢复

### Memory（记忆）
- **定位**：Agent的"大脑"
- **生命周期**：长期持久
- **特点**：历史、学习、共享
- **用途**：记住对话、学习偏好、跨任务信息

### 协作关系
```
Memory（长期存储） → Context（临时工作台） → Agent执行 → Memory（保存结果）
```

**两者互补，缺一不可！**

- Context提供执行环境
- Memory提供历史知识
- 一起支撑Agent的智能行为

