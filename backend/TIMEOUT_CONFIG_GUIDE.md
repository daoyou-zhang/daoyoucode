# DaoyouCode 超时配置指南

## 问题说明

你遇到的超时问题：
```
警告: 请求超时（120秒），请检查网络或稍后重试。
```

## 超时层级

DaoyouCode 有多个超时层级：

### 1. CLI 命令超时（最外层）⚠️
**位置**: `backend/cli/commands/chat.py:566`
```python
result = loop.run_until_complete(asyncio.wait_for(_run(), timeout=120))
```

**当前值**: 120 秒（硬编码）
**问题**: 这个超时太短，会在 LLM 响应之前就超时

### 2. LLM 配置超时（配置文件）✅
**位置**: `backend/config/llm_config.yaml`
```yaml
default:
  timeout: 1800  # 30 分钟
```

**当前值**: 1800 秒（30分钟）
**状态**: 配置正确，但被 CLI 超时覆盖了

### 3. 超时恢复配置 ✅
**位置**: `backend/daoyoucode/agents/core/timeout_recovery.py`
```python
initial_timeout: float = 1800.0  # 30分钟
max_timeout: float = 3600.0      # 1小时
```

**状态**: 配置合理

## 问题根源

CLI 命令的 120 秒超时太短，导致：
1. LLM 还在处理请求
2. CLI 就已经超时退出
3. 配置文件中的 1800 秒超时没有生效

## 解决方案

### 方案 1: 修改 CLI 超时（推荐）

修改 `backend/cli/commands/chat.py`，从配置文件读取超时：

```python
# 从配置读取超时
from daoyoucode.agents.llm.config_loader import load_llm_config

llm_config = load_llm_config()
timeout = llm_config.get('default', {}).get('timeout', 1800)

# 使用配置的超时
result = loop.run_until_complete(asyncio.wait_for(_run(), timeout=timeout))
```

### 方案 2: 增加 CLI 超时（快速修复）

直接修改硬编码的超时值：

```python
# 从 120 改为 1800（30分钟）
result = loop.run_until_complete(asyncio.wait_for(_run(), timeout=1800))
```

### 方案 3: 移除 CLI 超时（最灵活）

让 LLM 配置的超时生效：

```python
# 移除 asyncio.wait_for，让内部超时控制
result = loop.run_until_complete(_run())
```

## 超时配置最佳实践

### 推荐超时值

根据任务类型设置不同的超时：

```yaml
# backend/config/llm_config.yaml
default:
  timeout: 1800  # 30分钟 - 适合大多数任务
  
# 对于特定场景
quick_tasks:
  timeout: 300   # 5分钟 - 简单问答
  
complex_tasks:
  timeout: 3600  # 1小时 - 复杂分析、大规模重构
```

### 超时层级建议

1. **CLI 超时**: 应该 >= LLM 超时 + 缓冲时间
   ```python
   cli_timeout = llm_timeout + 60  # 额外1分钟缓冲
   ```

2. **LLM 超时**: 根据任务复杂度
   - 简单问答: 300秒（5分钟）
   - 代码生成: 600秒（10分钟）
   - 代码审查: 1200秒（20分钟）
   - 复杂重构: 1800秒（30分钟）

3. **工具超时**: 应该 < LLM 超时
   - 文件读取: 10秒
   - LSP 请求: 30秒
   - Git 操作: 60秒

## 快速修复

立即修复超时问题：

```bash
# 1. 编辑 chat.py
cd backend/cli/commands

# 2. 找到第 566 行
# 将: timeout=120
# 改为: timeout=1800

# 3. 保存并重新安装
cd ../..
pip install -e .
```

## 监控超时

### 查看超时日志

```python
import logging
logging.getLogger('daoyoucode.agents').setLevel(logging.DEBUG)
```

### 超时统计

在日志中查找：
```
TimeoutError
asyncio.TimeoutError
请求超时
```

## 常见超时场景

### 1. LLM 响应慢
**原因**: 
- 网络延迟
- API 限流
- 模型负载高

**解决**: 
- 增加超时时间
- 使用更快的模型
- 启用重试机制

### 2. 工具执行慢
**原因**:
- 大文件读取
- LSP 分析耗时
- Git 操作慢

**解决**:
- 优化工具调用
- 限制文件大小
- 使用缓存

### 3. 多次工具调用
**原因**:
- ReAct 编排器多次调用工具
- 每次调用都需要时间

**解决**:
- 使用 simple 编排器（更快）
- 限制最大工具调用次数
- 增加总超时时间

## 配置示例

### 开发环境（快速反馈）
```yaml
default:
  timeout: 300  # 5分钟
  max_tokens: 2000
```

### 生产环境（稳定可靠）
```yaml
default:
  timeout: 1800  # 30分钟
  max_tokens: 4000
```

### 复杂任务（充足时间）
```yaml
default:
  timeout: 3600  # 1小时
  max_tokens: 8000
```

## 调试超时

### 1. 启用详细日志
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 2. 测量执行时间
```python
import time
start = time.time()
# ... 执行任务
print(f"耗时: {time.time() - start:.2f}秒")
```

### 3. 分析瓶颈
- LLM 响应时间
- 工具执行时间
- 网络延迟

## 总结

**当前问题**: CLI 超时（120秒）< LLM 配置超时（1800秒）

**解决方案**: 
1. 修改 `cli/commands/chat.py:566`
2. 将 `timeout=120` 改为 `timeout=1800`
3. 或从配置文件读取超时值

**长期建议**:
- 统一超时配置管理
- 从配置文件读取所有超时值
- 根据任务类型动态调整超时
- 添加超时监控和告警

## 立即行动

修改这一行代码即可解决问题：

**文件**: `backend/cli/commands/chat.py`
**行号**: 566
**修改前**: `result = loop.run_until_complete(asyncio.wait_for(_run(), timeout=120))`
**修改后**: `result = loop.run_until_complete(asyncio.wait_for(_run(), timeout=1800))`

或者更好的方式，从配置读取：

```python
# 在文件开头添加
from daoyoucode.agents.llm.config_loader import load_llm_config

# 在 main 函数中
llm_config = load_llm_config()
cli_timeout = llm_config.get('default', {}).get('timeout', 1800)

# 使用配置的超时
result = loop.run_until_complete(asyncio.wait_for(_run(), timeout=cli_timeout))
```
