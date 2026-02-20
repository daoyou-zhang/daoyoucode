# Skills 目录

> Skill驱动的Agent系统配置

---

## 目录结构

```
skills/
├── translation/              # 翻译服务
│   ├── skill.yaml
│   └── prompts/
│       └── translator.md
│
├── programming/              # 编程服务
│   ├── skill.yaml
│   └── prompts/
│       └── programmer.md
│
├── code-analysis/            # 代码分析
│   ├── skill.yaml
│   └── prompts/
│       └── oracle.md
│
├── code-exploration/         # 代码搜索
│   ├── skill.yaml
│   └── prompts/
│       └── explore.md
│
├── refactoring/              # 代码重构
│   ├── skill.yaml
│   └── prompts/
│       └── refactor.md
│
├── testing/                  # 测试编写和修复
│   ├── skill.yaml
│   └── prompts/
│       └── test.md
│
└── README.md                 # 本文件
```

---

## 已实现的Skills

### 1. translation - 翻译服务
- **Agent**: translator
- **模型**: qwen-max
- **用途**: 专业翻译服务
- **特点**: 准确、流畅、专业

### 2. programming - 编程服务
- **Agent**: programmer
- **模型**: qwen-coder-plus
- **用途**: 代码编写、调试、优化
- **特点**: 高质量代码、最佳实践

### 3. code-analysis - 代码分析
- **Agent**: code_analyzer
- **模型**: qwen-max
- **用途**: 架构分析、代码审查
- **特点**: 只读分析、务实建议

### 4. code-exploration - 代码搜索
- **Agent**: code_explorer
- **模型**: qwen-coder-plus
- **用途**: 快速查找代码位置
- **特点**: 并行搜索、结构化输出

### 5. refactoring - 代码重构
- **Agent**: refactor_master
- **模型**: qwen-coder-plus
- **用途**: 安全渐进式重构
- **特点**: 测试驱动、可回滚

### 6. testing - 测试服务
- **Agent**: test_expert
- **模型**: deepseek-coder
- **用途**: 测试编写和修复
- **特点**: TDD工作流、高覆盖率

---

## Skill配置格式

每个Skill包含两个文件：

### 1. skill.yaml - Skill配置

```yaml
name: skill-name
version: 1.0.0
description: Skill描述

# 编排器
orchestrator: simple

# Agent
agent: agent_name

# Prompt配置
prompt:
  file: prompts/prompt.md

# LLM配置
llm:
  model: qwen-max
  temperature: 0.7
  max_tokens: 2000

# 中间件
middleware:
  - context_management

# 权限（可选）
permissions:
  read:
    - pattern: "*"
      permission: allow

# 输入
inputs:
  - name: input_name
    type: string
    required: true
    description: 输入描述

# 输出
outputs:
  - name: output_name
    type: string
    description: 输出描述

# Hook（可选）
hooks:
  - logging
  - metrics

# 元数据（可选）
metadata:
  category: category_name
  cost: CHEAP/MEDIUM/EXPENSIVE
```

### 2. prompts/*.md - Prompt文件

Markdown格式的Prompt，包含：
- 角色定义
- 核心能力
- 工作原则
- 输出格式
- 注意事项

---

## 使用方式

### 方式1: 通过execute_skill

```python
from daoyoucode.agents import execute_skill

result = await execute_skill(
    skill_name='translation',
    user_input='翻译这段话',
    context={'target_language': 'en'}
)
```

### 方式2: 直接使用Agent

```python
from daoyoucode.agents.builtin import TranslatorAgent

agent = TranslatorAgent()
result = await agent.execute(
    prompt_source={'file': 'skills/translation/prompts/translator.md'},
    user_input='翻译这段话'
)
```

---

## 创建新Skill

### 步骤1: 创建目录结构

```bash
mkdir -p skills/my-skill/prompts
```

### 步骤2: 创建skill.yaml

```yaml
name: my-skill
version: 1.0.0
description: 我的Skill

orchestrator: simple
agent: my_agent

prompt:
  file: prompts/my-prompt.md

llm:
  model: qwen-max
  temperature: 0.7
```

### 步骤3: 创建prompt文件

```markdown
# skills/my-skill/prompts/my-prompt.md

你是...

## 核心能力
...
```

### 步骤4: 创建Agent（如果需要）

```python
# backend/daoyoucode/agents/builtin/my_agent.py
from ..core.agent import BaseAgent, AgentConfig

class MyAgent(BaseAgent):
    def __init__(self):
        config = AgentConfig(
            name="my_agent",
            description="我的Agent",
            model="qwen-max",
            temperature=0.7,
            system_prompt=""
        )
        super().__init__(config)
```

### 步骤5: 注册Agent

```python
# backend/daoyoucode/agents/builtin/__init__.py
from .my_agent import MyAgent

def register_builtin_agents():
    ...
    register_agent(MyAgent())
```

---

## 设计原则

1. **配置驱动** - 所有配置在YAML文件中
2. **Prompt分离** - Prompt独立存放在Markdown文件
3. **Agent简洁** - Agent只负责注册，不包含业务逻辑
4. **完全可插拔** - Agent、Prompt、Skill都可插拔

---

## 最佳实践

1. **Skill命名** - 使用小写字母和连字符，如 `code-analysis`
2. **Prompt文件** - 使用清晰的Markdown格式，包含完整说明
3. **版本管理** - 使用语义化版本号
4. **文档完整** - 每个Skill都要有清晰的描述和使用说明
5. **测试验证** - 创建Skill后要测试验证

---

## 参考资源

- [Agent系统文档](../backend/daoyoucode/agents/README.md)
- [编程Agent文档](../backend/PROGRAMMING_AGENTS.md)
