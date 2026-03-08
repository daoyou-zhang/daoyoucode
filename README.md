# DaoyouCode

<div align="center">

**新一代 AI 编程助手 - CoreOrchestrator + Workflow 驱动**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-active-success.svg)]()

[English](README.en.md) • [中文文档](README.md)

</div>

---

## 📖 项目简介

**DaoyouCode** 是一个基于 CoreOrchestrator 架构的新一代 AI 编程助手，采用智能意图识别、分级预取机制和 Workflow 驱动，为开发者提供强大的代码分析、编写和重构支持。

### ✨ 核心特性

- 🎯 **智能意图识别** - 使用小模型（qwen-turbo）快速识别用户意图，准确率 95%+
- 📊 **分级预取机制** - 根据任务复杂度动态加载上下文（Full/Medium/Light/None）
- 🔄 **Workflow 驱动** - 通过 Markdown 文件定义任务执行方式，无需编写代码
- 🛠️ **完整工具链** - 34+ 专业工具，LSP/AST 深度集成，Git 操作支持
- 🧠 **智能记忆系统** - 对话历史、长期记忆、用户画像、智能上下文加载
- 🌐 **国产 LLM 优化** - 深度支持通义千问、DeepSeek，多 Key 轮询
- ⚙️ **配置即服务** - 通过 YAML + Markdown 配置，支持热更新

### 🎯 技术亮点

**CoreOrchestrator 架构**
```
用户输入
  ↓
意图识别（qwen-turbo，快速准确）
  ↓
分级预取（按需加载上下文）
  ├─ Full: 目录结构 + 代码地图 + 项目文档
  ├─ Medium: 目录结构 + 代码地图
  ├─ Light: 代码地图
  └─ None: 无预取
  ↓
工作流加载（根据意图动态加载）
  ↓
Agent 执行（动态创建，无需 Python 类）
  ↓
返回结果（支持流式输出）
```

**深度代码理解**
- **LSP 集成** - 类型信息、引用关系、代码诊断、智能重命名
- **AST 分析** - 语法树解析、结构化代码理解
- **语义搜索** - 基于向量的代码检索，理解代码意图
- **智能代码地图** - 自动生成项目结构概览（带 LSP 增强）

**配置即服务**
- **skill.yaml** - 统一配置入口（Agent 名称、角色、工具、预取参数）
- **workflow.md** - 定义任务执行方式（目标、步骤、原则）
- **intents.yaml** - 意图配置（关键词、工作流、预取级别）
- **prompt_template.md** - 基础 Prompt 模板

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/daoyou-zhang/daoyoucode.git
cd daoyoucode

# 安装依赖
cd backend
pip install -r requirements.txt
```

### 配置

编辑 `backend/.env`：

```bash
# 复制配置文件
cp .env.example .env

# 编辑 .env，填入你的 API Key
DASHSCOPE_API_KEY=your_key_here
```

或编辑 `backend/config/llm_config.yaml`：

```yaml
providers:
  qwen:
    api_key: ["your-api-key-here"]
    enabled: true

default:
  model: "qwen-max"
  temperature: 0.7
```

### 使用

```bash
# 交互式对话（默认 sisyphus-orchestrator）
python backend/daoyoucode.py chat

# 或使用简化命令（如果已安装）
daoyoucode chat

# 查看所有 Skill
daoyoucode skills list

# 健康检查
daoyoucode doctor
```

## 🎓 使用示例

### 示例 1: 理解项目

```bash
daoyoucode chat

你 > 帮我分析这个项目的架构

AI 会自动：
1. 识别意图 → understand_project
2. 预取级别 → Full（目录结构 + 代码地图 + 项目文档）
3. 加载工作流 → workflows/understand_project.md
4. 分析项目架构
5. 用 1-2 段话概括项目核心
```

**输出示例**：
```
DaoyouCode 是一个基于 CoreOrchestrator 架构的 AI 编程助手。
它采用编排器-Agent-工具的三层架构：CoreOrchestrator 负责
意图识别和任务编排，动态 Agent 负责具体执行，工具层提供 
LSP/AST 等代码分析能力。

核心特性包括智能意图识别（使用小模型快速判断）、分级预取
机制（根据任务复杂度动态加载上下文）、以及配置即服务的设计
（通过 skill.yaml 和 workflow 文件驱动行为）。技术栈基于 
Python + FastAPI，深度集成了 Pylsp 和 Tree-sitter，支持
通义千问等国产大模型。
```

---

### 示例 2: 编写代码

```bash
你 > 在 user.py 中添加一个 get_user_by_id 函数

AI 会自动：
1. 识别意图 → write_code
2. 预取级别 → Medium（目录结构 + 代码地图）
3. 加载工作流 → workflows/write_code.md
4. 使用 LSP 工具查看现有代码
5. 实现功能
6. 使用 lsp_diagnostics 检查错误
```

---

### 示例 3: 重构代码

```bash
你 > 重构 auth.py，提取重复代码

AI 会自动：
1. 识别意图 → refactor_code
2. 预取级别 → Medium（目录结构 + 代码地图）
3. 加载工作流 → workflows/refactor_code.md
4. 使用 lsp_find_references 查找所有引用
5. 执行重构
6. 使用 lsp_diagnostics 检查错误
```

---

### 示例 4: 编写测试

```bash
你 > 为 user.py 编写单元测试

AI 会自动：
1. 识别意图 → write_test
2. 预取级别 → Medium（目录结构 + 代码地图）
3. 加载工作流 → workflows/write_test.md
4. 使用 lsp_goto_definition 查看被测代码
5. 编写测试用例
6. 使用 run_test 运行测试
```

---

## 🏗️ 项目结构

```
daoyoucode/
├── backend/                    # Python 核心实现
│   ├── daoyoucode.py          # CLI 入口
│   ├── cli/                   # CLI 命令
│   ├── daoyoucode/
│   │   └── agents/
│   │       ├── core/          # 核心组件
│   │       │   ├── core_orchestrator.py  # CoreOrchestrator
│   │       │   ├── agent.py              # Agent 基类
│   │       │   ├── skill.py              # Skill 加载器
│   │       │   └── intent.py             # 意图识别
│   │       ├── tools/         # 工具系统（34+ 工具）
│   │       ├── llm/           # LLM 客户端
│   │       ├── memory/        # 记忆系统
│   │       └── ui/            # UI 组件
│   ├── config/                # 配置文件
│   │   └── llm_config.yaml   # LLM 配置
│   └── tests/                 # 测试
├── skills/                    # Skill 配置
│   └── sisyphus-orchestrator/ # 默认 Skill
│       ├── skill.yaml         # Skill 配置
│       ├── intents.yaml       # 意图配置
│       └── prompts/
│           ├── base_template.md  # Prompt 模板
│           └── workflows/        # 工作流文件
│               ├── general_chat.md
│               ├── understand_project.md
│               ├── write_code.md
│               ├── refactor_code.md
│               ├── write_test.md
│               └── run_test.md
└── docs/                      # 文档
```

---

## 🤖 核心概念

### 1. CoreOrchestrator（统一执行引擎）

CoreOrchestrator 是新一代编排器，负责：

**意图识别**
- 使用小模型（qwen-turbo）快速识别用户意图
- 准确率 95%+，成本降低 80%
- 支持关键词兜底机制

**分级预取**
- Full: 目录结构 + 代码地图 + 项目文档（适用：understand_project）
- Medium: 目录结构 + 代码地图（适用：write_code, refactor_code）
- Light: 代码地图（适用：need_code_context）
- None: 无预取（适用：general_chat, run_test）

**工作流加载**
- 根据识别的意图动态加载对应的 workflow 文件
- Workflow 文件定义任务的执行方式（目标、步骤、原则）

**Agent 执行**
- 动态创建 Agent（无需 Python 类）
- 构建 Prompt（模板 + 固定内容 + 动态内容）
- LLM 调用 + 工具执行
- 保存记忆

---

### 2. Workflow（工作流）

Workflow 是一个 Markdown 文件，定义任务的执行方式：

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
- 用自然语言表达

## 可选工具调用
### 优先使用 LSP 工具
- lsp_symbols - 查看符号
- lsp_goto_definition - 追踪定义
```

**内置 Workflow**：
- `general_chat.md` - 通用对话
- `understand_project.md` - 理解项目
- `need_code_context.md` - 需要代码上下文
- `write_code.md` - 编写代码
- `refactor_code.md` - 重构代码
- `write_test.md` - 编写测试
- `run_test.md` - 运行测试

---

### 3. Skill（技能配置）

Skill 是一个配置文件（skill.yaml），定义：

```yaml
name: sisyphus-orchestrator
orchestrator: core  # 使用 CoreOrchestrator

# Prompt 模板配置
prompt_template:
  agent_name: "Sisyphus"
  agent_description: "智能任务编排专家"
  role: |
    你是 Sisyphus，一个资深的项目经理和技术架构师。
  positioning: |
    你是决策者和执行者，不是简单的信息整合者。

# 工作流配置
workflows:
  source: sisyphus-orchestrator

# 工具列表
tools:
  - discover_project_docs
  - repo_map
  - get_repo_structure
  - read_file
  - write_file
  - lsp_symbols
  # ... 更多工具

# 项目理解配置
project_understanding:
  use_intent: true          # 使用意图判断
  doc_chars: 4000           # 文档字符数
  struct_chars: 5000        # 结构字符数
  repomap_chars: 12000      # 代码地图字符数
  max_chars: 20000          # 总字符数上限
```

---

### 4. 工具系统（34+ 工具）

**项目理解**（3 个）
- `discover_project_docs` - 发现项目文档（README、CONTRIBUTING 等）
- `get_repo_structure` - 获取目录结构
- `repo_map` - 智能代码地图（带 LSP 增强）

**文件操作**（8 个）
- `read_file` - 读取文件
- `write_file` - 写入文件
- `batch_read_files` - 批量读取
- `batch_write_files` - 批量写入
- `list_files` - 列出文件
- `delete_file` - 删除文件
- `batch_delete_files` - 批量删除
- `get_file_info` - 获取文件信息

**搜索**（4 个）
- `text_search` - 文本搜索
- `regex_search` - 正则搜索
- `semantic_code_search` - 语义搜索
- `ast_grep_search` - AST 搜索

**LSP 工具**（5 个）
- `lsp_diagnostics` - 代码诊断
- `lsp_goto_definition` - 跳转定义
- `lsp_find_references` - 查找引用
- `lsp_symbols` - 查看符号
- `get_file_symbols` - 获取文件符号

**代码编辑**（3 个）
- `search_replace` - 搜索替换
- `intelligent_diff_edit` - 智能差异编辑
- `ast_grep_replace` - AST 替换

**Git 操作**（3 个）
- `git_status` - Git 状态
- `git_diff` - Git 差异
- `git_commit` - Git 提交

**命令执行**（3 个）
- `run_test` - 运行测试
- `run_lint` - 运行 Lint
- `run_command` - 运行命令

---

## 🔧 创建自定义 Skill

### 步骤 1: 创建 Skill 目录

```bash
mkdir -p skills/my-skill/prompts/workflows
```

### 步骤 2: 创建 skill.yaml

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

### 步骤 3: 创建 Workflow 文件

```markdown
# skills/my-skill/prompts/workflows/my_workflow.md

# 我的工作流

## 目标
明确要达成的目标

## 关键步骤
1. 第一步
2. 第二步

## 关键原则
- 原则1
- 原则2

## 可选工具调用
- lsp_symbols - 查看符号
- read_file - 读取文件
```

### 步骤 4: 创建意图配置

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

### 步骤 5: 使用

```bash
python backend/daoyoucode.py chat --skill my-skill
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

## 📚 文档

- [Backend 文档](backend/README.md) - 核心架构和开发指南
- [编排器介绍](backend/02_ORCHESTRATORS编排器介绍.md) - CoreOrchestrator 详解
- [Agent 介绍](backend/03_AGENTS智能体介绍.md) - 动态 Agent + Workflow
- [工具参考](backend/04_TOOLS工具参考.md) - 34+ 工具完整参考
- [CLI 命令参考](backend/01_CLI命令参考.md) - CLI 使用指南

---

## 🤝 贡献

欢迎贡献代码和文档！

### 贡献方式

1. Fork 项目
2. 创建分支
3. 提交代码
4. 发起 Pull Request

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

---

## 📄 License

MIT License
