# 编排器介绍

> DaoyouCode 7个内置编排器完整介绍

---

## ❓ 编排器的意义

很多人会问：**CLI传参是Skill，那编排器有什么意义？**

答案：**编排器决定Agent的协作方式！**

### 架构关系

```
CLI --skill sisyphus-orchestrator
    ↓
Skill配置文件
    ├─ orchestrator: multi_agent    ← 指定编排器
    ├─ agents: [sisyphus, ...]      ← 指定Agent列表
    └─ tools: [repo_map, ...]       ← 指定工具列表
    ↓
编排器（Orchestrator）
    ↓
协调Agent工作方式
    ├─ 顺序执行？并行执行？
    ├─ 如何重试？如何超时？
    └─ 如何聚合结果？
```

### 编排器的3大职责

1. **决定协作方式**
   - 顺序执行（sequential）
   - 并行执行（parallel）
   - 辩论模式（debate）
   - 主从协作（main_with_helpers）

2. **控制执行流程**
   - 重试机制（失败后重试）
   - 超时控制（避免卡死）
   - 失败回滚（恢复状态）

3. **管理结果聚合**
   - 如何组合多个Agent的输出
   - 如何处理冲突
   - 如何生成最终答案

### 举例说明

**同样的Agent列表，不同的编排器，结果完全不同**：

```yaml
# 配置1：使用simple编排器
orchestrator: simple
agents:
  - programmer
# 结果：只执行programmer，其他Agent被忽略

# 配置2：使用multi_agent编排器（顺序模式）
orchestrator: multi_agent
collaboration_mode: sequential
agents:
  - code_analyzer
  - programmer
  - test_expert
# 结果：code_analyzer → programmer → test_expert（顺序执行）

# 配置3：使用multi_agent编排器（并行模式）
orchestrator: multi_agent
collaboration_mode: parallel
agents:
  - code_analyzer
  - programmer
  - test_expert
# 结果：3个Agent同时执行，然后聚合结果

# 配置4：使用multi_agent编排器（主从模式）
orchestrator: multi_agent
collaboration_mode: main_with_helpers
agents:
  - sisyphus        # 主Agent
  - code_analyzer   # 辅助Agent
  - programmer      # 辅助Agent
# 结果：辅助Agent先执行，主Agent看到结果后决策
```

**所以编排器的意义是**：
- ✅ 不是简单地"调用Agent"
- ✅ 而是"如何协调多个Agent工作"
- ✅ 决定了系统的智能程度和效率

---

## 编排器总览

| 编排器 | Agent数 | 复杂度 | 特点 |
|--------|---------|--------|------|
| simple | 1 | LOW | 简单编排，单Agent顺序执行 |
| react | 1 | MEDIUM | ReAct模式，推理-行动循环 |
| multi_agent | 多个 | HIGH | 多Agent协作，4种协作模式 |
| workflow | 多个 | MEDIUM | 工作流编排，预定义步骤 |
| parallel | 多个 | MEDIUM | 并行执行，多任务同时 |
| parallel_explore | 多个 | HIGH | 并行探索，多路径尝试 |
| conditional | 多个 | MEDIUM | 条件编排，根据条件选择路径 |

---

## 核心编排器详解

### 1. Simple - 简单编排器

**功能**：
- 直接执行单个Agent
- 自动重试机制
- 结果验证
- 成本追踪

**特点**：
- 最简单的编排器
- 适合单一任务
- 支持重试（最多3次）
- 自动验证结果

**使用场景**：
- 简单任务
- 单一Agent即可完成
- 不需要多Agent协作

**配置示例**：
```yaml
orchestrator: simple
agent: programmer
max_retries: 3
retry_delay: 1.0
```

**工作流程**：
```
用户输入 → Agent执行 → 结果验证 → 返回结果
         ↑_____________↓ (失败重试)
```

---

### 2. ReAct - ReAct循环编排器

**功能**：
- Reason（推理）：分析任务
- Act（行动）：执行工具
- Observe（观察）：检查结果
- Reflect（反思）：调整策略

**特点**：
- LLM自动控制循环
- 无需额外规划步骤
- 成本低，效率高
- 适合需要工具调用的任务

**使用场景**：
- 需要工具调用
- 需要多步推理
- 需要动态调整策略

**配置示例**：
```yaml
orchestrator: react
agent: programmer
tools:
  - read_file
  - write_file
  - lsp_diagnostics
```

**工作流程**：
```
用户输入 → LLM分析 → 调用工具 → 观察结果 → LLM决定下一步
         ↑_______________________________________↓ (循环)
```

**核心逻辑**：
- ReAct循环的核心逻辑在Agent层实现（通过Function Calling）
- LLM自动决定是否调用工具
- 编排器只负责调用Agent和处理结果

---

### 3. MultiAgent - 多Agent编排器

**功能**：
- 支持4种协作模式
- 智能Agent选择
- 结果聚合
- 共享记忆

**4种协作模式**：

#### 3.1 Sequential（顺序执行）
- 每个Agent处理前一个的输出
- 适合需要逐步处理的任务

```
Agent1 → Agent2 → Agent3 → 最终结果
```

#### 3.2 Parallel（并行执行）
- 所有Agent同时处理相同输入
- 适合独立任务可并行

```
        ┌→ Agent1 ┐
输入 → ├→ Agent2 ├→ 聚合结果
        └→ Agent3 ┘
```

#### 3.3 Debate（辩论模式）
- Agent之间进行多轮讨论
- 使用共享记忆
- 适合需要多角度分析

```
轮1: Agent1观点 ← Agent2观点 ← Agent3观点
轮2: Agent1观点 ← Agent2观点 ← Agent3观点
轮3: Agent1观点 ← Agent2观点 ← Agent3观点
     ↓
   综合结论
```

#### 3.4 MainWithHelpers（主Agent + 辅助Agent）
- 第一个Agent是主Agent
- 其他Agent是辅助Agent
- 主Agent可以看到辅助Agent的结果

```
        ┌→ Helper1 ┐
输入 → ├→ Helper2 ├→ MainAgent → 最终结果
        └→ Helper3 ┘
```

**使用场景**：
- 复杂任务需要多个专业Agent
- 需要多角度分析
- 需要Agent协作

**配置示例**：
```yaml
orchestrator: multi_agent
collaboration_mode: main_with_helpers
agents:
  - sisyphus        # 主Agent
  - code_analyzer   # 辅助Agent
  - programmer      # 辅助Agent
  - refactor_master # 辅助Agent
  - test_expert     # 辅助Agent
```

---

### 4. Workflow - 工作流编排器

**功能**：
- 按步骤执行
- 步骤依赖检查
- 条件分支
- 失败回滚
- 步骤超时和重试

**特点**：
- 预定义步骤
- 支持依赖关系
- 支持条件执行
- 支持回滚

**使用场景**：
- 固定流程的任务
- 需要步骤依赖
- 需要条件分支
- 需要失败回滚

**配置示例**：
```yaml
orchestrator: workflow
workflow:
  - name: analyze
    agent: code_analyzer
    output: analysis_result
    max_retries: 3
    timeout: 30.0
  
  - name: implement
    agent: programmer
    depends_on: [analyze]
    input: ${analysis_result}
    condition: ${analysis_result.feasible}
    output: code_changes
    rollback: cleanup_agent
  
  - name: test
    agent: test_expert
    depends_on: [implement]
    input: ${code_changes}
```

**工作流程**：
```
Step1 → Step2 → Step3 → 成功
  ↓       ↓       ↓
失败 → 回滚 ← 回滚 ← 失败
```

---

### 5. Parallel - 并行编排器

**功能**：
- LLM智能任务拆分
- 并行执行多个任务
- LLM智能结果聚合
- 批量执行控制

**特点**：
- 自动拆分任务
- 并行执行提高效率
- 智能聚合结果
- 支持批量控制

**使用场景**：
- 独立任务可并行
- 需要提高执行效率
- 需要智能任务拆分

**配置示例**：
```yaml
orchestrator: parallel
use_llm_split: true        # 使用LLM智能拆分
use_llm_aggregate: true    # 使用LLM智能聚合
batch_size: 3              # 批量大小
timeout: 60.0              # 超时时间
```

**工作流程**：
```
用户输入 → LLM拆分任务 → 并行执行 → LLM聚合结果
                ↓
        ┌→ Task1 (Agent1)
        ├→ Task2 (Agent2)
        └→ Task3 (Agent3)
```

---

### 6. ParallelExplore - 并行探索编排器

**功能**：
- 多路径同时尝试
- 自动选择最佳结果
- 探索性任务
- 智能评分和排序

**特点**：
- 同时尝试多种方案
- 自动评分和选择
- 适合探索性任务
- 支持提前停止（找到满意方案）

**使用场景**：
- 探索性任务（不确定最佳方案）
- 需要多种方案对比
- 需要快速找到可行方案
- 创意性任务（多个角度）

**配置示例**：
```yaml
orchestrator: parallel_explore
agents:
  - programmer          # 方案1：传统实现
  - refactor_master     # 方案2：重构优化
  - test_expert         # 方案3：测试驱动
batch_size: 3           # 批量大小
timeout: 60.0           # 超时时间
```

**工作流程**：
```
用户输入 → 并行执行多个方案 → 评分排序 → 选择最佳
                ↓
        ┌→ 方案1 (Agent1) → 评分: 8.5
        ├→ 方案2 (Agent2) → 评分: 9.2 ← 最佳
        └→ 方案3 (Agent3) → 评分: 7.8
```

**实际案例**：
```yaml
# skills/explore-solution/skill.yaml
name: explore-solution
orchestrator: parallel_explore
agents:
  - name: traditional
    description: 传统实现方案
  - name: modern
    description: 现代化方案
  - name: performance
    description: 性能优化方案
```

**评分标准**：
- 代码质量
- 性能表现
- 可维护性
- 测试覆盖率

---

### 7. Conditional - 条件编排器

**功能**：
- 根据条件选择路径
- 动态决策
- 条件分支
- 支持复杂条件表达式

**特点**：
- 支持条件判断（`${variable} == value`）
- 动态选择Agent
- 灵活的分支逻辑
- 支持默认分支
- 支持嵌套条件

**使用场景**：
- 需要条件判断（根据输入选择不同Agent）
- 需要动态选择Agent（根据上下文）
- 需要分支逻辑（if-else）
- 需要多路分支（switch-case）

**配置示例**：

#### 简单模式（二选一）：
```yaml
orchestrator: conditional
condition: ${context.language} == 'python'
if_path:
  agent: python_expert
else_path:
  agent: general_programmer
```

#### 多路分支模式：
```yaml
orchestrator: conditional
conditions:
  - condition: ${context.language} == 'python'
    path:
      agent: python_expert
  
  - condition: ${context.language} == 'javascript'
    path:
      agent: js_expert
  
  - condition: ${context.language} == 'rust'
    path:
      agent: rust_expert
  
  - default: true
    path:
      agent: general_programmer
```

**工作流程**：
```
用户输入 → 评估条件 → 选择路径 → 执行Agent
    ↓
条件1: language == 'python' → Python专家
条件2: language == 'javascript' → JS专家
条件3: language == 'rust' → Rust专家
默认: → 通用程序员
```

**实际案例**：
```yaml
# skills/language-specific/skill.yaml
name: language-specific
orchestrator: conditional
conditions:
  - condition: ${task_type} == "refactor"
    path:
      agent: refactor_master
      tools: [ast_grep_search, ast_grep_replace]
  
  - condition: ${task_type} == "test"
    path:
      agent: test_expert
      tools: [run_test, lsp_diagnostics]
  
  - condition: ${task_type} == "debug"
    path:
      agent: debugger
      tools: [lsp_diagnostics, lsp_goto_definition]
  
  - default: true
    path:
      agent: programmer
      tools: [read_file, write_file]
```

**条件表达式语法**：
```python
# 支持的操作符
${variable} == "value"     # 等于
${variable} != "value"     # 不等于
${variable} > 10           # 大于
${variable} < 10           # 小于
${variable} >= 10          # 大于等于
${variable} <= 10          # 小于等于

# 支持的变量
${context.language}        # 上下文变量
${context.task_type}       # 任务类型
${context.user_input}      # 用户输入
${result.success}          # 前一步结果
```

---

## 编排器选择指南

### 按任务复杂度选择

| 复杂度 | 推荐编排器 | 原因 |
|--------|-----------|------|
| 简单 | simple | 单Agent即可 |
| 中等 | react | 需要工具调用 |
| 复杂 | multi_agent | 需要多Agent协作 |
| 很复杂 | workflow | 需要步骤控制 |

### 按Agent数量选择

| Agent数 | 推荐编排器 | 说明 |
|---------|-----------|------|
| 1个 | simple, react | 单Agent编排 |
| 2-5个 | multi_agent, parallel | 多Agent协作 |
| 5+个 | workflow | 需要步骤控制 |

### 按协作模式选择

| 协作模式 | 推荐编排器 | 说明 |
|---------|-----------|------|
| 顺序执行 | multi_agent (sequential) | 逐步处理 |
| 并行执行 | multi_agent (parallel), parallel | 同时处理 |
| 辩论讨论 | multi_agent (debate) | 多角度分析 |
| 主从协作 | multi_agent (main_with_helpers) | 主Agent调度 |
| 工作流 | workflow | 预定义步骤 |

---

## 编排器对比

| 特性 | simple | react | multi_agent | workflow | parallel |
|------|--------|-------|-------------|----------|----------|
| Agent数 | 1 | 1 | 多个 | 多个 | 多个 |
| 工具调用 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 重试机制 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 结果验证 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 协作模式 | - | - | 4种 | - | - |
| 步骤控制 | - | - | - | ✅ | - |
| 并行执行 | - | - | ✅ | - | ✅ |
| 条件分支 | - | - | - | ✅ | - |
| 失败回滚 | - | - | - | ✅ | - |
| LLM拆分 | - | - | - | - | ✅ |
| 复杂度 | LOW | MEDIUM | HIGH | MEDIUM | MEDIUM |

---

## 使用建议

### 1. 新手推荐
- 从simple开始
- 熟悉后使用react
- 最后尝试multi_agent

### 2. 性能优化
- 简单任务用simple（最快）
- 需要工具用react（高效）
- 并行任务用parallel（提速）

### 3. 成本控制
- simple成本最低（单次调用）
- react成本中等（多次调用）
- multi_agent成本较高（多Agent）
- workflow成本可控（按步骤）

### 4. 可靠性
- simple最可靠（简单）
- react较可靠（自动重试）
- multi_agent可靠（多Agent验证）
- workflow最可靠（回滚机制）

---

## 相关文档

- [CLI命令参考.md](./CLI命令参考.md) - CLI使用指南
- [AGENTS智能体介绍.md](./AGENTS智能体介绍.md) - Agent详细介绍
- [TOOLS工具参考.md](./TOOLS工具参考.md) - 工具参考手册
- [编排器检查报告.md](./编排器检查报告.md) - 编排器质量检查

---

## FAQ

### Q1: 如何选择合适的编排器？

**A**: 根据任务复杂度和Agent数量：
- 1个Agent + 简单任务 → `simple`
- 1个Agent + 需要工具 → `react`
- 多个Agent + 顺序执行 → `multi_agent` (sequential)
- 多个Agent + 并行执行 → `parallel`
- 多个Agent + 固定流程 → `workflow`
- 多个Agent + 条件分支 → `conditional`
- 多个Agent + 探索方案 → `parallel_explore`

### Q2: 编排器可以嵌套吗？

**A**: 可以！例如：
```yaml
# 外层：workflow
orchestrator: workflow
workflow:
  - name: step1
    # 内层：multi_agent
    orchestrator: multi_agent
    agents: [agent1, agent2]
  
  - name: step2
    # 内层：parallel
    orchestrator: parallel
    agents: [agent3, agent4]
```

### Q3: 如何调试编排器？

**A**: 
1. 查看日志：`--verbose` 参数
2. 检查元数据：结果中的 `metadata` 字段
3. 使用简单编排器测试：先用 `simple` 测试单个Agent
4. 逐步增加复杂度：simple → react → multi_agent

### Q4: 编排器的性能如何？

**A**: 
- `simple`: 最快（单次调用）
- `react`: 中等（多次调用，但智能）
- `parallel`: 快（并行执行）
- `multi_agent`: 较慢（多Agent顺序）
- `workflow`: 可控（按步骤）

### Q5: 编排器的成本如何？

**A**: 
- `simple`: 最低（1次LLM调用）
- `react`: 中等（3-10次LLM调用）
- `multi_agent`: 较高（N个Agent × M次调用）
- `parallel`: 中等（并行但多Agent）
- `workflow`: 可控（按步骤计费）

### Q6: 哪个编排器最可靠？

**A**: 
1. `workflow` - 有回滚机制
2. `multi_agent` - 多Agent验证
3. `react` - 自动重试
4. `simple` - 简单可靠

### Q7: 如何处理编排器超时？

**A**: 
```yaml
# 方式1：在Skill中配置
orchestrator: react
timeout: 300  # 5分钟

# 方式2：在CLI中配置
daoyou --skill my-skill --timeout 300
```

### Q8: 编排器可以自定义吗？

**A**: 可以！创建自定义编排器：
```python
from daoyoucode.agents.core.orchestrator import BaseOrchestrator

class MyOrchestrator(BaseOrchestrator):
    async def execute(self, skill, user_input, context):
        # 自定义逻辑
        pass

# 注册
from daoyoucode.agents.core.orchestrator import register_orchestrator
register_orchestrator('my_orchestrator', MyOrchestrator)
```

---

## 完整对比表

| 特性 | simple | react | multi_agent | workflow | parallel | parallel_explore | conditional |
|------|--------|-------|-------------|----------|----------|------------------|-------------|
| **基本信息** |
| Agent数量 | 1 | 1 | 多个 | 多个 | 多个 | 多个 | 多个 |
| 复杂度 | LOW | MEDIUM | HIGH | MEDIUM | MEDIUM | HIGH | MEDIUM |
| 学习曲线 | 简单 | 中等 | 较难 | 中等 | 中等 | 较难 | 中等 |
| **功能特性** |
| 工具调用 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 重试机制 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 结果验证 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 超时控制 | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ |
| 协作模式 | - | - | 4种 | - | - | - | - |
| 步骤控制 | - | - | - | ✅ | - | - | - |
| 并行执行 | - | - | ✅ | - | ✅ | ✅ | - |
| 条件分支 | - | - | - | ✅ | - | - | ✅ |
| 失败回滚 | - | - | - | ✅ | - | - | - |
| LLM拆分 | - | - | - | - | ✅ | - | - |
| 智能评分 | - | - | - | - | - | ✅ | - |
| **性能指标** |
| 执行速度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| 成本 | ⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| 可靠性 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| 灵活性 | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **适用场景** |
| 简单任务 | ✅ | ✅ | - | - | - | - | - |
| 工具调用 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 多Agent协作 | - | - | ✅ | ✅ | ✅ | ✅ | ✅ |
| 固定流程 | - | - | - | ✅ | - | - | - |
| 探索性任务 | - | ✅ | - | - | - | ✅ | - |
| 条件分支 | - | - | - | ✅ | - | - | ✅ |
| 并行加速 | - | - | ✅ | - | ✅ | ✅ | - |

---

## 更新日志

### 2026-02-18
- ✅ 补充了ParallelExplore的详细介绍
- ✅ 补充了Conditional的详细介绍
- ✅ 添加了完整对比表
- ✅ 添加了FAQ部分
- ✅ 添加了实际案例
- ✅ 添加了条件表达式语法说明
