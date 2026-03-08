# Context 集成实施计划

## 目标

将现有的 Context 类集成到 Agent 中，实现：
1. 工具结果自动保存
2. 路径自动提取
3. 变量在 Prompt 中可见
4. 支持变量替换（可选）

## 实施步骤

### 阶段1：基础集成（核心）⭐⭐⭐⭐⭐

#### 任务1.1：修改 Agent 使用 Context 对象

**文件**：`backend/daoyoucode/agents/core/agent.py`

**修改点**：
1. 导入 Context 相关类
2. 在 `__init__` 中初始化 ContextManager
3. 在 `execute()` 中使用 Context 对象
4. 保持向后兼容（接受字典参数）

**代码位置**：
- 第 1-50 行：导入部分
- 第 50-100 行：`__init__` 方法
- 第 347-600 行：`execute()` 方法

#### 任务1.2：在工具调用后自动保存结果

**文件**：`backend/daoyoucode/agents/core/agent.py`

**修改点**：
1. 找到工具调用的位置
2. 在工具调用后保存结果到 Context
3. 自动提取路径（text_search, repo_map）

**代码位置**：
- 第 800-1000 行：工具调用循环

#### 任务1.3：自动提取路径的辅助函数

**文件**：`backend/daoyoucode/agents/core/agent.py`

**新增方法**：
```python
def _extract_paths_from_result(self, tool_name: str, result: Any) -> List[str]
def _save_tool_result_to_context(self, context: Context, tool_name: str, result: Any)
```

### 阶段2：Prompt 增强（重要）⭐⭐⭐⭐

#### 任务2.1：在 Prompt 中显示 Context 信息

**文件**：`backend/daoyoucode/agents/core/agent.py`

**修改点**：
1. 修改 `_render_prompt()` 方法
2. 添加 Context 信息到 Prompt
3. 显示可用变量和最近的工具结果

**代码位置**：
- 第 1400-1500 行：`_render_prompt()` 方法

#### 任务2.2：格式化 Context 信息

**文件**：`backend/daoyoucode/agents/core/agent.py`

**新增方法**：
```python
def _format_context_info(self, context: Context) -> str
```

### 阶段3：变量替换（可选）⭐⭐⭐

#### 任务3.1：实现变量替换

**文件**：`backend/daoyoucode/agents/core/agent.py`

**新增方法**：
```python
def _replace_variables(self, text: str, context: Context) -> str
```

#### 任务3.2：在工具调用前替换变量

**文件**：`backend/daoyoucode/agents/core/agent.py`

**修改点**：
1. 在解析工具调用参数时替换变量
2. 支持 {{variable}} 语法

## 详细代码修改

### 修改1：导入 Context

```python
# backend/daoyoucode/agents/core/agent.py
# 在文件开头添加

from .context import Context, ContextManager, get_context_manager
```

### 修改2：初始化 ContextManager

```python
# backend/daoyoucode/agents/core/agent.py
# 在 Agent.__init__ 中添加

class Agent:
    def __init__(self, config: AgentConfig):
        # ... 现有代码 ...
        
        # 🆕 上下文管理器
        self.context_manager = get_context_manager()
        self.logger.debug("上下文管理器已就绪")
```

### 修改3：在 execute() 中使用 Context

```python
# backend/daoyoucode/agents/core/agent.py
# 修改 execute() 方法

async def execute(
    self,
    prompt_source: Dict[str, Any],
    user_input: str,
    context_dict: Optional[Dict[str, Any]] = None,  # 重命名参数
    llm_config: Optional[Dict[str, Any]] = None,
    tools: Optional[List[str]] = None,
    max_tool_iterations: int = 15
) -> AgentResult:
    """
    执行Agent任务
    
    Args:
        prompt_source: Prompt来源
        user_input: 用户输入
        context_dict: 上下文字典（向后兼容）
        ...
    """
    if context_dict is None:
        context_dict = {}
    
    # 🆕 获取或创建 Context 对象
    session_id = context_dict.get('session_id', 'default')
    context = self.context_manager.get_or_create_context(session_id)
    
    # 🆕 将字典中的数据导入 Context
    context.update(context_dict, track_change=False)
    
    # 后续使用 context 对象而不是 context_dict
    user_id = context.get('user_id')
    
    # ... 其他代码 ...
```

### 修改4：保存工具结果到 Context

```python
# backend/daoyoucode/agents/core/agent.py
# 在工具调用循环中添加

# 找到工具调用的位置（大约在第 800-1000 行）
# 在工具执行后添加：

# 执行工具
result = await tool.execute(**tool_kwargs)

# 🆕 保存结果到 Context
self._save_tool_result_to_context(context, tool_name, result)

# 🆕 自动提取路径
if tool_name in ["text_search", "repo_map"]:
    paths = self._extract_paths_from_result(tool_name, result)
    if paths:
        context.set("last_search_paths", paths)
        if len(paths) == 1:
            context.set("target_file", paths[0])
            # 提取目录
            import os
            target_dir = os.path.dirname(paths[0])
            if target_dir:
                context.set("target_dir", target_dir)
```

### 修改5：添加辅助方法

```python
# backend/daoyoucode/agents/core/agent.py
# 在 Agent 类中添加新方法

def _save_tool_result_to_context(
    self,
    context: Context,
    tool_name: str,
    result: Any
):
    """
    保存工具结果到 Context
    
    Args:
        context: Context 对象
        tool_name: 工具名称
        result: 工具结果
    """
    # 保存最近的工具结果
    context.set("last_tool_result", {
        "tool": tool_name,
        "result": result,
        "timestamp": datetime.now().isoformat()
    })
    
    # 保存特定工具的结果
    context.set(f"last_{tool_name}_result", result)
    
    self.logger.debug(f"已保存工具结果到 Context: {tool_name}")

def _extract_paths_from_result(
    self,
    tool_name: str,
    result: Any
) -> List[str]:
    """
    从工具结果中提取文件路径
    
    Args:
        tool_name: 工具名称
        result: 工具结果
    
    Returns:
        提取的路径列表
    """
    import re
    
    paths = []
    result_str = str(result)
    
    if tool_name == "text_search":
        # 匹配格式：path/to/file.py:line_number
        pattern = r'([^\s:]+\.(?:py|js|ts|java|cpp|c|h|go|rs|rb|php)):\d+'
        matches = re.findall(pattern, result_str)
        paths = list(set(matches))
    
    elif tool_name == "repo_map":
        # repo_map 结果中的路径格式可能不同
        # 匹配常见的文件路径
        pattern = r'([^\s:]+\.(?:py|js|ts|java|cpp|c|h|go|rs|rb|php))'
        matches = re.findall(pattern, result_str)
        paths = list(set(matches))
    
    if paths:
        self.logger.info(f"从 {tool_name} 结果中提取了 {len(paths)} 个路径")
    
    return paths

def _format_context_info(self, context: Context) -> str:
    """
    格式化 Context 信息用于 Prompt
    
    Args:
        context: Context 对象
    
    Returns:
        格式化的 Context 信息
    """
    lines = ["## 当前上下文变量", ""]
    
    # 重要变量
    important_keys = [
        "target_file",
        "target_dir",
        "config_file",
        "last_search_paths"
    ]
    
    has_important = False
    for key in important_keys:
        if context.has(key):
            value = context.get(key)
            if isinstance(value, list):
                lines.append(f"- **{key}**: {len(value)} 个路径")
                for i, path in enumerate(value[:3], 1):  # 只显示前3个
                    lines.append(f"  {i}. {path}")
                if len(value) > 3:
                    lines.append(f"  ... 还有 {len(value) - 3} 个")
            else:
                lines.append(f"- **{key}**: `{value}`")
            has_important = True
    
    if not has_important:
        lines.append("（暂无重要变量）")
    
    lines.append("")
    
    # 最近的工具结果
    if context.has("last_tool_result"):
        last_result = context.get("last_tool_result")
        tool_name = last_result.get("tool", "unknown")
        lines.append(f"### 最近的工具调用: {tool_name}")
        lines.append("")
        lines.append("⚠️ 工具结果已保存到上下文，可以直接使用上述变量")
        lines.append("")
    
    return "\n".join(lines)
```

### 修改6：在 Prompt 中显示 Context

```python
# backend/daoyoucode/agents/core/agent.py
# 修改 _render_prompt() 方法

def _render_prompt(
    self,
    prompt: str,
    user_input: str,
    context: Context  # 改为 Context 对象
) -> str:
    """
    渲染Prompt
    
    Args:
        prompt: Prompt模板
        user_input: 用户输入
        context: Context 对象
    
    Returns:
        渲染后的Prompt
    """
    # 🆕 添加 Context 信息
    context_info = self._format_context_info(context)
    
    # 构建完整 Prompt
    full_prompt = f"""{context_info}

{prompt}

## 用户输入
{user_input}
"""
    
    return full_prompt
```

### 修改7：变量替换（可选）

```python
# backend/daoyoucode/agents/core/agent.py
# 添加变量替换方法

def _replace_variables(self, text: str, context: Context) -> str:
    """
    替换文本中的变量占位符
    
    支持格式：{{variable_name}}
    
    Args:
        text: 原始文本
        context: Context 对象
    
    Returns:
        替换后的文本
    """
    import re
    
    # 匹配 {{variable_name}} 格式
    pattern = r'\{\{(\w+)\}\}'
    
    def replace_func(match):
        var_name = match.group(1)
        value = context.get(var_name)
        if value is not None:
            return str(value)
        # 变量不存在，保持原样
        self.logger.warning(f"变量 {var_name} 不存在于 Context 中")
        return match.group(0)
    
    result = re.sub(pattern, replace_func, text)
    
    # 如果有替换，记录日志
    if result != text:
        self.logger.debug(f"已替换变量: {text} -> {result}")
    
    return result
```

## 测试计划

### 测试1：基础功能测试

```python
# 测试 Context 是否正常工作

# 1. 创建 Agent
agent = Agent(config)

# 2. 执行任务
result = await agent.execute(
    prompt_source={"use_agent_default": True},
    user_input="搜索 BaseAgent 类",
    context_dict={"session_id": "test_session"}
)

# 3. 检查 Context
context = agent.context_manager.get_context("test_session")
assert context is not None
assert context.has("last_tool_result")
```

### 测试2：路径提取测试

```python
# 测试路径是否被正确提取

# 1. 执行搜索
result = await agent.execute(
    prompt_source={"use_agent_default": True},
    user_input="搜索 class BaseAgent",
    context_dict={"session_id": "test_session"}
)

# 2. 检查路径
context = agent.context_manager.get_context("test_session")
assert context.has("target_file")
assert context.has("target_dir")

target_file = context.get("target_file")
print(f"提取的路径: {target_file}")
```

### 测试3：变量在 Prompt 中可见

```python
# 测试 Prompt 中是否显示 Context 信息

# 1. 设置一些变量
context = agent.context_manager.get_context("test_session")
context.set("target_file", "backend/daoyoucode/agents/core/agent.py")
context.set("target_dir", "backend/daoyoucode/agents/core")

# 2. 渲染 Prompt
prompt = agent._render_prompt(
    "这是测试 Prompt",
    "用户输入",
    context
)

# 3. 检查 Prompt 中是否包含 Context 信息
assert "target_file" in prompt
assert "target_dir" in prompt
print(prompt)
```

## 回滚计划

如果集成出现问题，可以快速回滚：

### 回滚步骤

1. 恢复 `agent.py` 的备份
2. 或者使用 git 回滚：
   ```bash
   git checkout backend/daoyoucode/agents/core/agent.py
   ```

### 保持向后兼容

代码修改保持向后兼容：
- 参数名从 `context` 改为 `context_dict`
- 内部使用 Context 对象
- 外部调用不需要修改

## 预期效果

### 效果1：工具结果自动保存 ✅

```
执行 text_search → 结果自动保存到 Context
→ last_tool_result
→ last_text_search_result
→ last_search_paths
→ target_file
→ target_dir
```

### 效果2：路径自动提取 ✅

```
text_search 结果：
  backend/daoyoucode/agents/core/agent.py:100: class BaseAgent

自动提取：
  target_file = "backend/daoyoucode/agents/core/agent.py"
  target_dir = "backend/daoyoucode/agents/core"
```

### 效果3：Prompt 中可见 ✅

```
## 当前上下文变量

- **target_file**: `backend/daoyoucode/agents/core/agent.py`
- **target_dir**: `backend/daoyoucode/agents/core`

### 最近的工具调用: text_search

⚠️ 工具结果已保存到上下文，可以直接使用上述变量
```

### 效果4：减少重复搜索 ✅

LLM 可以看到已经提取的路径，不需要重复搜索

### 效果5：支持变量替换（可选）✅

```markdown
read_file(file_path={{target_file}})
→ 自动替换为
read_file(file_path="backend/daoyoucode/agents/core/agent.py")
```

## 时间估算

- 修改1-3：2 小时
- 修改4-5：2 小时
- 修改6：1 小时
- 修改7：1 小时（可选）
- 测试：1 小时

**总计**：6-7 小时

## 下一步

1. 备份 `agent.py`
2. 开始修改代码
3. 逐步测试
4. 验证效果
