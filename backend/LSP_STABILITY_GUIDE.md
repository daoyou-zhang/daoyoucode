# LSP 服务稳定性指南

## 问题诊断

如果遇到 LSP 服务不稳定（一会好一会不好），可能的原因：

### 1. 超时问题
- 默认超时 15 秒可能不够
- 大型项目分析需要更长时间
- 网络或磁盘 I/O 慢

### 2. 进程死亡
- LSP 服务器进程意外退出
- 内存不足
- 文件过多导致崩溃

### 3. 并发问题
- 多个请求同时发送
- 请求队列堵塞
- 资源竞争

### 4. 环境问题
- 虚拟环境路径问题
- PATH 配置不正确
- 权限问题

## 解决方案

### 方案 1: 运行健康检查

```bash
# 激活虚拟环境
cd backend
.\venv\Scripts\activate

# 运行健康检查
python lsp_health_check.py

# 如果有问题，运行修复
python lsp_health_check.py --fix
```

### 方案 2: 应用稳定性补丁

在项目启动时应用稳定性配置：

```python
from lsp_stability_patch import apply_stability_config

# 在应用启动时调用
apply_stability_config()
```

这会：
- 增加超时时间到 30 秒
- 启用自动重试（最多 3 次）
- 改进错误恢复

### 方案 3: 使用包装器

使用稳定性包装器来自动处理重试和重启：

```python
from lsp_stability_patch import wrap_lsp_client
from daoyoucode.agents.tools.lsp_tools import get_lsp_manager, BUILTIN_LSP_SERVERS

manager = get_lsp_manager()
pyright_config = BUILTIN_LSP_SERVERS['pyright']

# 获取客户端
client = await manager.get_client(root, pyright_config)

# 包装客户端
wrapped_client = wrap_lsp_client(client, manager, root, pyright_config)

# 使用包装后的客户端（自动重试和恢复）
result = await wrapped_client.diagnostics(file_path)
```

### 方案 4: 手动配置

修改 `backend/daoyoucode/agents/tools/lsp_tools.py` 中的超时配置：

```python
# 在 LSPClient._send 方法中
async def timeout_handler():
    await asyncio.sleep(30)  # 改为 30 秒
    # ...
```

## 最佳实践

### 1. 合理使用 LSP

```python
# ❌ 不好：频繁创建和销毁客户端
for file in files:
    client = await manager.get_client(root, config)
    await client.diagnostics(file)
    manager.release_client(root, config.id)

# ✅ 好：复用客户端
client = await manager.get_client(root, config)
try:
    for file in files:
        await client.diagnostics(file)
finally:
    manager.release_client(root, config.id)
```

### 2. 控制并发

```python
# ❌ 不好：无限制并发
tasks = [client.diagnostics(f) for f in files]
await asyncio.gather(*tasks)

# ✅ 好：限制并发数
from asyncio import Semaphore

sem = Semaphore(5)  # 最多 5 个并发请求

async def process_file(file):
    async with sem:
        return await client.diagnostics(file)

tasks = [process_file(f) for f in files]
results = await asyncio.gather(*tasks)
```

### 3. 错误处理

```python
# ✅ 好：总是处理异常
try:
    result = await client.diagnostics(file_path)
except TimeoutError:
    logger.warning(f"LSP 请求超时: {file_path}")
    # 降级处理或重试
except RuntimeError as e:
    if "not running" in str(e):
        logger.error("LSP 服务器已停止")
        # 重启服务器
    else:
        raise
```

### 4. 定期清理

```python
# 在长时间运行的应用中
import asyncio

async def cleanup_task():
    while True:
        await asyncio.sleep(600)  # 每 10 分钟
        await manager._cleanup_idle_clients()

# 启动清理任务
asyncio.create_task(cleanup_task())
```

## 性能优化

### 1. 减少诊断等待时间

```python
# 默认等待 2 秒
diagnostics = await client.diagnostics(file_path, wait_time=2.0)

# 如果文件小或已缓存，可以减少等待时间
diagnostics = await client.diagnostics(file_path, wait_time=1.0)
```

### 2. 批量处理

```python
# 一次性打开多个文件
for file in files:
    await client.open_file(file)

# 然后批量获取诊断
results = {}
for file in files:
    results[file] = await client.diagnostics(file, wait_time=0.5)
```

### 3. 使用缓存

```python
# LSP 客户端会缓存诊断信息
# 第一次调用会等待分析
diagnostics1 = await client.diagnostics(file_path, wait_time=2.0)

# 后续调用可以直接使用缓存
diagnostics2 = await client.diagnostics(file_path, wait_time=0.1)
```

## 故障排查

### 问题：LSP 服务器启动失败

```bash
# 检查安装
python -c "from daoyoucode.agents.tools.lsp_tools import BUILTIN_LSP_SERVERS, LSPClient; client = LSPClient('.', BUILTIN_LSP_SERVERS['pyright']); print(client.is_server_installed())"

# 检查命令
.\venv\Scripts\pyright-langserver.exe --stdio
```

### 问题：请求总是超时

```python
# 增加超时时间
from lsp_stability_patch import LSP_STABILITY_CONFIG
LSP_STABILITY_CONFIG["request_timeout"] = 60  # 60 秒
```

### 问题：内存占用过高

```python
# 限制打开的文件数
if len(client.opened_files) > 50:
    # 清理一些文件
    await client.stop()
    client = await manager.get_client(root, config)
```

### 问题：进程频繁死亡

```bash
# 检查 stderr 日志
python -c "
from daoyoucode.agents.tools.lsp_tools import get_lsp_manager, BUILTIN_LSP_SERVERS
import asyncio

async def check():
    manager = get_lsp_manager()
    config = BUILTIN_LSP_SERVERS['pyright']
    client = await manager.get_client('.', config)
    print('stderr:', client.stderr_buffer)

asyncio.run(check())
"
```

## 监控和日志

### 启用详细日志

```python
import logging

# 设置 LSP 工具日志级别
logging.getLogger('daoyoucode.agents.tools.lsp_tools').setLevel(logging.DEBUG)

# 查看所有 LSP 请求和响应
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
logging.getLogger('daoyoucode.agents.tools.lsp_tools').addHandler(handler)
```

### 监控客户端状态

```python
# 定期检查客户端状态
def print_client_status(client):
    print(f"进程存活: {client.is_alive()}")
    print(f"已打开文件: {len(client.opened_files)}")
    print(f"待处理请求: {len(client.pending_requests)}")
    print(f"诊断缓存: {len(client.diagnostics_store)}")
    print(f"stderr 缓冲: {len(client.stderr_buffer)} 行")
```

## 总结

LSP 服务稳定性的关键：

1. ✅ 使用健康检查工具定期检测
2. ✅ 应用稳定性补丁（重试 + 超时）
3. ✅ 合理复用客户端，避免频繁创建
4. ✅ 控制并发请求数量
5. ✅ 处理所有异常情况
6. ✅ 定期清理空闲资源
7. ✅ 启用日志监控

如果问题持续，请运行：
```bash
python lsp_health_check.py --fix
```
