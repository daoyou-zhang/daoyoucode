# 关键文件名问题修复 🚨

## 问题严重性：高 ⚠️⚠️⚠️

### 问题
用户问："tsconfig.json报错，是误报么"

AI 的错误行为：
```
read_file(file_path="tsconfig.json")
⚠️ 工具返回错误: File not found: tsconfig.json 
(resolved to D:\daoyouspace\daoyoucode\tsconfig.json)
```

**实际情况**: `tsconfig.json` 在 `oh-my-opencode/` 目录下，不在项目根目录。

### 根本原因

AI **完全忽略了** prompt 中的所有文件路径规则：
1. ❌ 没有先查找完整路径
2. ❌ 直接使用文件名
3. ❌ 没有使用 list_files
4. ❌ 没有考虑文件可能在子目录

**这是一个严重的模式识别失败！**

## 紧急修复

### 修复1: 在 Step 3 添加醒目提醒

**位置**: Phase 0 → Step 3: 验证前行动

**新增**:
```markdown
- **用户提到的文件名是否需要先查找完整路径？** ⭐⭐⭐ 极其重要
  - 如果用户只提供文件名（如 "tsconfig.json"、"README.md"、"chat_assistant.md"）
  - **必须先使用 list_files 查找完整路径**
  - **绝对不要直接使用 read_file(file_path="文件名")**
  - 示例：`list_files(directory=".", pattern="**/tsconfig.json", recursive=True)`
```

### 修复2: 在"开始推理"添加关键提醒

**位置**: 最后的"开始推理"部分

**新增**:
```markdown
**⚠️ 关键提醒 - 文件路径 ⚠️**
- **如果用户只提供文件名（如 "tsconfig.json"、"README.md"）**
- **必须先用 list_files 查找完整路径**
- **绝对不要直接 read_file(file_path="文件名")**
```

**核心原则第一条**:
```markdown
- **文件名 → 先查找路径 → 再读取** ⭐⭐⭐
```

## 正确的处理流程

### 用户输入："tsconfig.json报错，是误报么"

**AI 应该这样做** ✅:

```
Thought: 用户提到了 tsconfig.json 文件。
这是一个文件名，我需要先找到它的完整路径。

我将使用 list_files 工具：
- 原因: 查找 tsconfig.json 的完整路径
- 参数: 
  - directory="."
  - pattern="**/tsconfig.json"
  - recursive=True
- 预期结果: 找到所有 tsconfig.json 文件
- 备选方案: 如果没找到，告诉用户文件不存在

Action 1: list_files(directory=".", pattern="**/tsconfig.json", recursive=True)

Observation:
[
  {
    "path": "oh-my-opencode/tsconfig.json",
    "name": "tsconfig.json",
    "size": 1234
  }
]

Thought: 找到了文件在 oh-my-opencode/ 目录下，现在读取

我将使用 read_file 工具：
- 原因: 读取文件内容检查是否有错误
- 参数: file_path="oh-my-opencode/tsconfig.json"
- 预期结果: 文件内容
- 备选方案: 无

Action 2: read_file(file_path="oh-my-opencode/tsconfig.json")

Answer: [分析文件内容，判断是否误报]
```

### AI 实际做的 ❌:

```
Action: read_file(file_path="tsconfig.json")
Error: File not found
```

**完全跳过了查找步骤！**

## 为什么这么严重？

### 1. 这是基础操作
- 文件查找是最基本的操作
- 如果这个都做不对，其他功能都会受影响

### 2. 用户体验极差
- 用户明确提到文件名
- AI 却说"找不到"
- 用户会认为系统有问题

### 3. 违反了多条规则
- 违反了 Step 3 的验证
- 违反了示例3的指导
- 违反了原则13的规则
- 违反了 list_files 的说明

### 4. 模式识别失败
- AI 没有识别出"用户只提供文件名"这个模式
- 没有触发"先查找路径"的流程

## 改进措施

### 短期（已实施）✅

1. ✅ 在 Step 3 添加醒目提醒（⭐⭐⭐）
2. ✅ 在"开始推理"添加关键提醒（⚠️）
3. ✅ 将"文件名→查找→读取"作为第一核心原则

### 中期（建议）

1. 🔄 在每个涉及文件的示例中都强调这一点
2. 🔄 创建专门的"文件操作检查清单"
3. 🔄 在 read_file 工具说明中添加警告

### 长期（考虑）

1. 🚀 在工具层面添加自动检测
2. 🚀 如果 read_file 收到纯文件名，自动触发查找
3. 🚀 提供更友好的错误提示

## 测试验证

### 测试用例1: tsconfig.json

**输入**: "tsconfig.json报错，是误报么"

**预期**:
1. AI 使用 `list_files(directory=".", pattern="**/tsconfig.json", recursive=True)`
2. 找到 `oh-my-opencode/tsconfig.json`
3. 使用 `read_file(file_path="oh-my-opencode/tsconfig.json")`
4. 分析内容，判断是否误报

### 测试用例2: README.md

**输入**: "看下README.md"

**预期**:
1. AI 使用 `list_files(directory=".", pattern="**/README.md", recursive=True)`
2. 找到所有 README.md 文件
3. 根据上下文选择正确的文件
4. 读取并分析

### 测试用例3: package.json

**输入**: "package.json里有什么依赖"

**预期**:
1. AI 使用 `list_files(directory=".", pattern="**/package.json", recursive=True)`
2. 找到所有 package.json 文件
3. 读取并分析依赖

## 关键点总结

### 必须记住 ⭐⭐⭐

**当用户提到文件名时**:
1. **第一步**: 使用 list_files 查找完整路径
2. **第二步**: 使用返回的 path 字段
3. **第三步**: 使用 read_file 读取

**绝对不要**:
- ❌ 直接 `read_file(file_path="文件名")`
- ❌ 假设文件在项目根目录
- ❌ 跳过查找步骤

### 为什么这么重要？

1. **项目可能有多个同名文件**
   - 多个 tsconfig.json（根目录、子项目）
   - 多个 README.md（根目录、子目录）
   - 多个 package.json（monorepo）

2. **文件可能在任何位置**
   - 子目录
   - 子项目
   - 第三方代码

3. **用户不会提供完整路径**
   - 用户习惯只说文件名
   - 期望AI自动找到

## 修改的文件

- ✅ `skills/chat-assistant/prompts/chat_assistant.md`
  - Step 3: 添加文件路径检查（⭐⭐⭐）
  - 开始推理: 添加关键提醒（⚠️）
  - 核心原则: 文件名→查找→读取（第一条）

## 总结

这是一个**关键的基础操作问题**，必须确保AI每次都能正确处理。

**核心规则**:
```
文件名 → list_files 查找 → 使用 path → read_file 读取
```

**绝对不要跳过查找步骤！**

修复完成！🚨
