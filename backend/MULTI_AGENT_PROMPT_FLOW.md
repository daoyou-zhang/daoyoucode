# 多Agent Prompt流转图

## 简化版流程图

```
用户请求："重构登录模块并添加测试"
         ↓
    加载Skill配置
         ↓
┌────────────────────────────────────────────┐
│ skills/sisyphus-orchestrator/skill.yaml    │
│                                            │
│ agents:                                    │
│   - sisyphus        ← 主Agent              │
│   - code_analyzer   ← 辅助Agent 1          │
│   - programmer      ← 辅助Agent 2          │
│   - test_expert     ← 辅助Agent 3          │
│                                            │
│ prompt:                                    │
│   file: prompts/sisyphus.md  ← 只给主Agent │
└────────────────────────────────────────────┘
         ↓
    多Agent编排器
         ↓
┌────────────────────────────────────────────┐
│ 步骤1：并行执行辅助Agent                    │
└────────────────────────────────────────────┘
         ↓
    ┌────────────────┬────────────────┬────────────────┐
    ↓                ↓                ↓                ↓
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ Agent 1 │    │ Agent 2 │    │ Agent 3 │    │ Agent 4 │
│ code_   │    │program- │    │ test_   │    │ ...     │
│analyzer │    │mer      │    │expert   │    │         │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
    ↓                ↓                ↓                ↓
使用自己的      使用自己的      使用自己的      使用自己的
默认Prompt     默认Prompt     默认Prompt     默认Prompt
    ↓                ↓                ↓                ↓
"架构分析..."  "代码建议..."  "测试策略..."  "..."
    ↓                ↓                ↓                ↓
    └────────────────┴────────────────┴────────────────┘
                     ↓
            收集辅助Agent结果
                     ↓
         helper_results = [
           {agent: 'code_analyzer', content: '...'},
           {agent: 'programmer', content: '...'},
           {agent: 'test_expert', content: '...'}
         ]
                     ↓
┌────────────────────────────────────────────┐
│ 步骤2：执行主Agent                          │
└────────────────────────────────────────────┘
                     ↓
              ┌─────────────┐
              │   Sisyphus  │
              │  (主Agent)  │
              └─────────────┘
                     ↓
         使用Skill配置的Prompt
         (prompts/sisyphus.md)
                     ↓
         可以看到helper_results
                     ↓
         "综合分析和执行计划..."
                     ↓
              返回给用户
```

---

## 详细版：Prompt来源

```
┌─────────────────────────────────────────────────────────┐
│                    Skill配置                             │
│  skills/sisyphus-orchestrator/skill.yaml                │
│                                                         │
│  agents: [sisyphus, code_analyzer, programmer, ...]     │
│  prompt: {file: prompts/sisyphus.md}  ← 主Agent用       │
└─────────────────────────────────────────────────────────┘
                          ↓
        ┌─────────────────┴─────────────────┐
        ↓                                   ↓
┌───────────────────┐            ┌───────────────────┐
│   辅助Agent执行    │            │   主Agent执行      │
└───────────────────┘            └───────────────────┘
        ↓                                   ↓
┌───────────────────┐            ┌───────────────────┐
│ code_analyzer     │            │ sisyphus          │
│ .execute(         │            │ .execute(         │
│   prompt_source=  │            │   prompt_source=  │
│   {'use_agent_    │            │   {'file':        │
│    default': True}│            │    'prompts/      │
│ )                 │            │     sisyphus.md'} │
└───────────────────┘            │ )                 │
        ↓                        └───────────────────┘
        ↓                                   ↓
┌───────────────────┐            ┌───────────────────┐
│ _load_prompt()    │            │ _load_prompt()    │
│                   │            │                   │
│ 检测到            │            │ 检测到            │
│ use_agent_default │            │ file参数          │
│                   │            │                   │
│ 返回：            │            │ 返回：            │
│ self.config.      │            │ 从文件加载        │
│ system_prompt     │            │ prompts/          │
└───────────────────┘            │ sisyphus.md       │
        ↓                        └───────────────────┘
        ↓                                   ↓
┌───────────────────┐            ┌───────────────────┐
│ Agent默认Prompt   │            │ Skill配置的Prompt │
│                   │            │                   │
│ 来源：            │            │ 来源：            │
│ code_analyzer.py  │            │ skills/sisyphus-  │
│ 中的              │            │ orchestrator/     │
│ system_prompt     │            │ prompts/          │
│ 字段              │            │ sisyphus.md       │
└───────────────────┘            └───────────────────┘
        ↓                                   ↓
"你是代码分析专家..."        "你是Sisyphus，主编排Agent..."
        ↓                                   ↓
    调用LLM                             调用LLM
        ↓                                   ↓
    返回结果                            返回结果
```

---

## Prompt内容对比

### 辅助Agent的Prompt（code_analyzer）

**位置**：`backend/daoyoucode/agents/builtin/code_analyzer.py`

```python
class CodeAnalyzerAgent(BaseAgent):
    def __init__(self):
        config = AgentConfig(
            name="code_analyzer",
            system_prompt="""
你是代码分析专家。

职责：
- 分析代码架构
- 识别问题
- 提供改进建议

工具：
- repo_map
- read_file
- text_search
- get_diagnostics
- parse_ast

注意：
- 你是辅助Agent
- 专注于分析，不要编写代码
- 提供清晰的分析报告
"""
        )
```

**特点**：
- 简洁明了
- 专注于单一职责
- 不需要知道其他Agent

---

### 主Agent的Prompt（sisyphus）

**位置**：`skills/sisyphus-orchestrator/prompts/sisyphus.md`

```markdown
# Sisyphus - 主编排Agent

你是Sisyphus，负责任务分解和Agent调度。

## 可用的辅助Agent

你可以协调以下辅助Agent：

1. **code_analyzer**（架构顾问）
   - 擅长：架构分析、代码审查
   - 何时使用：需要理解代码架构

2. **programmer**（编程专家）
   - 擅长：代码编写、Bug修复
   - 何时使用：编写新功能

3. **test_expert**（测试专家）
   - 擅长：测试编写、TDD
   - 何时使用：编写单元测试

## 辅助Agent的结果

{% if helper_results %}
系统已自动执行辅助Agent，结果如下：

{% for result in helper_results %}
### {{ result.agent }}
{{ result.content }}
{% endfor %}
{% endif %}

## 你的任务

基于辅助Agent的分析，制定完整的执行计划。

输出格式：
1. 任务分析
2. 执行计划
3. Agent建议
4. 最终方案
5. 下一步
```

**特点**：
- 详细完整
- 知道所有辅助Agent
- 可以看到辅助Agent的结果
- 负责综合和决策

---

## Context传递

```
┌─────────────────────────────────────────────────────┐
│ 辅助Agent执行                                        │
├─────────────────────────────────────────────────────┤
│ code_analyzer.execute(                              │
│     user_input="重构登录模块",                       │
│     context={                                       │
│         'session_id': 'xxx',                        │
│         'user_id': 'yyy'                            │
│     }                                               │
│ )                                                   │
│ → 返回："架构分析：登录模块耦合度高..."              │
└─────────────────────────────────────────────────────┘
                        ↓
                收集所有结果
                        ↓
┌─────────────────────────────────────────────────────┐
│ 主Agent执行                                          │
├─────────────────────────────────────────────────────┤
│ sisyphus.execute(                                   │
│     user_input="重构登录模块",                       │
│     context={                                       │
│         'session_id': 'xxx',                        │
│         'user_id': 'yyy',                           │
│         'helper_results': [  ← 新增！               │
│             {                                       │
│                 'agent': 'code_analyzer',           │
│                 'content': '架构分析：...'           │
│             },                                      │
│             {                                       │
│                 'agent': 'programmer',              │
│                 'content': '建议：...'               │
│             },                                      │
│             {                                       │
│                 'agent': 'test_expert',             │
│                 'content': '测试策略：...'           │
│             }                                       │
│         ]                                           │
│     }                                               │
│ )                                                   │
└─────────────────────────────────────────────────────┘
                        ↓
                Prompt渲染
                        ↓
┌─────────────────────────────────────────────────────┐
│ Jinja2模板渲染                                       │
├─────────────────────────────────────────────────────┤
│ 原始Prompt：                                         │
│ {% if helper_results %}                             │
│ {% for result in helper_results %}                  │
│ ### {{ result.agent }}                              │
│ {{ result.content }}                                │
│ {% endfor %}                                        │
│ {% endif %}                                         │
│                                                     │
│ 渲染后：                                             │
│ ### code_analyzer                                   │
│ 架构分析：登录模块耦合度高...                         │
│                                                     │
│ ### programmer                                      │
│ 建议：拆分为3个模块...                               │
│                                                     │
│ ### test_expert                                     │
│ 测试策略：单元测试 + 集成测试...                      │
└─────────────────────────────────────────────────────┘
                        ↓
                    调用LLM
                        ↓
                "综合分析和计划..."
```

---

## 配置文件对应关系

```
项目结构：

skills/
├── sisyphus-orchestrator/
│   ├── skill.yaml              ← Skill配置
│   └── prompts/
│       └── sisyphus.md         ← 主Agent的Prompt
│
├── oracle/
│   ├── skill.yaml
│   └── prompts/
│       └── oracle.md
│
└── librarian/
    ├── skill.yaml
    └── prompts/
        └── librarian.md

backend/daoyoucode/agents/builtin/
├── sisyphus.py                 ← 主Agent定义（Prompt在Skill中）
├── code_analyzer.py            ← 辅助Agent定义（Prompt在这里）
├── programmer.py               ← 辅助Agent定义（Prompt在这里）
└── test_expert.py              ← 辅助Agent定义（Prompt在这里）
```

**关键点**：
- **主Agent**：Prompt在Skill配置中（`skills/*/prompts/*.md`）
- **辅助Agent**：Prompt在Agent定义中（`builtin/*.py`的`system_prompt`）

---

## 为什么辅助Agent不用Skill配置？

### 原因1：复用性

```yaml
# Skill A
agents:
  - sisyphus
  - code_analyzer  ← 使用默认Prompt

# Skill B
agents:
  - oracle
  - code_analyzer  ← 同一个Agent，同样的Prompt

# Skill C
agents:
  - main_agent
  - code_analyzer  ← 同一个Agent，同样的Prompt
```

**如果每个Skill都配置Prompt**：
- 需要复制3次相同的Prompt
- 修改Prompt需要改3个地方
- 容易不一致

**使用默认Prompt**：
- 只定义一次
- 修改一处生效
- 保证一致性

---

### 原因2：简化配置

```yaml
# 如果每个Agent都配置Prompt（不推荐）
agents:
  - name: sisyphus
    prompt: prompts/sisyphus.md
  - name: code_analyzer
    prompt: prompts/code_analyzer.md
  - name: programmer
    prompt: prompts/programmer.md
  - name: test_expert
    prompt: prompts/test_expert.md

# 当前设计（推荐）
agents:
  - sisyphus          # 主Agent（使用Skill的prompt配置）
  - code_analyzer     # 辅助Agent（使用默认Prompt）
  - programmer        # 辅助Agent（使用默认Prompt）
  - test_expert       # 辅助Agent（使用默认Prompt）

prompt:
  file: prompts/sisyphus.md  # 只配置主Agent
```

**更简洁！**

---

### 原因3：职责清晰

- **主Agent**：需要定制化Prompt（每个Skill不同）
- **辅助Agent**：通用Prompt（所有Skill相同）

---

## 总结

### 核心原则

1. **一个Skill配置 = 一个主Agent的Prompt**
2. **辅助Agent使用默认Prompt**
3. **主Agent通过Context看到辅助Agent的结果**
4. **不需要传递多个Prompt**

### 配置清单

```yaml
# skills/my-skill/skill.yaml
name: my-skill
orchestrator: multi_agent
collaboration_mode: main_with_helpers

agents:
  - main_agent        # 主Agent
  - helper_agent_1    # 辅助Agent 1
  - helper_agent_2    # 辅助Agent 2

prompt:               # 只给主Agent用
  file: prompts/main.md

tools:                # 只给主Agent用
  - tool1
  - tool2

llm:                  # 只给主Agent用
  model: qwen-max
  temperature: 0.1
```

### 执行流程

```
1. 加载Skill配置
2. 并行执行辅助Agent（使用默认Prompt）
3. 收集辅助Agent结果
4. 执行主Agent（使用Skill配置的Prompt + 辅助Agent结果）
5. 返回主Agent的结果
```

---

**简单记忆**：Skill配置只管主Agent，辅助Agent自己管自己！
