# Skill系统完整指南

> 配置驱动的Agent任务编排系统

## 📍 Skill目录位置

```
项目根目录/
├── backend/                    # 后端代码
├── frontend/                   # 前端代码
├── skills/                     # ⭐ Skill配置目录（在这里！）
│   ├── chat-assistant/         # 对话助手Skill
│   ├── programming/            # 编程Skill
│   ├── translation/            # 翻译Skill
│   ├── code-analysis/          # 代码分析Skill
│   ├── code-exploration/       # 代码搜索Skill
│   ├── refactoring/            # 重构Skill
│   ├── testing/                # 测试Skill
│   └── README.md
└── ...
```

**位置**: `项目根目录/skills/`

---

## 🎯 Skill系统概览

### 什么是Skill？

Skill是一个**配置驱动的任务单元**，包含：
- Agent选择（谁来执行）
- 编排器选择（如何执行）
- Prompt模板（如何指导）
- 工具配置（可以用什么）
- 权限配置（可以做什么）

### Skill vs Agent

| 概念 | 职责 | 配置位置 |
|------|------|----------|
| Agent | 执行者（决策和调用工具） | `backend/daoyoucode/agents/builtin/` |
| Skill | 任务配置（如何使用Agent） | `skills/` |

**关系**：
```
Skill（任务配置）→ 选择 → Agent（执行者）→ 调用 → 工具（实际操作）
```

---

## 📁 Skill目录结构

### 标准结构

```
skills/
├── chat-assistant/              # Skill名称
│   ├── skill.yaml              # Skill配置文件 ⭐
│   └── prompts/                # Prompt目录
│       └── chat_assistant.md   # Prompt模板 ⭐
│
├── programming/
│   ├── skill.yaml
│   └── prompts/
│       └── programmer.md
│
└── README.md                    # Skill系统说明
```

### 两个核心文件

1. **skill.yaml** - Skill配置
   - Agent选择
   - 编排器选择
   - LLM配置
   - 工具配置
   - 权限配置

2. **prompts/*.md** - Prompt模板
   - 角色定义
   - 能力说明
   - 工作方式
   - 输出格式

---

## 📝 Skill配置详解

### chat-assistant/skill.yaml

```yaml
name: chat_assistant
version: 1.0.0
description: 交互式对话助手，支持代码理解、编写和项目分析

# ========== 核心配置 ==========

# 编排器：如何执行任务
orchestrator: react              # ReAct循环（推理-行动）

# Agent：谁来执行
agent: MainAgent                 # 主对话Agent

# Prompt：如何指导
prompt:
  file: prompts/chat_assistant.md

# ========== LLM配置 ==========

llm:
  model: qwen-max               # 使用的模型
  temperature: 0.7              # 创造性（0-1）
  max_tokens: 4000              # 最大token数

# ========== 工具配置 ==========

tools:
  - repo_map                    # 生成代码地图
  - get_repo_structure          # 获取目录结构
  - read_file                   # 读取文件
  - text_search                 # 文本搜索
  - regex_search                # 正则搜索
  - write_file                  # 写入文件
  - list_files                  # 列出目录

# ========== 中间件 ==========

middleware:
  - context_management          # 上下文管理
  - memory_integration          # 记忆集成

# ========== 权限配置 ==========

permissions:
  read:
    - pattern: "*"
      permission: allow         # 允许读取所有文件
  write:
    - pattern: "*.py"
      permission: allow         # 允许写入Python文件
    - pattern: "*.js"
      permission: allow
    - pattern: "*.ts"
      permission: allow
    - pattern: "*.md"
      permission: allow
  execute:
    - pattern: "*"
      permission: deny          # 禁止执行命令

# ========== 输入输出 ==========

inputs:
  - name: user_input
    type: string
    required: true
    description: 用户输入的问题或指令
  
  - name: session_id
    type: string
    required: false
    description: 会话ID

outputs:
  - name: response
    type: string
    description: AI的响应内容
  
  - name: tools_used
    type: array
    description: 使用的工具列表

# ========== Hook配置 ==========

hooks:
  - logging                     # 日志记录
  - metrics                     # 指标统计
  - memory_save                 # 保存记忆

# ========== 元数据 ==========

metadata:
  category: assistant
  cost: MEDIUM
  triggers:
    - "对话"
    - "提问"
    - "代码编写"
  features:
    - "自动工具调用"
    - "推理循环"
    - "记忆集成"
```

---

## 📄 Prompt模板详解

### chat-assistant/prompts/chat_assistant.md

```markdown
# DaoyouCode AI助手

你是DaoyouCode AI助手，基于18大核心系统。

## 你的能力

- 智能代码编写和重构
- 多Agent协作
- 完整的记忆系统
- **主动调用工具理解项目**

## 你的风格

- 专业但友好
- 简洁而清晰
- 注重实用性

## 可用工具

### 1. repo_map
生成智能代码地图
- **使用场景**: 用户问"项目结构"、"有哪些模块"

### 2. get_repo_structure
获取目录树
- **使用场景**: 用户问"目录结构"、"文件列表"

### 3. read_file
读取文件内容
- **使用场景**: 需要查看代码细节

## 工作方式

### ReAct循环

1. **Thought（思考）**: 分析用户问题
2. **Action（行动）**: 调用工具获取信息
3. **Observation（观察）**: 查看工具结果
4. **Thought（再思考）**: 决定下一步
5. **Answer（回答）**: 给出最终答案

## 重要原则

1. **主动调用工具**: 不要说"我需要查看"，直接调用
2. **链式推理**: 可以多次调用工具
3. **基于事实**: 只基于工具返回的内容回答

## 用户输入

{{user_input}}

## 上下文

{% if files %}
已加载的文件:
{% for file in files %}
- {{file}}
{% endfor %}
{% endif %}

## 开始推理

请使用ReAct循环回答用户问题。
```

**关键特性**：
- ✅ 使用Jinja2模板语法
- ✅ 支持变量插值 `{{user_input}}`
- ✅ 支持条件判断 `{% if files %}`
- ✅ 支持循环 `{% for file in files %}`

---

## 🔄 Skill执行流程

### 完整流程

```
用户输入
    ↓
execute_skill("chat_assistant", user_input, context)
    ↓
1. 加载Skill配置
    └─ 读取 skills/chat-assistant/skill.yaml
    └─ 解析配置
    {
        name: "chat_assistant",
        orchestrator: "react",
        agent: "MainAgent",
        prompt: {file: "prompts/chat_assistant.md"},
        llm: {model: "qwen-max", ...},
        tools: ["repo_map", "read_file", ...],
        ...
    }
    ↓
2. 获取编排器
    └─ get_orchestrator("react")
    └─ 返回 ReActOrchestrator 实例
    ↓
3. 执行编排器
    └─ orchestrator.execute(skill, user_input, context)
        ↓
        3.1 获取Agent
            └─ agent = get_agent("MainAgent")
        ↓
        3.2 加载Prompt
            └─ 读取 prompts/chat_assistant.md
            └─ 使用Jinja2渲染
            └─ 插入 user_input、files、context等
        ↓
        3.3 执行Agent
            └─ agent.execute(rendered_prompt, context)
                ↓
                3.3.1 加载Memory
                    └─ 对话历史、用户偏好
                ↓
                3.3.2 调用LLM
                    └─ client = client_manager.get_client("qwen-max")
                    └─ response = await client.chat(messages, tools)
                        ↓
                        3.3.2.1 ReAct循环
                            ├─ Thought: LLM思考
                            ├─ Action: 调用工具
                            ├─ Observation: 工具结果
                            ├─ Thought: 再思考
                            └─ Answer: 最终答案
                ↓
                3.3.3 保存Memory
                    └─ 保存对话历史
        ↓
        3.4 返回结果
    ↓
4. 返回结果
    {
        success: true,
        content: "AI响应",
        tools_used: ["repo_map", "read_file"],
        reasoning: "推理过程",
        ...
    }
```

---

## 🎨 已有的Skills

### 1. chat-assistant - 对话助手

**用途**: 交互式对话，代码理解和编写

**配置**:
- Agent: MainAgent
- 编排器: react（ReAct循环）
- 模型: qwen-max
- 工具: repo_map, read_file, text_search等

**使用场景**:
- 用户提问
- 代码编写
- 项目分析

---

### 2. programming - 编程服务

**用途**: 专业代码编写和调试

**配置**:
- Agent: ProgrammerAgent
- 编排器: simple
- 模型: qwen-coder-plus
- 工具: 文件操作、代码搜索

**使用场景**:
- 编写新代码
- 修复bug
- 代码优化

---

### 3. translation - 翻译服务

**用途**: 专业翻译

**配置**:
- Agent: TranslatorAgent
- 编排器: simple
- 模型: qwen-max
- 工具: 无（纯文本处理）

**使用场景**:
- 文档翻译
- 代码注释翻译
- 多语言支持

---

### 4. code-analysis - 代码分析

**用途**: 架构分析和代码审查

**配置**:
- Agent: CodeAnalyzerAgent
- 编排器: simple
- 模型: qwen-max
- 工具: repo_map, read_file（只读）

**灵感来源**: oh-my-opencode Oracle

**使用场景**:
- 架构分析
- 代码审查
- 最佳实践建议

---

### 5. code-exploration - 代码搜索

**用途**: 快速查找代码位置

**配置**:
- Agent: CodeExplorerAgent
- 编排器: parallel（并行搜索）
- 模型: qwen-coder-plus
- 工具: text_search, regex_search, ast_grep

**灵感来源**: oh-my-opencode Explore

**使用场景**:
- 查找函数定义
- 查找类实现
- 查找使用位置

---

### 6. refactoring - 代码重构

**用途**: 安全渐进式重构

**配置**:
- Agent: RefactorMasterAgent
- 编排器: simple
- 模型: qwen-coder-plus
- 工具: 文件操作、测试工具

**使用场景**:
- 代码重构
- 结构优化
- 技术债务清理

---

### 7. testing - 测试服务

**用途**: 测试编写和修复

**配置**:
- Agent: TestExpertAgent
- 编排器: simple
- 模型: deepseek-coder
- 工具: 文件操作、测试执行

**使用场景**:
- 编写单元测试
- 修复失败测试
- 提高测试覆盖率

---

## 🚀 创建新Skill

### 步骤1: 创建目录结构

```bash
# 在项目根目录下
mkdir -p skills/my-skill/prompts
```

### 步骤2: 创建skill.yaml

```yaml
# skills/my-skill/skill.yaml

name: my_skill
version: 1.0.0
description: 我的自定义Skill

orchestrator: simple
agent: MainAgent

prompt:
  file: prompts/my_prompt.md

llm:
  model: qwen-max
  temperature: 0.7
  max_tokens: 2000

tools:
  - read_file
  - write_file

permissions:
  read:
    - pattern: "*"
      permission: allow
  write:
    - pattern: "*.txt"
      permission: allow

inputs:
  - name: user_input
    type: string
    required: true

outputs:
  - name: response
    type: string
```

### 步骤3: 创建Prompt模板

```markdown
# skills/my-skill/prompts/my_prompt.md

# 我的自定义助手

你是一个专门的助手，负责...

## 你的能力

- 能力1
- 能力2

## 可用工具

### read_file
读取文件内容

### write_file
写入文件内容

## 用户输入

{{user_input}}

## 开始工作

请根据用户输入完成任务。
```

### 步骤4: 使用Skill

```python
from daoyoucode.agents.executor import execute_skill

result = await execute_skill(
    skill_name="my_skill",
    user_input="用户输入",
    context={"key": "value"}
)

print(result['content'])
```

---

## 💡 最佳实践

### 1. Skill命名

✅ **推荐**:
- `chat-assistant` - 小写字母 + 连字符
- `code-analysis` - 清晰描述功能
- `programming` - 简洁明了

❌ **不推荐**:
- `ChatAssistant` - 驼峰命名
- `chat_assistant` - 下划线（保留给Python）
- `ca` - 缩写不清晰

---

### 2. Prompt编写

✅ **推荐**:
```markdown
# 角色定义
你是XXX助手

## 你的能力
- 能力1
- 能力2

## 可用工具
### tool1
描述和使用场景

## 工作方式
1. 步骤1
2. 步骤2

## 用户输入
{{user_input}}
```

❌ **不推荐**:
```markdown
你是助手，帮助用户。

用户输入: {{user_input}}
```

---

### 3. 工具配置

✅ **推荐**:
```yaml
tools:
  - repo_map          # 只列出需要的工具
  - read_file
  - text_search
```

❌ **不推荐**:
```yaml
tools:
  - "*"               # 不要使用通配符
```

---

### 4. 权限配置

✅ **推荐**:
```yaml
permissions:
  read:
    - pattern: "*"
      permission: allow
  write:
    - pattern: "*.py"    # 明确指定可写文件类型
      permission: allow
  execute:
    - pattern: "*"
      permission: deny    # 默认禁止执行
```

❌ **不推荐**:
```yaml
permissions:
  write:
    - pattern: "*"        # 不要允许写入所有文件
      permission: allow
```

---

## 🔍 Skill加载机制

### SkillLoader

```python
# backend/daoyoucode/agents/core/skill.py

class SkillLoader:
    def __init__(self, skills_dir: str = None):
        if skills_dir is None:
            # 默认为项目根目录的skills/
            project_root = Path(__file__).parent.parent.parent.parent.parent
            skills_dir = project_root / "skills"
        
        self.skills_dir = Path(skills_dir)
        self._skills: Dict[str, SkillConfig] = {}
        self._load_all_skills()
    
    def _load_all_skills(self):
        """加载所有Skill"""
        for skill_dir in self.skills_dir.iterdir():
            if skill_dir.is_dir():
                skill_file = skill_dir / "skill.yaml"
                if skill_file.exists():
                    skill = self._load_skill(skill_file)
                    self._skills[skill.name] = skill
    
    def get_skill(self, name: str) -> Optional[SkillConfig]:
        """获取Skill配置"""
        return self._skills.get(name)
```

### 加载流程

```
程序启动
    ↓
get_skill_loader()
    ↓
SkillLoader.__init__()
    ↓
_load_all_skills()
    ↓
遍历 skills/ 目录
    ├─ skills/chat-assistant/
    │   └─ 加载 skill.yaml
    ├─ skills/programming/
    │   └─ 加载 skill.yaml
    └─ ...
    ↓
缓存所有Skill配置
    {
        "chat_assistant": SkillConfig(...),
        "programming": SkillConfig(...),
        ...
    }
```

---

## 📊 Skill vs Agent vs 编排器

### 对比表

| 概念 | 职责 | 配置位置 | 数量 |
|------|------|----------|------|
| Skill | 任务配置 | `skills/` | 7个 |
| Agent | 执行者 | `backend/daoyoucode/agents/builtin/` | 7个 |
| 编排器 | 执行策略 | `backend/daoyoucode/agents/orchestrators/` | 3个 |
| 工具 | 实际操作 | `backend/daoyoucode/agents/tools/` | 25个 |

### 关系图

```
Skill（任务配置）
    ├─ 选择 → Agent（执行者）
    │           └─ 调用 → 工具（实际操作）
    │
    └─ 选择 → 编排器（执行策略）
                ├─ simple: 简单执行
                ├─ react: ReAct循环
                └─ parallel: 并行执行
```

---

## 🎯 总结

### Skill目录位置

```
项目根目录/skills/  ← 在这里！
```

### Skill核心文件

1. `skill.yaml` - Skill配置
2. `prompts/*.md` - Prompt模板

### Skill执行流程

```
execute_skill()
  → 加载Skill配置
  → 获取编排器
  → 获取Agent
  → 加载Prompt
  → 调用LLM
  → 返回结果
```

### 创建新Skill

1. 创建目录 `skills/my-skill/`
2. 创建 `skill.yaml`
3. 创建 `prompts/my_prompt.md`
4. 使用 `execute_skill("my_skill", ...)`

---

## 🔗 相关文档

- [Skill系统README](../skills/README.md)
- [Agent架构](AGENT_ARCHITECTURE.md)
- [可插拔架构](PLUGGABLE_ARCHITECTURE.md)
- [调用链路分析](CALL_CHAIN_ANALYSIS.md)

---

**现在你知道Skill目录在哪里了！** 🎉

