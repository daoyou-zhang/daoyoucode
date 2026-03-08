# Context 集成当前进度

## 已完成 ✅

### 1. 导入 Context 类
```python
from .context import Context, ContextManager, get_context_manager
from datetime import datetime
```

### 2. 初始化 ContextManager
```python
self.context_manager = get_context_manager()
self.logger.debug("上下文管理器已就绪")
```

### 3. 在 execute() 开头创建 Context 对象
```python
# 获取或创建 Context 对象
session_id = context_dict.get('session_id', 'default')
try:
    ctx = self.context_manager.get_or_create_context(session_id)
    ctx.update(context_dict, track_change=False)
    context_dict['_context_obj'] = ctx
    self.logger.debug(f"✅ Context 对象已创建: session={session_id}")
except Exception as e:
    self.logger.warning(f"创建 Context 对象失败: {e}，继续使用字典模式")
    ctx = None
```

## 待完成 ⚠️

### 1. 全局替换 context → context_dict

**问题**：execute() 方法中有大量 `context[...]` 的使用

**影响范围**：约 50+ 处

**解决方案**：
- 方案A：全局替换（风险较高）
- 方案B：保持参数名为 `context`，只在内部使用 Context 对象（推荐）

### 2. 在工具调用后保存结果

**位置**：工具调用循环（约第 800-1000 行）

**需要添加**：
```python
# 执行工具后
ctx = context_dict.get('_context_obj')
if ctx:
    self._save_tool_result_to_context(ctx, tool_name, result)
```

### 3. 添加辅助方法

需要添加 3 个方法：
- `_save_tool_result_to_context()`
- `_extract_paths_from_result()`
- `_format_context_info()`

## 建议的实施策略

### 策略1：最小化修改（推荐）⭐⭐⭐⭐⭐

**核心思想**：不改变参数名，只在关键位置使用 Context 对象

**优点**：
- 修改量最小
- 风险最低
- 向后兼容

**具体做法**：

#### 1. 保持参数名为 `context`
```python
async def execute(
    self,
    prompt_source: Dict[str, Any],
    user_input: str,
    context: Optional[Dict[str, Any]] = None,  # 保持原名
    ...
):
    if context is None:
        context = {}
    
    # 创建 Context 对象
    session_id = context.get('session_id', 'default')
    try:
        ctx = self.context_manager.get_or_create_context(session_id)
        ctx.update(context, track_change=False)
        context['_context_obj'] = ctx  # 保存到字典中
    except Exception as e:
        self.logger.warning(f"创建 Context 对象失败: {e}")
        ctx = None
    
    # 后续代码不变，继续使用 context 字典
    # 只在需要的地方使用 ctx 对象
```

#### 2. 只在关键位置使用 Context 对象

**位置1：工具调用后**
```python
# 执行工具
result = await tool.execute(**tool_kwargs)

# 保存到 Context
ctx = context.get('_context_obj')
if ctx:
    self._save_tool_result_to_context(ctx, tool_name, result)
```

**位置2：渲染 Prompt 时**
```python
def _render_prompt(self, prompt, user_input, context):
    ctx = context.get('_context_obj')
    if ctx:
        context_info = self._format_context_info(ctx)
        prompt = f"{context_info}\n\n{prompt}"
    ...
```

#### 3. 添加辅助方法（在类的末尾）

这些方法不影响现有代码，可以安全添加。

### 策略2：完全重构（不推荐）❌

**问题**：
- 需要修改 50+ 处代码
- 风险高
- 可能引入 bug
- 测试工作量大

## 当前状态

### 已修改的代码

1. ✅ 导入语句
2. ✅ `__init__` 方法
3. ✅ `execute()` 方法开头（但参数名改成了 `context_dict`）

### 问题

参数名改成 `context_dict` 后，后续所有使用 `context` 的地方都需要改成 `context_dict`，这会导致大量修改。

## 建议的修复方案

### 方案：回退参数名修改，采用策略1

#### 步骤1：回退 execute() 的参数名

将 `context_dict` 改回 `context`，但在内部创建 Context 对象：

```python
async def execute(
    self,
    prompt_source: Dict[str, Any],
    user_input: str,
    context: Optional[Dict[str, Any]] = None,  # 改回原名
    llm_config: Optional[Dict[str, Any]] = None,
    tools: Optional[List[str]] = None,
    max_tool_iterations: int = 15,
    enable_streaming: bool = False
):
    if context is None:
        context = {}
    
    # 🆕 获取或创建 Context 对象
    session_id = context.get('session_id', 'default')
    try:
        ctx = self.context_manager.get_or_create_context(session_id)
        ctx.update(context, track_change=False)
        context['_context_obj'] = ctx
        self.logger.debug(f"✅ Context 对象已创建: session={session_id}")
    except Exception as e:
        self.logger.warning(f"创建 Context 对象失败: {e}，继续使用字典模式")
    
    # 后续代码不变
    session_id = context.get('session_id', 'default')
    user_id = context.get('user_id')
    ...
```

#### 步骤2：找到工具调用的位置

搜索工具执行的代码，添加保存逻辑。

#### 步骤3：添加辅助方法

在类的末尾添加 3 个辅助方法。

## 下一步行动

### 选项A：继续当前方向（不推荐）

- 需要将所有 `context` 改为 `context_dict`
- 工作量大，风险高

### 选项B：回退并采用策略1（推荐）⭐⭐⭐⭐⭐

- 回退参数名修改
- 采用最小化修改策略
- 工作量小，风险低

### 选项C：暂停集成

- 当前的 Prompt 工程方案已经可以解决 70-80% 的问题
- 等待更好的时机再集成

## 我的建议

**采用选项B**：回退并采用策略1

**理由**：
1. 最小化修改，风险最低
2. 保持向后兼容
3. 可以快速完成
4. 效果明显

**具体步骤**：
1. 回退 execute() 的参数名（5分钟）
2. 找到工具调用位置，添加保存逻辑（30分钟）
3. 添加 3 个辅助方法（30分钟）
4. 测试（30分钟）

**总时间**：约 2 小时

你觉得如何？要我继续吗？
