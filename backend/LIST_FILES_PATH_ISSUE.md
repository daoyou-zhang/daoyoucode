# list_files 路径使用问题

## 问题现象

用户询问文件时，LLM的行为：

```
用户: "chat_assistant_v2.md和chat_assistant.md有俩，哪个有用"

1. list_files(pattern="chat_assistant*.md", directory=".")
   ✅ 成功，返回文件列表

2. read_file(file_path="chat_assistant.md")
   ❌ 失败: File not found (resolved to D:\...\backend\chat_assistant.md)

3. read_file(file_path="chat_assistant_v2.md")
   ❌ 失败: File not found (resolved to D:\...\backend\chat_assistant_v2.md)
```

## 根本原因

### list_files 返回格式

```python
# list_files 返回
[
    {
        "path": "D:\\daoyouspace\\daoyoucode\\skills\\chat-assistant\\prompts\\chat_assistant.md",  # 完整路径
        "name": "chat_assistant.md",  # 只有文件名
        "type": "file",
        "size": 9554
    },
    {
        "path": "D:\\daoyouspace\\daoyoucode\\skills\\chat-assistant\\prompts\\chat_assistant_v2.md",
        "name": "chat_assistant_v2.md",
        "type": "file",
        "size": 8839
    }
]
```

### LLM的错误行为

LLM只使用了 `name` 字段：
```python
read_file(file_path="chat_assistant.md")  # ❌ 只有文件名，没有路径
```

应该使用 `path` 字段：
```python
read_file(file_path="skills/chat-assistant/prompts/chat_assistant.md")  # ✅ 完整路径
```

或者直接使用绝对路径：
```python
read_file(file_path="D:\\daoyouspace\\daoyoucode\\skills\\chat-assistant\\prompts\\chat_assistant.md")  # ✅ 绝对路径
```

## 为什么会这样？

### 1. 提示词不够明确

当前提示词没有明确说明：
- `list_files` 返回的数据结构
- 应该使用 `path` 字段而不是 `name` 字段
- `path` 和 `name` 的区别

### 2. LLM的自然倾向

LLM看到文件名后，自然倾向于直接使用文件名，而不是完整路径。

## 解决方案

### 方案1: 优化提示词 ⭐ 推荐

在提示词中明确说明 `list_files` 的使用方法：

```markdown
#### list_files
列出目录内容

**返回格式**:
```json
[
  {
    "path": "完整路径（用于read_file）",  ⭐ 强调这个
    "name": "文件名",
    "type": "file/dir",
    "size": 文件大小
  }
]
```

**重要**: 使用返回的 `path` 字段传给 `read_file`，不要只用 `name`

**示例**:
```python
# 1. 列出文件
result = list_files(directory="skills/chat-assistant/prompts", pattern="*.md")
# 返回: [{"path": "skills/chat-assistant/prompts/chat_assistant.md", "name": "chat_assistant.md", ...}]

# 2. 读取文件 - 使用完整的 path
read_file(file_path="skills/chat-assistant/prompts/chat_assistant.md")  # ✅ 正确

# 不要只用 name
read_file(file_path="chat_assistant.md")  # ❌ 错误
```
```

### 方案2: 修改 list_files 返回格式

让 `list_files` 返回相对路径而不是绝对路径：

```python
# 当前返回（绝对路径）
{
    "path": "D:\\daoyouspace\\daoyoucode\\skills\\chat-assistant\\prompts\\chat_assistant.md",
    "name": "chat_assistant.md"
}

# 修改后返回（相对路径）
{
    "path": "skills/chat-assistant/prompts/chat_assistant.md",  # 相对于working_directory
    "name": "chat_assistant.md",
    "absolute_path": "D:\\daoyouspace\\daoyoucode\\skills\\chat-assistant\\prompts\\chat_assistant.md"
}
```

**优点**:
- 相对路径更简洁
- 更容易理解
- 跨平台兼容性更好

**缺点**:
- 需要修改代码
- 可能影响其他使用者

### 方案3: 添加示例到提示词

在提示词中添加完整的示例：

```markdown
### 示例：查找并读取文件

**用户**: "有哪些提示词文件？"

**Action 1**: list_files(directory="skills/chat-assistant/prompts", pattern="*.md")

**Observation**:
```json
[
  {
    "path": "skills/chat-assistant/prompts/chat_assistant.md",
    "name": "chat_assistant.md",
    "type": "file",
    "size": 9554
  },
  {
    "path": "skills/chat-assistant/prompts/chat_assistant_v2.md",
    "name": "chat_assistant_v2.md",
    "type": "file",
    "size": 8839
  }
]
```

**Thought**: 找到了2个文件，现在读取第一个文件

**Action 2**: read_file(file_path="skills/chat-assistant/prompts/chat_assistant.md")  ⭐ 使用完整的 path

**Observation**: [文件内容]

**Answer**: 有2个提示词文件：chat_assistant.md 和 chat_assistant_v2.md...
```

## 推荐实施

### 立即实施（方案1）

在 `chat_assistant_optimized.md` 中添加明确说明：

```markdown
## 可用工具详情

### 轻量工具（优先使用）⭐

#### list_files ⭐ 重要
列出目录内容

**返回格式**:
```json
[
  {
    "path": "完整路径（用于read_file）",
    "name": "文件名",
    "type": "file/dir",
    "size": 文件大小
  }
]
```

**关键规则**:
1. ✅ 使用 `path` 字段传给 `read_file`
2. ❌ 不要只用 `name` 字段
3. `path` 是相对于工作目录的完整路径
4. `name` 只是文件名，没有目录信息

**正确示例**:
```python
# 1. 列出文件
files = list_files(directory="skills/chat-assistant/prompts", pattern="*.md")
# 返回: [{"path": "skills/chat-assistant/prompts/chat_assistant.md", ...}]

# 2. 读取文件 - 使用 path
read_file(file_path=files[0]["path"])  # ✅ 正确
read_file(file_path="skills/chat-assistant/prompts/chat_assistant.md")  # ✅ 正确
```

**错误示例**:
```python
# 只用 name - 会找不到文件
read_file(file_path=files[0]["name"])  # ❌ 错误
read_file(file_path="chat_assistant.md")  # ❌ 错误
```
```

### 后续优化（方案2）

修改 `list_files` 返回相对路径：

```python
# backend/daoyoucode/agents/tools/file_tools.py

class ListFilesTool(BaseTool):
    async def execute(self, directory: str = ".", ...):
        path = self.resolve_path(directory)
        
        for item in path.iterdir():
            # 计算相对路径
            if self._working_directory:
                try:
                    relative_path = item.relative_to(self._working_directory)
                except ValueError:
                    relative_path = item
            else:
                relative_path = item
            
            files.append({
                'path': str(relative_path),  # 相对路径
                'name': item.name,
                'absolute_path': str(item),  # 绝对路径（可选）
                'type': 'dir' if item.is_dir() else 'file',
                'size': item.stat().st_size if item.is_file() else 0
            })
```

## 总结

### 问题
- LLM使用 `list_files` 返回的 `name` 而不是 `path`
- 导致 `read_file` 找不到文件

### 原因
- 提示词没有明确说明应该使用 `path`
- LLM自然倾向于使用简短的文件名

### 解决
1. **立即**: 在提示词中明确说明使用 `path` 字段
2. **后续**: 修改 `list_files` 返回相对路径

### 效果
- ✅ LLM知道应该使用 `path` 字段
- ✅ 文件读取成功率提高
- ✅ 用户体验改善
