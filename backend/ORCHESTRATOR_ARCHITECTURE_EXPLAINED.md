# 编排器架构详解 - 循环控制在哪里？

## 你的困惑

你看到了多个编排器（react.py, multi_agent.py, workflow.py, simple.py），不知道：
1. 应该保留哪个？
2. 它们的区别是什么？
3. 工具调用的循环在哪里控制？

## 答案：循环控制的层次

### 核心发现：循环控制在两个层次

```
┌─────────────────────────────────────────────────────────────┐
│  第1层：编排器层（Orchestrator）                            │
│  ├─ simple.py      - 单Agent，无循环                        │
│  ├─ react.py       - 单Agent，无循环（依赖Agent内部循环）   │
│  ├─ workflow.py    - 多步骤，步骤间循环                     │
│  └─ multi_agent.py - 多Agent，Agent间循环                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  第2层：Agent层（BaseAgent）                                │
│  └─ agent.py 的 _call_llm_with_tools()                      │
│     - 工具调用循环（最多15次）                              │
│     - 这是真正的 ReAct 循环！                               │
└─────────────────────────────────────────────────────────────┘
```

## 详细解释

### 第1层：编排器层（任务级循环）

#### 1. SimpleOrchestrator（simple.py）
```python
# 最简单：调用一个Agent，带重试
async def execute(skill, user_input, context):
    for attempt in range(max_retries):  # ← 重试循环（不是工具循环）
        result = await agent.execute(...)
        if validate_result(result):
            return result
```

**特点**：
- 单Agent
- 只有重试循环（失败重试）
- 没有工具调用循环（依赖Agent内部）
- 适合：简单任务

---

#### 2. ReactOrchestrator（react.py）
```python
# 调用一个Agent，Agent内部有ReAct循环
async def execute(skill, user_input, context):
    agent = get_agent(skill.agent)
    result = await agent.execute(
        ...,
        tools=skill.tools,  # ← 传递工具
        max_tool_iterations=15  # ← Agent内部会循环15次
    )
    return result
```

**特点**：
- 单Agent
- 编排器层没有循环
- 工具调用循环在Agent内部（agent.py的_call_llm_with_tools）
- 适合：需要工具调用的单Agent任务

---

#### 3. WorkflowOrchestrator（workflow.py）
```python
# 多步骤工作流，步骤间循环
async def execute(skill, user_input, context):
    for step in workflow:  # ← 步骤循环
        # 检查依赖
        if not check_dependencies(step):
            continue
        
        # 执行步骤（可能带重试）
        result = await execute_step_with_retry(step)
        
        # 保存结果
        results[step.name] = result
        
        # 如果失败，回滚
        if not result.success:
            await rollback_steps(executed_steps)
            break
    
    return aggregate_results(results)
```

**特点**：
- 多步骤
- 步骤间循环（顺序执行）
- 每个步骤内部可能有工具调用循环（如果步骤调用的Agent使用工具）
- 支持依赖检查、回滚
- 适合：复杂的多步骤任务

---

#### 4. MultiAgentOrchestrator（multi_agent.py）
```python
# 多Agent协作，Agent间循环
async def execute(skill, user_input, context):
    agents = get_agents_from_skill(skill)
    
    if mode == 'sequential':
        # 顺序执行Agent
        for agent in agents:  # ← Agent循环
            result = await agent.execute(...)
            current_input = result.content  # 传递给下一个
    
    elif mode == 'parallel':
        # 并行执行Agent
        results = await asyncio.gather(*[
            agent.execute(...) for agent in agents
        ])
    
    elif mode == 'main_with_helpers':
        # 主Agent + 辅助Agent
        helper_results = await asyncio.gather(*[
            agent.execute(...) for agent in helper_agents
        ])
        main_result = await main_agent.execute(
            ...,
            context={'helper_results': helper_results}
        )
    
    return aggregate_results(results)
```

**特点**：
- 多Agent
- Agent间循环（sequential模式）或并行执行
- 每个Agent内部可能有工具调用循环
- 适合：需要多个专业Agent协作的任务

---

### 第2层：Agent层（工具调用循环）

#### BaseAgent._call_llm_with_tools()（agent.py）

这是真正的 ReAct 循环！

```python
async def _call_llm_with_tools(
    self,
    initial_messages,
    tool_names,
    max_iterations=15  # ← 最多15次工具调用
):
    messages = initial_messages.copy()
    tools_used = []
    
    # 工具调用循环（ReAct循环）
    for iteration in range(max_iterations):  # ← 这是核心循环！
        # 1. 调用LLM（带工具列表）
        response = await self._call_llm_with_functions(
            messages,
            function_schemas
        )
        
        # 2. 检查是否有工具调用
        function_call = response.get('function_call')
        
        if not function_call:
            # 没有工具调用，返回最终答案
            return response.content, tools_used
        
        # 3. 执行工具
        tool_name = function_call['name']
        tool_args = json.loads(function_call['arguments'])
        tool_result = await tool_registry.execute_tool(tool_name, **tool_args)
        
        # 4. 将工具结果添加到消息历史
        messages.append({
            "role": "assistant",
            "content": None,
            "function_call": function_call
        })
        messages.append({
            "role": "function",
            "name": tool_name,
            "content": str(tool_result.content)
        })
        
        # 5. 继续下一次循环（LLM看到工具结果后继续推理）
    
    # 达到最大迭代次数
    return final_response, tools_used
```

**这就是 ReAct 模式**：
1. **Reasoning**：LLM思考需要什么工具
2. **Action**：调用工具
3. **Observation**：观察工具结果
4. **重复**：继续推理，直到得出最终答案

---

## 架构总结

### 完整的调用链

```
用户请求："重构登录模块，添加测试"
    ↓
┌─────────────────────────────────────────────────────────┐
│ 编排器层（任务级）                                      │
│                                                         │
│ 选项1: SimpleOrchestrator                              │
│   └─ 调用 MainAgent                                    │
│       └─ Agent内部工具循环（15次）                     │
│                                                         │
│ 选项2: ReactOrchestrator                               │
│   └─ 调用 MainAgent（带工具）                          │
│       └─ Agent内部工具循环（15次）                     │
│                                                         │
│ 选项3: WorkflowOrchestrator                            │
│   ├─ 步骤1: 调用 CodeAnalyzer                          │
│   │   └─ Agent内部工具循环（15次）                     │
│   ├─ 步骤2: 调用 RefactorMaster                        │
│   │   └─ Agent内部工具循环（15次）                     │
│   └─ 步骤3: 调用 TestExpert                            │
│       └─ Agent内部工具循环（15次）                     │
│                                                         │
│ 选项4: MultiAgentOrchestrator                          │
│   ├─ 并行执行：                                        │
│   │   ├─ CodeAnalyzer → 工具循环（15次）               │
│   │   ├─ RefactorMaster → 工具循环（15次）             │
│   │   └─ TestExpert → 工具循环（15次）                 │
│   └─ 主Agent聚合结果                                   │
└─────────────────────────────────────────────────────────┘
```

---

## 应该保留哪些编排器？

### 全部保留！它们各有用途

| 编排器 | 用途 | 循环类型 | 何时使用 |
|--------|------|---------|---------|
| **simple** | 单Agent，简单任务 | 重试循环 | 翻译、格式化、简单问答 |
| **react** | 单Agent，工具调用 | Agent内部工具循环 | 需要工具的单Agent任务 |
| **workflow** | 多步骤工作流 | 步骤循环 + 工具循环 | 复杂的多步骤任务 |
| **multi_agent** | 多Agent协作 | Agent循环 + 工具循环 | 需要多专业领域协作 |

---

## 循环控制的最佳实践

### 1. 工具调用循环（Agent层）

**位置**：`agent.py` 的 `_call_llm_with_tools()`

**控制参数**：
```python
max_tool_iterations = 15  # 最多15次工具调用
```

**何时修改**：
- 简单任务：5-10次足够
- 复杂任务：15-20次
- 极复杂任务：20-30次（但要注意成本）

**配置方式**：
```yaml
# skills/my-skill/skill.yaml
llm:
  max_tool_iterations: 20  # 覆盖默认值
```

---

### 2. 步骤循环（Workflow层）

**位置**：`workflow.py` 的 `execute()`

**控制参数**：
```yaml
# skills/my-workflow/skill.yaml
workflow:
  - name: step1
    agent: analyzer
    max_retries: 3  # 步骤重试次数
    timeout: 30.0   # 步骤超时
  
  - name: step2
    agent: programmer
    depends_on: [step1]  # 依赖控制
```

---

### 3. Agent循环（MultiAgent层）

**位置**：`multi_agent.py` 的各种模式

**控制参数**：
```yaml
# skills/my-multi-agent/skill.yaml
orchestrator: multi_agent
collaboration_mode: sequential  # 或 parallel, main_with_helpers

agents:
  - agent1
  - agent2
  - agent3
```

---

## 推荐配置

### 配置1：简单任务（单Agent，无工具）

```yaml
# skills/simple-task/skill.yaml
orchestrator: simple
agent: translator

# 不需要工具
# Agent内部不会有工具循环
```

---

### 配置2：中等任务（单Agent，带工具）

```yaml
# skills/coding-task/skill.yaml
orchestrator: react  # 或 simple（效果相同）
agent: programmer

tools:
  - read_file
  - write_file
  - git_commit

llm:
  max_tool_iterations: 10  # Agent内部最多10次工具调用
```

---

### 配置3：复杂任务（多步骤工作流）

```yaml
# skills/complex-workflow/skill.yaml
orchestrator: workflow

workflow:
  - name: analyze
    agent: code_analyzer
    max_retries: 2
    timeout: 30.0
    # 这个Agent内部可能有工具循环
  
  - name: refactor
    agent: refactor_master
    depends_on: [analyze]
    input: ${results.analyze.content}
    # 这个Agent内部可能有工具循环
  
  - name: test
    agent: test_expert
    depends_on: [refactor]
    # 这个Agent内部可能有工具循环
```

---

### 配置4：极复杂任务（多Agent协作）

```yaml
# skills/sisyphus/skill.yaml
orchestrator: multi_agent
collaboration_mode: main_with_helpers

agents:
  - main_agent          # 主编排（工具循环：4个工具）
  - code_analyzer       # 辅助（工具循环：10个工具）
  - refactor_master     # 辅助（工具循环：13个工具）
  - test_expert         # 辅助（工具循环：10个工具）

# 每个Agent内部都有自己的工具循环
```

---

## 性能对比

### 工具调用次数估算

| 配置 | 编排器循环 | Agent数量 | 每Agent工具循环 | 总工具调用 |
|------|-----------|----------|----------------|-----------|
| 简单任务 | 0 | 1 | 0 | 0 |
| 中等任务 | 0 | 1 | 10 | 10 |
| 工作流 | 3步骤 | 3 | 10 | 30 |
| 多Agent | 0 | 4 | 10 | 40（并行） |

---

## 总结

### 核心答案

1. **循环控制在哪里？**
   - **工具调用循环**：在 `agent.py` 的 `_call_llm_with_tools()`（最多15次）
   - **步骤循环**：在 `workflow.py` 的 `execute()`
   - **Agent循环**：在 `multi_agent.py` 的各种模式

2. **应该保留哪些编排器？**
   - **全部保留**！它们各有用途，不冲突

3. **如何选择？**
   - 简单任务 → `simple`
   - 需要工具 → `react`（或`simple`，效果相同）
   - 多步骤 → `workflow`
   - 多Agent → `multi_agent`

4. **工具调用循环是编程向的核心**
   - 这是 ReAct 模式的实现
   - 在 Agent 层，不在编排器层
   - 所有编排器都可以利用这个循环（通过调用Agent）

### 最佳实践

1. **不要在编排器层实现工具循环**（已经在Agent层实现了）
2. **编排器层负责任务级的编排**（步骤、Agent）
3. **Agent层负责工具级的循环**（ReAct）
4. **根据任务复杂度选择合适的编排器**
5. **通过配置控制循环次数**（不要硬编码）

---

## 你的下一步

1. ✅ 理解了循环控制的层次
2. ✅ 知道了每个编排器的用途
3. ⏳ 选择一个编排器测试（建议从`react`开始）
4. ⏳ 根据任务类型选择合适的编排器
5. ⏳ 配置工具分组（参考之前的文档）
