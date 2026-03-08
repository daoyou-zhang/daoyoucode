# 搜索代码工作流

## 工具使用原则

⚠️ **必读**：请先阅读 [工具使用指南](tool_usage_guide.md)，了解工具优先级和最佳实践。

**核心原则：优先使用 repo_map 获取全局视图，再使用搜索工具定位细节！**

## 任务目标

你现在需要执行**搜索代码**任务。请使用最合适的搜索工具，快速准确地定位代码。

## 🎯 工作流程

### 步骤 0：优先使用 repo_map（推荐）

**在使用搜索工具前，先考虑 repo_map**：

```
使用工具：repo_map
参数：
  - repo_path: "."
  - max_depth: 3
  - include_tests: false

作用：
- ✅ 一次性获取整个项目的代码地图
- ✅ 包含所有类、函数、模块的定义和引用
- ✅ 通常已经包含了你要搜索的内容
- ✅ 比逐个搜索高效得多

何时使用：
- 查找类、函数、模块的定义
- 了解代码在项目中的位置
- 查看引用关系
- 任何涉及"在哪里"的问题
```

**示例**：
```
用户："Agent 类在哪里？"

✅ 推荐方式：
1. repo_map(repo_path=".") 
   → 从结果中直接找到文件路径（如 "daoyoucode/agents/core/agent.py"）
2. 回复用户

⚠️ 注意：路径相对于当前工作目录
- 如果在 backend 目录下运行，路径是：daoyoucode/agents/core/agent.py
- 如果在项目根目录运行，路径是：backend/daoyoucode/agents/core/agent.py

❌ 低效方式：
1. text_search(query="class Agent")
   → 返回几十个结果
2. 逐个查看
3. 回复用户
```

### 步骤 1：选择搜索工具（repo_map 不够时）

**只有在 repo_map 不够详细时，才使用搜索工具**：

**1. 语义搜索（推荐，最精准）**
- 工具：`semantic_code_search(query="自然语言描述", top_k=8)`
- 适用：理解功能、查找实现、定位逻辑
- 示例："登录功能在哪里"、"如何处理错误"

**2. 文本搜索（快速，关键词匹配）**
- 工具：`text_search(query="具体的类名或函数名", file_pattern="**/*.py")`
- 适用：查找特定字符串、类名、函数名
- 示例："UserLogin"、"def authenticate"
- ⚠️ 不要搜索 "def"、"class" 等太宽泛的关键词

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
   
2. 结果：找到文件路径（如 daoyoucode/agents/core/agent.py）

3. 回复用户：
   "Agent 类在 [找到的路径] 中定义"
   
⚠️ 注意：路径相对于当前工作目录
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

| 需求 | 第一选择 | 第二选择 | 原因 |
|------|---------|---------|------|
| 查找类/函数定义 | repo_map | text_search | repo_map 已包含所有定义 |
| 理解功能实现 | repo_map | semantic_code_search | repo_map 提供全局视图 |
| 查找引用关系 | repo_map | lsp_find_references | repo_map 包含引用信息 |
| 查找文件 | repo_map | list_files | repo_map 包含文件结构 |
| 复杂模式匹配 | - | regex_search | 需要正则表达式时 |

**核心原则**：repo_map 优先，搜索工具兜底！

## ⚠️ 注意事项

- ✅ **优先使用 repo_map**（最高效，包含最多信息）
- ✅ repo_map 不够时才使用 semantic_code_search（最精准）
- ✅ 如果结果太多，缩小搜索范围
- ✅ 如果结果太少，换工具或扩大范围
- ❌ 不要一次搜索太多关键词
- ❌ 不要搜索太宽泛的关键词（如 "def"、"class"）
- ❌ 不要忽略搜索结果的上下文
- ❌ 不要跳过 repo_map 直接搜索

## 🎓 工作流总结

1. **优先 repo_map** - 检查是否已包含所需信息
2. **选择工具** - repo_map 不够时选择搜索工具
3. **执行搜索** - 调用工具获取结果
4. **分析结果** - 检查结果质量
5. **返回结果** - 清晰地告诉用户

**核心原则**：repo_map 优先，搜索工具兜底，快速准确定位代码！
