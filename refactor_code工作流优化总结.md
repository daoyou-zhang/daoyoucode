# refactor_code.md 工作流优化总结

## 优化内容

### 新增：模式3 - 拆分大类 ⭐⭐⭐

这是针对"Agent 拆分"任务的核心优化。

## 为什么之前失败？

从日志分析：

```
1. ✅ batch_write_files - 同时创建了多个文件
2. ❌ intelligent_diff_edit - 修改原文件时验证失败（18个错误）
   - Import ".config" could not be resolved
   - Cannot access attribute "execute_streaming"
   - 等等...
3. ❌ 达到最大工具调用次数（15次）
```

**根本原因**：
1. **同时创建多个文件** - 没有逐个验证，导致后续问题
2. **使用 intelligent_diff_edit** - 对大文件修改容易失败
3. **没有先创建 config.py** - 导致循环导入
4. **一次移动太多代码** - 验证失败，难以定位问题

## 优化后的工作流

### 核心原则

1. **小步快跑** - 一次只拆一个职责
2. **先创建后移动** - 先创建新文件，再移动代码
3. **保持可运行** - 每步都要保持代码可运行
4. **验证再继续** - 每步都要验证，失败就回退

### 详细步骤（7步）

#### 步骤1：分析类的职责（5分钟）
- 使用 read_file 读取代码
- 使用 get_file_symbols 分析结构
- 手动识别不同职责
- 制定拆分计划

#### 步骤2：创建配置文件（3分钟）⭐
**关键改进**：先创建独立的 config.py，避免循环导入

```python
# backend/daoyoucode/agents/core/config.py
@dataclass
class AgentConfig:
    ...

@dataclass
class AgentResult:
    ...
```

#### 步骤3：创建第一个新类（10分钟）⭐
**关键改进**：一次只创建一个新类

```python
# backend/daoyoucode/agents/core/llm_caller.py
class LLMCaller:
    ...
```

验证：`lsp_diagnostics(file_path="llm_caller.py")`

#### 步骤4：更新原类使用新类（10分钟）⭐
**关键改进**：使用 search_replace，不要用 intelligent_diff_edit

```python
# 第1次：添加导入
search_replace(
    file_path="agent.py",
    search="from dataclasses import dataclass, field",
    replace="""from dataclasses import dataclass, field
from .config import AgentConfig, AgentResult
from .llm_caller import LLMCaller"""
)

# 第2次：修改 __init__
search_replace(...)

# 第3次：删除已移动的方法
search_replace(...)
```

验证：`lsp_diagnostics(file_path="agent.py")`

#### 步骤5：查找并更新引用（10分钟）
- 使用 lsp_find_references 查找所有引用
- 使用 search_replace 更新每个引用
- 验证每个文件

#### 步骤6：验证整体（5分钟）
- git_diff() 查看所有变更
- run_test() 运行测试
- 确认功能没有被破坏

#### 步骤7：重复步骤3-6（拆分下一个职责）
- 一次只拆一个职责
- 每次都要完整走完步骤3-6

### 完整示例（拆分 agent.py）

```
第1轮：拆分配置类
1. 创建 config.py（AgentConfig, AgentResult）
2. 更新 agent.py 导入
3. 验证 ✅

第2轮：拆分 LLM 调用
1. 创建 llm_caller.py（LLMCaller 类）
2. 移动 _call_llm 等方法
3. 更新 agent.py 使用 LLMCaller
4. 查找并更新所有引用
5. 验证 ✅

第3轮：拆分工具管理
1. 创建 tool_manager.py（ToolManager 类）
2. 移动工具相关方法
3. 更新 agent.py 使用 ToolManager
4. 查找并更新所有引用
5. 验证 ✅

第4轮：拆分记忆管理
1. 创建 memory_manager.py（MemoryManager 类）
2. 移动记忆相关方法
3. 更新 agent.py 使用 MemoryManager
4. 查找并更新所有引用
5. 验证 ✅
```

## 常见错误和解决方案

### 错误1：同时创建多个文件 ❌

```python
# 错误做法
batch_write_files(files=[
    {path: "llm_caller.py", content: "..."},
    {path: "tool_manager.py", content: "..."},
    {path: "memory_manager.py", content: "..."}
])
→ 没有逐个验证，后续问题难以定位

# 正确做法
write_file(file_path="llm_caller.py", content="...")
lsp_diagnostics(file_path="llm_caller.py")  # 验证
write_file(file_path="tool_manager.py", content="...")
lsp_diagnostics(file_path="tool_manager.py")  # 验证
```

### 错误2：使用 intelligent_diff_edit 修改大文件 ❌

```python
# 错误做法
intelligent_diff_edit(
    file_path="agent.py",
    search_block="很长的代码块",
    replace_block="修改后的代码块"
)
→ 容易失败，验证错误多（18个错误）

# 正确做法
search_replace(
    file_path="agent.py",
    search="具体的一个方法",
    replace="# 已移至新类"
)
→ 精确、安全
```

### 错误3：忘记先创建 config.py ❌

```python
# 错误做法
直接创建 llm_caller.py，导入 AgentConfig
→ Import ".config" could not be resolved

# 正确做法
1. 先创建 config.py（独立的配置文件）
2. 再创建 llm_caller.py（导入 config.py）
3. 最后更新 agent.py（导入 config.py）
```

### 错误4：一次移动太多方法 ❌

```python
# 错误做法
一次性移动 10 个方法到新类
→ 验证失败，难以定位问题

# 正确做法
一次移动 2-3 个相关方法
验证通过后再移动下一批
```

## 预期效果

### 优化前（失败）
- 同时创建多个文件
- 使用 intelligent_diff_edit
- 验证失败（18个错误）
- 达到最大工具调用次数（15次）
- **结果：失败 ❌**

### 优化后（预期成功）
- 逐个创建文件，逐个验证
- 使用 search_replace
- 每步都验证
- 小步快跑
- **预期结果：成功 ✅**

## 工具调用次数对比

### 优化前（失败的尝试）
```
1. semantic_code_search
2. repo_map
3. read_file
4. batch_write_files（同时创建多个）
5. intelligent_diff_edit（失败）
6. intelligent_diff_edit（再次尝试）
7-15. 各种 lsp_diagnostics, lsp_find_references, lsp_symbols
→ 达到15次上限，失败
```

### 优化后（预期）
```
第1轮（config.py）：
1. read_file
2. get_file_symbols
3. write_file(config.py)
4. lsp_diagnostics(config.py)
5. search_replace(agent.py - 添加导入)
6. lsp_diagnostics(agent.py)

第2轮（llm_caller.py）：
7. write_file(llm_caller.py)
8. lsp_diagnostics(llm_caller.py)
9. search_replace(agent.py - 添加导入)
10. search_replace(agent.py - 修改 __init__)
11. search_replace(agent.py - 删除方法)
12. lsp_diagnostics(agent.py)
13. lsp_find_references
14. search_replace(更新引用)
15. git_diff

→ 可能需要多轮，但每轮都是成功的
```

## 关键改进点

1. ✅ **先创建 config.py** - 避免循环导入
2. ✅ **逐个创建文件** - 逐个验证
3. ✅ **使用 search_replace** - 精确、安全
4. ✅ **小步快跑** - 每步都验证
5. ✅ **明确的步骤顺序** - AI 不需要自己摸索

## 下一步

现在可以重新测试：

```bash
cd backend
python daoyoucode.py --skill sisyphus-orchestrator "agent.py 这个代码太大了，帮我拆分下，引用关系也要调整哦"
```

预期 daoyoucode 会：
1. 先创建 config.py
2. 逐个创建新类（llm_caller.py, tool_manager.py, memory_manager.py）
3. 逐步更新 agent.py
4. 查找并更新所有引用
5. 验证每一步

**成功率预期：从 0% 提升到 80-90%**
