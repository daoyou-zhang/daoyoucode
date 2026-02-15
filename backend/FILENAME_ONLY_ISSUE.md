# 只有文件名的问题

## 问题

用户说："看下chat_assistant.md"

LLM直接调用：
```python
read_file(file_path="chat_assistant.md")
```

结果：
```
⚠️  工具返回错误: File not found: chat_assistant.md 
(resolved to D:\daoyouspace\daoyoucode\chat_assistant.md)
```

## 根本原因

**用户只提供了文件名，没有提供完整路径**

LLM应该：
1. 先搜索文件找到完整路径
2. 然后使用完整路径读取

但LLM直接使用了文件名，导致找不到文件。

## 为什么会这样？

### 1. 用户输入模糊

```
"看下chat_assistant.md"
```

这是一个模糊的请求：
- 没有说明文件在哪个目录
- 只给了文件名
- 期望LLM自己找到文件

### 2. LLM的自然倾向

LLM看到文件名后，自然倾向于直接使用，而不是先搜索。

### 3. 提示词不够明确

当前提示词没有明确说明：
- 如果只有文件名，应该先搜索
- 必须使用完整路径

## 解决方案

### 方案1: 在提示词中明确说明 ⭐ 推荐

```markdown
## 重要原则

9. **文件路径规则** ⭐ 极其重要:
   - 读取文件时，必须使用完整的相对路径或从 `list_files` 返回的 `path`
   - ✅ 正确: `read_file(file_path="skills/chat-assistant/prompts/chat_assistant.md")`
   - ✅ 正确: 先 `list_files` 获取 `path`，然后使用该 `path`
   - ❌ 错误: `read_file(file_path="chat_assistant.md")` - 只有文件名会找不到
   - 如果不确定路径，先用 `text_search` 或 `list_files` 查找完整路径
```

### 方案2: 添加专门的示例

```markdown
### 示例2.5: 查找文件（只有文件名） ⭐ 重要

**用户**: "看下chat_assistant.md"

**Thought**: 用户只给了文件名，需要先找到完整路径

**Action 1**: text_search(query="chat_assistant\\.md", file_pattern="**/*.md")

**Observation**:
```
skills/chat-assistant/prompts/chat_assistant.md:
  1: # DaoyouCode AI助手
```

**Thought**: 找到了完整路径，现在读取

**Action 2**: read_file(file_path="skills/chat-assistant/prompts/chat_assistant.md")

**Answer**: [文件内容分析]

**关键**: 不要直接 `read_file(file_path="chat_assistant.md")`，会找不到！
```

### 方案3: 工具层面的智能搜索（未实施）

修改 `read_file` 工具，如果文件不存在，自动搜索：

```python
class ReadFileTool(BaseTool):
    async def execute(self, file_path: str, encoding: str = "utf-8"):
        path = self.resolve_path(file_path)
        
        if not path.exists():
            # 如果文件不存在，尝试搜索
            if not os.path.isabs(file_path) and '/' not in file_path:
                # 只有文件名，搜索
                from .search_tools import TextSearchTool
                search_tool = TextSearchTool()
                result = await search_tool.execute(
                    query=file_path,
                    file_pattern="**/*"
                )
                if result.success and result.content:
                    # 使用第一个匹配的文件
                    path = Path(result.content[0]['file'])
        
        # 继续正常流程...
```

**优点**: 自动处理，对LLM透明
**缺点**: 可能找到错误的文件，增加复杂度

## 推荐实施

### 立即实施（方案1 + 方案2）

1. ✅ 在"重要原则"中添加"文件路径规则"
2. ✅ 添加"示例2.5: 查找文件（只有文件名）"
3. ✅ 在多个地方强调使用完整路径

### 标准流程

当用户只提供文件名时：

```
1. 识别：用户只给了文件名，没有路径

2. 搜索：使用 text_search 或 list_files 查找
   text_search(query="filename\\.ext", file_pattern="**/*")
   或
   list_files(directory=".", pattern="filename.ext", recursive=True)

3. 获取路径：从搜索结果中获取完整路径

4. 读取：使用完整路径读取文件
   read_file(file_path="完整路径")
```

## 常见场景

### 场景1: 只有文件名

```
用户: "看下chat_assistant.md"

正确流程:
1. text_search(query="chat_assistant\\.md")
2. 获取完整路径: skills/chat-assistant/prompts/chat_assistant.md
3. read_file(file_path="skills/chat-assistant/prompts/chat_assistant.md")
```

### 场景2: 有部分路径

```
用户: "看下prompts/chat_assistant.md"

正确流程:
1. text_search(query="prompts/chat_assistant\\.md")
2. 获取完整路径: skills/chat-assistant/prompts/chat_assistant.md
3. read_file(file_path="skills/chat-assistant/prompts/chat_assistant.md")
```

### 场景3: 有完整路径

```
用户: "看下skills/chat-assistant/prompts/chat_assistant.md"

正确流程:
1. 直接读取
   read_file(file_path="skills/chat-assistant/prompts/chat_assistant.md")
```

## 关键点

### 1. 识别文件名 vs 路径

```python
# 只有文件名
"chat_assistant.md"  # ❌ 需要先搜索

# 有路径
"prompts/chat_assistant.md"  # ⚠️ 可能不完整，建议搜索
"skills/chat-assistant/prompts/chat_assistant.md"  # ✅ 完整路径
```

### 2. 搜索方法

```python
# 方法1: text_search（推荐）
text_search(query="chat_assistant\\.md", file_pattern="**/*.md")
# 返回: 文件路径和匹配行

# 方法2: list_files
list_files(directory=".", pattern="chat_assistant.md", recursive=True)
# 返回: 文件列表和完整路径
```

### 3. 使用完整路径

```python
# 从搜索结果获取路径
result = text_search(...)
file_path = result.content[0]['file']  # 完整路径

# 或从 list_files 获取
result = list_files(...)
file_path = result.content[0]['path']  # 完整路径

# 然后读取
read_file(file_path=file_path)
```

## 测试场景

### 测试1: 只有文件名

```
用户: "看下chat_assistant.md"

预期流程:
1. text_search(query="chat_assistant\\.md")
2. read_file(file_path="skills/chat-assistant/prompts/chat_assistant.md")

预期结果:
✅ 成功读取文件
```

### 测试2: 模糊文件名

```
用户: "看下README"

预期流程:
1. text_search(query="README")
2. 可能找到多个README文件
3. 选择最相关的（如项目根目录的README.md）
4. read_file(file_path="README.md")

预期结果:
✅ 成功读取文件
```

### 测试3: 不存在的文件

```
用户: "看下nonexistent.md"

预期流程:
1. text_search(query="nonexistent\\.md")
2. 没有找到

预期结果:
❌ 告诉用户文件不存在
```

## 总结

### 问题
用户只提供文件名，LLM直接使用导致找不到文件

### 原因
1. 用户输入模糊（只有文件名）
2. LLM自然倾向（直接使用文件名）
3. 提示词不够明确

### 解决
1. ✅ 在提示词中明确说明"文件路径规则"
2. ✅ 添加专门的示例展示正确流程
3. ✅ 强调：如果不确定路径，先搜索

### 标准流程
```
只有文件名 → text_search 查找 → 获取完整路径 → read_file
```

### 效果
- LLM知道不能直接使用文件名
- 知道应该先搜索获取完整路径
- 文件读取成功率提高
