# 单例模式分析与Working Directory设计

## 问题

用户问：每次都重新初始化？这和其他一样么？

## 答案

**不是每次都重新初始化**。所有核心系统都使用**单例模式**。

---

## 单例模式实现对比

### 1. ToolRegistry - 全局变量单例 ✅

```python
# backend/daoyoucode/agents/tools/registry.py

# 全局单例
_tool_registry = None

def get_tool_registry() -> ToolRegistry:
    """获取工具注册表单例"""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
        _register_builtin_tools()
    return _tool_registry
```

**特点**:
- 使用全局变量
- 第一次调用时创建
- 后续调用返回同一个实例
- 工具只注册一次

---

### 2. LLMClientManager - __new__ 单例 ✅

```python
# backend/daoyoucode/agents/llm/client_manager.py

class LLMClientManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        # 初始化代码
        self._initialized = True

def get_client_manager() -> LLMClientManager:
    return LLMClientManager()
```

**特点**:
- 使用 `__new__` 方法
- 确保只有一个实例
- HTTP连接池共享
- 配置只加载一次

---

### 3. AgentRegistry - 全局变量单例 ✅

```python
# backend/daoyoucode/agents/core/agent.py

# 全局注册表
_agent_registry = AgentRegistry()

def get_agent_registry() -> AgentRegistry:
    """获取Agent注册表"""
    return _agent_registry
```

**特点**:
- 直接创建全局实例
- 所有调用共享同一个注册表
- Agent只注册一次

---

### 4. OrchestratorRegistry - 全局变量单例 ✅

```python
# backend/daoyoucode/agents/core/orchestrator.py

# 全局注册表
_orchestrator_registry = OrchestratorRegistry()

def get_orchestrator_registry() -> OrchestratorRegistry:
    """获取编排器注册表"""
    return _orchestrator_registry
```

**特点**:
- 直接创建全局实例
- 所有调用共享同一个注册表
- 编排器只注册一次

---

## 初始化系统 - 幂等操作 ✅

```python
# backend/daoyoucode/agents/init.py

_initialized = False

def initialize_agent_system():
    """初始化Agent系统（幂等操作）"""
    global _initialized
    
    if _initialized:
        logger.debug("Agent系统已初始化，跳过")
        return get_tool_registry()
    
    # 初始化代码...
    _initialized = True
    return tool_registry
```

**特点**:
- 可以多次调用
- 只初始化一次
- 后续调用直接返回

---

## Working Directory 设计

### 为什么需要两次设置？

虽然工具注册表是单例，但 `working_directory` 是实例变量，可能在不同场景下需要不同的值。

### 设置点1: handle_chat() - 每次用户输入

```python
# backend/cli/commands/chat.py

def handle_chat(user_input: str, ui_context: dict):
    # 每次用户输入都会调用
    repo_path = os.path.abspath(ui_context["repo"])
    
    # 初始化系统（幂等，只初始化一次）
    initialize_agent_system()
    
    # 设置工作目录（每次都设置）✅
    registry = get_tool_registry()
    registry.set_working_directory(repo_path)
    
    # 执行skill
    result = loop.run_until_complete(execute_skill(...))
```

**为什么每次都设置？**
- 确保当前会话的工作目录正确
- 防止其他代码修改了工作目录
- 为后续工具调用提供正确的上下文

### 设置点2: _execute_skill_internal() - 每次skill执行

```python
# backend/daoyoucode/agents/executor.py

async def _execute_skill_internal(
    skill_name: str,
    user_input: str,
    context: Dict[str, Any]
):
    # 从context读取并设置工作目录 ✅
    if 'working_directory' in context or 'repo' in context:
        registry = get_tool_registry()
        working_dir = context.get('working_directory') or context.get('repo')
        if working_dir:
            registry.set_working_directory(working_dir)
    
    # 执行skill...
```

**为什么再次设置？**
- 防御性编程：确保即使有其他地方修改了工作目录，也能恢复
- 支持多会话：不同会话可能有不同的工作目录
- 从context读取：保证一致性

---

## 对比总结

| 系统 | 单例模式 | 初始化次数 | 配置更新 |
|------|---------|-----------|---------|
| ToolRegistry | ✅ 全局变量 | 1次 | 每次调用可更新 |
| LLMClientManager | ✅ __new__ | 1次 | 每次调用可更新 |
| AgentRegistry | ✅ 全局变量 | 1次 | 不可更新 |
| OrchestratorRegistry | ✅ 全局变量 | 1次 | 不可更新 |
| initialize_agent_system | ✅ 幂等 | 1次 | - |

---

## Working Directory 的特殊性

### 为什么 working_directory 需要每次设置？

1. **不是注册信息**
   - 工具、Agent、编排器是"注册一次，永久使用"
   - working_directory 是"运行时上下文"，可能变化

2. **会话相关**
   - 不同会话可能在不同目录工作
   - 需要根据当前会话动态设置

3. **防御性编程**
   - 即使是单例，实例变量也可能被修改
   - 每次设置确保正确性

### 类比其他系统

```python
# LLM配置也是每次可以更新的
client_manager = get_client_manager()  # 单例
client_manager.configure_provider(...)  # 每次可以更新配置

# 工具注册表也是每次可以更新工作目录的
tool_registry = get_tool_registry()  # 单例
tool_registry.set_working_directory(...)  # 每次可以更新工作目录
```

---

## 设计原则

### 1. 单例模式用于"注册表"

- ToolRegistry
- AgentRegistry
- OrchestratorRegistry
- LLMClientManager

**原因**: 避免重复注册，共享资源

### 2. 实例变量用于"运行时配置"

- working_directory
- provider_configs
- session_id

**原因**: 需要根据运行时上下文动态变化

### 3. 防御性设置

```python
# 设置1: 确保初始状态正确
registry.set_working_directory(repo_path)

# 设置2: 确保执行时状态正确
if 'working_directory' in context:
    registry.set_working_directory(context['working_directory'])
```

**原因**: 防止中间状态被修改

---

## 总结

### 问题：每次都重新初始化？

**答案**: ❌ 不是

- 工具注册表是**单例**，只初始化一次
- 工具只注册一次
- `initialize_agent_system()` 是**幂等**的

### 问题：这和其他一样么？

**答案**: ✅ 是的

- 所有核心系统都使用单例模式
- LLMClientManager、AgentRegistry、OrchestratorRegistry 都是单例
- 都只初始化一次

### 问题：为什么 working_directory 每次都设置？

**答案**: 因为它是**运行时配置**，不是注册信息

- 类似于 LLMClientManager 的 `configure_provider()`
- 需要根据当前会话动态设置
- 防御性编程，确保正确性

---

## 最佳实践

### 1. 注册信息 - 初始化一次

```python
# 工具注册
registry.register(MyTool())  # 只注册一次

# Agent注册
register_agent(MyAgent())  # 只注册一次
```

### 2. 运行时配置 - 每次设置

```python
# 工作目录
registry.set_working_directory(path)  # 每次设置

# LLM配置
client_manager.configure_provider(...)  # 每次可以更新
```

### 3. 防御性编程

```python
# 在关键点设置，确保正确性
def handle_chat(...):
    registry.set_working_directory(repo_path)  # 设置1
    execute_skill(...)

async def _execute_skill_internal(...):
    registry.set_working_directory(context['working_directory'])  # 设置2
    # 执行...
```

这样设计既保证了性能（单例），又保证了正确性（防御性设置）。
