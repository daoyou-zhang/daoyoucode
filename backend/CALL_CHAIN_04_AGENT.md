# 调用链路分析 - 04 Agent层

## 4. Agent层：智能决策

### 入口函数
```
📁 backend/daoyoucode/agents/core/agent.py :: BaseAgent.execute()
```

### 调用流程

#### 4.1 Agent执行入口

**代码**:
```python
async def execute(
    self,
    prompt_source: Dict[str, Any],
    user_input: str,
    context: Optional[Dict[str, Any]] = None,
    llm_config: Optional[Dict[str, Any]] = None,
    tools: Optional[List[str]] = None,
    max_tool_iterations: int = 5
) -> AgentResult:
    """
    执行任务
    
    流程：
    1. 获取记忆（对话历史、用户偏好、任务历史）
    2. 加载Prompt
    3. 渲染Prompt
    4. 调用LLM（带或不带工具）
    5. 保存到记忆
    """
```

**职责**:
- 协调整个执行流程
- 管理记忆系统
- 调用LLM
- 处理工具调用

---

#### 4.2 记忆加载

**代码**:
```python
# 提取session_id和user_id
session_id = context.get('session_id', 'default')
user_id = context.get('user_id', session_id)

# 1. 对话历史（LLM层记忆）
history = self.memory.get_conversation_history(session_id, limit=3)
if history:
    context['conversation_history'] = history

# 2. 用户偏好（Agent层记忆）
prefs = self.memory.get_preferences(user_id)
if prefs:
    context['user_preferences'] = prefs

# 3. 任务历史（Agent层记忆）
task_history = self.memory.get_task_history(user_id, limit=5)
if task_history:
    context['recent_tasks'] = task_history
```

**记忆类型**:
- **对话历史** - 最近3轮对话
- **用户偏好** - 用户的编程语言偏好等
- **任务历史** - 最近5个任务

---

#### 4.3 Prompt处理

**加载Prompt**:
```python
prompt = await self._load_prompt(prompt_source, context)
```

**渲染Prompt**（Jinja2模板）:
```python
def _render_prompt(self, prompt: str, user_input: str, context: Dict) -> str:
    """渲染Prompt（支持Jinja2模板）"""
    try:
        from jinja2 import Template
        template = Template(prompt)
        return template.render(user_input=user_input, **context)
    except Exception as e:
        # 回退到简单替换
        return prompt.replace('{{user_input}}', user_input)
```

---

#### 4.4 LLM调用分支

**分支逻辑**:
```python
if tools:
    # ========== 带工具调用 ==========
    # 构建初始消息（包含历史对话）
    initial_messages = []
    
    # 添加历史对话
    if history:
        for h in history:
            initial_messages.append({
                "role": "user",
                "content": h.get('user', '')
            })
            initial_messages.append({
                "role": "assistant",
                "content": h.get('ai', '')
            })
    
    # 添加当前用户输入
    initial_messages.append({
        "role": "user",
        "content": full_prompt
    })
    
    response, tools_used = await self._call_llm_with_tools(
        initial_messages,
        tools,
        llm_config,
        max_tool_iterations
    )
else:
    # ========== 不带工具调用 ==========
    response = await self._call_llm(full_prompt, llm_config)
```

**决策点**:
- 如果Skill配置了tools → 使用Function Calling
- 否则 → 简单的LLM调用

---

#### 4.5 Function Calling循环（核心）

**函数**: `_call_llm_with_tools()`

**代码**:
```python
async def _call_llm_with_tools(
    self,
    initial_messages: List[Dict],
    tool_names: List[str],
    llm_config: Optional[Dict] = None,
    max_iterations: int = 5
) -> tuple[str, List[str]]:
    """
    调用LLM并支持工具调用
    
    流程：
    1. 获取工具的Function schemas
    2. 调用LLM（带functions参数）
    3. 检查是否有function_call
    4. 如果有，执行工具
    5. 将工具结果添加到消息历史
    6. 重复步骤2-5，直到LLM不再调用工具或达到最大迭代次数
    """
    
    # 获取工具schemas
    function_schemas = tool_registry.get_function_schemas(tool_names)
    
    # 使用初始消息作为起点
    messages = initial_messages.copy()
    tools_used = []
    
    # 工具调用循环
    for iteration in range(max_iterations):
        # 1. 调用LLM（带工具）
        response = await self._call_llm_with_functions(
            messages,
            function_schemas,
            llm_config
        )
        
        # 2. 检查是否有function_call
        function_call = response.get('metadata', {}).get('function_call')
        
        if not function_call:
            # 没有工具调用，返回最终响应
            return response.get('content', ''), tools_used
        
        # 3. 解析工具调用
        tool_name = function_call['name']
        tool_args = json.loads(function_call['arguments'])
        
        print(f"\n🔧 执行工具: {tool_name}")
        print(f"   参数: {tool_args}")
        tools_used.append(tool_name)
        
        # 4. 执行工具
        tool_result = await tool_registry.execute_tool(tool_name, **tool_args)
        
        # ========== 智能后处理 ==========
        if tool_result.success:
            user_query = self._extract_user_query(messages)
            tool_result = await self.tool_postprocessor.process(
                tool_name=tool_name,
                result=tool_result,
                user_query=user_query,
                context=context
            )
        
        # 5. 添加到消息历史
        messages.append({
            "role": "assistant",
            "content": None,
            "function_call": function_call
        })
        messages.append({
            "role": "function",
            "name": tool_name,
            "content": str(tool_result.content)
        })
    
    # 达到最大迭代次数
    return "达到最大工具调用迭代次数", tools_used
```

**循环逻辑**:
```
开始
  ↓
调用LLM（带functions）
  ↓
检查function_call
  ├─ 无 → 返回最终响应 ✓
  └─ 有 → 继续
      ↓
  执行工具
      ↓
  智能后处理（新增）
      ↓
  添加到消息历史
      ↓
  iteration++
      ↓
  检查是否达到max_iterations
      ├─ 是 → 返回（可能未完成）
      └─ 否 → 回到"调用LLM"
```

---

#### 4.6 记忆保存

**代码**:
```python
# 1. 保存对话（LLM层记忆）
self.memory.add_conversation(
    session_id,
    user_input,
    response,
    metadata={'agent': self.name}
)

# 2. 保存任务（Agent层记忆）
self.memory.add_task(user_id, {
    'agent': self.name,
    'input': user_input[:200],
    'result': response[:200],
    'success': True,
    'tools_used': tools_used
})

# 3. 学习用户偏好
if 'python' in user_input.lower():
    self.memory.remember_preference(user_id, 'preferred_language', 'python')
```

---

### 关键文件清单

| 文件 | 职责 | 关键函数 |
|------|------|---------|
| `daoyoucode/agents/core/agent.py` | Agent基类 | `execute()`, `_call_llm_with_tools()` |
| `daoyoucode/agents/builtin/main_agent.py` | MainAgent | 继承BaseAgent |
| `daoyoucode/agents/memory/__init__.py` | Memory管理器 | `get_memory_manager()` |
| `daoyoucode/agents/tools/postprocessor.py` | 工具后处理器 | `process()` |

---

### 依赖关系

```
agent.py (BaseAgent)
    ↓
├─ memory/ (记忆系统)
│   ├─ get_conversation_history()
│   ├─ get_preferences()
│   └─ add_conversation()
├─ tools/ (工具系统)
│   ├─ get_tool_registry()
│   └─ execute_tool()
├─ tools/postprocessor.py (后处理)
│   └─ process()
└─ llm/ (LLM客户端)
    └─ get_client_manager()
```

---

### 下一步

Agent层完成后，控制权转移到 **工具层** 或 **LLM层**

→ 继续阅读 `CALL_CHAIN_05_TOOL.md` (工具调用)
→ 或 `CALL_CHAIN_06_LLM.md` (LLM调用)
