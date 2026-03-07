# Skill 配置参数说明：orchestrator 和 agent

## 概述

每个 skill.yaml 文件中都有两个核心参数：`orchestrator` 和 `agent`。它们决定了任务的**执行方式**和**AI 角色**。

## orchestrator（编排器）

**作用**：决定任务的执行逻辑和流程控制

**代码位置**：`backend/daoyoucode/agents/orchestrators/`

### 可用的编排器类型

#### 1. simple（简单编排器）
```yaml
orchestrator: simple
```

**特点**：
- 单个 agent 执行
- 提供基础功能：重试机制、结果验证、项目信息预取、成本追踪
- 最简单直接的执行方式

**适用场景**：
- 单一职责的任务
- 不需要多 agent 协作
- 只读分析任务

**示例 skills**：
- `oracle` - 架构分析和技术咨询
- `code-analysis` - 代码分析
- `code-exploration` - 代码探索

#### 2. react（ReAct 编排器）
```yaml
orchestrator: react
```

**特点**：
- ReAct = Reason(思考) + Act(行动) + Observe(观察) 循环
- 自动进行推理循环，调用工具，观察结果
- 支持多步推理和工具调用
- 适合交互式任务

**适用场景**：
- 交互式对话
- 需要多步推理的任务
- 需要根据结果动态调整策略

**示例 skills**：
- `chat-assistant` - 交互式对话助手
- `code-review` - 代码审查
- `librarian` - 文档搜索
- `edit-single` - 单次文件编辑

#### 3. multi_agent（多智能体编排器）
```yaml
orchestrator: multi_agent
collaboration_mode: main_with_helpers  # 协作模式
agents:
  - main_agent      # 主 agent
  - helper_agent_1  # 辅助 agent 1
  - helper_agent_2  # 辅助 agent 2
```

**特点**：
- 支持多个 agents 协作
- 主 agent 负责任务分解和调度
- 辅助 agents 并行或顺序执行
- 聚合所有 agents 的结果

**协作模式**：
- `main_with_helpers`: 主 agent + 辅助 agents（默认，最常用）
- `parallel`: 所有 agents 并行执行
- `sequential`: 所有 agents 顺序执行
- `debate`: agents 之间辩论讨论

**适用场景**：
- 复杂任务，需要多个专家协作
- 需要分析 + 编程 + 测试的完整流程
- 需要多角度评估的任务

**示例 skills**：
- `sisyphus-orchestrator` - 主编排器（5个 agents）
- `programming` - 编程服务（3个 agents）
- `refactoring` - 重构服务（3个 agents）
- `testing` - 测试服务（3个 agents）

## agent（智能体）

**作用**：决定 AI 的角色、能力和行为

**代码位置**：`backend/daoyoucode/agents/builtin/`

### 可用的智能体

#### 通用智能体

**MainAgent**
```yaml
agent: MainAgent
```
- 通用智能体，适合多种任务
- 用于：chat-assistant, code-review 等

#### 专业智能体

**sisyphus**
```yaml
agent: sisyphus
```
- 主编排智能体
- 负责：任务分解、调度、协调其他 agents
- 用于：sisyphus-orchestrator, programming, refactoring, testing

**programmer**
```yaml
agent: programmer
```
- 编程智能体
- 负责：代码编写、Bug 修复、功能实现
- 用于：programming skill（作为辅助 agent）

**code_analyzer**
```yaml
agent: code_analyzer
```
- 代码分析智能体
- 负责：架构分析、代码审查、技术咨询
- 用于：code-analysis skill, sisyphus-orchestrator（作为辅助 agent）

**oracle**
```yaml
agent: oracle
```
- 高级咨询智能体
- 负责：架构决策、技术建议、深度分析
- 特点：只读，不修改代码
- 用于：oracle skill

**refactor_master**
```yaml
agent: refactor_master
```
- 重构智能体
- 负责：代码重构、性能优化、设计改进
- 用于：refactoring skill（作为辅助 agent）

**test_expert**
```yaml
agent: test_expert
```
- 测试智能体
- 负责：测试编写、测试修复、质量保证
- 用于：testing skill（作为辅助 agent）

**librarian**
```yaml
agent: librarian
```
- 文档搜索智能体
- 负责：搜索文档、查找代码、定位信息
- 用于：librarian skill

**code_explorer**
```yaml
agent: code_explorer
```
- 代码探索智能体
- 负责：代码库搜索、模式发现、结构分析
- 用于：code-exploration skill

## 组合示例

### 示例 1：简单单 agent
```yaml
name: oracle
orchestrator: simple      # 简单编排器
agent: oracle            # 咨询智能体
```
**执行流程**：
1. simple 编排器启动
2. 调用 oracle 智能体
3. oracle 分析问题，调用工具
4. 返回结果

### 示例 2：ReAct 推理循环
```yaml
name: chat-assistant
orchestrator: react      # ReAct 编排器
agent: MainAgent        # 通用智能体
```
**执行流程**：
1. react 编排器启动
2. MainAgent 思考（Reason）
3. MainAgent 行动（Act）- 调用工具
4. MainAgent 观察（Observe）- 查看结果
5. 重复 2-4 直到完成任务

### 示例 3：多智能体协作
```yaml
name: sisyphus-orchestrator
orchestrator: multi_agent           # 多智能体编排器
collaboration_mode: main_with_helpers
agents:
  - sisyphus          # 主 agent：任务分解和调度
  - code_analyzer     # 辅助：代码分析
  - programmer        # 辅助：代码编写
  - refactor_master   # 辅助：代码重构
  - test_expert       # 辅助：测试编写
```
**执行流程**：
1. multi_agent 编排器启动
2. sisyphus（主 agent）分析用户请求
3. sisyphus 决定需要哪些辅助 agents
4. 并行调用辅助 agents（如 code_analyzer, programmer）
5. sisyphus 看到辅助 agents 的结果
6. sisyphus 聚合结果，返回给用户

## 如何选择？

### 选择编排器

| 场景 | 推荐编排器 | 原因 |
|------|-----------|------|
| 简单分析任务 | simple | 直接高效 |
| 交互式对话 | react | 支持多轮推理 |
| 复杂任务需要多专家 | multi_agent | 协作完成 |
| 需要根据结果调整策略 | react | 动态推理 |
| 只读分析 | simple | 简单直接 |

### 选择智能体

| 任务类型 | 推荐智能体 | 原因 |
|---------|-----------|------|
| 通用对话 | MainAgent | 多功能 |
| 代码编写 | programmer | 专业编程 |
| 代码分析 | code_analyzer | 专业分析 |
| 架构咨询 | oracle | 高级咨询 |
| 代码重构 | refactor_master | 专业重构 |
| 测试编写 | test_expert | 专业测试 |
| 任务编排 | sisyphus | 协调调度 |

## 常见问题

### Q1: 为什么 programming skill 使用 multi_agent 而不是 simple？

A: 虽然 programming skill 主要是编程任务，但使用 multi_agent 可以：
1. 支持未来扩展（添加更多辅助 agents）
2. 与 sisyphus-orchestrator 保持一致的架构
3. 享受 multi_agent 的高级功能（智能选择、并行执行等）
4. 可以在需要时调用 code_analyzer 进行分析

### Q2: react 和 simple 有什么区别？

A: 
- **simple**: 一次性执行，agent 调用工具后直接返回结果
- **react**: 循环执行，agent 可以根据工具结果继续思考和行动，直到完成任务

### Q3: 什么时候需要使用 multi_agent？

A: 当任务需要：
- 多个专业领域的知识（分析 + 编程 + 测试）
- 并行处理提高效率
- 多角度评估和决策
- 复杂的任务分解和调度

### Q4: agent 和 orchestrator 是什么关系？

A:
- **orchestrator**: 控制流程（怎么执行）
- **agent**: 提供能力（做什么）
- 类比：orchestrator 是指挥家，agent 是乐手

## 总结

- **orchestrator** = 执行逻辑（simple/react/multi_agent）
- **agent** = AI 角色（MainAgent/programmer/oracle/sisyphus 等）
- 两者配合决定了 skill 的完整行为
- 选择合适的组合可以最大化效率和效果
