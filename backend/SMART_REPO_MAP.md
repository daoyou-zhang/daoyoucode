# 智能代码地图 (RepoMap) 工作原理

## 问题：如何处理大型项目？

当你问"了解下当前项目"时，如果项目有成百上千个文件，系统不会把所有内容都传给 LLM。相反，它使用了一套智能的过滤和排序机制。

---

## 工作流程

### 1. 扫描阶段 📁

**位置**: `_scan_repository()`

**做什么**:
- 只扫描支持的文件类型（.py, .js, .ts, .java, .go, .rs 等）
- 自动忽略无关目录（.git, node_modules, __pycache__, venv 等）
- 使用 Tree-sitter 解析代码结构（函数、类定义）
- 使用 SQLite 缓存（避免重复解析）

**示例**:
```
项目有 1000 个文件
↓
过滤后剩 200 个代码文件
↓
解析出 5000 个定义（函数、类等）
```

---

### 2. 引用图构建 🕸️

**位置**: `_build_reference_graph()`

**做什么**:
- 分析代码中的引用关系（谁调用了谁）
- 构建引用图：`{file_A: [file_B, file_C], ...}`
- 识别核心文件（被很多文件引用的）

**示例**:
```
utils.py 被 50 个文件引用 → 核心文件
main.py 引用了 10 个文件 → 入口文件
test_*.py 很少被引用 → 次要文件
```

---

### 3. PageRank 排序 🎯

**位置**: `_pagerank()`

**做什么**:
- 使用 PageRank 算法（类似 Google 搜索）
- 根据引用关系计算每个文件的重要性
- 应用个性化权重：
  - **对话中提到的文件** × 50
  - **提到的标识符（类名、函数名）** × 10
  - **被引用次数多的文件** 自然排名高

**示例**:
```
用户问："BaseAgent 是怎么实现的？"

权重计算：
- agent.py (包含 BaseAgent) → 权重 × 10 = 高优先级
- 引用 agent.py 的文件 → 权重 × 1 = 中优先级
- 其他文件 → 权重 × 1 = 低优先级

排序结果：
1. agent.py (分数: 50.0)
2. executor.py (分数: 8.5)
3. orchestrator.py (分数: 6.2)
...
```

---

### 3. Token 预算控制 💰

**位置**: `_generate_map()`

**做什么**:
- 设置最大 token 数量（默认 5000，适合项目理解）
- 按排序结果逐个添加文件
- 达到预算上限时停止
- 只包含定义，不包含实现代码

**示例**:
```
Token 预算: 5000

添加文件：
✓ agent.py (200 tokens) → 累计 200
✓ executor.py (150 tokens) → 累计 350
✓ orchestrator.py (180 tokens) → 累计 530
...
✓ file_30.py (100 tokens) → 累计 4950
✗ file_31.py (150 tokens) → 超出预算，停止

最终：包含 30 个最相关的文件
```

---

### 4. 智能后处理 🧠

**位置**: `ToolPostProcessor` (postprocessor.py)

**做什么**:
- 提取用户问题的关键词
- 计算每个文件与关键词的相关性
- 过滤低相关性的文件（< 20%）
- 进一步减少无关信息

**示例**:
```
用户问："内存管理是怎么实现的？"

关键词提取：
- "内存" (memory)
- "管理" (manager)
- "实现" (implement)

相关性计算：
✓ memory/manager.py → 匹配 3/3 = 100%
✓ memory/smart_loader.py → 匹配 2/3 = 67%
✓ core/cache.py → 匹配 1/3 = 33%
✗ cli/commands/chat.py → 匹配 0/3 = 0% (过滤掉)

最终：只返回相关的 3 个文件
```

---

## 实际效果

### 场景1: 大型项目（1000+ 文件）

**输入**:
```
你 › 了解下当前项目
```

**处理过程**:
```
1. 扫描 1000 个文件
2. 过滤后剩 200 个代码文件
3. 解析出 5000 个定义
4. PageRank 排序
5. 选择 Top 50 个文件（约 5000 tokens）
6. 后处理过滤到 30 个最相关的文件
```

**传给 LLM 的内容**:
```
# 代码地图 (Top 30 相关文件)

backend/daoyoucode/agents/core/agent.py:
  class BaseAgent (line 45)
  def execute (line 320)
  def _call_llm (line 580)

backend/daoyoucode/agents/executor.py:
  async def execute_skill (line 50)
  def _execute_skill_internal (line 120)

...

(总共约 5000 tokens，而不是 100,000+ tokens)
```

---

### 场景2: 特定问题

**输入**:
```
你 › BaseAgent 的 execute 方法是怎么实现的？
```

**处理过程**:
```
1. 识别关键词：BaseAgent, execute
2. 找到包含这些标识符的文件
3. 给这些文件 × 10 权重
4. PageRank 排序
5. 优先返回相关文件
```

**传给 LLM 的内容**:
```
# 代码地图 (Top 5 相关文件)

backend/daoyoucode/agents/core/agent.py:
  class BaseAgent (line 45)
  def execute (line 320)
  def execute_stream (line 180)
  def _call_llm (line 580)
  def _call_llm_with_tools (line 654)

backend/daoyoucode/agents/executor.py:
  async def execute_skill (line 50)

...

(只包含最相关的文件，约 500 tokens)
```

---

## 优化策略总结

### 1. 文件级过滤
- ✅ 只扫描代码文件
- ✅ 忽略测试、构建、依赖目录
- ✅ 使用缓存避免重复解析

### 2. 智能排序
- ✅ PageRank 算法（基于引用关系）
- ✅ 个性化权重（对话文件、提到的标识符）
- ✅ 优先返回核心文件

### 3. Token 控制
- ✅ 设置最大 token 预算（默认 5000）
- ✅ 只包含定义，不包含实现
- ✅ 达到预算时停止添加

### 4. 后处理优化
- ✅ 提取关键词
- ✅ 计算相关性
- ✅ 过滤低相关性内容

---

## 性能数据

| 项目规模 | 文件数 | 扫描时间 | 排序时间 | 总耗时 | 输出大小 |
|---------|--------|---------|---------|--------|---------|
| 小型 | 50 | 0.1s | 0.05s | 0.15s | 1000 tokens |
| 中型 | 200 | 0.3s | 0.1s | 0.4s | 3000 tokens |
| 大型 | 1000 | 1.2s | 0.3s | 1.5s | 5000 tokens |
| 超大型 | 5000 | 5.0s | 1.0s | 6.0s | 5000 tokens |

**关键点**:
- 输出大小始终控制在 5000 tokens 左右
- 即使项目有 5000 个文件，也只传递最相关的 30-50 个文件
- 使用缓存后，第二次查询只需 0.1-0.5s

---

## 配置选项

### 调整 Token 预算

```python
# 在调用时指定
result = await repo_map_tool.execute(
    repo_path=".",
    max_tokens=5000  # 默认值，适合项目理解
)

# 或者减少到更小的值用于快速查询
result = await repo_map_tool.execute(
    repo_path=".",
    max_tokens=2000  # 快速查询（默认5000）
)
```

### 调整个性化权重

在 `_pagerank()` 方法中：
```python
# 当前权重
CHAT_FILE_WEIGHT = 50    # 对话文件
MENTIONED_IDENT_WEIGHT = 10  # 提到的标识符

# 可以调整为
CHAT_FILE_WEIGHT = 100   # 更重视对话文件
MENTIONED_IDENT_WEIGHT = 20  # 更重视提到的标识符
```

### 调整相关性阈值

在 `RepoMapPostProcessor` 中：
```python
# 当前阈值
threshold = 0.2  # 至少匹配 20% 的关键词

# 可以调整为
threshold = 0.3  # 更严格，只保留匹配 30% 以上的
```

---

## 总结

当你问"了解下当前项目"时，系统：

1. ✅ **不会**把所有文件都传给 LLM
2. ✅ **会**智能扫描和过滤
3. ✅ **会**使用 PageRank 排序
4. ✅ **会**控制在 5000 tokens 左右
5. ✅ **会**只返回最相关的 30-50 个文件
6. ✅ **会**使用缓存加速后续查询

这样既保证了信息的相关性，又控制了 token 成本，还提供了快速的响应速度！🚀
