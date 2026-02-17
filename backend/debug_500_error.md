# Debug 500错误指南

## 快速Debug步骤

### 1. 启用详细日志

设置环境变量启用DEBUG模式：

```bash
# Windows CMD
set DEBUG_LLM_REQUEST=1
set PYTHONPATH=D:\daoyouspace\daoyoucode\backend

# Windows PowerShell
$env:DEBUG_LLM_REQUEST="1"
$env:PYTHONPATH="D:\daoyouspace\daoyoucode\backend"

# 然后运行你的程序
python daoyoucode.py chat --skill sisyphus-orchestrator
```

### 2. 查看日志输出

运行后，日志会显示：

```
============================================================
🔍 LLM请求调试信息
模型: qwen-max
API Key: sk-d2971f201557...3b87
消息数量: 5
Functions数量: 26
消息 1 (user): 你好，请回复'测试成功'...
消息 2 (assistant): 测试成功...
...
Payload大小: 45678 字节 (44.61 KB)
💾 完整请求已保存到: debug_llm_request_1234567890.json
============================================================
```

### 3. 检查关键信息

从日志中查看：

#### ✅ 检查点1: Payload大小
```
Payload大小: 45678 字节 (44.61 KB)
```
- **如果 > 100KB**: 可能太大，尝试减少历史消息或Functions
- **正常范围**: 10-50KB

#### ✅ 检查点2: 消息数量
```
消息数量: 15
```
- **如果 > 20**: 历史消息太多，尝试减少
- **建议**: 保持在10条以内

#### ✅ 检查点3: Functions数量
```
Functions数量: 26
```
- **如果 > 30**: 工具太多，可能导致500错误
- **建议**: 只提供必要的工具（5-15个）

#### ✅ 检查点4: API Key轮询
```
API Key: sk-d2971f201557...3b87
```
下次请求应该切换到另一个key

### 4. 查看完整请求文件

如果设置了 `DEBUG_LLM_REQUEST=1`，会生成JSON文件：

```bash
# 查看文件
cat debug_llm_request_1234567890.json

# 或用编辑器打开
code debug_llm_request_1234567890.json
```

检查JSON内容：
- `messages`: 对话历史
- `functions`: 工具列表
- `model`: 使用的模型
- `temperature`: 温度参数

### 5. 常见问题排查

#### 问题1: Payload太大

**症状**: Payload > 100KB

**解决**:
```python
# 在 agent.py 中减少历史消息
MAX_HISTORY_ROUNDS = 5  # 改为 3
```

#### 问题2: Functions太多

**症状**: Functions数量 > 30

**解决**:
```yaml
# 在 skill.yaml 中只保留必要工具
tools:
  - read_file
  - write_file
  - text_search
  # 注释掉不常用的工具
```

#### 问题3: 消息内容过长

**症状**: 单条消息 > 10000字符

**解决**:
- 检查工具返回的内容是否过长
- 使用工具的截断功能

#### 问题4: API配额耗尽

**症状**: 所有key都返回500

**解决**:
1. 检查阿里云账户余额
2. 查看API调用统计
3. 添加更多API Key

### 6. 使用Python调试器

```bash
# 使用pdb调试
python -m pdb daoyoucode.py chat --skill sisyphus-orchestrator

# 在关键位置设置断点
(Pdb) b daoyoucode/agents/llm/clients/unified.py:85
(Pdb) c
(Pdb) p payload
(Pdb) p len(json.dumps(payload))
```

### 7. 抓包分析（高级）

使用mitmproxy抓取HTTP请求：

```bash
# 安装mitmproxy
pip install mitmproxy

# 启动代理
mitmproxy -p 8080

# 配置环境变量
set HTTP_PROXY=http://localhost:8080
set HTTPS_PROXY=http://localhost:8080

# 运行程序
python daoyoucode.py chat
```

## 快速修复建议

### 修复1: 减少历史消息

编辑 `backend/daoyoucode/agents/core/agent.py`:

```python
# 找到这一行（约第424行）
MAX_HISTORY_ROUNDS = 5

# 改为
MAX_HISTORY_ROUNDS = 3  # 减少历史消息
```

### 修复2: 减少工具数量

编辑 `skills/sisyphus-orchestrator/skill.yaml`:

```yaml
tools:
  - repo_map
  - read_file
  - write_file
  - text_search
  # 只保留最常用的4-5个工具
```

### 修复3: 使用更小的模型

编辑 `skills/sisyphus-orchestrator/skill.yaml`:

```yaml
llm:
  model: qwen-plus  # 从 qwen-max 改为 qwen-plus
  temperature: 0.3
```

### 修复4: 禁用用户画像更新

如果不需要用户画像功能，可以临时禁用：

编辑 `backend/daoyoucode/agents/core/agent.py`:

```python
# 找到这一行（约第530行）
await self._check_and_update_profile(user_id, session_id)

# 注释掉
# await self._check_and_update_profile(user_id, session_id)
```

## 日志级别控制

### 查看更多日志

```python
# 在 daoyoucode.py 开头添加
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 只看关键日志

```python
import logging
logging.basicConfig(level=logging.INFO)
logging.getLogger('httpx').setLevel(logging.WARNING)
```

## 测试简化请求

创建测试脚本 `test_simple_request.py`:

```python
import asyncio
from daoyoucode.agents.llm import get_client_manager
from daoyoucode.agents.llm.config_loader import auto_configure
from daoyoucode.agents.llm.base import LLMRequest

async def test():
    cm = get_client_manager()
    auto_configure(cm)
    
    client = cm.get_client('qwen-plus')
    
    # 最简单的请求
    request = LLMRequest(
        prompt="你好",
        model="qwen-plus",
        temperature=0.7,
        max_tokens=100
    )
    
    print("发送简单请求...")
    response = await client.chat(request)
    print(f"响应: {response.content}")

asyncio.run(test())
```

运行：
```bash
python test_simple_request.py
```

如果简单请求成功，说明API Key没问题，是请求内容导致的500错误。

## 联系我

如果以上方法都无法解决，提供以下信息：

1. 日志输出（特别是 🔍 LLM请求调试信息 部分）
2. Payload大小
3. Functions数量
4. 消息数量
5. 使用的模型
6. 是否所有API Key都失败

这样我可以帮你精确定位问题！
