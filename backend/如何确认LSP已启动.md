# 如何确认LSP已启动

## 方法1: 运行验证脚本（推荐）

```bash
cd backend
python verify_lsp_running.py
```

### 预期输出

```
LSP启动验证工具

============================================================
验证LSP是否真正启动
============================================================

[1] 检查pyright安装状态...
    pyright: ✅ 已安装

[2] 启动LSP客户端...
    ✅ LSP客户端已创建

[3] 检查LSP进程...
    进程ID: 14240          ← 有进程ID说明LSP真正启动了
    返回码: None           ← None说明进程还在运行
    存活: True             ← True说明进程存活

[4] 测试LSP功能...
    测试文件: executor.py
    ✅ LSP功能正常
    符号数量: 9            ← 成功获取到符号

    前3个符号:
      1. logger (kind: 13)
      2. execute_skill (kind: 12)
      3. _execute_skill_internal (kind: 12)

[5] LSP管理器状态...
    活跃客户端: 1
    - D:\daoyouspace\daoyoucode\backend::pyright
      引用计数: 1
      存活: True

============================================================
✅ LSP已真正启动并正常工作！
============================================================
```

### 关键指标

1. **进程ID存在** - 说明LSP服务器进程真正启动
2. **返回码为None** - 说明进程还在运行（不是已退出）
3. **存活状态True** - 进程健康运行
4. **符号数量>0** - LSP功能正常工作

## 方法2: 检查进程

### Windows

```powershell
# 查找pyright进程
tasklist | findstr pyright

# 或者
Get-Process | Where-Object {$_.ProcessName -like "*pyright*"}
```

### Linux/Mac

```bash
# 查找pyright进程
ps aux | grep pyright

# 或者
pgrep -f pyright
```

### 预期输出

```
pyright-langserver  14240  ...  # 有进程说明LSP已启动
```

## 方法3: 在代码中检查

```python
from daoyoucode.agents.tools.lsp_tools import get_lsp_manager

manager = get_lsp_manager()

# 检查活跃客户端
print(f"活跃客户端数: {len(manager.clients)}")

for key, managed in manager.clients.items():
    client = managed['client']
    print(f"客户端: {key}")
    print(f"  进程ID: {client.process.pid if client.process else 'N/A'}")
    print(f"  存活: {client.is_alive()}")
    print(f"  引用计数: {managed['ref_count']}")
```

### 预期输出

```
活跃客户端数: 1
客户端: D:\daoyouspace\daoyoucode\backend::pyright
  进程ID: 14240
  存活: True
  引用计数: 1
```

## 方法4: 查看日志

LSP启动时会有日志输出：

```
开始初始化Agent系统...
✓ 工具注册表已初始化: 30 个工具
✓ 内置Agent已注册
✓ 编排器已注册: 3 个
✓ 中间件已注册
✓ LSP系统已就绪（pyright已安装）
  提示: LSP将在首次使用时自动启动    ← 这里说明LSP就绪
Agent系统初始化完成
```

首次使用semantic_code_search时：

```
🔍 LSP增强检索: 16 个候选
[LSP] 启动LSP客户端...              ← 这里说明LSP正在启动
[LSP] LSP客户端已启动
[LSP] 进程ID: 14240
```

## 方法5: 测试LSP功能

```python
import asyncio
from daoyoucode.agents.tools.codebase_search_tool import SemanticCodeSearchTool

async def test():
    tool = SemanticCodeSearchTool()
    
    result = await tool.execute(
        query="execute_skill",
        top_k=3,
        enable_lsp=True
    )
    
    # 检查是否有LSP信息
    has_lsp = result.metadata.get('has_lsp_info', False)
    print(f"LSP信息: {'✅ 有' if has_lsp else '❌ 无'}")
    
    # 检查输出中是否有LSP标记
    if result.content:
        markers = ["⭐", "✅ 有类型注解", "🔥 热点代码", "📝 符号信息"]
        found = [m for m in markers if m in result.content]
        if found:
            print(f"发现LSP标记: {', '.join(found)}")

asyncio.run(test())
```

## 常见问题

### Q1: 验证脚本显示"LSP未启动"

**原因**:
1. pyright未安装
2. 启动失败（权限问题、路径问题）
3. 代码bug

**解决**:
```bash
# 1. 确认pyright已安装
pip install pyright

# 2. 测试pyright命令
pyright --version

# 3. 查看详细错误
python verify_lsp_running.py  # 查看完整错误信息
```

### Q2: LSP启动了但搜索没有LSP信息

**原因**:
1. LSP获取信息失败
2. 文件不在LSP支持范围
3. LSP缓存问题

**解决**:
```python
# 清除LSP缓存
from daoyoucode.agents.memory.codebase_index_lsp_enhanced import LSPEnhancedCodebaseIndex

index = LSPEnhancedCodebaseIndex(repo_path)
index._lsp_cache.clear()  # 清除缓存
```

### Q3: LSP进程存在但不响应

**原因**:
1. LSP服务器卡住
2. 文件太大
3. 超时

**解决**:
```python
# 重启LSP服务器
from daoyoucode.agents.tools.lsp_tools import get_lsp_manager

manager = get_lsp_manager()
await manager.stop_all()  # 停止所有LSP服务器

# 下次使用时会自动重启
```

## 总结

### LSP已启动的标志

1. ✅ 验证脚本显示"LSP已真正启动并正常工作"
2. ✅ 进程列表中有pyright进程
3. ✅ manager.clients不为空
4. ✅ client.is_alive()返回True
5. ✅ 能成功获取符号信息

### LSP未启动的标志

1. ❌ 验证脚本显示"LSP未启动"
2. ❌ 进程列表中没有pyright进程
3. ❌ manager.clients为空
4. ❌ client.is_alive()返回False
5. ❌ 获取符号信息失败

### 当前状态（2026-02-19）

根据验证脚本输出：

```
[3] 检查LSP进程...
    进程ID: 14240
    返回码: None
    存活: True

[4] 测试LSP功能...
    ✅ LSP功能正常
    符号数量: 9
```

**结论**: ✅ LSP已真正启动并正常工作！

进程ID 14240，存活状态True，成功获取到9个符号。LSP服务器正在运行并响应请求。
