# Skill、编排器、Agent的关系 - 终极解答

## 你的困惑

> "多编排器编排多智能体，多对多了，于是重点就放在cli进入时的编排器选择了吧？然后重点就是编排器和智能体的skill上？？智能体有skill么？还是主要是编排器skill,调用智能体时传递不同？"

## 核心答案

### 1. 关系图

```
用户 → CLI → Skill → 编排器 → Agent(s) → 工具
```

**关键点**：
- **Skill是配置文件**（不是代码）
- **Skill指定编排器和Agent**
- **Agent没有Skill**（Agent只是执行者）
- **一个Skill = 一个编排器 + 一个或多个Agent**

---

## 详细解释

### 架构层次

```
┌─────────────────────────────────────────────────────────────┐
│ 第1层：用户入口（CLI）                                      │
│                                                             │
│ daoyoucode chat                                             │
│     ↓                                                       │
│ 选择Skill: "chat_assistant"                                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 第2层：Skill配置（YAML文件）                                │
│                                                             │
│ skills/chat-assistant/skill.yaml:                           │
│   orchestrator: react        ← 指定编排器                   │
│   agent: MainAgent           ← 指定Agent                    │
│   tools: [...]               ← 指定工具                     │
│   prompt: {...}              ← 指定Prompt                   │
│   llm: {...}                 ← 指定LLM配置                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 第3层：编排器（Orchestrator）                               │
│                                                             │
│ ReactOrchestrator:                                          │
│   1. 读取Skill配置                                          │
│   2. 获取Agent（MainAgent）                                 │
│   3. 调用Agent.execute(tools=skill.tools)                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 第4层：Agent（智能体）                                      │
│                                                             │
│ MainAgent:                                                  │
│   1. 接收用户输入                                           │
│   2. 加载Prompt（从Skill配置）                              │
│   3. 调用LLM（带工具列表）                                  │
│   4. 工具调用循环（ReAct）                                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 第5层：工具（Tools）                                        │
│                                                             │
│ read_file, write_file, git_commit, ...                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 核心概念

### 1. Skill（技能配置）

**定义**：Skill是一个YAML配置文件，定义了如何完成一个任务

**位置**：`skills/<skill-name>/skill.yaml`

**内容**：
```yaml
name: chat_assistant
orchestrator: react        # 使用哪个编排器
agent: MainAgent           # 使用哪个Agent
tools:                     # 可用工具列表
  - read_file
  - write_file
prompt:                    # Prompt配置
  file: prompts/chat.md
llm:                       # LLM配置
  model: qwen-max
  temperature: 0.7
```

**关键点**：
- Skill是配置，不是代码
- Skill指定编排器和Agent
- Skill可以覆盖Agent的默认配置

---

### 2. 编排器（Orchestrator）

**定义**：编排器是代码，负责执行Skill

**位置**：`backend/daoyoucode/agents/orchestrators/`

**职责**：
1. 读取Skill配置
2. 获取Agent实例
3. 调用Agent执行
4. 处理结果

**示例**：
```python
# ReactOrchestrator
async def execute(skill, user_input, context):
    # 1. 获取Agent
    agent = get_agent(skill.agent)  # 从Skill读取
    
    # 2. 调用Agent
    result = await agent.execute(
        user_input=user_input,
        tools=skill.tools,  # 从Skill传递工具
        llm_config=skill.llm  # 从Skill传递LLM配置
    )
    
    return result
```

---

### 3. Agent（智能体）

**定义**：Agent是代码，负责实际执行任务

**位置**：`backend/daoyoucode/agents/builtin/`

**职责**：
1. 接收用户输入
2. 加载Prompt
3. 调用LLM
4. 工具调用循环

**关键点**：
- Agent没有Skill
- Agent只是执行者
- Agent的配置来自Skill

---

## 多对多关系

### 关系矩阵

```
           simple  react  workflow  multi_agent
MainAgent    ✅     ✅      ✅         ✅
Programmer   ✅     ✅      ✅         ✅
Analyzer     ✅     ✅      ✅         ✅
Refactor     ✅     ✅      ✅         ✅
TestExpert   ✅     ✅      ✅         ✅
```

**结论**：任何编排器都可以使用任何Agent（多对多）

---

### 如何组合？

**通过Skill配置！**

#### 示例1：simple + MainAgent

```yaml
# skills/simple-chat/skill.yaml
orchestrator: simple
agent: MainAgent
```

#### 示例2：react + Programmer

```yaml
# skills/coding/skill.yaml
orchestrator: react
agent: programmer
tools:
  - read_file
  - write_file
```

#### 示例3：workflow + 多个Agent

```yaml
# skills/complex-task/skill.yaml
orchestrator: workflow
workflow:
  - name: analyze
    agent: code_analyzer
  - name: implement
    agent: programmer
  - name: test
    agent: test_expert
```

#### 示例4：multi_agent + 多个Agent

```yaml
# skills/sisyphus/skill.yaml
orchestrator: multi_agent
collaboration_mode: main_with_helpers
agents:
  - main_agent
  - code_analyzer
  - programmer
  - test_expert
```

---

## CLI入口流程

### 完整流程

```python
# 1. 用户执行命令
$ daoyoucode chat

# 2. CLI加载Skill
from daoyoucode.agents.executor import execute_skill

result = await execute_skill(
    skill_name="chat_assistant",  # ← 指定Skill名称
    user_input="重构登录模块",
    context={...}
)

# 3. execute_skill内部流程
def execute_skill(skill_name, user_input, context):
    # 3.1 加载Skill配置
    skill_loader = get_skill_loader()
    skill = skill_loader.get_skill(skill_name)
    # skill = {
    #     orchestrator: "react",
    #     agent: "MainAgent",
    #     tools: [...],
    #     ...
    # }
    
    # 3.2 获取编排器
    orchestrator = get_orchestrator(skill.orchestrator)
    # orchestrator = ReactOrchestrator()
    
    # 3.3 执行编排器
    result = await orchestrator.execute(
        skill=skill,
        user_input=user_input,
        context=context
    )
    
    return result

# 4. 编排器内部流程
class ReactOrchestrator:
    async def execute(self, skill, user_input, context):
        # 4.1 获取Agent
        agent = get_agent(skill.agent)
        # agent = MainAgent()
        
        # 4.2 调用Agent
        result = await agent.execute(
            user_input=user_input,
            tools=skill.tools,  # ← 从Skill传递
            llm_config=skill.llm  # ← 从Skill传递
        )
        
        return result

# 5. Agent内部流程
class MainAgent:
    async def execute(self, user_input, tools, llm_config):
        # 5.1 加载Prompt（从Skill配置）
        prompt = load_prompt(skill.prompt)
        
        # 5.2 调用LLM（带工具）
        response = await llm.chat(
            prompt=prompt,
            tools=tools,  # ← 从Skill传递
            model=llm_config.model  # ← 从Skill传递
        )
        
        # 5.3 工具调用循环
        for iteration in range(15):
            if response.has_tool_call:
                tool_result = execute_tool(...)
                response = await llm.chat(...)
            else:
                break
        
        return response
```

---

## 重点总结

### 1. CLI入口时的选择

**不是选择编排器，而是选择Skill！**

```bash
# 错误理解
$ daoyoucode --orchestrator react  # ❌ 没有这个参数

# 正确理解
$ daoyoucode chat  # ✅ 使用chat_assistant Skill
# chat_assistant Skill内部指定了orchestrator: react
```

---

### 2. Skill是核心

**Skill配置了一切**：
- 使用哪个编排器
- 使用哪个Agent（或多个）
- 使用哪些工具
- 使用什么Prompt
- 使用什么LLM配置

**示例**：
```yaml
# skills/my-task/skill.yaml
orchestrator: multi_agent  # ← 编排器
collaboration_mode: sequential

agents:                    # ← Agent列表
  - code_analyzer
  - programmer
  - test_expert

tools:                     # ← 工具列表
  - read_file
  - write_file
  - git_commit

prompt:                    # ← Prompt配置
  file: prompts/my-task.md

llm:                       # ← LLM配置
  model: qwen-max
  temperature: 0.7
```

---

### 3. Agent没有Skill

**Agent只是执行者**：
- Agent不知道自己在哪个Skill中
- Agent只接收参数（tools, llm_config等）
- Agent的配置来自Skill

**示例**：
```python
# Agent定义（没有Skill）
class ProgrammerAgent(BaseAgent):
    def __init__(self):
        config = AgentConfig(
            name="programmer",
            description="编程专家",
            model="qwen-coder-plus",  # 默认模型
            temperature=0.1  # 默认温度
        )
        super().__init__(config)

# Skill可以覆盖Agent的默认配置
# skills/my-coding/skill.yaml
agent: programmer
llm:
  model: deepseek-coder  # ← 覆盖默认的qwen-coder-plus
  temperature: 0.3       # ← 覆盖默认的0.1
```

---

### 4. 编排器和Agent的关系

**编排器调用Agent**：
- 编排器从Skill读取Agent名称
- 编排器获取Agent实例
- 编排器调用Agent.execute()
- 编排器传递Skill的配置给Agent

**示例**：
```python
# 编排器代码
class ReactOrchestrator:
    async def execute(self, skill, user_input, context):
        # 从Skill读取Agent名称
        agent_name = skill.agent  # "programmer"
        
        # 获取Agent实例
        agent = get_agent(agent_name)  # ProgrammerAgent()
        
        # 调用Agent（传递Skill配置）
        result = await agent.execute(
            user_input=user_input,
            tools=skill.tools,      # ← 从Skill
            llm_config=skill.llm,   # ← 从Skill
            prompt_source=skill.prompt  # ← 从Skill
        )
        
        return result
```

---

## 实际使用示例

### 场景1：简单对话

**需求**：启动对话

**CLI命令**：
```bash
$ daoyoucode chat
```

**内部流程**：
```
1. CLI → execute_skill("chat_assistant")
2. 加载 skills/chat-assistant/skill.yaml
   - orchestrator: react
   - agent: MainAgent
   - tools: [read_file, write_file, ...]
3. ReactOrchestrator.execute()
4. MainAgent.execute(tools=[...])
5. 工具调用循环
6. 返回结果
```

---

### 场景2：代码编写

**需求**：编写代码

**CLI命令**：
```bash
$ daoyoucode edit main.py "添加日志功能"
```

**内部流程**：
```
1. CLI → execute_skill("programming")
2. 加载 skills/programming/skill.yaml
   - orchestrator: react
   - agent: programmer
   - tools: [read_file, write_file, git_commit]
3. ReactOrchestrator.execute()
4. ProgrammerAgent.execute(tools=[...])
5. 工具调用循环
6. 返回结果
```

---

### 场景3：复杂重构

**需求**：重构 + 测试

**CLI命令**：
```bash
$ daoyoucode run complex-refactor "重构登录模块"
```

**内部流程**：
```
1. CLI → execute_skill("complex-refactor")
2. 加载 skills/complex-refactor/skill.yaml
   - orchestrator: workflow
   - workflow:
     - step1: code_analyzer
     - step2: refactor_master
     - step3: test_expert
3. WorkflowOrchestrator.execute()
4. 顺序执行：
   - CodeAnalyzerAgent.execute()
   - RefactorMasterAgent.execute()
   - TestExpertAgent.execute()
5. 返回聚合结果
```

---

## 配置优先级

### Agent配置的覆盖

```
Agent默认配置 < Skill配置 < CLI参数
```

**示例**：
```python
# 1. Agent默认配置
class ProgrammerAgent:
    model = "qwen-coder-plus"
    temperature = 0.1

# 2. Skill配置（覆盖Agent默认）
# skills/my-coding/skill.yaml
agent: programmer
llm:
  model: deepseek-coder  # ← 覆盖
  temperature: 0.3       # ← 覆盖

# 3. CLI参数（覆盖Skill配置）
$ daoyoucode chat --model gpt-4  # ← 覆盖

# 最终使用：gpt-4, temperature=0.3
```

---

## 创建新Skill的步骤

### 步骤1：创建目录

```bash
mkdir -p skills/my-new-skill/prompts
```

### 步骤2：创建skill.yaml

```yaml
# skills/my-new-skill/skill.yaml
name: my-new-skill
version: 1.0.0
description: 我的新技能

orchestrator: react  # 选择编排器
agent: programmer    # 选择Agent

tools:               # 选择工具
  - read_file
  - write_file

prompt:              # 配置Prompt
  file: prompts/my-prompt.md

llm:                 # 配置LLM
  model: qwen-max
  temperature: 0.7
```

### 步骤3：创建Prompt

```markdown
# skills/my-new-skill/prompts/my-prompt.md

你是一个专业的代码助手。

用户输入：{{user_input}}

请帮助用户完成任务。
```

### 步骤4：使用Skill

```bash
$ daoyoucode run my-new-skill "做某事"
```

---

## 常见问题

### Q1: Agent有Skill吗？

**A**: 没有。Agent只是执行者，不包含Skill配置。

### Q2: 如何选择编排器？

**A**: 在Skill配置中指定`orchestrator`字段。

### Q3: 一个Agent可以用在多个Skill中吗？

**A**: 可以！同一个Agent可以被多个Skill使用，只是配置不同。

### Q4: 一个Skill可以使用多个编排器吗？

**A**: 不可以。一个Skill只能指定一个编排器。

### Q5: 如何传递不同的配置给Agent？

**A**: 通过Skill的`llm`、`tools`、`prompt`等字段配置。

---

## 总结

### 核心关系

```
Skill（配置） → 编排器（代码） → Agent（代码） → 工具（代码）
```

### 关键点

1. **Skill是配置文件**，不是代码
2. **Skill指定编排器和Agent**
3. **Agent没有Skill**，Agent只是执行者
4. **编排器从Skill读取配置**，然后调用Agent
5. **CLI选择Skill**，不是选择编排器
6. **多对多关系**通过Skill配置实现

### 最佳实践

1. 为每个任务类型创建一个Skill
2. 在Skill中选择合适的编排器
3. 在Skill中选择合适的Agent
4. 在Skill中配置工具和Prompt
5. 通过CLI执行Skill

### 下一步

1. 查看现有Skill配置（`skills/`目录）
2. 理解Skill、编排器、Agent的关系
3. 创建自己的Skill
4. 测试和优化

---

**记住**：Skill是核心，它连接了CLI、编排器、Agent和工具！
