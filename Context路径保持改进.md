# Context 路径保持改进

## 问题描述

在多步骤工作流中（搜索 → 读取 → 理解 → 修改），如果中间执行了其他搜索操作，`target_file` 会被覆盖，导致后续操作使用错误的文件路径。

### 问题场景

```
步骤1：搜索目标文件 (agent.py)
  → target_file = "agent.py" ✅

步骤2：读取文件
  → 读取 agent.py ✅

步骤3：搜索配置文件 (config.yaml)
  → target_file = "config.yaml" ❌ 覆盖了！

步骤4：修改文件
  → 修改 config.yaml ❌ 错误！应该修改 agent.py
```

## 解决方案

### 核心改进

1. **添加搜索历史** (`search_history`)
   - 记录所有搜索操作
   - 包含工具名、路径、时间戳
   - 可以回溯查找

2. **target_file 只在首次设置**
   - 第一次搜索时自动设置 `target_file`
   - 后续搜索不会覆盖
   - 手动设置的值也不会被覆盖

3. **last_search_paths 总是更新**
   - 保存最近一次搜索的结果
   - 可以用于临时引用

### 代码改进

修改了 `backend/daoyoucode/agents/core/agent.py` 中的 `_save_tool_result_to_context()` 方法：

```python
# 🆕 添加到搜索历史（不覆盖之前的搜索）
search_history = context.get("search_history") or []
search_entry = {
    "tool": tool_name,
    "paths": paths,
    "timestamp": datetime.now().isoformat(),
    "result_preview": str(tool_result.content)[:200]
}
search_history.append(search_entry)
context.set("search_history", search_history, track_change=False)

# 总是保存最新的搜索路径
context.set("last_search_paths", paths, track_change=False)

# 🔧 只在 target_file 未设置时才自动设置（避免覆盖）
if not context.get("target_file"):
    context.set("target_file", paths[0], track_change=False)
    # ... 设置 target_dir, target_files, target_dirs
else:
    # target_file 已存在，不覆盖，但记录到历史
    self.logger.info(f"✅ 搜索结果已添加到历史")
```

## Context 变量说明

### 1. target_file (主目标文件)
- **用途**：当前要操作的主文件
- **设置时机**：首次搜索时自动设置
- **是否覆盖**：❌ 不会被后续搜索覆盖
- **使用场景**：修改、重构等主要操作

### 2. target_files (多文件列表)
- **用途**：首次搜索返回多个文件时保存所有文件
- **设置时机**：首次搜索返回 > 1 个文件时
- **是否覆盖**：❌ 不会被后续搜索覆盖
- **使用场景**：批量操作多个文件

### 3. target_dir / target_dirs (目录)
- **用途**：目标文件所在的目录
- **设置时机**：与 target_file 同时设置
- **是否覆盖**：❌ 不会被后续搜索覆盖
- **使用场景**：需要目录路径的操作

### 4. last_search_paths (最新搜索结果)
- **用途**：最近一次搜索的结果
- **设置时机**：每次搜索都更新
- **是否覆盖**：✅ 总是更新为最新搜索
- **使用场景**：临时引用、查看最新搜索

### 5. search_history (搜索历史)
- **用途**：所有搜索操作的历史记录
- **设置时机**：每次搜索都追加
- **是否覆盖**：❌ 只追加，不覆盖
- **使用场景**：回溯查找、查看所有搜索

## 使用示例

### 场景1：单文件工作流

```python
# 步骤1：搜索目标文件
text_search("agent.py")
# → target_file = "backend/daoyoucode/agents/core/agent.py"
# → search_history = [{"tool": "text_search", "paths": [...]}]

# 步骤2：读取文件
read_file(context.get("target_file"))

# 步骤3：搜索配置文件（不会覆盖 target_file）
text_search("config.yaml")
# → target_file = "backend/daoyoucode/agents/core/agent.py" (不变)
# → last_search_paths = ["backend/daoyoucode/config.yaml"]
# → search_history = [搜索1, 搜索2]

# 步骤4：修改目标文件（仍然是 agent.py）
write_file(context.get("target_file"), new_content)
```

### 场景2：访问搜索历史

```python
# 获取所有搜索历史
history = context.get("search_history")

# 获取第一次搜索的路径
first_search = history[0]["paths"][0]

# 获取最后一次搜索的路径
last_search = history[-1]["paths"][0]

# 获取所有搜索的路径
all_paths = [entry["paths"][0] for entry in history]
```

### 场景3：手动设置目标文件

```python
# 手动设置 target_file（不会被自动搜索覆盖）
context.set("target_file", "my_custom_file.py")

# 后续搜索不会覆盖手动设置的值
text_search("other_file.py")
# → target_file = "my_custom_file.py" (保持不变)
```

## 测试验证

创建了两个测试脚本：

### 1. test_context_workflow.py
- 验证问题场景
- 展示解决方案

### 2. test_context_improved.py
- 测试改进后的功能
- 验证所有场景

运行测试：
```bash
python test_context_improved.py
```

测试结果：
```
✅ 所有测试通过！

📊 改进总结:
   1. ✅ target_file 只在首次搜索时自动设置
   2. ✅ 后续搜索不会覆盖 target_file
   3. ✅ 所有搜索都记录到 search_history
   4. ✅ last_search_paths 总是更新为最新搜索
   5. ✅ 手动设置的 target_file 不会被覆盖
   6. ✅ 可以通过 search_history 访问所有搜索结果
```

## 工作流建议

### 在工作流中使用 Context 变量

```markdown
## 步骤1：定位目标文件

使用 text_search 或 grep_search 搜索目标文件。

**重要**：第一次搜索会自动设置 `target_file`，后续搜索不会覆盖。

## 步骤2：读取文件

使用 `{{target_file}}` 读取目标文件：
```
read_file(path="{{target_file}}")
```

## 步骤3：搜索参考文件（可选）

如果需要搜索其他文件（如配置文件），直接搜索即可，不会影响 `target_file`。

搜索结果会保存到 `last_search_paths` 和 `search_history`。

## 步骤4：修改目标文件

使用 `{{target_file}}` 修改文件：
```
write_file(path="{{target_file}}", content="...")
```
```

## 优势

1. **路径保持**：target_file 在整个工作流中保持不变
2. **历史记录**：可以回溯查看所有搜索操作
3. **灵活性**：可以手动设置 target_file
4. **向后兼容**：不影响现有功能
5. **自动化**：首次搜索自动设置，无需手动操作

## 下一步

1. ✅ 代码改进完成
2. ✅ 测试验证通过
3. 🔄 在实际工作流中测试（如"拆分 agent.py"）
4. 📝 更新工作流文档，说明 Context 变量的使用
5. 🎯 可选：在 Prompt 中显示 Context 信息（阶段2）

## 相关文件

- `backend/daoyoucode/agents/core/agent.py` - Context 集成实现
- `backend/daoyoucode/agents/core/context.py` - Context 类定义
- `test_context_integration.py` - 基础功能测试
- `test_context_workflow.py` - 问题场景演示
- `test_context_improved.py` - 改进后的功能测试
- `Context集成完成总结.md` - Context 集成总体说明
