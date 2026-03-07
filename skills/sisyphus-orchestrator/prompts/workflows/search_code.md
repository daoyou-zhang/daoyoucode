# 搜索代码工作流

你现在需要执行**搜索代码**任务。请使用最合适的搜索工具，快速准确地定位代码。

## 🎯 工作流程

### 步骤 1：选择搜索工具

根据搜索需求选择最合适的工具：

**1. 语义搜索（推荐，最精准）**
- 工具：`semantic_code_search(query="自然语言描述", top_k=8)`
- 适用：理解功能、查找实现、定位逻辑
- 示例："登录功能在哪里"、"如何处理错误"

**2. 文本搜索（快速，关键词匹配）**
- 工具：`text_search(query="关键词", file_pattern="**/*.py")`
- 适用：查找特定字符串、类名、函数名
- 示例："UserLogin"、"def authenticate"

**3. 正则搜索（精确，模式匹配）**
- 工具：`regex_search(pattern="正则表达式", file_pattern="**/*.py")`
- 适用：复杂模式匹配
- 示例：`"class \w+Agent"`

**4. 列出文件（简单，文件名匹配）**
- 工具：`list_files(directory=".", pattern="*.py", recursive=True)`
- 适用：查找特定文件
- 示例："找到所有 test 文件"

### 步骤 2：执行搜索

根据选择的工具执行搜索，获取结果。

### 步骤 3：分析结果

1. 检查搜索结果数量
2. 如果结果太多，缩小搜索范围
3. 如果结果太少，扩大搜索范围或换工具

### 步骤 4：返回结果

清晰地告诉用户：
- 找到了什么
- 在哪个文件
- 相关的代码片段（如果有）

## 📝 完整示例

### 示例 1：查找功能实现

```
用户："登录功能在哪里实现的？"

你的操作：
1. 使用语义搜索（最精准）
   semantic_code_search(query="登录功能实现", top_k=8)
   
2. 结果：找到 backend/auth/login.py

3. 回复用户：
   "登录功能在 backend/auth/login.py 中实现，主要包括：
   - authenticate() 函数：验证用户凭证
   - generate_token() 函数：生成 JWT token
   - login_handler() 函数：处理登录请求"
```

### 示例 2：查找类定义

```
用户："找到 Agent 类"

你的操作：
1. 使用文本搜索（关键词匹配）
   text_search(query="class Agent", file_pattern="**/*.py")
   
2. 结果：找到 backend/daoyoucode/agents/core/agent.py

3. 回复用户：
   "Agent 类在 backend/daoyoucode/agents/core/agent.py 中定义"
```

### 示例 3：查找所有测试文件

```
用户："列出所有测试文件"

你的操作：
1. 使用列出文件（文件名匹配）
   list_files(directory=".", pattern="test_*.py", recursive=True)
   
2. 结果：找到 15 个测试文件

3. 回复用户：
   "找到 15 个测试文件：
   - backend/tests/test_agent.py
   - backend/tests/test_tools.py
   - ..."
```

## 🔍 工具选择指南

| 需求 | 推荐工具 | 原因 |
|------|---------|------|
| 理解功能 | semantic_code_search | 最精准，理解语义 |
| 查找类名 | text_search | 快速，关键词匹配 |
| 查找函数 | text_search | 快速，关键词匹配 |
| 复杂模式 | regex_search | 精确，支持正则 |
| 查找文件 | list_files | 简单，文件名匹配 |

## ⚠️ 注意事项

- ✅ 优先使用 semantic_code_search（最精准）
- ✅ 如果结果太多，缩小搜索范围
- ✅ 如果结果太少，换工具或扩大范围
- ❌ 不要一次搜索太多关键词
- ❌ 不要忽略搜索结果的上下文

## 🎓 工作流总结

1. **选择工具** - 根据需求选择最合适的搜索工具
2. **执行搜索** - 调用工具获取结果
3. **分析结果** - 检查结果质量
4. **返回结果** - 清晰地告诉用户

**核心原则**：优先使用语义搜索，快速准确定位代码！
