# 删除文件工作流

## 工具使用原则

⚠️ **必读**：请先阅读 [工具使用指南](tool_usage_guide.md)，了解工具优先级和最佳实践。

**核心原则：优先使用 repo_map 定位文件，避免盲目搜索！**

## 任务目标

你现在需要执行**删除文件**任务。请严格按照以下步骤操作，确保安全准确。

## 🎯 工作流程

### 步骤 1：定位文件

**推荐方式（最高效）**：
1. 使用 `repo_map(repo_path=".")` 获取项目结构
2. 从代码地图中找到目标文件的路径
3. 确认文件位置

**备选方式（repo_map 不够时）**：

**如果用户只提供了文件名**（如 "temp.txt"）：
1. 使用 `list_files(directory=".", pattern="文件名", recursive=True)` 搜索
2. 或使用 `text_search(query="文件名")` 定位
3. 找到文件的完整相对路径

**如果用户提供了路径**（如 "backend/temp.txt"）：
1. 验证路径是否正确
2. 如果路径不存在，使用搜索工具定位

**示例**：
```
用户："删除 temp.txt"

✅ 推荐方式：
1. 调用 repo_map(repo_path=".")
2. 从结果中找到 "backend/temp.txt"
3. 继续下一步

备选方式：
1. 调用 list_files(directory=".", pattern="temp.txt", recursive=True)
2. 找到 "backend/temp.txt"
3. 继续下一步
```

### 步骤 2：确认并删除

**单个文件**：
```python
delete_file(file_path="相对路径")
```

**多个文件**：
```python
batch_delete_files(file_paths=["路径1", "路径2"])
```

**目录**（需要明确指定 recursive=True）：
```python
delete_file(file_path="目录路径", recursive=True)
```

### 步骤 3：验证结果并结束

1. 检查工具返回的 `success` 状态
2. 如果成功，告知用户已删除
3. 如果失败，分析错误原因并告知用户
4. **⚠️ 删除成功后，不要再尝试访问该文件**（如使用 lsp_symbols、read_file 等工具）

**示例**：
```
✅ 正确：
1. delete_file("temp.txt") → success=True
2. 回复用户："已删除 temp.txt"
3. 结束任务

❌ 错误：
1. delete_file("temp.txt") → success=True
2. lsp_symbols("temp.txt") → 错误：文件不存在
3. 回复用户："未找到文件"（这是错误的，文件已被删除）
```

## ⚠️ 重要注意事项

### 必须做到
- ✅ **先搜索定位，再删除** - 这是最重要的规则
- ✅ 使用相对路径（相对于项目根目录）
- ✅ 删除目录时必须设置 `recursive=True`
- ✅ 检查工具返回结果
- ✅ **删除成功后立即结束任务** - 不要再访问已删除的文件

### 绝对禁止
- ❌ 不要直接删除未定位的文件
- ❌ 不要使用绝对路径
- ❌ 不要猜测文件路径
- ❌ 不要使用其他工具（如 write_file）来删除文件
- ❌ **不要在删除后再访问该文件**（如使用 lsp_symbols、read_file 等）

## 📝 完整示例

### 示例 1：删除单个文件

```
用户："删除 temp.txt"

你的操作：
1. 调用 list_files(directory=".", pattern="temp.txt", recursive=True)
   结果：找到 "backend/temp.txt"

2. 调用 delete_file(file_path="backend/temp.txt")
   结果：success=True

3. 回复用户："已删除 backend/temp.txt"
```

### 示例 2：删除多个文件

```
用户："删除 temp1.txt 和 temp2.txt"

你的操作：
1. 调用 list_files(directory=".", pattern="temp*.txt", recursive=True)
   结果：找到 ["backend/temp1.txt", "backend/temp2.txt"]

2. 调用 batch_delete_files(file_paths=["backend/temp1.txt", "backend/temp2.txt"])
   结果：success=True

3. 回复用户："已删除 2 个文件：backend/temp1.txt, backend/temp2.txt"
```

### 示例 3：删除目录

```
用户："删除 old_folder 目录"

你的操作：
1. 调用 list_files(directory=".", pattern="old_folder", recursive=True)
   结果：找到 "backend/old_folder"

2. 调用 delete_file(file_path="backend/old_folder", recursive=True)
   结果：success=True

3. 回复用户："已删除目录 backend/old_folder"
```

### 示例 4：文件不存在

```
用户："删除 nonexistent.txt"

你的操作：
1. 调用 list_files(directory=".", pattern="nonexistent.txt", recursive=True)
   结果：未找到文件

2. 回复用户："未找到文件 nonexistent.txt，请确认文件名是否正确"
```

## 🔍 常见错误和解决方案

### 错误 1：直接删除未定位的文件
```
❌ 错误：delete_file("temp.txt")
✅ 正确：先 list_files 定位，再 delete_file("backend/temp.txt")
```

### 错误 2：使用绝对路径
```
❌ 错误：delete_file("D:/project/backend/temp.txt")
✅ 正确：delete_file("backend/temp.txt")
```

### 错误 3：删除目录忘记 recursive
```
❌ 错误：delete_file("old_folder")
✅ 正确：delete_file("old_folder", recursive=True)
```

### 错误 4：使用错误的工具
```
❌ 错误：write_file("temp.txt", "")  # 试图用写空文件来删除
✅ 正确：delete_file("temp.txt")
```

## 🎓 工作流总结

记住这个简单的流程：
1. **搜索** - 找到文件位置
2. **删除** - 使用正确的工具和参数
3. **验证** - 检查结果并告知用户

**核心原则**：先定位，再删除，永远不要猜测路径！
