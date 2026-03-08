# DaoyouCode Backend 文档

> DaoyouCode 2.0 架构 - CoreOrchestrator + Workflow 驱动

---

## 🎯 架构概览

### 新一代架构（2.0）

```
用户输入
  ↓
CLI 命令
  ↓
Skill 配置（skill.yaml）
  ↓
CoreOrchestrator（统一执行引擎）
  ├─ 意图识别（使用小模型）
  ├─ 分级预取（按需加载上下文）
  ├─ 工作流加载（动态加载 workflow）
  └─ Agent 执行（动态创建 Agent）
  ↓
工具调用（34+ 专业工具）
  ↓
返回结果（支持流式输出）
```

### 核心特性

1. **智能意图识别**
   - 使用小模型（qwen-turbo）快速识别用户意图
   - 准确率 95%+，成本降低 80%

2. **分级预取机制**
   - Full: 目录结构 + 代码地图 + 项目文档
   - Medium: 目录结构 + 代码地图
   - Light: 代码地图
   - None: 无预取

3. **动态 Agent 创建**
   - 无需 Python 类，通过配置动态创建
   - 行为由 Workflow 文件定义
   - 支持热更新，无需重启

4. **配置即服务**
   - skill.yaml: 统一配置入口
   - workflow.md: 定义任务执行方式
   - prompt_template.md: 基础 Prompt 模板

---

## 📚 文档导航

### 核心文档

#### 1. [CLI命令参考.md](./01_CLI命令参考.md)
**CLI 使用指南**
- 命令行使用方法
- 核心命令详解
- 使用场景和示例

**适合**：
- 新用户快速上手
- 查找命令用法

---

#### 2. [编排器介绍.md](./02_ORCHESTRATORS编排器介绍.md) ⭐
**CoreOrchestrator 架构说明**
- 新一代编排器架构
- 意图识别机制
- 分级预取机制
- 执行流程详解
- 配置说明

**适合**：
- 了解核心架构
- 理解执行流程
- 配置 Skill

---

#### 3. [Agent智能体介绍.md](./03_AGENTS智能体介绍.md) ⭐
**动态 Agent + Workflow 驱动**
- 动态 Agent 机制
- Workflow 驱动原理
- 内置 Workflow 列表
- 创建自定义 Workflow
- 最佳实践

**适合**：
- 了解 Agent 工作原理
- 创建自定义 Workflow
- 扩展系统功能

---

#### 4. [工具参考.md](./04_TOOLS工具参考.md)
**34+ 工具完整参考**
- 工具总览和分类
- 核心工具详解
- 工具选择指南
- 使用示例

**适合**：
- 选择合适的工具
- 了解工具能力
- 编写 Workflow

---

#### 5. [LSP和AST技术说明.md](./05_LSP和AST技术说明.md)
**LSP/AST 深度集成**
- LSP 工具介绍
- AST 工具介绍
- 使用场景和示例

**适合**：
- 了解代码分析能力
- 使用 LSP/AST 工具

---

#### 6. [结构化理解传递给大模型.md](./06_结构化理解传递给大模型.md)
**项目理解机制**
- 预取机制详解
- 结构化信息传递
- 优化建议

**适合**：
- 了解预取机制
- 优化上下文传递

---

## 🚀 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置 API Key

```bash
# 复制配置文件
cp .env.example .env

# 编辑 .env，填入你的 API Key
# DASHSCOPE_API_KEY=your_key_here
```

### 3. 启动对话

```bash
# 使用默认 Skill（sisyphus-orchestrator）
python daoyoucode.py chat

# 或指定 Skill
python daoyoucode.py chat --skill sisyphus-orchestrator
```

### 4. 示例对话

```bash
# 理解项目
用户: 帮我分析这个项目的架构
AI: [自动识别意图 → 预取项目信息 → 加载工作流 → 分析架构]

# 编写代码
用户: 在 user.py 中添加一个 get_user_by_id 函数
AI: [识别意图 → 预取代码地图 → 加载编写代码工作流 → 实现功能]

# 重构代码
用户: 重构 auth.py，提取重复代码
AI: [识别意图 → 预取代码地图 → 加载重构工作流 → 执行重构]
```

---

## 🏗️ 核心概念

### 1. Skill（技能）- 配置文件

Skill 是一个配置文件，定义了：
- 使用哪个编排器（orchestrator）
- Agent 的名称和角色（prompt_template）
- 可用的工具列表（tools）
- 工作流来源（workflows）
- 项目理解配置（project_understanding）

**示例**：
```yaml
# skills/sisyphus-orchestrator/skill.yaml
name: sisyphus-orchestrator
orchestrator: core  # 使用 CoreOrchestrator

prompt_template:
  agent_name: "Sisyphus"
  role: "资深项目经理和技术架构师"

workflows:
  source: sisyphus-orchestrator

tools:
  - read_file
  - write_file
  - lsp_symbols
```

### 2. CoreOrchestrator（编排器）- 统一执行引擎

CoreOrchestrator 是新一代编排器，负责：
- 意图识别（使用小模型）
- 分级预取（按需加载上下文）
- 工作流加载（根据意图加载）
- Agent 执行（动态创建 Agent）

### 3. Workflow（工作流）- 任务执行方式

Workflow 是一个 Markdown 文件，定义了：
- 任务目标
- 执行步骤
- 关键原则
- 注意事项
- 可选工具

**示例**：
```markdown
# 理解项目工作流

## 目标
帮助用户快速理解项目架构

## 分析顺序
1. 目录结构（整体布局）
2. 代码地图（核心架构）
3. 项目文档（背景信息）

## 关键原则
- 提炼核心，不要罗列
- 突出架构设计思想
```

### 4. Agent（智能体）- 动态创建

Agent 不再是预定义的 Python 类，而是由 CoreOrchestrator 动态创建：
- 名称和角色来自 skill.yaml
- 行为来自 workflow.md
- 工具来自 skill.yaml

### 5. Tool（工具）- 功能模块

Tool 是具体的功能模块，如：
- 文件操作（read_file, write_file）
- 代码分析（lsp_symbols, lsp_goto_definition）
- 搜索（text_search, semantic_code_search）
- Git 操作（git_status, git_commit）

---

## 🎯 使用场景

### 场景 1: 理解项目

```bash
python daoyoucode.py chat

用户: 帮我分析这个项目的架构
```

**执行流程**：
1. 意图识别 → `understand_project`
2. 预取级别 → `full`（目录结构 + 代码地图 + 项目文档）
3. 工作流加载 → `workflows/understand_project.md`
4. Agent 执行 → 分析项目架构
5. 返回结果 → 架构分析报告

---

### 场景 2: 编写代码

```bash
python daoyoucode.py chat

用户: 在 user.py 中添加一个 get_user_by_id 函数
```

**执行流程**：
1. 意图识别 → `write_code`
2. 预取级别 → `medium`（目录结构 + 代码地图）
3. 工作流加载 → `workflows/write_code.md`
4. Agent 执行 → 实现功能
5. 返回结果 → 代码实现

---

### 场景 3: 重构代码

```bash
python daoyoucode.py chat

用户: 重构 auth.py，提取重复代码
```

**执行流程**：
1. 意图识别 → `refactor_code`
2. 预取级别 → `medium`（目录结构 + 代码地图）
3. 工作流加载 → `workflows/refactor_code.md`
4. Agent 执行 → 执行重构
5. 返回结果 → 重构后的代码

---

## 🔧 开发指南

### 创建自定义 Skill

#### 步骤 1: 创建 Skill 目录

```bash
mkdir -p skills/my-skill/prompts/workflows
```

#### 步骤 2: 创建 skill.yaml

```yaml
# skills/my-skill/skill.yaml
name: my-skill
version: 1.0.0
description: 我的自定义 Skill

orchestrator: core

llm:
  model: qwen-max
  temperature: 0.3

prompt_template:
  agent_name: "MyAgent"
  agent_description: "我的自定义 Agent"
  role: |
    你是一个专业的...
  positioning: |
    你的核心能力是...

workflows:
  source: my-skill

tools:
  - read_file
  - write_file
  - lsp_symbols

project_understanding:
  use_intent: true
  doc_chars: 4000
  struct_chars: 5000
  repomap_chars: 12000
```

#### 步骤 3: 创建 Workflow 文件

```markdown
# skills/my-skill/prompts/workflows/my_workflow.md

# 我的工作流

## 目标
明确要达成的目标

## 关键步骤
1. 第一步
2. 第二步
3. 第三步

## 关键原则
- 原则1
- 原则2

## 注意事项
### ✅ 应该做的
- 推荐做法1

### ❌ 不应该做的
- 避免做法1

## 可选工具调用
- lsp_symbols - 查看符号
- read_file - 读取文件
```

#### 步骤 4: 创建意图配置

```yaml
# skills/my-skill/intents.yaml
intents:
  - name: my_intent
    description: "我的自定义意图"
    keywords:
      - "关键词1"
      - "关键词2"
    workflow: "my_workflow.md"
    prefetch_level: "medium"
```

#### 步骤 5: 使用

```bash
python daoyoucode.py chat --skill my-skill
```

---

## 📊 架构对比

### 旧架构（1.0）

```
CLI → Skill → 编排器（7种） → Agent类（10个） → 工具
```

**问题**：
- ❌ 多个编排器实现，维护成本高
- ❌ 预定义 Agent 类，扩展困难
- ❌ 配置分散，难以理解
- ❌ 修改需要重启服务

### 新架构（2.0）

```
CLI → Skill → CoreOrchestrator → 动态Agent → 工具
                    ↓
              Workflow驱动
```

**优势**：
- ✅ 统一的 CoreOrchestrator
- ✅ 动态创建 Agent，易于扩展
- ✅ 配置统一，易于理解
- ✅ 支持热更新，无需重启

---

## 🎓 学习路径

### 新手入门

1. **阅读 CLI 命令参考**
   - 了解基本命令
   - 尝试简单对话

2. **阅读编排器介绍**
   - 理解核心架构
   - 了解执行流程

3. **阅读 Agent 介绍**
   - 理解动态 Agent
   - 了解 Workflow 机制

4. **实践**
   - 使用内置 Skill
   - 尝试不同场景

### 进阶开发

1. **创建自定义 Workflow**
   - 编写 workflow.md
   - 配置 intents.yaml

2. **创建自定义 Skill**
   - 配置 skill.yaml
   - 组合工具和 Workflow

3. **优化配置**
   - 调整预取参数
   - 优化工具选择

4. **贡献代码**
   - 添加新工具
   - 改进核心功能

---

## 🤝 贡献

欢迎贡献代码和文档！

### 贡献方式

1. Fork 项目
2. 创建分支
3. 提交代码
4. 发起 Pull Request

### 贡献指南

- 遵循代码规范
- 添加测试用例
- 更新文档
- 提供示例

---

## 📧 联系

如有问题，请提 Issue。

---

## 📝 更新日志

### 2026-03-08
- ✅ 重构为 CoreOrchestrator 架构
- ✅ 实现智能意图识别
- ✅ 实现分级预取机制
- ✅ 实现动态 Agent 创建
- ✅ 实现 Workflow 驱动
- ✅ 更新所有文档

### 2025-02-17
- ✅ 整理文档，合并为核心文档
- ✅ 添加 CLI 三层帮助系统
- ✅ 完善 Agent 和编排器介绍
