# Agent 智能体介绍（2.0 架构）

> DaoyouCode 新一代 Agent 架构 - 动态 Agent + Workflow 驱动

---

## 🎯 架构演进

### 旧架构（1.0）- 预定义 Agent 类
```python
# 需要为每个 Agent 创建 Python 类
class SisyphusAgent(BaseAgent):
    def __init__(self):
        self.tools = [...]
        self.prompt = "..."
    
    async def execute(self, user_input):
        # 硬编码逻辑
        pass

class ProgrammerAgent(BaseAgent):
    # ...

class OracleAgent(BaseAgent):
    # ...
```

**问题**：
- ❌ 需要写大量 Python 代码
- ❌ 配置分散（Python + YAML + MD）
- ❌ 难以维护和扩展
- ❌ 修改需要重启服务

### 新架构（2.0）- 动态 Agent + Workflow
```yaml
# skill.yaml - 配置即可
orchestrator: core
prompt_template:
  agent_name: "Sisyphus"
  role: "资深项目经理和技术架构师"
workflows:
  source: sisyphus-orchestrator
tools:
  - read_file
  - write_file
```

```markdown
# workflows/understand_project.md - 定义行为
## 目标
帮助用户理解项目架构

## 分析顺序
1. 目录结构
2. 代码地图
3. 项目文档
```

**优势**：
- ✅ 无需 Python 代码
- ✅ 配置统一（YAML + MD）
- ✅ 易于维护和扩展
- ✅ 热更新（无需重启）

---

## 🆕 动态 Agent 机制

### 工作原理

```
用户输入
  ↓
CoreOrchestrator
  ↓
1. 意图识别 → understand_project
  ↓
2. 加载工作流 → workflows/understand_project.md
  ↓
3. 动态创建 Agent
   - 名称：从 skill.yaml 读取
   - 角色：从 skill.yaml 读取
   - 工作流：从 workflow 文件读取
   - 工具：从 skill.yaml 读取
  ↓
4. Agent 执行
   - 构建 Prompt（模板 + 工作流 + 上下文）
   - LLM 调用
   - 工具执行
  ↓
5. 返回结果
```

### 核心组件

#### 1. Prompt 模板（base_template.md）
```markdown
# {{agent_name}} - {{agent_description}}

## 用户请求
{{user_input}}

## 角色定义
{{role}}

## 工作目录
{{repo}}

## 角色定位
{{positioning}}

## 当前任务工作流
{{workflow}}

## 对话历史
{{conversation_history}}

## 开始工作
请根据上述信息完成用户的请求。
```

#### 2. 固定内容（skill.yaml）
```yaml
prompt_template:
  agent_name: "Sisyphus"
  agent_description: "智能任务编排专家"
  role: |
    你是 Sisyphus，一个资深的项目经理和技术架构师。
  positioning: |
    你是决策者和执行者，不是简单的信息整合者。
```

#### 3. 动态内容（运行时）
```python
{
    'user_input': "帮我分析项目架构",
    'repo': "/path/to/project",
    'workflow': "# 理解项目工作流\n...",
    'conversation_history': "...",
    'project_understanding_block': "【目录结构】\n..."
}
```

---

## 📋 Workflow 驱动

### Workflow 文件结构

```markdown
# 工作流名称

## 目标
明确这个工作流要达成什么目标

## 分析顺序（可选）
如果有特定的分析步骤，在这里说明

## 关键原则
告诉 Agent 应该遵循的原则

## 注意事项
### ✅ 应该做的
- 列出推荐的做法

### ❌ 不应该做的
- 列出应该避免的做法

## 可选工具调用
如果预取信息不够，可以调用的工具
```

### 示例：理解项目工作流

```markdown
# 理解项目工作流

## 目标
帮助用户快速理解当前项目的架构、功能、技术栈和设计思想。

## 分析顺序（从整体到细节）

### 1. 目录结构分析（整体布局）
先看【目录结构】，了解项目的整体组织方式：
- 识别主要模块和子系统（如 backend、frontend、docs 等）
- 找出配置文件位置（package.json、requirements.txt 等）
- 定位核心代码目录（src、lib、app 等）

### 2. 代码地图分析（核心架构）
再看【代码地图】，掌握核心代码和架构设计：
- 识别关键类和函数（高引用数 = 核心组件）
- 理解模块间的依赖关系（谁调用谁）
- 找出入口文件和主流程

### 3. 项目文档分析（背景信息）
最后看【项目文档】，补充背景和细节：
- README：项目简介、功能特性
- CONTRIBUTING：开发规范
- 技术栈和依赖版本

## 关键原则
- **提炼核心**：用 1-2 段话概括项目本质，不要逐条罗列
- **突出架构**：重点说明架构设计思想和核心流程
- **自然表达**：像资深工程师在做技术分享

## 注意事项

### ✅ 应该做的
- 综合三个维度（结构、代码、文档）给出整体理解
- 突出项目的核心价值和设计亮点
- 如果用户问到具体模块，可以深入分析该部分

### ❌ 不应该做的
- 不要逐条罗列文件和目录
- 不要简单复述文档内容
- 不要过度关注配置细节

## 可选工具调用

### 优先使用 LSP 工具（精确、高效）
- `lsp_symbols` - 查看文件或整个项目的符号
- `lsp_goto_definition` - 追踪函数/类的定义位置
- `lsp_find_references` - 查找符号的所有引用

### 其次使用文件读取
- `read_file` - 读取关键文件
- `batch_read_files` - 批量读取多个相关文件

### 最后使用搜索工具（模糊查询）
- `semantic_code_search` - 语义搜索
- `text_search` 或 `regex_search` - 文本搜索
```

---

## 🎭 内置 Workflow 列表

### 1. general_chat - 通用对话
**适用场景**：
- 简单问候
- 闲聊
- 不涉及代码的对话

**预取级别**：None

**特点**：
- 不调用工具
- 快速响应
- 友好交流

---

### 2. need_code_context - 需要代码上下文
**适用场景**：
- 询问代码实现
- 查找函数定义
- 了解代码逻辑

**预取级别**：Light（代码地图）

**推荐工具**：
- lsp_symbols
- lsp_goto_definition
- read_file

---

### 3. understand_project - 理解项目
**适用场景**：
- 分析项目架构
- 了解项目结构
- 技术栈调研

**预取级别**：Full（目录结构 + 代码地图 + 项目文档）

**分析顺序**：
1. 目录结构（整体布局）
2. 代码地图（核心架构）
3. 项目文档（背景信息）

**推荐工具**：
- lsp_symbols
- lsp_find_references
- read_file

---

### 4. write_code - 编写代码
**适用场景**：
- 实现新功能
- 修复 Bug
- 添加代码

**预取级别**：Medium（目录结构 + 代码地图）

**关键原则**：
- 先理解现有代码
- 保持代码风格一致
- 添加必要的注释
- 确保代码可运行

**推荐工具**：
- lsp_diagnostics（检查错误）
- lsp_goto_definition（查看定义）
- read_file（读取相关文件）
- write_file（写入代码）
- search_replace（精确修改）

---

### 5. refactor_code - 重构代码
**适用场景**：
- 代码重构
- 优化结构
- 提取函数/类
- 重命名符号

**预取级别**：Medium（目录结构 + 代码地图）

**关键原则**：
- 保持功能不变
- 渐进式重构
- 使用 LSP 工具（精确）
- 重构后运行测试

**推荐工具**：
- lsp_find_references（查找所有引用）
- lsp_goto_definition（查看定义）
- search_replace（精确替换）
- lsp_diagnostics（检查错误）

---

### 6. write_test - 编写测试
**适用场景**：
- 编写单元测试
- 添加测试用例
- 提高测试覆盖率

**预取级别**：Medium（目录结构 + 代码地图）

**关键原则**：
- 测试要全面（正常 + 异常）
- 测试要独立（不依赖其他测试）
- 测试要清晰（命名要明确）
- 使用合适的断言

**推荐工具**：
- lsp_goto_definition（查看被测代码）
- read_file（读取被测文件）
- write_file（写入测试）
- run_test（运行测试）

---

### 7. run_test - 运行测试
**适用场景**：
- 运行测试
- 检查测试结果
- 修复失败的测试

**预取级别**：None

**关键原则**：
- 先运行测试
- 分析失败原因
- 修复后再次运行

**推荐工具**：
- run_test（运行测试）
- lsp_diagnostics（检查错误）
- read_file（读取测试文件）

---

## 🔧 创建自定义 Workflow

### 步骤 1：创建 Skill

```yaml
# skills/my-skill/skill.yaml
name: my-skill
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
```

### 步骤 2：创建 Workflow 文件

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
- 推荐做法2

### ❌ 不应该做的
- 避免做法1
- 避免做法2

## 可选工具调用
- 工具1 - 用途
- 工具2 - 用途
```

### 步骤 3：创建意图配置

```yaml
# skills/my-skill/intents.yaml
intents:
  - name: my_intent
    description: "我的自定义意图"
    keywords:
      - "关键词1"
      - "关键词2"
    workflow: "my_workflow.md"
    prefetch_level: "medium"  # none/light/medium/full
```

### 步骤 4：使用

```bash
python backend/daoyoucode.py chat --skill my-skill
```

---

## 📊 新旧对比

| 维度 | 旧架构（1.0） | 新架构（2.0） |
|------|--------------|--------------|
| **Agent 定义** | Python 类 | YAML 配置 |
| **行为定义** | 硬编码 | Workflow 文件 |
| **配置方式** | 分散（Python + YAML + MD） | 统一（YAML + MD） |
| **开发成本** | 高（需要写代码） | 低（只需配置） |
| **维护成本** | 高（修改需要重启） | 低（热更新） |
| **扩展性** | 低（需要写新类） | 高（只需加文件） |
| **学习曲线** | 陡（需要懂 Python） | 平（只需懂 YAML） |

---

## 🎯 最佳实践

### 1. Workflow 编写

**✅ 好的 Workflow**：
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
```

**❌ 不好的 Workflow**：
```markdown
# 理解项目

## 步骤
1. 读取所有文件
2. 分析所有代码
3. 输出详细报告

## 输出格式
必须按照以下格式输出：
- 项目名称：xxx
- 技术栈：xxx
- 文件列表：xxx
```

**问题**：
- 步骤太死板（不灵活）
- 限制输出格式（限制 LLM 发挥）
- 没有指导原则（不知道为什么这么做）

### 2. 意图设计

**✅ 好的意图**：
```yaml
- name: understand_project
  keywords: ["理解", "分析", "架构", "项目结构"]
  workflow: "understand_project.md"
  prefetch_level: "full"
```

**❌ 不好的意图**：
```yaml
- name: up  # 名称不清晰
  keywords: ["看看"]  # 关键词太模糊
  workflow: "workflow1.md"  # 文件名不清晰
  prefetch_level: "full"  # 可能不需要 full
```

### 3. 工具选择

**优先级**：
1. LSP 工具（精确、高效）
2. 文件读取（直接、快速）
3. 搜索工具（模糊、兜底）

**示例**：
```markdown
## 可选工具调用

### 优先使用 LSP 工具
- lsp_symbols - 查看符号
- lsp_goto_definition - 追踪定义
- lsp_find_references - 查找引用

### 其次使用文件读取
- read_file - 读取文件
- batch_read_files - 批量读取

### 最后使用搜索工具
- semantic_code_search - 语义搜索
- text_search - 文本搜索
```

---

## 🚀 高级用法

### 1. 多意图组合

```yaml
# intents.yaml
intents:
  - name: refactor_and_test
    keywords: ["重构并测试", "重构+测试"]
    workflows:
      - "refactor_code.md"
      - "write_test.md"
    prefetch_level: "medium"
```

### 2. 条件工作流

```yaml
# intents.yaml
intents:
  - name: fix_bug
    keywords: ["修复", "bug", "错误"]
    workflow: "fix_bug.md"
    prefetch_level: "medium"
    conditions:
      - if: "has_test_file"
        then: "run_test_first"
```

### 3. 自定义预取

```yaml
# skill.yaml
project_understanding:
  use_intent: true
  doc_chars: 6000      # 增加文档字符数
  struct_chars: 8000   # 增加结构字符数
  repomap_chars: 15000 # 增加代码地图字符数
  max_chars: 30000     # 增加总字符数
```

---

## 📝 相关文档

- [编排器介绍](./02_ORCHESTRATORS编排器介绍_NEW.md)
- [工具参考](./04_TOOLS工具参考.md)
- [Skill 配置示例](../skills/sisyphus-orchestrator/skill.yaml)
- [Workflow 示例](../skills/sisyphus-orchestrator/prompts/workflows/)

---

## 🤔 FAQ

### Q1: 为什么要从 Agent 类改为 Workflow？

**A**: 
- 更灵活：修改行为只需编辑 MD 文件
- 更简单：不需要写 Python 代码
- 更易维护：配置统一，易于理解
- 热更新：无需重启服务

### Q2: Workflow 和 Prompt 有什么区别？

**A**:
- Prompt：完整的输入给 LLM（模板 + 固定内容 + 动态内容）
- Workflow：Prompt 的一部分，定义任务的执行方式

### Q3: 如何调试 Workflow？

**A**:
```bash
# 1. 查看日志
python backend/daoyoucode.py chat --skill my-skill --verbose

# 2. 检查意图识别
[意图识别] 识别到意图: my_intent

# 3. 检查工作流加载
[工作流] 加载工作流: workflows/my_workflow.md

# 4. 检查 Prompt 构建
[Prompt] 最终 Prompt 长度: 5234 字符
```

### Q4: 可以在 Workflow 中调用其他 Workflow 吗？

**A**: 
目前不支持，但可以通过多意图组合实现类似效果：
```yaml
workflows:
  - "workflow1.md"
  - "workflow2.md"
```

### Q5: Workflow 文件可以使用变量吗？

**A**:
可以，使用 `{{variable}}` 语法：
```markdown
## 当前任务
用户想要{{user_input}}

## 项目路径
{{repo}}
```
