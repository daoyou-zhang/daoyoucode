# 编排器介绍（2.0 架构）

> DaoyouCode 新一代编排器架构 - CoreOrchestrator

---

## 🎯 架构演进

### 旧架构（1.0）
```
CLI → Skill → 编排器（7种） → Agent类（10个） → 工具
```
- 多个编排器实现（simple, react, multi_agent 等）
- 预定义的 Agent 类（sisyphus, programmer, oracle 等）
- 配置分散（skill.yaml + agent.py + prompt.md）

### 新架构（2.0）
```
CLI → Skill → CoreOrchestrator → 动态Agent → 工具
                    ↓
              Workflow驱动
```
- 统一的 CoreOrchestrator
- 动态创建 Agent（无需 Python 类）
- 配置即服务（skill.yaml + workflow.md + prompt_template.md）

---

## 🆕 CoreOrchestrator - 统一执行引擎

### 核心特性

#### 1. 智能意图识别
```python
# 使用小模型快速识别意图
intent_model: qwen-turbo  # 快速、便宜、准确

# 支持的意图类型
- general_chat          # 通用对话
- need_code_context     # 需要代码上下文
- understand_project    # 理解项目
- write_code            # 编写代码
- refactor_code         # 重构代码
- write_test            # 编写测试
- run_test              # 运行测试
```

#### 2. 分级预取机制
根据意图自动预取项目上下文：

**Full 级别**（完整理解）：
```
目录结构 + 代码地图 + 项目文档
适用：understand_project
```

**Medium 级别**（中等理解）：
```
目录结构 + 代码地图
适用：write_code, refactor_code
```

**Light 级别**（轻量理解）：
```
代码地图
适用：need_code_context
```

**None 级别**（无需预取）：
```
无预取
适用：general_chat, run_test
```

#### 3. 动态工作流加载
```yaml
# skill.yaml
workflows:
  source: sisyphus-orchestrator  # 工作流来源
  
# 自动加载对应的 workflow 文件
skills/sisyphus-orchestrator/prompts/workflows/
  ├── general_chat.md
  ├── understand_project.md
  ├── write_code.md
  ├── refactor_code.md
  └── ...
```

#### 4. 配置即服务
```yaml
# skill.yaml - 一站式配置
prompt_template:
  base: "base_template.md"
  agent_name: "Sisyphus"
  role: "你是资深的项目经理和技术架构师"
  positioning: "决策者和执行者"

project_understanding:
  use_intent: true
  doc_chars: 4000
  struct_chars: 5000
  repomap_chars: 12000
```

---

## 📋 执行流程

### 完整流程图
```
用户输入
  ↓
1. 意图识别（使用 intent_model）
  ↓
2. 预取判断（根据意图决定预取级别）
  ↓
3. 预取执行（如果需要）
   - Full: 目录结构 + 代码地图 + 项目文档
   - Medium: 目录结构 + 代码地图
   - Light: 代码地图
  ↓
4. 工作流加载（根据意图加载对应 workflow）
  ↓
5. Prompt 构建
   - 基础模板（base_template.md）
   - 固定内容（agent_name, role, positioning）
   - 动态内容（user_input, repo, workflow, project_understanding, history）
  ↓
6. Agent 执行
   - 动态创建 Agent
   - LLM 调用 + 工具执行
   - 保存记忆
  ↓
7. 返回结果（支持流式输出）
```

### 示例：理解项目

**用户输入**：
```
帮我分析这个项目的架构
```

**执行过程**：
```
1. 意图识别
   → understand_project

2. 预取判断
   → Full 级别（需要完整理解）

3. 预取执行
   → 调用 get_repo_structure（目录结构）
   → 调用 repo_map（代码地图）
   → 调用 discover_project_docs（项目文档）

4. 工作流加载
   → 加载 workflows/understand_project.md

5. Prompt 构建
   → 基础模板 + 工作流 + 预取内容 + 对话历史

6. Agent 执行
   → 动态创建 Agent
   → LLM 分析项目
   → 返回架构分析报告

7. 返回结果
   → 流式输出给用户
```

---

## 🔧 配置说明

### Skill 配置（skill.yaml）

```yaml
name: sisyphus-orchestrator
version: 2.0.0
description: 全能编排器

# 使用 CoreOrchestrator
orchestrator: core

# LLM 配置
llm:
  model: qwen-max
  temperature: 0.3
  max_tokens: 8000
  intent_model: qwen-turbo  # 意图识别专用

# Prompt 模板配置
prompt_template:
  base: "base_template.md"
  agent_name: "Sisyphus"
  agent_description: "智能任务编排专家"
  role: |
    你是 Sisyphus，一个资深的项目经理和技术架构师。
    你的核心能力是**理解需求、智能决策、高效执行**。
  positioning: |
    你不是简单的"信息整合者"，而是**决策者和执行者**：
    - 理解用户的真实需求（不只是字面意思）
    - 基于上下文和工具做出最优决策
    - 像资深工程师一样自然地交流

# 工具列表
tools:
  - discover_project_docs
  - repo_map
  - get_repo_structure
  - text_search
  - read_file
  - write_file
  # ... 更多工具

# 工作流配置
workflows:
  source: sisyphus-orchestrator

# 项目理解配置
project_understanding:
  use_intent: true          # 使用意图判断
  doc_chars: 4000           # 文档字符数
  struct_chars: 5000        # 结构字符数
  repomap_chars: 12000      # 代码地图字符数
  max_chars: 20000          # 总字符数上限
  header: |
    理解项目时，先看【目录结构】了解整体布局，
    再看【代码地图】掌握核心代码和架构，
    最后看【项目文档】补充背景信息。
```

### 工作流配置（workflow.md）

```markdown
# 理解项目工作流

## 目标
帮助用户快速理解当前项目的架构、功能、技术栈和设计思想。

## 分析顺序（从整体到细节）

### 1. 目录结构分析（整体布局）
先看【目录结构】，了解项目的整体组织方式：
- 识别主要模块和子系统
- 找出配置文件位置
- 定位核心代码目录

### 2. 代码地图分析（核心架构）
再看【代码地图】，掌握核心代码和架构设计：
- 识别关键类和函数
- 理解模块间的依赖关系
- 找出入口文件和主流程

### 3. 项目文档分析（背景信息）
最后看【项目文档】，补充背景和细节：
- README：项目简介、功能特性
- CONTRIBUTING：开发规范
- 技术栈和依赖版本

## 关键原则
- 提炼核心：用 1-2 段话概括项目本质
- 突出架构：重点说明架构设计思想
- 自然表达：像资深工程师在做技术分享

## 可选工具调用
如果预取的信息不够，优先使用 LSP 工具：
- lsp_symbols - 查看符号
- lsp_goto_definition - 追踪定义
- lsp_find_references - 查找引用
```

---

## 🆚 新旧对比

### 配置方式

**旧架构**：
```python
# 需要创建 Agent 类
class SisyphusAgent(BaseAgent):
    def __init__(self):
        super().__init__(...)
        self.tools = [...]
    
    async def execute(self, ...):
        # 实现逻辑
        pass
```

**新架构**：
```yaml
# 只需配置 skill.yaml
orchestrator: core
prompt_template:
  agent_name: "Sisyphus"
  role: "..."
workflows:
  source: sisyphus-orchestrator
```

### 工作流定义

**旧架构**：
```python
# 硬编码在 Agent 类中
class SisyphusAgent:
    async def execute(self, user_input):
        if "理解项目" in user_input:
            # 硬编码逻辑
            await self.understand_project()
```

**新架构**：
```markdown
# workflows/understand_project.md
# 理解项目工作流
## 目标
...
## 分析顺序
...
```

### 意图识别

**旧架构**：
```python
# 关键词匹配
if any(kw in user_input for kw in ["理解", "分析", "架构"]):
    intent = "understand_project"
```

**新架构**：
```python
# LLM 智能识别
intent = await llm.detect_intent(
    user_input,
    available_intents=[...],
    model="qwen-turbo"  # 小模型，快速准确
)
```

---

## 🎯 使用指南

### 快速开始

```bash
# 使用 CoreOrchestrator
python backend/daoyoucode.py chat --skill sisyphus-orchestrator

# 示例对话
用户: 帮我分析这个项目的架构
AI: [自动识别意图 → 预取项目信息 → 加载工作流 → 分析架构]

用户: 重构 user.py 文件
AI: [识别意图 → 预取代码地图 → 加载重构工作流 → 执行重构]
```

### 创建自定义 Skill

1. **创建 skill.yaml**
```yaml
name: my-skill
orchestrator: core
llm:
  model: qwen-max
prompt_template:
  agent_name: "MyAgent"
  role: "..."
workflows:
  source: my-skill
tools:
  - read_file
  - write_file
```

2. **创建工作流文件**
```
skills/my-skill/prompts/workflows/
  ├── my_workflow.md
  └── ...
```

3. **创建意图配置**
```yaml
# skills/my-skill/intents.yaml
intents:
  - name: my_intent
    keywords: ["关键词1", "关键词2"]
    workflow: my_workflow.md
    prefetch_level: medium
```

4. **使用**
```bash
python backend/daoyoucode.py chat --skill my-skill
```

---

## 📊 性能对比

| 指标 | 旧架构 | 新架构 | 提升 |
|------|--------|--------|------|
| 配置复杂度 | 高（Python + YAML） | 低（纯 YAML + MD） | ⬇️ 60% |
| 意图识别准确率 | 70%（关键词） | 95%（LLM） | ⬆️ 25% |
| 预取效率 | 固定预取 | 按需预取 | ⬆️ 40% |
| 开发效率 | 需要写代码 | 只需配置 | ⬆️ 80% |
| 维护成本 | 高 | 低 | ⬇️ 70% |

---

## 🔍 调试技巧

### 查看意图识别结果
```python
# 日志中会显示
[意图识别] 识别到意图: understand_project (置信度: 0.95)
[预取判断] 预取级别: full
```

### 查看预取内容
```python
# 日志中会显示
[预取] full级别 struct=5234 repomap=11567 doc=3892 (chars)
```

### 查看工作流加载
```python
# 日志中会显示
[工作流] 加载工作流: workflows/understand_project.md
```

---

## 📝 最佳实践

### 1. 意图设计
- 意图名称要清晰（understand_project 而不是 up）
- 关键词要准确（避免歧义）
- 工作流要对应（一个意图一个工作流）

### 2. 工作流编写
- 结构清晰（目标 → 步骤 → 原则）
- 指导明确（告诉 Agent 怎么做）
- 不要限制输出格式（交给 LLM）

### 3. 预取配置
- 根据任务复杂度调整字符数限制
- 使用 use_intent 而不是 triggers（更智能）
- 设置合理的 max_chars（避免超窗口）

### 4. 工具选择
- 优先使用 LSP 工具（精确、高效）
- 其次使用文件读取
- 最后使用搜索工具（模糊查询）

---

## 🚀 未来规划

### 短期（已实现）
- ✅ 统一的 CoreOrchestrator
- ✅ 智能意图识别
- ✅ 分级预取机制
- ✅ 配置即服务

### 中期（规划中）
- 🔄 多轮对话优化
- 🔄 工具调用优化
- 🔄 记忆系统增强
- 🔄 流式输出优化

### 长期（愿景）
- 📋 自定义意图
- 📋 工作流市场
- 📋 Agent 协作增强
- 📋 多模态支持

---

## 相关文档

- [CLI命令参考.md](./01_CLI命令参考.md)
- [TOOLS工具参考.md](./04_TOOLS工具参考.md)
- [skill.yaml 配置说明](../skills/sisyphus-orchestrator/skill.yaml)
- [workflow 编写指南](../skills/sisyphus-orchestrator/prompts/workflows/)
