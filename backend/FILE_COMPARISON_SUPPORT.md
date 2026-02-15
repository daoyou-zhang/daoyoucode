# 文件对比功能支持

## 用户需求

用户问："chat_assistant_v2.md和chat_assistant.md有俩，哪个有用？"

这是要求**对比两个文档文件**，判断哪个更有用。

## 当前状态

### 已有功能 ✅

1. **类型5: 对比分析**
   - 关键词：XX和YY的区别、对比XX和YY、比较
   - 策略：定位→读取→对比
   - 工具：repo_map + read_file

2. **工具支持**
   - `list_files`: 列出文件
   - `read_file`: 读取文件内容
   - 可以读取多个文件

### 缺少的内容 ❌

1. **文件对比的明确示例**
   - 当前示例只有代码对比（Simple vs ReAct编排器）
   - 没有文档文件对比的示例

2. **关键词不够全面**
   - 缺少"哪个有用"、"选哪个"等关键词

## 已实施的改进

### 1. 更新类型5定义

```markdown
#### 类型5: 对比分析
**关键词**: XX和YY的区别、对比XX和YY、比较、哪个有用、选哪个
**策略**: 定位→读取→对比
**工具**:
- 对比代码: repo_map(mentioned_idents=[XX, YY]) → read_file
- 对比文件: list_files → read_file (读取两者) → 对比内容
**总成本**: ~3000 tokens
```

### 2. 添加文件对比示例

```markdown
### 示例3: 对比两个文件 ⭐ 新增

**用户**: "chat_assistant_v2.md和chat_assistant.md有俩，哪个有用？"

**Thought**: 这是对比文件，需要先找到文件，然后读取对比

**Action 1**: list_files(directory="skills/chat-assistant/prompts", pattern="chat_assistant*.md")

**Observation**:
```json
[
  {
    "path": "skills/chat-assistant/prompts/chat_assistant.md",
    "name": "chat_assistant.md",
    "size": 9554
  },
  {
    "path": "skills/chat-assistant/prompts/chat_assistant_v2.md",
    "name": "chat_assistant_v2.md",
    "size": 8839
  },
  {
    "path": "skills/chat-assistant/prompts/chat_assistant_optimized.md",
    "name": "chat_assistant_optimized.md",
    "size": 13067
  }
]
```

**Thought**: 找到了3个文件，现在读取前两个对比内容

**Action 2**: read_file(file_path="skills/chat-assistant/prompts/chat_assistant.md")

**Observation**: [chat_assistant.md 的内容]

**Action 3**: read_file(file_path="skills/chat-assistant/prompts/chat_assistant_v2.md")

**Observation**: [chat_assistant_v2.md 的内容]

**Thought**: 已读取两个文件，现在对比它们的内容和用途

**Answer**: 
这两个文件都是chat_assistant的提示词，但有不同的版本：

1. **chat_assistant.md** (9554字节)
   - 当前使用的版本
   - 包含完整的工具选择决策树
   - 有详细的示例和说明

2. **chat_assistant_v2.md** (8839字节)
   - 实验性版本
   - 更简洁的结构
   - 强调成本优化

3. **chat_assistant_optimized.md** (13067字节) ⭐ 推荐
   - 最新优化版本
   - 包含7种问题类型决策树
   - 添加了编程最佳实践和代码规范
   - 预期成本降低85%

**建议**: 使用 `chat_assistant_optimized.md`，它是最完整和优化的版本。

**成本**: ~2500 tokens（list_files + 2个read_file）
```

## 工作流程

### 对比文件的标准流程

```
1. 识别问题类型
   关键词：对比、比较、哪个有用、选哪个、区别

2. 列出文件
   list_files(directory="...", pattern="...")
   
3. 读取文件
   read_file(file_path=文件1的path)
   read_file(file_path=文件2的path)
   
4. 对比分析
   - 比较文件大小
   - 比较内容结构
   - 比较功能特性
   - 给出建议

5. 回答用户
   - 说明每个文件的特点
   - 指出主要区别
   - 给出使用建议
```

## 关键点

### 1. 使用 path 字段 ⭐ 重要

```python
# list_files 返回
files = [
    {"path": "skills/chat-assistant/prompts/chat_assistant.md", "name": "chat_assistant.md"},
    {"path": "skills/chat-assistant/prompts/chat_assistant_v2.md", "name": "chat_assistant_v2.md"}
]

# 读取文件 - 使用 path
read_file(file_path=files[0]["path"])  # ✅ 正确
read_file(file_path="skills/chat-assistant/prompts/chat_assistant.md")  # ✅ 正确

# 不要只用 name
read_file(file_path=files[0]["name"])  # ❌ 错误
read_file(file_path="chat_assistant.md")  # ❌ 错误
```

### 2. 对比维度

对比文件时，应该从多个维度分析：

1. **基本信息**
   - 文件大小
   - 文件名
   - 位置

2. **内容结构**
   - 章节组织
   - 详细程度
   - 示例数量

3. **功能特性**
   - 包含哪些功能
   - 优化点
   - 适用场景

4. **使用建议**
   - 哪个更适合当前需求
   - 各自的优缺点
   - 推荐使用哪个

### 3. 成本控制

```
list_files: ~100 tokens
read_file (文件1): ~500-2000 tokens
read_file (文件2): ~500-2000 tokens
总计: ~1100-4100 tokens

相比3阶段理解（~8500 tokens），节省约50-75%
```

## 测试场景

### 场景1: 对比两个提示词文件

```
用户: "chat_assistant_v2.md和chat_assistant.md有俩，哪个有用？"

预期流程:
1. list_files(directory="skills/chat-assistant/prompts", pattern="chat_assistant*.md")
2. read_file(file_path="skills/chat-assistant/prompts/chat_assistant.md")
3. read_file(file_path="skills/chat-assistant/prompts/chat_assistant_v2.md")
4. 对比分析，给出建议

预期结果:
- 说明两个文件的区别
- 推荐使用 chat_assistant_optimized.md
```

### 场景2: 对比两个配置文件

```
用户: "skill.yaml和config.yaml有什么区别？"

预期流程:
1. list_files(pattern="*.yaml")
2. read_file(file_path="skill.yaml")
3. read_file(file_path="config.yaml")
4. 对比配置项

预期结果:
- 说明两个配置文件的用途
- 指出主要区别
```

### 场景3: 对比两个代码文件

```
用户: "simple.py和react.py编排器有什么区别？"

预期流程:
1. text_search 或 list_files 定位文件
2. read_file(file_path="backend/daoyoucode/agents/orchestrators/simple.py")
3. read_file(file_path="backend/daoyoucode/agents/orchestrators/react.py")
4. 对比实现

预期结果:
- 说明两个编排器的实现差异
- 指出适用场景
```

## 总结

### 问题
用户问"chat_assistant_v2.md和chat_assistant.md有俩，哪个有用"，需要对比两个文件

### 解决
1. ✅ 更新类型5定义，添加"哪个有用"、"选哪个"等关键词
2. ✅ 明确区分"对比代码"和"对比文件"的策略
3. ✅ 添加完整的文件对比示例
4. ✅ 强调使用 `path` 字段而不是 `name` 字段

### 效果
- LLM能够识别文件对比需求
- 知道使用 list_files → read_file 的流程
- 知道使用完整的 path 字段
- 能够从多个维度对比文件
- 给出明确的使用建议

### 成本
- 对比两个文件：~2500 tokens
- 相比3阶段理解：节省约70%
