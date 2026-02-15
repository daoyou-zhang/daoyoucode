# 结构化代码理解策略

## 问题场景

```
用户: "看看目前代码，针对llm超时报错，有什么优化建议？"

AI 当前行为：
→ text_search("timeout")
→ read_file("timeout_recovery.py")
→ read_file("timeout_handler.py")
→ 给出建议

问题：
1. 不理解超时在整个 LLM 调用流程中的位置
2. 可能遗漏其他相关模块
3. 建议可能不全面
```

---

## 核心洞察

### 洞察1: 应该先理解流程

**问题**：直接看具体实现 → 缺乏上下文 → 建议不全面

**正确做法**：
1. 先理解整体流程（LLM 调用从哪里开始？经过哪些模块？）
2. 定位超时发生的位置
3. 查看超时处理的实现
4. 基于完整理解给出建议

### 洞察2: 应该用结构化工具

**问题**：直接 `read_file` → 只看到代码，看不到结构和关系

**正确做法**：
- 用 `repo_map`（Tree-sitter）→ 获取代码结构、函数关系、调用链
- 用 `get_repo_structure` → 查看目录组织
- 用 `ast_grep_search` → 搜索特定模式（如所有 async 函数）

---

## 解决方案

### 在 Prompt 中添加"分层理解"策略

```markdown
## 执行流程：分步思考模式

### 核心原则：先理解流程，再看具体实现

第1步：理解整体流程（使用结构化工具）
- 理解用户意图
- 确定需要理解的流程
- 使用结构化工具获取概览：
  * repo_map - 获取代码结构和关系（Tree-sitter）
  * get_repo_structure - 查看目录组织
  * ast_grep_search - 搜索特定模式
- 理解：从哪里开始？经过哪些模块？

第2步：定位关键代码（基于流程理解）
- 确定需要深入的模块
- 读取具体实现

第3步：分析与建议（基于完整理解）
- 分析现有实现
- 给出具体建议
```

---

## 对比

### 改进前（直接看实现）

```
用户: "LLM超时报错的优化建议"

AI:
→ text_search("timeout")
→ read_file("timeout_recovery.py")
→ read_file("timeout_handler.py")
→ 给建议

结果：
- 只看到超时恢复的实现
- 不知道超时在整个流程中的位置
- 可能遗漏其他相关模块（如 llm_client）
- 建议不全面
```

### 改进后（先理解流程）

```
用户: "LLM超时报错的优化建议"

AI 第1步 - 理解 LLM 调用流程：
→ repo_map(repo_path=".", mentioned_idents=["llm", "call", "timeout"])
  或
→ get_repo_structure(repo_path=".", annotate=True)

理解：
- LLM 调用入口：agents/llm/
- 调用链：executor → agent → llm_client → http_client
- 超时可能发生在：
  * llm_client.chat() - 请求超时
  * agent.execute() - 整体超时
  * executor.execute_skill() - 任务超时

AI 第2步 - 查看超时处理：
→ read_file("agents/llm/clients/unified.py")  # 看请求超时
→ read_file("agents/core/timeout_recovery.py")  # 看恢复策略
→ read_file("agents/core/timeout_handler.py")  # 看集成方式

AI 第3步 - 给出建议：
基于完整的流程理解：
1. 请求层优化：调整 httpx 超时配置
2. 恢复层优化：改进重试策略
3. 任务层优化：添加任务级别超时控制
4. 监控优化：添加超时指标收集
```

---

## 工具选择指南

### 1. repo_map（推荐用于理解代码结构）

**优势**：
- Tree-sitter 解析，理解代码结构
- PageRank 算法智能排序
- 显示函数关系和调用链
- 支持 mentioned_idents（关注特定标识符）

**使用场景**：
- 理解模块之间的关系
- 查找特定功能的实现位置
- 理解调用链

**示例**：
```python
repo_map(
    repo_path=".",
    mentioned_idents=["llm", "call", "timeout"],
    max_tokens=6000
)
```

### 2. get_repo_structure（推荐用于查看目录组织）

**优势**：
- 快速了解项目布局
- 支持注释（annotate=True）
- 轻量级（~1000 tokens）

**使用场景**：
- 了解项目整体结构
- 查找特定模块的位置
- 理解目录组织

**示例**：
```python
get_repo_structure(
    repo_path=".",
    max_depth=3,
    annotate=True
)
```

### 3. ast_grep_search（推荐用于搜索特定模式）

**优势**：
- AST 级别精确搜索
- 支持元变量（$VAR）
- 支持 25 种语言

**使用场景**：
- 搜索所有 async 函数
- 搜索特定模式的代码
- 重构前的影响分析

**示例**：
```python
ast_grep_search(
    pattern="async def $FUNC($$):",
    lang="python",
    path="agents/"
)
```

### 4. text_search（用于快速关键词搜索）

**优势**：
- 快速
- 支持正则

**使用场景**：
- 搜索特定关键词
- 查找错误消息
- 快速定位

### 5. read_file（用于读取具体实现）

**使用场景**：
- 已知文件位置
- 需要查看完整代码
- 理解具体实现

---

## 决策树

```
用户问题
    ↓
需要理解流程/架构？
    ├─ 是 → repo_map 或 get_repo_structure
    │         ↓
    │      理解流程后，需要看具体实现？
    │         ├─ 是 → read_file
    │         └─ 否 → 基于结构给出建议
    │
    └─ 否 → 已知文件位置？
              ├─ 是 → read_file
              └─ 否 → text_search 或 list_files
```

---

## 实际案例

### 案例1: LLM 超时优化

```
用户: "LLM超时报错的优化建议"

步骤1: 理解 LLM 调用流程
→ repo_map(mentioned_idents=["llm", "call"])
→ 发现：executor → agent → llm_client → http_client

步骤2: 查看各层超时处理
→ read_file("agents/llm/clients/unified.py")  # 请求层
→ read_file("agents/core/timeout_recovery.py")  # 恢复层
→ read_file("agents/core/timeout_handler.py")  # 集成层

步骤3: 给出全面建议
- 请求层：调整 httpx 超时
- 恢复层：改进重试策略
- 集成层：添加任务级超时
- 监控层：添加指标收集
```

### 案例2: 理解 Agent 执行流程

```
用户: "Agent 是怎么执行的？"

步骤1: 查看整体结构
→ get_repo_structure(repo_path="agents", annotate=True)
→ 发现：core/agent.py, orchestrators/, tools/

步骤2: 理解调用关系
→ repo_map(mentioned_idents=["agent", "execute"])
→ 发现：executor → orchestrator → agent → tools

步骤3: 查看具体实现
→ read_file("agents/core/agent.py")
→ read_file("agents/orchestrators/react.py")
```

### 案例3: 查找所有 async 函数

```
用户: "项目中有哪些 async 函数？"

步骤1: AST 搜索
→ ast_grep_search(
    pattern="async def $FUNC($$):",
    lang="python",
    path="."
)

步骤2: 分析结果
→ 列出所有 async 函数
→ 按模块分类
```

---

## 总结

### 核心原则

1. **先理解流程，再看实现**
   - 不要直接跳到具体代码
   - 先用结构化工具理解整体

2. **使用正确的工具**
   - 理解结构 → repo_map, get_repo_structure
   - 搜索模式 → ast_grep_search
   - 快速搜索 → text_search
   - 读取代码 → read_file

3. **分层理解**
   - 第1层：整体流程
   - 第2层：关键模块
   - 第3层：具体实现

### 预期效果

- ✅ 更全面的理解
- ✅ 更准确的建议
- ✅ 不遗漏相关模块
- ✅ 更好的用户体验

### 实施位置

**文件**: `skills/chat-assistant/prompts/chat_assistant.md`

**修改内容**:
- 更新"执行流程"部分
- 添加"工具选择指南"
- 添加具体示例
