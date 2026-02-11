# 失败恢复系统

借鉴daoyouCodePilot的自动重试和失败分析机制，提供智能的失败恢复能力。

## 核心特性

- ✅ 自动重试（可配置次数）
- ✅ 结果验证
- ✅ 错误分析和修复建议
- ✅ 执行历史记录
- ✅ 重试延迟控制
- ✅ 可插拔验证器和分析器

## 快速开始

### 基本使用

```python
from daoyoucode.agents.core.recovery import RecoveryManager, RecoveryConfig

# 创建恢复管理器
manager = RecoveryManager(RecoveryConfig(
    max_retries=3,
    retry_delay=1.0
))

# 执行带恢复的函数
result = await manager.execute_with_recovery(
    some_async_function,
    arg1="value1",
    arg2="value2"
)
```

### 集成到Skill执行

```python
from daoyoucode.agents.executor import execute_skill
from daoyoucode.agents.core.recovery import RecoveryConfig, validate_success_flag

# 执行Skill，启用自动恢复
result = await execute_skill(
    skill_name='translation',
    user_input='翻译这段话',
    session_id='session_123',
    recovery_config=RecoveryConfig(max_retries=3),
    validator=validate_success_flag
)
```

## 配置选项

### RecoveryConfig

```python
@dataclass
class RecoveryConfig:
    max_retries: int = 3           # 最大重试次数
    enable_analysis: bool = True   # 启用错误分析
    enable_rollback: bool = False  # 启用回滚（预留）
    retry_delay: float = 1.0       # 重试延迟（秒）
```

## 验证器

验证器用于检查执行结果是否有效。

### 内置验证器

```python
from daoyoucode.agents.core.recovery import (
    validate_non_empty,      # 验证结果非空
    validate_success_flag,   # 验证success标志
    validate_no_error        # 验证无error字段
)

# 使用内置验证器
result = await manager.execute_with_recovery(
    func,
    validator=validate_success_flag
)
```

### 自定义验证器

```python
def my_validator(result: Any) -> bool:
    """自定义验证器"""
    if not isinstance(result, dict):
        return False
    
    # 检查必需字段
    if 'data' not in result:
        return False
    
    # 检查数据有效性
    if len(result['data']) == 0:
        return False
    
    return True

# 使用自定义验证器
result = await manager.execute_with_recovery(
    func,
    validator=my_validator
)
```

## 分析器

分析器用于分析错误并生成修复建议。

### 简单分析器

```python
from daoyoucode.agents.core.recovery import simple_analyzer

result = await manager.execute_with_recovery(
    func,
    analyzer=simple_analyzer
)
```

### LLM分析器

```python
from daoyoucode.agents.core.recovery import llm_analyzer
from daoyoucode.llm import get_client_manager

# 获取LLM客户端
client_manager = get_client_manager()
client = await client_manager.get_client(model="qwen-max")

# 使用LLM分析器
result = await manager.execute_with_recovery(
    func,
    analyzer=lambda result, error: llm_analyzer(result, error, client)
)
```

### 自定义分析器

```python
def my_analyzer(result: Optional[Any], error: Optional[Exception]) -> str:
    """自定义分析器"""
    if error:
        # 分析错误类型
        if isinstance(error, ValueError):
            return "输入格式不正确，请检查输入"
        elif isinstance(error, KeyError):
            return "缺少必需字段，请补充完整"
        else:
            return f"发生错误: {error}，请重试"
    
    if result:
        # 分析结果
        if not result.get('data'):
            return "结果为空，请提供更多信息"
    
    return ""

# 使用自定义分析器
result = await manager.execute_with_recovery(
    func,
    analyzer=my_analyzer
)
```

## 执行历史

```python
# 执行后查看历史
result = await manager.execute_with_recovery(func)

history = manager.get_history()
for record in history:
    print(f"尝试 {record['attempt']}: {'成功' if record['success'] else '失败'}")
    if not record['success']:
        print(f"  错误: {record['error']}")
    else:
        print(f"  结果: {record['result']}")

# 重置状态
manager.reset()
```

## 完整示例

### 示例1: 翻译任务自动恢复

```python
from daoyoucode.agents.executor import execute_skill
from daoyoucode.agents.core.recovery import (
    RecoveryConfig,
    validate_non_empty,
    simple_analyzer
)

async def translate_with_recovery(text: str):
    """带自动恢复的翻译"""
    
    result = await execute_skill(
        skill_name='translation',
        user_input=f'翻译: {text}',
        recovery_config=RecoveryConfig(
            max_retries=3,
            retry_delay=1.0
        ),
        validator=validate_non_empty,
        analyzer=simple_analyzer
    )
    
    return result

# 使用
result = await translate_with_recovery("Hello, world!")
print(result['content'])
```

### 示例2: 代码生成自动修复

```python
from daoyoucode.agents.core.recovery import RecoveryManager, RecoveryConfig

async def generate_code_with_fix(prompt: str):
    """生成代码，自动修复语法错误"""
    
    def validate_code(result: dict) -> bool:
        """验证代码是否有效"""
        if not result.get('success'):
            return False
        
        code = result.get('content', '')
        if not code:
            return False
        
        # 简单语法检查
        try:
            compile(code, '<string>', 'exec')
            return True
        except SyntaxError:
            return False
    
    def analyze_code_error(result: dict, error: Exception) -> str:
        """分析代码错误"""
        if error:
            return f"生成失败: {error}，请重新生成"
        
        if result:
            code = result.get('content', '')
            try:
                compile(code, '<string>', 'exec')
            except SyntaxError as e:
                return f"代码有语法错误: {e}，请修复"
        
        return ""
    
    manager = RecoveryManager(RecoveryConfig(max_retries=3))
    
    result = await manager.execute_with_recovery(
        execute_skill,
        skill_name='programmer',
        user_input=prompt,
        validator=validate_code,
        analyzer=analyze_code_error
    )
    
    return result

# 使用
result = await generate_code_with_fix("写一个快速排序函数")
print(result['content'])
```

### 示例3: API调用自动重试

```python
import aiohttp
from daoyoucode.agents.core.recovery import RecoveryManager, RecoveryConfig

async def call_api_with_retry(url: str, data: dict):
    """调用API，自动重试"""
    
    async def api_call():
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                if response.status != 200:
                    raise Exception(f"API错误: {response.status}")
                return await response.json()
    
    def validate_response(result: dict) -> bool:
        """验证响应"""
        return result.get('status') == 'success'
    
    manager = RecoveryManager(RecoveryConfig(
        max_retries=5,
        retry_delay=2.0
    ))
    
    result = await manager.execute_with_recovery(
        api_call,
        validator=validate_response
    )
    
    return result

# 使用
result = await call_api_with_retry(
    'https://api.example.com/translate',
    {'text': 'Hello', 'target': 'zh'}
)
```

## 异常处理

```python
from daoyoucode.agents.core.recovery import MaxRetriesExceeded

try:
    result = await manager.execute_with_recovery(func)
except MaxRetriesExceeded as e:
    print(f"执行失败: {e}")
    print(f"最后错误: {e.last_error}")
    
    # 查看执行历史
    history = manager.get_history()
    for record in history:
        print(f"尝试 {record['attempt']}: {record}")
```

## 最佳实践

### 1. 合理设置重试次数

```python
# 快速操作：少重试
RecoveryConfig(max_retries=2)

# 网络请求：多重试
RecoveryConfig(max_retries=5)

# 复杂任务：适中重试
RecoveryConfig(max_retries=3)
```

### 2. 使用适当的延迟

```python
# 本地操作：短延迟
RecoveryConfig(retry_delay=0.5)

# 网络请求：长延迟
RecoveryConfig(retry_delay=2.0)

# API限流：更长延迟
RecoveryConfig(retry_delay=5.0)
```

### 3. 组合验证器

```python
def combined_validator(result: dict) -> bool:
    """组合多个验证条件"""
    return (
        validate_non_empty(result) and
        validate_success_flag(result) and
        validate_no_error(result)
    )
```

### 4. 智能分析器

```python
async def smart_analyzer(result: dict, error: Exception) -> str:
    """智能分析器"""
    # 1. 先用规则分析
    if error:
        if isinstance(error, TimeoutError):
            return "请求超时，请稍后重试"
        elif isinstance(error, ConnectionError):
            return "网络连接失败，请检查网络"
    
    # 2. 如果规则无法处理，使用LLM
    if llm_client:
        return await llm_analyzer(result, error, llm_client)
    
    # 3. 默认建议
    return simple_analyzer(result, error)
```

## 性能考虑

### 1. 避免过度重试

```python
# ❌ 不好：重试太多次
RecoveryConfig(max_retries=10)

# ✅ 好：合理的重试次数
RecoveryConfig(max_retries=3)
```

### 2. 控制延迟时间

```python
# ❌ 不好：延迟太长
RecoveryConfig(retry_delay=10.0)

# ✅ 好：适当的延迟
RecoveryConfig(retry_delay=1.0)
```

### 3. 禁用不需要的功能

```python
# 如果不需要分析，禁用它
RecoveryConfig(
    max_retries=3,
    enable_analysis=False
)
```

## 与其他系统集成

### 与Hook系统集成

```python
from daoyoucode.agents.hooks import RetryHook

# Hook系统已经提供了重试功能
# 可以选择使用Hook或RecoveryManager

# 方式1: 使用Hook（简单场景）
# 在skill.yaml中配置hooks: [retry]

# 方式2: 使用RecoveryManager（复杂场景）
result = await execute_skill(
    skill_name='my_skill',
    user_input='...',
    recovery_config=RecoveryConfig(max_retries=3)
)
```

### 与权限系统集成

```python
from daoyoucode.agents.core.permission import PermissionManager

async def execute_with_permission_and_recovery(skill_name: str, user_input: str):
    """同时使用权限和恢复"""
    
    # 1. 检查权限
    permission_manager = PermissionManager()
    if not await permission_manager.check_permission('execute', skill_name, 'user'):
        raise PermissionError(f"无权执行: {skill_name}")
    
    # 2. 执行（带恢复）
    result = await execute_skill(
        skill_name=skill_name,
        user_input=user_input,
        recovery_config=RecoveryConfig(max_retries=3)
    )
    
    return result
```

## 总结

失败恢复系统提供了：

1. **自动重试**: 减少人工干预
2. **智能分析**: 自动生成修复建议
3. **灵活配置**: 适应不同场景
4. **完整历史**: 便于调试和分析
5. **易于集成**: 与现有系统无缝配合

通过合理使用失败恢复系统，可以大幅提升系统的鲁棒性和用户体验。
