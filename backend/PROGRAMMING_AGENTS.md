# 编程辅助Agent系统

> 基于oh-my-opencode的智能体设计，采用Skill驱动架构

---

## 架构设计

```
Skill配置 (YAML) → Agent (Python) → Prompt (Markdown)
     ↓                  ↓                ↓
  可插拔            简洁注册          独立管理
```

### 设计原则

1. **配置驱动**: Skill用YAML配置，不硬编码
2. **Prompt分离**: Prompt独立存放在Markdown文件
3. **Agent简洁**: Agent只负责注册，不包含业务逻辑
4. **原汁原味**: 保留oh-my-opencode的原始Prompt内容

---

## 已实现的Agent

### 1. CodeAnalyzerAgent (Oracle)

**来源**: oh-my-opencode Oracle  
**用途**: 代码架构分析和技术咨询  
**模型**: qwen-max / gpt-5.2  
**温度**: 0.1

**文件结构**:
```
skills/code-analysis/
├── skill.yaml              # Skill配置
└── prompts/
    └── oracle.md          # 原始Prompt（来自oh-my-opencode）
```

**使用场景**:
- 复杂架构设计
- 代码审查
- 性能分析
- 安全审查
- 2次以上修复失败后的咨询

**特点**:
- 只读分析，不修改代码
- 提供Quick/Short/Medium/Large工作量估算
- 务实的最小化建议

---

### 2. CodeExplorerAgent (Explore)

**来源**: oh-my-opencode Explore  
**用途**: 代码库搜索和探索  
**模型**: qwen-coder-plus / grok-code  
**温度**: 0.1

**文件结构**:
```
skills/code-exploration/
├── skill.yaml
└── prompts/
    └── explore.md
```

**使用场景**:
- "在哪里实现X？"
- "哪些文件包含Y？"
- "查找代码Z"
- 多角度并行搜索

**特点**:
- 并行执行3+工具
- 返回绝对路径
- 结构化输出（files/answer/next_steps）

---

### 3. RefactorMasterAgent

**用途**: 代码重构专家  
**模型**: qwen-coder-plus  
**温度**: 0.2

**文件结构**:
```
skills/refactoring/
├── skill.yaml
└── prompts/
    └── refactor.md
```

**使用场景**:
- 提取方法/类
- 重命名
- 简化条件表达式
- 引入设计模式
- 性能优化

**特点**:
- 安全第一，渐进式重构
- 测试驱动
- 提供回滚方案

---

### 4. TestExpertAgent

**用途**: 测试编写和修复  
**模型**: deepseek-coder  
**温度**: 0.3

**文件结构**:
```
skills/testing/
├── skill.yaml
└── prompts/
    └── test.md
```

**使用场景**:
- 单元测试编写
- 测试修复
- TDD工作流
- 测试策略

**特点**:
- FIRST原则
- AAA模式
- 测试覆盖率分析

---

## 使用方式

### 方式1: 通过Skill执行

```python
from daoyoucode.agents import execute_skill

# 代码分析
result = await execute_skill(
    skill_name='code-analysis',
    user_input='分析这个模块的架构设计',
    context={
        'code_content': code,
        'file_path': 'src/main.py'
    }
)

# 代码搜索
result = await execute_skill(
    skill_name='code-exploration',
    user_input='在哪里实现了用户认证？',
    context={
        'search_scope': 'src/',
        'thoroughness': 'thorough'
    }
)
```

### 方式2: 直接使用Agent

```python
from daoyoucode.agents.builtin import CodeAnalyzerAgent

agent = CodeAnalyzerAgent()
result = await agent.execute(
    prompt_source={'file': 'skills/code-analysis/prompts/oracle.md'},
    user_input='分析这个模块',
    context={'code_content': code}
)
```

---

## Skill配置示例

```yaml
# skills/code-analysis/skill.yaml
name: code-analysis
version: 1.0.0
description: 代码架构分析和技术咨询

orchestrator: simple
agent: code_analyzer

# Prompt配置（使用独立文件）
prompt:
  file: prompts/oracle.md

llm:
  model: qwen-max
  temperature: 0.1
  max_tokens: 4000

# 权限（只读）
permissions:
  read:
    - pattern: "*"
      permission: allow
  write:
    - pattern: "*"
      permission: deny

# Hook
hooks:
  - logging
  - metrics

# 元数据
metadata:
  category: advisor
  cost: EXPENSIVE
  source: oh-my-opencode
```

---

## Agent注册

所有Agent在 `backend/daoyoucode/agents/builtin/__init__.py` 中注册：

```python
def register_builtin_agents():
    """注册所有内置Agent"""
    
    # 基础Agent
    register_agent(TranslatorAgent())
    register_agent(ProgrammerAgent())
    
    # 编程辅助Agent（借鉴oh-my-opencode）
    register_agent(CodeAnalyzerAgent())      # Oracle
    register_agent(CodeExplorerAgent())      # Explore
    register_agent(RefactorMasterAgent())    # 重构专家
    register_agent(TestExpertAgent())        # 测试专家
```

---

## 扩展新Agent

### 步骤1: 创建Agent类

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
            system_prompt=""  # Prompt由Skill管理
        )
        super().__init__(config)
```

### 步骤2: 创建Skill配置

```yaml
# skills/my-skill/skill.yaml
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

### 步骤3: 创建Prompt文件

```markdown
# skills/my-skill/prompts/my-prompt.md

你是...

## 核心能力
...

## 工作流程
...
```

### 步骤4: 注册Agent

```python
# backend/daoyoucode/agents/builtin/__init__.py
from .my_agent import MyAgent

def register_builtin_agents():
    ...
    register_agent(MyAgent())
```

---

## 优势总结

### 1. 配置驱动
- Skill用YAML配置，易于修改
- 不需要修改Python代码

### 2. Prompt独立
- Markdown文件管理Prompt
- 保留oh-my-opencode原始内容
- 易于版本控制和对比

### 3. Agent简洁
- Agent代码只有10行左右
- 只负责注册，不包含业务逻辑
- 易于维护和扩展

### 4. 完全可插拔
- Agent可插拔
- Prompt可插拔
- Skill可插拔
- 符合现有架构设计

---

## 下一步计划

### Phase 1: 补充更多Agent（优先编程辅助）

1. **LibrarianAgent** - 文档查找专家（oh-my-opencode）
2. **FrontendExpert** - 前端专家
3. **BackendExpert** - 后端专家
4. **SecurityExpert** - 安全专家
5. **PerformanceExpert** - 性能优化专家

### Phase 2: 工具集成

1. **LSP工具** - 代码诊断、重命名、引用查找
2. **AST工具** - AST级搜索和替换
3. **Git工具** - 原子提交、历史分析

### Phase 3: 编排增强

1. **多Agent协作** - 并行执行
2. **后台任务** - 异步执行
3. **智能路由** - 自动选择Agent

---

**当前状态**: Phase 1 - 已完成4个核心编程辅助Agent ✅
