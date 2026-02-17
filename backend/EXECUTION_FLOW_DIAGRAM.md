# 执行流程图 - 从CLI到工具调用

## 完整执行流程

```
┌─────────────────────────────────────────────────────────────┐
│ 用户                                                        │
│                                                             │
│ $ daoyoucode chat                                           │
│ > 重构登录模块，添加测试                                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ CLI入口 (cli/app.py)                                        │
│                                                             │
│ def chat():                                                 │
│     handle_chat(user_input, context)                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Skill执行器 (agents/executor.py)                            │
│                                                             │
│ execute_skill(                                              │
│     skill_name="chat_assistant",  ← 固定使用这个Skill       │
│     user_input="重构登录模块，添加测试",                    │
│     context={...}                                           │
│ )                                                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Skill加载器 (agents/core/skill.py)                          │
│                                                             │
│ skill_loader = get_skill_loader()                           │
│ skill = skill_loader.get_skill("chat_assistant")            │
│                                                             │
│ 加载: skills/chat-assistant/skill.yaml                      │
│ ┌─────────────────────────────────────────────────────┐    │
│ │ orchestrator: react                                 │    │
│ │ agent: MainAgent                                    │    │
│ │ tools:                                              │    │
│ │   - repo_map                                        │    │
│ │   - read_file                                       │    │
│ │   - write_file                                      │    │
│ │   - git_commit                                      │    │
│ │   - ...                                             │    │
│ │ prompt:                                             │    │
│ │   file: prompts/chat_assistant.md                   │    │
│ │ llm:                                                │    │
│ │   model: qwen-max                                   │    │
│ │   temperature: 0.7                                  │    │
│ └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 编排器注册表 (agents/core/orchestrator.py)                  │
│                                                             │
│ orchestrator = get_orchestrator(skill.orchestrator)         │
│ # orchestrator = "react"                                    │
│ # 返回: ReactOrchestrator实例                               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ React编排器 (agents/orchestrators/react.py)                 │
│                                                             │
│ async def execute(skill, user_input, context):              │
│     # 1. 应用中间件                                         │
│     for middleware in skill.middleware:                     │
│         context = apply_middleware(middleware, context)     │
│                                                             │
│     # 2. 获取Agent                                          │
│     agent = get_agent(skill.agent)  # "MainAgent"          │
│                                                             │
│     # 3. 调用Agent                                          │
│     result = await agent.execute(                           │
│         prompt_source=skill.prompt,                         │
│         user_input=user_input,                              │
│         context=context,                                    │
│         llm_config=skill.llm,                               │
│         tools=skill.tools  ← 传递工具列表                   │
│     )                                                       │
│                                                             │
│     return result                                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Agent注册表 (agents/core/agent.py)                          │
│                                                             │
│ agent = get_agent("MainAgent")                              │
│ # 返回: MainAgent实例                                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ MainAgent (agents/builtin/main_agent.py)                    │
│                                                             │
│ async def execute(                                          │
│     prompt_source,                                          │
│     user_input,                                             │
│     context,                                                │
│     llm_config,                                             │
│     tools  ← 接收工具列表                                   │
│ ):                                                          │
│     # 1. 加载记忆                                           │
│     history = memory.load_context(session_id)               │
│                                                             │
│     # 2. 加载Prompt                                         │
│     prompt = load_prompt(prompt_source)                     │
│     # 从 skills/chat-assistant/prompts/chat_assistant.md    │
│                                                             │
│     # 3. 渲染Prompt                                         │
│     full_prompt = render_prompt(prompt, user_input, context)│
│                                                             │
│     # 4. 调用LLM（带工具）                                  │
│     if tools:                                               │
│         response = await _call_llm_with_tools(              │
│             full_prompt,                                    │
│             tools,  ← 传递工具列表                          │
│             llm_config                                      │
│         )                                                   │
│     else:                                                   │
│         response = await _call_llm(full_prompt, llm_config) │
│                                                             │
│     # 5. 保存记忆                                           │
│     memory.add_conversation(session_id, user_input, response)│
│                                                             │
│     return AgentResult(                                     │
│         success=True,                                       │
│         content=response                                    │
│     )                                                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 工具调用循环 (agents/core/agent.py)                         │
│                                                             │
│ async def _call_llm_with_tools(                             │
│     prompt,                                                 │
│     tool_names,  ← ["repo_map", "read_file", ...]          │
│     llm_config                                              │
│ ):                                                          │
│     # 获取工具的Function schemas                            │
│     tool_registry = get_tool_registry()                     │
│     function_schemas = tool_registry.get_function_schemas(  │
│         tool_names                                          │
│     )                                                       │
│                                                             │
│     messages = [{"role": "user", "content": prompt}]        │
│                                                             │
│     # ReAct循环（最多15次）                                 │
│     for iteration in range(15):                             │
│         # 1. 调用LLM（带工具列表）                          │
│         response = await llm.chat(                          │
│             messages=messages,                              │
│             functions=function_schemas  ← 工具定义          │
│         )                                                   │
│                                                             │
│         # 2. 检查是否有工具调用                             │
│         if response.function_call:                          │
│             tool_name = response.function_call.name         │
│             tool_args = response.function_call.arguments    │
│                                                             │
│             # 3. 执行工具                                   │
│             tool_result = await tool_registry.execute_tool( │
│                 tool_name,                                  │
│                 **tool_args                                 │
│             )                                               │
│                                                             │
│             # 4. 将结果添加到消息历史                       │
│             messages.append({                               │
│                 "role": "assistant",                        │
│                 "function_call": response.function_call     │
│             })                                              │
│             messages.append({                               │
│                 "role": "function",                         │
│                 "name": tool_name,                          │
│                 "content": str(tool_result.content)         │
│             })                                              │
│                                                             │
│             # 5. 继续循环（LLM看到结果后继续推理）          │
│         else:                                               │
│             # 没有工具调用，返回最终答案                    │
│             return response.content                         │
│                                                             │
│     # 达到最大迭代次数                                      │
│     return "任务完成"                                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 工具注册表 (agents/tools/registry.py)                       │
│                                                             │
│ tool_registry.execute_tool("read_file", path="main.py")     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 具体工具 (agents/tools/file_operations.py)                  │
│                                                             │
│ @tool(name="read_file")                                     │
│ async def read_file(path: str) -> ToolResult:               │
│     content = Path(path).read_text()                        │
│     return ToolResult(                                      │
│         success=True,                                       │
│         content=content                                     │
│     )                                                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
                    返回工具结果
                            ↓
                    继续ReAct循环
                            ↓
                    返回最终答案
                            ↓
                    显示给用户
```

---

## 关键流程节点

### 1. CLI入口

**文件**：`cli/app.py`, `cli/commands/chat.py`

**职责**：
- 接收用户输入
- 调用Skill执行器

**代码**：
```python
def handle_chat(user_input, context):
    result = await execute_skill(
        skill_name="chat_assistant",
        user_input=user_input,
        context=context
    )
```

---

### 2. Skill加载

**文件**：`agents/core/skill.py`

**职责**：
- 加载Skill配置文件
- 解析YAML配置

**代码**：
```python
skill_loader = get_skill_loader()
skill = skill_loader.get_skill("chat_assistant")
# skill.orchestrator = "react"
# skill.agent = "MainAgent"
# skill.tools = ["read_file", "write_file", ...]
```

---

### 3. 编排器选择

**文件**：`agents/core/orchestrator.py`

**职责**：
- 根据Skill配置获取编排器
- 返回编排器实例

**代码**：
```python
orchestrator = get_orchestrator(skill.orchestrator)
# 返回: ReactOrchestrator实例
```

---

### 4. 编排器执行

**文件**：`agents/orchestrators/react.py`

**职责**：
- 获取Agent
- 调用Agent.execute()
- 传递Skill配置

**代码**：
```python
agent = get_agent(skill.agent)
result = await agent.execute(
    tools=skill.tools,  # ← 从Skill传递
    llm_config=skill.llm  # ← 从Skill传递
)
```

---

### 5. Agent执行

**文件**：`agents/core/agent.py`, `agents/builtin/main_agent.py`

**职责**：
- 加载Prompt
- 调用LLM
- 工具调用循环

**代码**：
```python
# 加载Prompt
prompt = load_prompt(skill.prompt)

# 调用LLM（带工具）
response = await _call_llm_with_tools(
    prompt,
    tools,  # ← 从编排器传递
    llm_config
)
```

---

### 6. 工具调用循环（ReAct）

**文件**：`agents/core/agent.py`

**职责**：
- LLM推理
- 调用工具
- 观察结果
- 继续推理

**代码**：
```python
for iteration in range(15):
    # 1. LLM推理
    response = await llm.chat(messages, functions)
    
    # 2. 检查工具调用
    if response.function_call:
        # 3. 执行工具
        tool_result = await execute_tool(...)
        
        # 4. 添加结果到消息历史
        messages.append(tool_result)
        
        # 5. 继续循环
    else:
        # 返回最终答案
        return response.content
```

---

### 7. 工具执行

**文件**：`agents/tools/registry.py`, `agents/tools/*.py`

**职责**：
- 执行具体工具
- 返回结果

**代码**：
```python
@tool(name="read_file")
async def read_file(path: str):
    content = Path(path).read_text()
    return ToolResult(success=True, content=content)
```

---

## 数据流

### 用户输入 → 最终输出

```
用户输入: "重构登录模块，添加测试"
    ↓
Skill配置: {
    orchestrator: "react",
    agent: "MainAgent",
    tools: ["read_file", "write_file", ...],
    prompt: "prompts/chat_assistant.md",
    llm: {model: "qwen-max", temperature: 0.7}
}
    ↓
编排器: ReactOrchestrator
    ↓
Agent: MainAgent
    ↓
Prompt: "你是DaoyouCode AI助手..."
    ↓
LLM调用1: "我需要先查看登录模块的代码"
    ↓
工具调用1: read_file("auth/login.py")
    ↓
工具结果1: "def login(username, password): ..."
    ↓
LLM调用2: "我需要分析代码结构"
    ↓
工具调用2: repo_map()
    ↓
工具结果2: "项目结构: auth/, tests/, ..."
    ↓
LLM调用3: "我现在可以提供重构方案了"
    ↓
最终输出: "重构方案：\n1. 提取认证逻辑...\n2. 添加单元测试..."
    ↓
显示给用户
```

---

## 配置传递链

### Skill配置如何传递到Agent

```
Skill配置 (YAML)
    ↓
SkillConfig对象
    ↓
编排器.execute(skill, ...)
    ↓
agent.execute(
    tools=skill.tools,
    llm_config=skill.llm,
    prompt_source=skill.prompt
)
    ↓
Agent使用这些配置
```

---

## 多Skill场景

### 不同命令使用不同Skill

```
$ daoyoucode chat
    ↓
execute_skill("chat_assistant")
    ↓
orchestrator: react
agent: MainAgent
tools: [read_file, write_file, repo_map, ...]

---

$ daoyoucode edit main.py "添加日志"
    ↓
execute_skill("programming")
    ↓
orchestrator: react
agent: programmer
tools: [read_file, write_file, git_commit]

---

$ daoyoucode run complex-refactor "重构登录"
    ↓
execute_skill("complex-refactor")
    ↓
orchestrator: workflow
agents: [code_analyzer, refactor_master, test_expert]
tools: [各Agent的专属工具]
```

---

## 总结

### 关键点

1. **CLI选择Skill**（不是编排器）
2. **Skill指定编排器和Agent**
3. **编排器调用Agent**
4. **Agent执行工具调用循环**
5. **工具返回结果**
6. **循环直到完成**

### 数据流

```
用户 → CLI → Skill → 编排器 → Agent → LLM → 工具 → 结果
```

### 配置流

```
Skill配置 → 编排器 → Agent → LLM/工具
```

### 控制流

```
CLI控制Skill选择
Skill控制编排器选择
编排器控制Agent调用
Agent控制工具调用循环
```

---

**记住**：整个流程由Skill配置驱动！
