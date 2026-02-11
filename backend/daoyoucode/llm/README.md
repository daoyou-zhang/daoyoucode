# LLM模块

统一的大语言模型调用接口，提供完整的Skill管理、上下文管理、限流熔断等功能。

## 快速开始

### 1. 基础使用

```python
from daoyoucode.llm import get_orchestrator

# 获取编排器
orchestrator = get_orchestrator()

# 执行Skill
result = await orchestrator.execute_skill(
    skill_name="documentation",
    user_message="帮我写一个README文档",
    session_id="user_123_session_1"
)

print(result['response'])
```

### 2. 普通对话

```python
# 不使用Skill的普通对话
result = await orchestrator.chat(
    user_message="你好",
    session_id="user_123_session_1",
    model="qwen-turbo"
)

print(result['response'])
```

### 3. 流式响应

```python
# 流式执行Skill
async for chunk in orchestrator.stream_execute_skill(
    skill_name="code_review",
    user_message="审查这段代码...",
    session_id="user_123_session_1"
):
    if chunk['type'] == 'token':
        print(chunk['content'], end='', flush=True)
    elif chunk['type'] == 'done':
        print(f"\n\n完成！元数据: {chunk['metadata']}")
```

## 核心功能

### 1. Skill管理

```python
# 列出所有Skill
skills = orchestrator.list_skills()
for name, desc in skills.items():
    print(f"{name}: {desc}")

# 获取Skill详细信息
info = orchestrator.get_skill_info("documentation")
print(f"版本: {info['version']}")
print(f"模型: {info['llm']['model']}")

# 搜索Skill
results = orchestrator.search_skills("文档")
for skill in results:
    print(f"{skill['name']}: {skill['description']}")
```

### 2. 自动追问判断

编排器会自动判断用户消息是否为追问，并选择合适的执行模式：

```python
# 第一次提问（完整模式）
result1 = await orchestrator.execute_skill(
    skill_name="documentation",
    user_message="写一个API文档",
    session_id="session_1"
)
# is_followup: False, 使用完整prompt

# 追问（轻量级模式，节省tokens）
result2 = await orchestrator.execute_skill(
    skill_name="documentation",
    user_message="再加上安装说明",
    session_id="session_1"
)
# is_followup: True, 使用轻量级prompt + 历史摘要
```

### 3. 上下文管理

```python
# 查看对话历史
history = orchestrator.context_manager.get_history("session_1")
for item in history:
    print(f"用户: {item['user']}")
    print(f"AI: {item['ai']}")

# 清除会话
orchestrator.clear_session("session_1")
```

### 4. 统计信息

```python
# 获取统计信息
stats = orchestrator.get_stats()

print(f"已加载Skill数: {stats['skills']['total']}")
print(f"总执行次数: {stats['executor']['total_executions']}")
print(f"成功率: {stats['executor']['successful_executions'] / stats['executor']['total_executions']:.2%}")
print(f"总成本: ¥{stats['executor']['total_cost']:.4f}")
```

## 高级功能

### 1. 强制完整模式

```python
# 即使是追问，也使用完整prompt
result = await orchestrator.execute_skill(
    skill_name="documentation",
    user_message="继续",
    session_id="session_1",
    force_full_mode=True  # 强制完整模式
)
```

### 2. 自定义上下文

```python
# 传入额外上下文
result = await orchestrator.execute_skill(
    skill_name="code_review",
    user_message="审查代码",
    session_id="session_1",
    context={
        'code': '...',
        'language': 'python',
        'focus_areas': ['security', 'performance']
    }
)
```

### 3. 用户限流

```python
# 指定用户ID，启用限流
result = await orchestrator.execute_skill(
    skill_name="documentation",
    user_message="写文档",
    session_id="session_1",
    user_id=123  # 用户ID，用于限流
)
```

## 模块结构

```
daoyoucode/llm/
├── __init__.py              # 主入口
├── orchestrator.py          # 编排器（主要接口）
├── base.py                  # 基础类
├── exceptions.py            # 异常定义
├── client_manager.py        # 客户端管理
├── clients/                 # LLM客户端
│   └── unified.py          # 统一客户端
├── skills/                  # Skill系统
│   ├── loader.py           # 加载器
│   ├── executor.py         # 执行器
│   ├── monitor.py          # 监控器
│   └── examples/           # 示例Skills
├── context/                 # 上下文管理
│   ├── followup_detector.py  # 追问判断
│   ├── memory_manager.py     # 记忆管理
│   └── manager.py            # 上下文管理器
└── utils/                   # 工具类
    ├── rate_limiter.py     # 限流器
    ├── circuit_breaker.py  # 熔断器
    └── fallback.py         # 降级策略
```

## 配置

### 1. 客户端配置

```python
from daoyoucode.llm import get_client_manager

client_manager = get_client_manager()

# 配置提供商
client_manager.configure_provider(
    "qwen",
    api_key="your-api-key",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)
```

### 2. 限流配置

```python
from daoyoucode.llm.utils import get_rate_limiter

rate_limiter = get_rate_limiter()

# 配置限流规则
rate_limiter.set_user_limit(user_id=123, requests_per_minute=10)
rate_limiter.set_model_limit(model="qwen-max", requests_per_minute=100)
```

### 3. 熔断配置

```python
from daoyoucode.llm.utils import get_circuit_breaker_manager

cb_manager = get_circuit_breaker_manager()

# 获取熔断器
breaker = cb_manager.get_breaker("qwen-max")

# 查看状态
print(f"状态: {breaker.state}")
print(f"失败次数: {breaker.failure_count}")
```

### 4. 降级配置

```python
from daoyoucode.llm.utils import get_fallback_strategy

fallback = get_fallback_strategy()

# 配置降级链
fallback.configure_fallback_chain("qwen-max", [
    "qwen-plus",
    "qwen-turbo"
])
```

## 性能指标

- **追问判断**: <5ms
- **Skill加载**: <100ms
- **执行延迟**: 取决于LLM响应（通常1-3秒）
- **追问优化**: tokens节省50%+
- **内存占用**: ~1KB/轮对话

## 最佳实践

### 1. 会话管理

- 使用有意义的session_id（如：`user_{user_id}_session_{timestamp}`）
- 定期清理不活跃的会话
- 避免在session_id中包含敏感信息

### 2. 错误处理

```python
from daoyoucode.llm.exceptions import (
    LLMError,
    LLMRateLimitError,
    SkillNotFoundError
)

try:
    result = await orchestrator.execute_skill(...)
except SkillNotFoundError:
    print("Skill不存在")
except LLMRateLimitError:
    print("请求过于频繁，请稍后再试")
except LLMError as e:
    print(f"LLM调用失败: {e}")
```

### 3. 资源清理

```python
# 应用关闭时清理资源
await orchestrator.client_manager.close()
```

## 测试

运行测试：

```bash
cd backend
python -m pytest tests/llm/ -v
```

测试覆盖：
- 基础模块: 31个测试 ✅
- 限流熔断: 26个测试 ✅
- Skill系统: 36个测试 ✅
- 上下文管理: 30个测试 ✅
- 编排器: 12个测试 ✅
- **总计**: 135个测试 ✅

## 更多信息

- [实施计划](../../../.kiro/specs/llm-module-architecture/IMPLEMENTATION_PLAN.md)
- [架构评审](../../../.kiro/specs/llm-module-architecture/architecture-review.md)
- [Skill系统文档](skills/README.md)
- [阶段完成报告](PHASE3_COMPLETE.md)

## 版本

当前版本: 0.1.0

## 许可

MIT License
