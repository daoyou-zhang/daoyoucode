# 编排器选择决策指南

## 快速决策流程图

```
开始：我有一个任务
    ↓
┌─────────────────────────────────────┐
│ 问题1：需要调用工具吗？             │
└─────────────────────────────────────┘
    ↓
    ├─ 不需要 → 使用 simple
    │   示例：翻译、格式化、纯对话
    │
    └─ 需要 → 继续
        ↓
┌─────────────────────────────────────┐
│ 问题2：需要多个步骤吗？             │
└─────────────────────────────────────┘
    ↓
    ├─ 不需要（单步骤）→ 继续
    │   ↓
    │   ┌─────────────────────────────────────┐
    │   │ 问题3：需要多个Agent吗？            │
    │   └─────────────────────────────────────┘
    │       ↓
    │       ├─ 不需要 → 使用 react
    │       │   示例：代码编写、Bug修复
    │       │
    │       └─ 需要 → 使用 multi_agent
    │           示例：需要多个专业领域
    │
    └─ 需要（多步骤）→ 使用 workflow
        示例：分析→重构→测试→验证
```

---

## 详细决策表

| 特征 | simple | react | workflow | multi_agent |
|------|--------|-------|----------|-------------|
| **工具调用** | ❌ | ✅ | ✅ | ✅ |
| **Agent数量** | 1 | 1 | 1-N | 2-N |
| **步骤数量** | 1 | 1 | 2-N | 1 |
| **并行执行** | ❌ | ❌ | ❌ | ✅ |
| **依赖管理** | ❌ | ❌ | ✅ | ✅ |
| **回滚支持** | ❌ | ❌ | ✅ | ❌ |
| **复杂度** | ⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **成本** | 低 | 中 | 高 | 高 |

---

## 实际场景示例

### 场景1：文档翻译

**需求**：将README.md翻译成中文

**分析**：
- ❌ 不需要工具
- ✅ 单步骤
- ✅ 单Agent

**选择**：`simple`

```yaml
orchestrator: simple
agent: translator
```

---

### 场景2：Bug修复

**需求**：修复登录验证的Bug

**分析**：
- ✅ 需要工具（read_file, write_file, git_commit）
- ✅ 单步骤
- ✅ 单Agent

**选择**：`react`

```yaml
orchestrator: react
agent: programmer
tools:
  - read_file
  - write_file
  - text_search
  - git_commit
```

---

### 场景3：完整功能开发

**需求**：添加邮件验证功能（分析→设计→实现→测试）

**分析**：
- ✅ 需要工具
- ✅ 多步骤（有依赖关系）
- ✅ 可以用单Agent或多Agent

**选择**：`workflow`

```yaml
orchestrator: workflow
workflow:
  - name: analyze
    agent: code_analyzer
    output: analysis
  
  - name: design
    agent: code_analyzer
    depends_on: [analyze]
    input: ${results.analysis.content}
    output: design
  
  - name: implement
    agent: programmer
    depends_on: [design]
    input: ${results.design.content}
    output: code
  
  - name: test
    agent: test_expert
    depends_on: [implement]
    input: ${results.code.content}
```

---

### 场景4：技术决策

**需求**：评估微服务架构迁移方案（需要多个专业视角）

**分析**：
- ✅ 需要工具（分析代码）
- ✅ 单步骤（但需要多角度）
- ✅ 多Agent（架构、性能、测试、实施）

**选择**：`multi_agent`（parallel模式）

```yaml
orchestrator: multi_agent
collaboration_mode: parallel

agents:
  - code_analyzer       # 架构分析
  - refactor_master     # 重构可行性
  - test_expert         # 测试策略
  - programmer          # 实施难度
```

---

### 场景5：复杂重构

**需求**：重构登录模块（需要分析、重构、测试、验证）

**分析**：
- ✅ 需要工具
- ✅ 多步骤（有依赖）
- ✅ 多Agent（不同专业领域）

**选择**：`workflow` + 多Agent

```yaml
orchestrator: workflow
workflow:
  - name: analyze
    agent: code_analyzer
  
  - name: refactor
    agent: refactor_master
    depends_on: [analyze]
  
  - name: test
    agent: test_expert
    depends_on: [refactor]
  
  - name: verify
    agent: code_analyzer
    depends_on: [test]
```

或者使用 `multi_agent`（sequential模式）：

```yaml
orchestrator: multi_agent
collaboration_mode: sequential

agents:
  - code_analyzer
  - refactor_master
  - test_expert
  - code_analyzer
```

---

## 编排器对比

### simple vs react

**相同点**：
- 都是单Agent
- 都是单步骤

**不同点**：
- `simple`：不传递工具，Agent不会调用工具
- `react`：传递工具，Agent会进行工具调用循环

**实际上**：
- 如果你给`simple`传递了`tools`参数，它也会调用工具
- 所以它们几乎是一样的！
- `react`只是一个更明确的名字（表示支持ReAct模式）

**建议**：
- 不需要工具 → 用`simple`
- 需要工具 → 用`react`（名字更清晰）

---

### workflow vs multi_agent (sequential)

**相同点**：
- 都是顺序执行
- 都支持多个Agent

**不同点**：

| 特性 | workflow | multi_agent (sequential) |
|------|----------|-------------------------|
| 依赖管理 | ✅ 显式依赖 | ❌ 隐式顺序 |
| 条件分支 | ✅ 支持 | ❌ 不支持 |
| 回滚 | ✅ 支持 | ❌ 不支持 |
| 超时控制 | ✅ 每步独立 | ❌ 全局 |
| 重试 | ✅ 每步独立 | ❌ 全局 |
| 数据传递 | ✅ 显式变量 | ✅ 前一个输出 |

**建议**：
- 需要精细控制（依赖、回滚、条件）→ 用`workflow`
- 简单的顺序执行 → 用`multi_agent (sequential)`

---

## 性能和成本对比

### 执行时间

| 编排器 | 串行时间 | 并行优化 | 实际时间 |
|--------|---------|---------|---------|
| simple | 5秒 | 无 | 5秒 |
| react | 10秒 | 无 | 10秒 |
| workflow (3步) | 15秒 | 无 | 15秒 |
| multi_agent (parallel, 3个) | 15秒 | ✅ | 5秒 |

### 成本

| 编排器 | Agent调用 | 工具调用 | Token消耗 | 成本 |
|--------|----------|---------|----------|------|
| simple | 1次 | 0次 | 2K | $0.02 |
| react | 1次 | 5次 | 5K | $0.05 |
| workflow (3步) | 3次 | 15次 | 15K | $0.15 |
| multi_agent (3个) | 3次 | 15次 | 15K | $0.15 |

---

## 推荐配置模板

### 模板1：简单任务

```yaml
name: simple-task
orchestrator: simple
agent: translator

llm:
  model: qwen-coder-plus
  temperature: 0.1
```

---

### 模板2：编程任务

```yaml
name: coding-task
orchestrator: react
agent: programmer

tools:
  - read_file
  - write_file
  - text_search
  - git_commit

llm:
  model: qwen-coder-plus
  temperature: 0.1
  max_tool_iterations: 10
```

---

### 模板3：分析任务

```yaml
name: analysis-task
orchestrator: react
agent: code_analyzer

tools:
  - repo_map
  - read_file
  - text_search
  - get_diagnostics

llm:
  model: qwen-max
  temperature: 0.1
  max_tool_iterations: 8
```

---

### 模板4：工作流任务

```yaml
name: workflow-task
orchestrator: workflow

workflow:
  - name: step1
    agent: agent1
    max_retries: 2
    timeout: 30.0
  
  - name: step2
    agent: agent2
    depends_on: [step1]
    input: ${results.step1.content}
  
  - name: step3
    agent: agent3
    depends_on: [step2]
    condition: ${results.step2.success}

llm:
  model: qwen-coder-plus
  temperature: 0.2
```

---

### 模板5：多Agent协作

```yaml
name: multi-agent-task
orchestrator: multi_agent
collaboration_mode: main_with_helpers

agents:
  - main_agent
  - code_analyzer
  - programmer
  - test_expert

llm:
  model: qwen-max
  temperature: 0.3
```

---

## 常见错误

### 错误1：用simple做复杂任务

```yaml
# ❌ 错误
orchestrator: simple
agent: programmer
# 问题：programmer需要工具，但simple不传递工具
```

**修复**：
```yaml
# ✅ 正确
orchestrator: react
agent: programmer
tools:
  - read_file
  - write_file
```

---

### 错误2：用workflow做简单任务

```yaml
# ❌ 过度设计
orchestrator: workflow
workflow:
  - name: translate
    agent: translator
# 问题：只有一个步骤，不需要workflow
```

**修复**：
```yaml
# ✅ 正确
orchestrator: simple
agent: translator
```

---

### 错误3：用multi_agent做顺序任务

```yaml
# ❌ 不合适
orchestrator: multi_agent
collaboration_mode: parallel
agents:
  - code_analyzer
  - refactor_master  # 依赖analyzer的结果
  - test_expert      # 依赖refactor的结果
# 问题：有依赖关系，不应该并行
```

**修复**：
```yaml
# ✅ 正确
orchestrator: multi_agent
collaboration_mode: sequential
agents:
  - code_analyzer
  - refactor_master
  - test_expert
```

或者：
```yaml
# ✅ 更好
orchestrator: workflow
workflow:
  - name: analyze
    agent: code_analyzer
  - name: refactor
    agent: refactor_master
    depends_on: [analyze]
  - name: test
    agent: test_expert
    depends_on: [refactor]
```

---

## 总结

### 快速选择指南

1. **不需要工具** → `simple`
2. **需要工具 + 单Agent** → `react`
3. **需要工具 + 多步骤** → `workflow`
4. **需要工具 + 多Agent** → `multi_agent`

### 记住

- **所有编排器都保留**（各有用途）
- **工具循环在Agent层**（不在编排器层）
- **根据任务选择编排器**（不要过度设计）
- **从简单开始**（simple → react → workflow → multi_agent）

### 下一步

1. 选择一个任务
2. 根据决策流程图选择编排器
3. 使用模板创建Skill配置
4. 测试和优化
