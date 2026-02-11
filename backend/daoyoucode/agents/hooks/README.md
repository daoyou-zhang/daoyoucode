# Hook系统

提供统一的扩展点，类似oh-my-opencode的Hook机制。

## 架构

```
Before Hooks → Execute Skill → After Hooks
                    ↓ (error)
                Error Hooks
```

## 内置Hooks

### 1. LoggingHook
记录Skill执行的详细日志。

```python
from daoyoucode.agents.hooks import LoggingHook
from daoyoucode.agents import register_hook

# 注册
register_hook(LoggingHook())
```

### 2. MetricsHook
收集性能指标（耗时、tokens、成本）。

```python
from daoyoucode.agents.hooks import MetricsHook

hook = MetricsHook()
register_hook(hook)

# 获取指标
metrics = hook.get_all_metrics()
```

### 3. ValidationHook
验证输入合法性。

```python
from daoyoucode.agents.hooks import ValidationHook

hook = ValidationHook(
    min_length=1,
    max_length=5000,
    forbidden_words=['spam', 'test']
)
register_hook(hook)
```

### 4. RetryHook
自动重试失败的执行。

```python
from daoyoucode.agents.hooks import RetryHook

hook = RetryHook(
    max_retries=3,
    retry_delay=1.0,
    exponential_backoff=True
)
register_hook(hook)
```

## 创建自定义Hook

```python
from daoyoucode.agents import BaseHook, HookContext, register_hook
from typing import Dict, Any, Optional

class MyHook(BaseHook):
    """自定义Hook"""
    
    def __init__(self):
        super().__init__("my_hook")
    
    async def on_before_execute(
        self,
        context: HookContext
    ) -> HookContext:
        """执行前"""
        print(f"Before: {context.skill_name}")
        return context
    
    async def on_after_execute(
        self,
        context: HookContext,
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行后"""
        print(f"After: {result.get('success')}")
        return result
    
    async def on_error(
        self,
        context: HookContext,
        error: Exception
    ) -> Optional[Dict[str, Any]]:
        """错误处理"""
        print(f"Error: {error}")
        return None  # 不处理，继续抛出

# 注册
register_hook(MyHook())
```

## 使用示例

### 基本使用

```python
from daoyoucode.agents import execute_skill, register_hook
from daoyoucode.agents.hooks import LoggingHook, MetricsHook

# 1. 注册Hooks
register_hook(LoggingHook())
register_hook(MetricsHook())

# 2. 执行Skill（自动应用Hooks）
result = await execute_skill(
    skill_name='translation',
    user_input='Hello World',
    session_id='session_123'
)

# 3. Hooks自动记录日志和指标
```

### 使用默认Hook集合

```python
from daoyoucode.agents.hooks import create_default_hooks
from daoyoucode.agents import register_hook

# 注册默认Hooks
for hook in create_default_hooks():
    register_hook(hook)
```

### 生产环境配置

```python
from daoyoucode.agents.hooks import create_production_hooks

# 注册生产环境Hooks（包含重试）
for hook in create_production_hooks():
    register_hook(hook)
```

### 动态启用/禁用Hook

```python
from daoyoucode.agents import get_hook_manager

manager = get_hook_manager()

# 获取Hook
hook = manager.get_hook('logging')

# 禁用
hook.disable()

# 启用
hook.enable()

# 注销
manager.unregister('logging')
```

## Hook执行顺序

1. **Before Hooks**: 按注册顺序执行
2. **Skill Execution**: 执行Skill
3. **After Hooks**: 按注册顺序执行
4. **Error Hooks**: 如果出错，按注册顺序执行

## 最佳实践

### 1. Hook应该轻量
```python
# ❌ 不好：耗时操作
async def on_before_execute(self, context):
    await heavy_database_query()  # 阻塞执行
    return context

# ✅ 好：异步后台任务
async def on_before_execute(self, context):
    asyncio.create_task(log_to_database())  # 不阻塞
    return context
```

### 2. Hook应该幂等
```python
# ✅ 好：可以多次执行
async def on_before_execute(self, context):
    context.metadata['timestamp'] = time.time()
    return context
```

### 3. Hook应该处理异常
```python
# ✅ 好：捕获异常
async def on_before_execute(self, context):
    try:
        # 可能失败的操作
        ...
    except Exception as e:
        self.logger.error(f"Hook失败: {e}")
    return context
```

### 4. 使用metadata传递数据
```python
# ✅ 好：使用metadata
async def on_before_execute(self, context):
    context.metadata['start_time'] = time.time()
    return context

async def on_after_execute(self, context, result):
    start_time = context.metadata.get('start_time')
    if start_time:
        duration = time.time() - start_time
        result['duration'] = duration
    return result
```

## 对比oh-my-opencode

| 特性 | oh-my-opencode | 本项目 |
|------|----------------|--------|
| Hook数量 | 31个 | 4个核心+可扩展 |
| 生命周期 | PreToolUse/PostToolUse/Stop等 | Before/After/Error |
| 配置方式 | TypeScript配置 | Python代码 |
| 扩展性 | 固定Hook | 完全可扩展 |
| 复杂度 | 高 | 低 |

## 优势

- ✅ **简单易用**: 只需3个方法
- ✅ **完全可扩展**: 任何人都可以创建Hook
- ✅ **统一接口**: 所有Hook使用相同接口
- ✅ **灵活组合**: 可以任意组合Hook
- ✅ **性能友好**: 轻量级设计
