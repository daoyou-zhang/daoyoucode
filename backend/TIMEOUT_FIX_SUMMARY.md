# 超时问题修复总结

## 问题描述

用户遇到请求超时错误：
```
警告: 请求超时（120秒），请检查网络或稍后重试。
```

## 问题根源

**CLI 命令超时设置过短**

- **配置文件**: `timeout: 1800` (30分钟) ✅
- **CLI 硬编码**: `timeout=120` (2分钟) ❌

CLI 的 120 秒超时覆盖了配置文件的 1800 秒，导致请求还在处理时就超时了。

## 修复方案

### 修改内容

**文件**: `backend/cli/commands/chat.py`
**行号**: 566-569

**修改前**:
```python
result = loop.run_until_complete(asyncio.wait_for(_run(), timeout=120))
```

**修改后**:
```python
# 从配置读取超时时间，默认30分钟
from daoyoucode.agents.llm.config_loader import load_llm_config
try:
    llm_config = load_llm_config()
    cli_timeout = llm_config.get('default', {}).get('timeout', 1800)
except:
    cli_timeout = 1800  # 默认30分钟

result = loop.run_until_complete(asyncio.wait_for(_run(), timeout=cli_timeout))
```

### 改进点

1. ✅ **从配置文件读取超时** - 不再硬编码
2. ✅ **默认值合理** - 1800秒（30分钟）
3. ✅ **容错处理** - 配置读取失败时使用默认值
4. ✅ **动态提示** - 错误信息显示实际超时时间

## 超时配置说明

### 当前配置

**配置文件**: `backend/config/llm_config.yaml`
```yaml
default:
  model: "qwen-max"
  temperature: 0.7
  max_tokens: 4000
  timeout: 1800  # 30 分钟
```

### 推荐超时值

根据任务类型：

| 任务类型 | 推荐超时 | 说明 |
|---------|---------|------|
| 简单问答 | 300秒 (5分钟) | 快速响应 |
| 代码生成 | 600秒 (10分钟) | 中等复杂度 |
| 代码审查 | 1200秒 (20分钟) | 需要多次工具调用 |
| 复杂重构 | 1800秒 (30分钟) | 大规模操作 |
| 项目分析 | 3600秒 (1小时) | 深度分析 |

### 修改超时

编辑 `backend/config/llm_config.yaml`:

```yaml
default:
  timeout: 1800  # 修改这个值
```

## 验证修复

### 1. 重新安装
```bash
cd backend
pip install -e .
```

### 2. 测试
```bash
daoyoucode chat "你好"
```

### 3. 检查日志
如果超时，会显示：
```
警告: 请求超时（1800秒），请检查网络或稍后重试。
```

## 其他超时配置

### LSP 超时
**文件**: `backend/daoyoucode/agents/tools/lsp_tools.py`
```python
await asyncio.sleep(15)  # LSP 请求超时15秒
```

### 超时恢复
**文件**: `backend/daoyoucode/agents/core/timeout_recovery.py`
```python
initial_timeout: float = 1800.0  # 初始超时30分钟
max_timeout: float = 3600.0      # 最大超时1小时
```

## 常见问题

### Q1: 为什么还是超时？

**可能原因**:
1. 网络问题 - 检查网络连接
2. API 限流 - 等待一段时间后重试
3. 模型负载高 - 换个时间段尝试
4. 任务太复杂 - 增加超时时间

**解决方案**:
```yaml
# 增加超时到1小时
default:
  timeout: 3600
```

### Q2: 如何设置不同任务的超时？

**方案**: 在 skill 配置中覆盖：

```yaml
# skills/programming/skill.yaml
llm:
  model: qwen-coder-plus
  timeout: 600  # 10分钟
```

### Q3: 如何禁用超时？

**不推荐**，但可以设置很大的值：

```yaml
default:
  timeout: 86400  # 24小时
```

## 监控建议

### 1. 启用详细日志
```python
import logging
logging.getLogger('daoyoucode').setLevel(logging.DEBUG)
```

### 2. 记录执行时间
在关键位置添加时间记录：
```python
import time
start = time.time()
# ... 执行
print(f"耗时: {time.time() - start:.2f}秒")
```

### 3. 超时告警
当超时频繁发生时：
- 检查网络质量
- 检查 API 配额
- 优化任务复杂度

## 总结

### 修复内容
✅ CLI 超时从 120秒 改为从配置读取（默认1800秒）
✅ 支持动态配置超时时间
✅ 改进错误提示信息

### 影响
- 不再频繁超时
- 可以处理更复杂的任务
- 配置更灵活

### 下一步
1. 重新安装: `pip install -e .`
2. 测试功能是否正常
3. 根据实际使用调整超时值

## 相关文档

- `TIMEOUT_CONFIG_GUIDE.md` - 详细的超时配置指南
- `config/llm_config.yaml` - LLM 配置文件
- `cli/commands/chat.py` - CLI 命令实现
