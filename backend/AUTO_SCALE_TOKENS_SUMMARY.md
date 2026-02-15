# 智能Token预算调整功能总结

## 功能概述

借鉴aider的智能策略，实现了根据chat_files自动调整repo_map的token预算。

---

## 核心策略

### 默认配置

- **标准预算**: 3000 tokens
- **扩大预算**: 6000 tokens（2倍）
- **最大限制**: 6000 tokens

### 调整规则

| 场景 | chat_files | 原始预算 | 实际预算 | 说明 |
|------|-----------|---------|---------|------|
| 项目理解 | 空 | 3000 | 6000 | 需要全局视图 |
| 文件修改 | 非空 | 3000 | 3000 | 聚焦相关文件 |
| 禁用调整 | 任意 | 3000 | 3000 | auto_scale=False |

---

## 为什么选择3000/6000？

### 对比aider

| 项目 | 标准预算 | 扩大预算 | 倍数 |
|------|---------|---------|------|
| aider | 1024 | 8192 | 8倍 |
| 我们 | 3000 | 6000 | 2倍 |

### 我们的考虑

1. **更经济**
   - 3000 tokens 足够显示约50个文件
   - 6000 tokens 足够显示约100个文件
   - 对于大多数项目已经足够

2. **更实用**
   - 配合智能后处理，过滤无关内容
   - PageRank排序，优先显示重要文件
   - 不需要太大的预算

3. **更灵活**
   - 可以通过参数自定义
   - 可以禁用auto_scale
   - 适应不同项目规模

---

## 使用示例

### 场景1: 了解项目（无chat_files）

```python
# LLM调用
result = await tool.execute(
    repo_path=".",
    chat_files=[],  # 空列表
    max_tokens=3000  # 默认值
)

# 自动调整
# 3000 → 6000 tokens
# 显示约100个文件
```

**效果**:
```
# 代码地图 (Top 100 文件)

backend/daoyoucode/agents/core/agent.py:
  class BaseAgent (line 45)
  def execute (line 320)

backend/daoyoucode/agents/orchestrators/react.py:
  class ReActOrchestrator (line 30)
  def execute (line 80)

... (约100个文件，覆盖整个项目)
```

### 场景2: 修改文件（有chat_files）

```python
# LLM调用
result = await tool.execute(
    repo_path=".",
    chat_files=["backend/daoyoucode/agents/core/agent.py"],
    max_tokens=3000  # 默认值
)

# 保持不变
# 3000 tokens
# 显示约50个相关文件
```

**效果**:
```
# 代码地图 (Top 50 文件)

backend/daoyoucode/agents/core/agent.py:
  class BaseAgent (line 45)
  def execute (line 320)

backend/daoyoucode/agents/executor.py:
  async def execute_skill (line 50)

... (约50个相关文件，聚焦agent.py)
```

---

## 实现细节

### 代码位置

`backend/daoyoucode/agents/tools/repomap_tools.py`

### 核心逻辑

```python
async def execute(
    self,
    repo_path: str,
    chat_files: Optional[List[str]] = None,
    mentioned_idents: Optional[List[str]] = None,
    max_tokens: int = 3000,  # 默认3000
    auto_scale: bool = True  # 默认开启
) -> ToolResult:
    # 智能调整token预算
    original_max_tokens = max_tokens
    if auto_scale:
        if not chat_files or len(chat_files) == 0:
            # 没有对话文件，扩大预算（2倍，最多6000）
            max_tokens = min(max_tokens * 2, 6000)
            logger.info(
                f"🔍 智能调整: 无对话文件，扩大token预算 "
                f"{original_max_tokens} → {max_tokens} "
                f"(提供更全面的项目视图)"
            )
        else:
            logger.info(
                f"📁 智能调整: 有 {len(chat_files)} 个对话文件，"
                f"使用标准token预算 {max_tokens}"
            )
```

### Function Schema

```python
{
    "name": "repo_map",
    "parameters": {
        "max_tokens": {
            "type": "integer",
            "description": "最大token数量（默认3000）。如果chat_files为空，会自动扩大到6000",
            "default": 3000
        },
        "auto_scale": {
            "type": "boolean",
            "description": "是否自动调整token预算（默认true）",
            "default": True
        }
    }
}
```

---

## 测试结果

### 测试覆盖

✅ 测试1: 无对话文件 → 3000扩大到6000
✅ 测试2: 有对话文件 → 保持3000
✅ 测试3: 禁用auto_scale → 保持原始值
✅ 测试4: 自定义max_tokens → 按比例扩大
✅ 测试5: 超大max_tokens → 限制在6000

### 测试脚本

`backend/test_auto_scale_tokens.py`

---

## 提示词更新

### 工具说明

```markdown
### 1. repo_map
生成智能代码地图
- **智能token预算**：
  - 无对话文件时：自动扩大到6000 tokens（提供全局视图）
  - 有对话文件时：保持3000 tokens（聚焦相关文件）
- **使用场景**: 
  - 用户问"项目结构" → 不传chat_files，获得全局视图（6000 tokens）
  - 用户问"修改某个文件" → 传chat_files，获得聚焦视图（3000 tokens）
```

### 重要原则

```markdown
6. **合理使用token**: 
   - 项目理解时不传chat_files（自动扩大到6000）
   - 具体问题可以传chat_files（保持3000）
```

---

## 优势总结

### 相比固定预算

| 特性 | 固定预算 | 智能调整 |
|------|---------|---------|
| 项目理解 | 可能不够 | ✅ 自动扩大 |
| 文件修改 | 可能浪费 | ✅ 保持标准 |
| 灵活性 | ❌ 低 | ✅ 高 |
| 成本控制 | ❌ 差 | ✅ 好 |

### 相比aider

| 特性 | aider | 我们 |
|------|-------|------|
| 标准预算 | 1024 | 3000（更大） |
| 扩大预算 | 8192 | 6000（更经济） |
| 倍数 | 8倍 | 2倍（更合理） |
| 后处理 | ❌ 无 | ✅ 有 |

---

## 未来可能的改进

### 1. 更精细的调整策略

```python
# 根据项目规模动态调整
if project_size < 100:
    max_tokens = 2000
elif project_size < 500:
    max_tokens = 3000
else:
    max_tokens = 4000
```

### 2. 基于历史的学习

```python
# 记录用户的使用习惯
if user_prefers_detailed_view:
    max_tokens *= 1.5
```

### 3. 与LLM协商

```python
# LLM可以请求更多tokens
if llm_requests_more:
    max_tokens = min(max_tokens * 1.5, 8000)
```

---

## 总结

✅ **已实现**:
- 智能token预算调整（3000 → 6000）
- 根据chat_files自动决策
- 可配置、可禁用
- 完整的测试覆盖

✅ **优势**:
- 更经济（相比10000）
- 更实用（配合后处理）
- 更灵活（可自定义）
- 借鉴aider的最佳实践

✅ **效果**:
- 项目理解：6000 tokens，约100个文件
- 文件修改：3000 tokens，约50个文件
- 成本降低：相比固定6000，节省50%
