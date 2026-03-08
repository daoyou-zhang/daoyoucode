# 系统 Context 使用现状分析

## 发现：系统已有完整的 Context 实现！✅

### 1. Context 类的位置和功能

**文件**：`backend/daoyoucode/agents/core/context.py`

**核心类**：
1. `Context` - 结构化上下文
2. `ContextManager` - 上下文管理器
3. `ContextSnapshot` - 上下文快照
4. `ContextChange` - 上下文变更记录

### 2. Context 类的功能（非常完整！）

#### 2.1 基础功能 ✅
```python
context = Context(session_id="xxx")

# 设置变量
context.set("target_file", "path/to/file.py")

# 获取变量
file_path = context.get("target_file")

# 检查变量
if context.has("target_file"):
    ...

# 删除变量
context.delete("target_file")

# 批量更新
context.update({"file1": "...", "file2": "..."})
```

#### 2.2 快照和回滚 ✅
```python
# 创建快照
snapshot_id = context.create_snapshot("before_refactor")

# 回滚到快照
context.rollback_to_snapshot(snapshot_id)

# 列出所有快照
snapshots = context.list_snapshots()
```

#### 2.3 变更历史 ✅
```python
# 获取变更历史
history = context.get_history(limit=10)

# 获取特定变量的变更历史
changes = context.get_changes_for_key("target_file")
```

#### 2.4 嵌套上下文 ✅
```python
# 创建子上下文
child_context = context.create_child()

# 子上下文可以访问父上下文的变量
value = child_context.get("parent_var")
```

#### 2.5 ContextManager 高级功能 ✅

**RepoMap 集成**：
```python
manager = get_context_manager()

# 自动添加 RepoMap 到上下文
await manager.add_repo_map(
    session_id="xxx",
    repo_path=".",
    max_tokens=2000
)
```

**Token 预算控制**：
```python
# 智能剪枝低优先级内容
stats = manager.enforce_token_budget(
    session_id="xxx",
    token_budget=8000,
    priority_keys=["target_file", "config_file"]
)
```

**智能摘要**：
```python
# 使用 LLM 压缩内容
await manager.summarize_content(
    session_id="xxx",
    key="large_content",
    target_ratio=0.33  # 压缩到 1/3
)
```

**自动优化**：
```python
# 组合摘要和剪枝
stats = await manager.auto_optimize_context(
    session_id="xxx",
    token_budget=8000,
    priority_keys=["target_file"],
    summarize_keys=["repo_map"]
)
```

### 3. 当前使用情况

#### 3.1 在 Agent 中的使用

**问题**：Agent 中使用的是简单的字典，不是 Context 类！

```python
# backend/daoyoucode/agents/core/agent.py

async def execute(
    self,
    prompt_source: Dict[str, Any],
    user_input: str,
    context: Optional[Dict[str, Any]] = None,  # ❌ 这是字典，不是 Context 对象
    ...
):
    if context is None:
        context = {}  # ❌ 简单字典
    
    # 使用字典操作
    session_id = context.get('session_id', 'default')
    context['user_id'] = user_id
    context['conversation_history'] = history
    ...
```

#### 3.2 在 Session 中的使用

```python
# backend/daoyoucode/agents/core/session.py

class Session:
    def __init__(self, session_id: str, agent):
        self.session_id = session_id
        self.agent = agent
        self.history: List[Dict] = []
        self.context: Dict = {}  # ❌ 也是简单字典
```

### 4. 核心问题

#### 问题1：Context 类没有被使用 ⚠️⚠️⚠️

**现状**：
- ✅ Context 类已经实现（功能完整）
- ❌ Agent 中使用的是简单字典
- ❌ 没有利用 Context 的高级功能

**影响**：
- 工具调用结果没有被自动保存
- 没有变量管理
- 没有快照和回滚
- 没有变更历史
- 没有 Token 预算控制

#### 问题2：工具结果没有自动保存到 Context

**现状**：
```python
# 工具调用
result = await tool.execute(**kwargs)

# 结果返回给 LLM
# ❌ 没有保存到 Context
# ❌ LLM 需要自己提取和记忆
```

**理想状态**：
```python
# 工具调用
result = await tool.execute(**kwargs)

# 自动保存到 Context
context.set("last_tool_result", result)

# 自动提取路径
if tool_name == "text_search":
    paths = extract_paths(result)
    context.set("last_search_paths", paths)
```

#### 问题3：工作流中的"变量"只是文本

**现状**：
```markdown
步骤1：搜索
text_search(...)
→ target_file = "path/to/file.py"  # ❌ 这只是 Prompt 中的文本

步骤2：使用
read_file(file_path=target_file)  # ❌ 依赖 LLM 理解和记忆
```

**理想状态**：
```markdown
步骤1：搜索
text_search(...)
# 系统自动保存到 Context
# context.set("target_file", "path/to/file.py")

步骤2：使用
read_file(file_path={{target_file}})  # ✅ 系统自动替换
```

---

## 解决方案

### 方案1：集成现有的 Context 类（推荐）⭐⭐⭐⭐⭐

#### 1.1 修改 Agent 使用 Context 对象

```python
# backend/daoyoucode/agents/core/agent.py

from .context import get_context_manager

class Agent:
    def __init__(self, config):
        self.config = config
        self.context_manager = get_context_manager()
        ...
    
    async def execute(
        self,
        prompt_source: Dict[str, Any],
        user_input: str,
        context_dict: Optional[Dict[str, Any]] = None,  # 保持向后兼容
        ...
    ):
        if context_dict is None:
            context_dict = {}
        
        # 获取或创建 Context 对象
        session_id = context_dict.get('session_id', 'default')
        context = self.context_manager.get_or_create_context(session_id)
        
        # 将字典中的数据导入 Context
        context.update(context_dict)
        
        # 后续使用 Context 对象
        user_id = context.get('user_id')
        context.set('conversation_history', history)
        ...
```

#### 1.2 在工具调用后自动保存结果

```python
# backend/daoyoucode/agents/core/agent.py

async def _execute_tool(self, tool_name: str, context: Context, **kwargs):
    """执行工具并保存结果到 Context"""
    
    # 执行工具
    result = await self.tools[tool_name].execute(**kwargs)
    
    # 保存结果到 Context
    context.set(f"last_{tool_name}_result", result)
    context.set("last_tool_result", result)
    
    # 自动提取路径
    if tool_name == "text_search":
        paths = self._extract_paths_from_search(result)
        if paths:
            context.set("last_search_paths", paths)
            if len(paths) == 1:
                context.set("target_file", paths[0])
                # 提取目录
                import os
                context.set("target_dir", os.path.dirname(paths[0]))
    
    return result

def _extract_paths_from_search(self, result):
    """从搜索结果中提取路径"""
    import re
    # 匹配路径模式：path/to/file.py:line
    pattern = r'([^\s:]+\.py):\d+'
    matches = re.findall(pattern, str(result))
    return list(set(matches))
```

#### 1.3 在 Prompt 中显示可用的 Context 变量

```python
# backend/daoyoucode/agents/core/agent.py

def _render_prompt(self, prompt: str, user_input: str, context: Context) -> str:
    """渲染 Prompt，包含 Context 信息"""
    
    # 获取所有变量
    variables = context.to_dict()
    
    # 构建 Context 信息
    context_info = "## 当前上下文\n\n"
    
    # 显示重要变量
    important_keys = ["target_file", "target_dir", "config_file", "last_search_paths"]
    for key in important_keys:
        if context.has(key):
            value = context.get(key)
            context_info += f"- {key}: {value}\n"
    
    # 显示最近的工具结果
    if context.has("last_tool_result"):
        context_info += f"\n### 最近的工具结果\n"
        context_info += f"```\n{context.get('last_tool_result')}\n```\n"
    
    # 插入到 Prompt 中
    full_prompt = f"{context_info}\n\n{prompt}\n\n## 用户输入\n{user_input}"
    
    return full_prompt
```

#### 1.4 支持变量替换

```python
# backend/daoyoucode/agents/core/agent.py

def _replace_variables(self, text: str, context: Context) -> str:
    """替换文本中的变量占位符"""
    import re
    
    # 匹配 {{variable_name}} 格式
    pattern = r'\{\{(\w+)\}\}'
    
    def replace_func(match):
        var_name = match.group(1)
        value = context.get(var_name)
        if value is not None:
            return str(value)
        return match.group(0)  # 保持原样
    
    return re.sub(pattern, replace_func, text)
```

### 方案2：增强工作流支持变量语法（可选）

#### 2.1 在工作流中使用变量语法

```markdown
## 步骤1：搜索定位

使用工具：text_search
参数：
  - query: "class BaseAgent"
  - file_pattern: "**/*.py"

⚠️ 系统会自动提取路径并保存到：
- {{target_file}} - 目标文件路径
- {{target_dir}} - 目标文件所在目录

## 步骤2：读取文件

使用工具：read_file
参数：
  - file_path: {{target_file}}  # 系统自动替换

## 步骤3：创建新文件

构造路径：
- config_file = {{target_dir}}/config.py

使用工具：write_file
参数：
  - file_path: {{config_file}}  # 系统自动替换
  - content: "..."
```

#### 2.2 在 Agent 中解析和替换变量

```python
# backend/daoyoucode/agents/core/agent.py

async def _execute_tool_with_context(
    self,
    tool_name: str,
    context: Context,
    **kwargs
):
    """执行工具，支持变量替换"""
    
    # 替换参数中的变量
    resolved_kwargs = {}
    for key, value in kwargs.items():
        if isinstance(value, str):
            # 替换 {{variable}} 格式
            resolved_value = self._replace_variables(value, context)
            resolved_kwargs[key] = resolved_value
        else:
            resolved_kwargs[key] = value
    
    # 执行工具
    result = await self._execute_tool(tool_name, context, **resolved_kwargs)
    
    return result
```

---

## 实施计划

### 阶段1：基础集成（1-2天）⭐⭐⭐⭐⭐

**目标**：让 Agent 使用 Context 对象

**任务**：
1. 修改 Agent.execute() 使用 Context 对象
2. 在工具调用后保存结果到 Context
3. 自动提取路径并保存到 Context

**文件**：
- `backend/daoyoucode/agents/core/agent.py`

**工作量**：4-6 小时

**效果**：
- ✅ 工具结果自动保存
- ✅ 路径自动提取
- ✅ 减少 LLM 负担

### 阶段2：Prompt 增强（1天）⭐⭐⭐⭐

**目标**：在 Prompt 中显示 Context 信息

**任务**：
1. 在 Prompt 中显示可用变量
2. 显示最近的工具结果
3. 显示提取的路径

**文件**：
- `backend/daoyoucode/agents/core/agent.py`

**工作量**：2-3 小时

**效果**：
- ✅ LLM 可以看到可用的变量
- ✅ 减少重复搜索
- ✅ 提高效率

### 阶段3：变量替换（1-2天）⭐⭐⭐

**目标**：支持 {{variable}} 语法

**任务**：
1. 实现变量替换函数
2. 在工具调用前替换变量
3. 更新工作流使用变量语法

**文件**：
- `backend/daoyoucode/agents/core/agent.py`
- `skills/sisyphus-orchestrator/prompts/workflows/*.md`

**工作量**：4-6 小时

**效果**：
- ✅ 工作流可以使用变量
- ✅ 不依赖 LLM 记忆
- ✅ 更可靠

### 阶段4：高级功能（可选）⭐⭐

**目标**：利用 Context 的高级功能

**任务**：
1. 使用快照和回滚（重构失败时回滚）
2. 使用 Token 预算控制（自动剪枝）
3. 使用智能摘要（压缩大内容）

**工作量**：1-2 天

**效果**：
- ✅ 更安全（可回滚）
- ✅ 更高效（Token 控制）
- ✅ 更智能（自动优化）

---

## 总结

### 好消息 ✅✅✅

1. **系统已有完整的 Context 实现**
   - Context 类功能完整
   - ContextManager 功能强大
   - 支持快照、回滚、历史、Token 控制、智能摘要

2. **只需要集成，不需要从头开发**
   - Context 类已经写好
   - 只需要在 Agent 中使用
   - 工作量小（1-2 天）

3. **可以立即解决路径问题**
   - 自动保存工具结果
   - 自动提取路径
   - 不依赖 LLM 记忆

### 当前问题 ⚠️

1. **Context 类没有被使用**
   - Agent 使用简单字典
   - 没有利用 Context 的功能

2. **工具结果没有自动保存**
   - 结果返回给 LLM 后就丢失
   - LLM 需要自己提取和记忆

3. **工作流中的"变量"只是文本**
   - 依赖 LLM 理解
   - 容易出错

### 建议 ⭐⭐⭐⭐⭐

**立即执行阶段1**：
- 让 Agent 使用 Context 对象
- 自动保存工具结果
- 自动提取路径

**工作量**：4-6 小时
**效果**：解决 80% 的路径问题

**后续执行阶段2-3**：
- 在 Prompt 中显示 Context
- 支持变量替换

**总工作量**：1-2 天
**效果**：完全解决路径问题

### 回答你的问题

**Q: 有系统级上下文吗？**
A: **有！** Context 类已经实现，功能非常完整

**Q: 为什么还有路径问题？**
A: **因为 Context 类没有被使用**，Agent 用的是简单字典

**Q: 需要怎么做？**
A: **集成现有的 Context 类**，让 Agent 使用它（1-2 天工作量）

**当前的 Prompt 工程方案是权宜之计，真正的解决方案是集成现有的 Context 类！**
