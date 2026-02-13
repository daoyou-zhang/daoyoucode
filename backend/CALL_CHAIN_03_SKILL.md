# 调用链路分析 - 03 Skill层

## 3. Skill层：任务编排

### 入口函数
```
📁 backend/daoyoucode/agents/executor.py :: execute_skill()
```

### Skill配置
```
📁 skills/chat-assistant/skill.yaml
```

### 调用流程

#### 3.1 Skill执行器

**代码**:
```python
async def execute_skill(
    skill_name: str,
    user_input: str,
    session_id: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    执行Skill
    
    Args:
        skill_name: Skill名称（如 "chat_assistant"）
        user_input: 用户输入
        session_id: 会话ID
        context: 上下文
    
    Returns:
        执行结果
    """
    # 1. 加载Skill配置
    skill_config = load_skill_config(skill_name)
    
    # 2. 获取编排器
    orchestrator_name = skill_config.get('orchestrator', 'simple')
    orchestrator = get_orchestrator(orchestrator_name)
    
    # 3. 获取Agent
    agent_name = skill_config.get('agent', 'MainAgent')
    agent = get_agent(agent_name)
    
    # 4. 准备Prompt
    prompt_config = skill_config.get('prompt', {})
    prompt_source = {
        'file': prompt_config.get('file')
    }
    
    # 5. 准备工具列表
    tools = skill_config.get('tools', [])
    
    # 6. 准备LLM配置
    llm_config = skill_config.get('llm', {})
    
    # 7. 执行
    result = await orchestrator.execute(
        agent=agent,
        prompt_source=prompt_source,
        user_input=user_input,
        context=context,
        llm_config=llm_config,
        tools=tools
    )
    
    return {
        'success': result.success,
        'content': result.content,
        'error': result.error,
        'tools_used': result.tools_used
    }
```

**职责**:
- 加载Skill配置
- 选择编排器
- 选择Agent
- 准备Prompt和工具
- 执行任务

---

#### 3.2 Skill配置解析

**文件**: `skills/chat-assistant/skill.yaml`

**内容**:
```yaml
name: chat_assistant
version: 1.0.0
description: 交互式对话助手

# 使用ReAct编排器
orchestrator: react

# 使用MainAgent
agent: MainAgent

# Prompt配置
prompt:
  file: prompts/chat_assistant.md

# LLM配置
llm:
  model: qwen-max
  temperature: 0.7
  max_tokens: 4000

# 可用工具
tools:
  - repo_map
  - get_repo_structure
  - read_file
  - text_search
  - regex_search
  - write_file
  - list_files
```

**关键配置**:
- `orchestrator: react` - 使用ReAct编排器（支持工具调用）
- `agent: MainAgent` - 使用主Agent
- `tools: [...]` - 可用工具列表
- `prompt.file` - Prompt模板文件

---

#### 3.3 编排器选择

**代码**:
```python
def get_orchestrator(name: str) -> BaseOrchestrator:
    """获取编排器"""
    from daoyoucode.agents.core.orchestrator import get_orchestrator_registry
    
    registry = get_orchestrator_registry()
    orchestrator = registry.get_orchestrator(name)
    
    if not orchestrator:
        raise ValueError(f"Orchestrator not found: {name}")
    
    return orchestrator
```

**可用编排器**:
```
📁 backend/daoyoucode/agents/orchestrators/
├─ simple.py      → SimpleOrchestrator（简单执行）
├─ react.py       → ReActOrchestrator（推理+行动循环）
├─ conditional.py → ConditionalOrchestrator（条件分支）
├─ parallel.py    → ParallelOrchestrator（并行执行）
└─ ...
```

**分支逻辑**:
```
orchestrator配置
├─ "simple"      → SimpleOrchestrator
├─ "react"       → ReActOrchestrator ✓ (chat_assistant使用)
├─ "conditional" → ConditionalOrchestrator
├─ "parallel"    → ParallelOrchestrator
└─ 其他          → 抛出异常
```

---

#### 3.4 Agent选择

**代码**:
```python
def get_agent(name: str) -> BaseAgent:
    """获取Agent"""
    from daoyoucode.agents.core.agent import get_agent_registry
    
    registry = get_agent_registry()
    agent = registry.get_agent(name)
    
    if not agent:
        raise ValueError(f"Agent not found: {name}")
    
    return agent
```

**可用Agent**:
```
📁 backend/daoyoucode/agents/builtin/
├─ main_agent.py  → MainAgent ✓ (chat_assistant使用)
├─ code_agent.py  → CodeAgent
├─ debug_agent.py → DebugAgent
└─ ...
```

---

#### 3.5 Prompt加载

**代码**:
```python
async def _load_prompt(prompt_source: Dict) -> str:
    """加载Prompt"""
    if 'file' in prompt_source:
        file_path = prompt_source['file']
        # 相对于skill目录
        full_path = Path('skills/chat-assistant') / file_path
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()
    elif 'inline' in prompt_source:
        return prompt_source['inline']
    else:
        raise ValueError("Invalid prompt source")
```

**Prompt文件**: `skills/chat-assistant/prompts/chat_assistant.md`

**内容**（简化）:
```markdown
你是DaoyouCode AI助手，基于18大核心系统。

你的能力：
- 智能代码编写和重构
- 可以主动调用工具来理解项目代码

可用工具：
1. repo_map - 生成代码地图
2. read_file - 读取文件
3. text_search - 搜索代码
...

请主动使用工具，帮助用户理解和改进代码。
```

---

### 关键文件清单

| 文件 | 职责 | 关键函数/类 |
|------|------|------------|
| `daoyoucode/agents/executor.py` | Skill执行器 | `execute_skill()` |
| `skills/chat-assistant/skill.yaml` | Skill配置 | YAML配置 |
| `skills/chat-assistant/prompts/chat_assistant.md` | Prompt模板 | Markdown文本 |
| `daoyoucode/agents/core/orchestrator.py` | 编排器注册表 | `get_orchestrator_registry()` |
| `daoyoucode/agents/core/agent.py` | Agent注册表 | `get_agent_registry()` |

---

### 依赖关系

```
executor.py
    ↓
├─ skill.yaml (配置)
├─ orchestrator.py (编排器注册表)
│   └─ orchestrators/react.py (ReAct编排器)
├─ agent.py (Agent注册表)
│   └─ builtin/main_agent.py (MainAgent)
└─ prompts/chat_assistant.md (Prompt模板)
```

---

### 下一步

Skill层完成后，控制权转移到 **Agent层**

→ 继续阅读 `CALL_CHAIN_04_AGENT.md`
