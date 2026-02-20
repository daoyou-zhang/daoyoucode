# AI 不调用工具问题诊断

## 问题描述

用户反馈：**AI 只是在回复中显示了修改后的代码，但没有真正调用工具去修改文件**

## 问题分析

### 1. 工具执行流程 ✅ 正常

代码流程：
```
用户输入 → execute_skill() → orchestrator.execute() → agent.execute() 
→ _call_llm_with_tools() → tool_registry.execute_tool() → SearchReplaceTool.execute()
→ path.write_text() → 文件被修改
```

**结论**: 如果工具被调用，文件会被修改（代码逻辑正确）

### 2. 问题根源：LLM 没有调用工具

**症状**:
- 用户看到 AI 在回复中描述了修改
- 但没有看到工具调用的 UI 提示（`🔧 执行工具: search_replace`）
- 文件没有被修改

**原因**: LLM 选择直接回复，而不是调用工具

### 3. 为什么 LLM 不调用工具？

可能的原因：

#### 3.1 Skill 没有配置工具 ❌

检查 Skill 配置：

```yaml
# skills/chat-assistant/skill.yaml
tools:
  - search_replace  # ← 必须包含这个工具
  - read_file
  - ...
```

**如果 `tools` 列表中没有 `search_replace`，LLM 就无法调用它**

#### 3.2 Prompt 没有引导 LLM 调用工具 ❌

检查 Prompt：

```markdown
# skills/chat-assistant/prompts/chat_assistant.md

你可以使用以下工具：
- search_replace: 修改文件内容
- read_file: 读取文件
...

当用户要求修改代码时，你应该：
1. 使用 search_replace 工具修改文件
2. 不要只是在回复中显示修改后的代码
```

**如果 Prompt 没有明确指示，LLM 可能选择直接回复**

#### 3.3 LLM 模型不支持 Function Calling ❌

检查模型：

```yaml
# backend/config/llm_config.yaml
default:
  model: "qwen-max"  # ← 支持 Function Calling
```

**qwen-max 支持 Function Calling，但 qwen-turbo 可能不支持**

#### 3.4 工具规则不清晰 ❌

当前工具规则：

```python
# backend/daoyoucode/agents/core/agent.py
default_tool_rules = """⚠️ 工具使用规则（必须遵守）：

1. 路径参数使用 '.' 表示当前工作目录
2. 文件路径：相对**项目根**
3. 搜索目录使用 '.' 或省略
4. 细粒度编辑与验证
5. 单文件符号（AST 深度）
6. 不要重复调用
"""
```

**问题**: 规则只说了"如何"使用工具，没有说"何时"使用工具

## 解决方案

### 方案 1: 检查 Skill 配置 ✅

```bash
# 查看 chat-assistant 的配置
cat skills/chat-assistant/skill.yaml
```

确保包含修改工具：

```yaml
tools:
  - search_replace  # ← 必须有
  - apply_patch
  - write_file
  - read_file
  - ...
```

### 方案 2: 改进 Prompt ✅

在 Skill 的 Prompt 中明确指示：

```markdown
# skills/chat-assistant/prompts/chat_assistant.md

## 代码修改规则

当用户要求修改代码时，你**必须**使用工具，而不是只在回复中显示代码：

1. ✅ 正确做法：
   - 使用 `search_replace` 工具修改文件
   - 或使用 `apply_patch` 工具应用补丁
   - 或使用 `write_file` 工具写入文件

2. ❌ 错误做法：
   - 不要只在回复中显示修改后的代码
   - 不要说"你可以这样修改"
   - 不要说"建议修改为"

3. 示例：
   用户："修改 backend/test.py，将 timeout 从 120 改为 1800"
   
   你应该：
   ```
   调用 search_replace(
     file_path="backend/test.py",
     search="timeout = 120",
     replace="timeout = 1800"
   )
   ```
   
   而不是：
   ```
   你可以将代码修改为：
   timeout = 1800
   ```
```

### 方案 3: 改进工具规则 ✅

在 `agent.py` 中添加"何时"使用工具的规则：

```python
default_tool_rules = """⚠️ 工具使用规则（必须遵守）：

## 何时使用工具

1. **修改代码时**：必须使用 search_replace 或 apply_patch
   - ❌ 不要只在回复中显示修改后的代码
   - ✅ 使用工具真正修改文件

2. **读取文件时**：必须使用 read_file
   - ❌ 不要说"我需要查看文件"
   - ✅ 直接调用 read_file 工具

3. **搜索代码时**：必须使用 text_search 或 semantic_code_search
   - ❌ 不要说"我不知道在哪里"
   - ✅ 直接调用搜索工具

## 如何使用工具

1. 路径参数使用 '.' 表示当前工作目录
2. 文件路径：相对**项目根**
3. 搜索目录使用 '.' 或省略
...
"""
```

### 方案 4: 使用更强的模型 ✅

```yaml
# backend/config/llm_config.yaml
default:
  model: "qwen-max"  # ← 使用 qwen-max，Function Calling 能力更强
```

### 方案 5: 创建专门的修改 Skill ✅

创建一个专门用于修改代码的 Skill：

```yaml
# skills/code-modifier/skill.yaml
name: code-modifier
version: "1.0.0"
description: "专门用于修改代码的 Skill"
orchestrator: react  # 使用 ReAct 编排器，更适合工具调用
agent: Programmer

tools:
  - search_replace
  - apply_patch
  - write_file
  - read_file
  - get_file_symbols
  - run_lint
  - run_test

prompt:
  file: "prompts/code_modifier.md"

llm:
  model: "qwen-max"
  temperature: 0.3  # 降低温度，更精确
```

```markdown
# skills/code-modifier/prompts/code_modifier.md

你是一个代码修改专家。

## 核心原则

**你必须使用工具来修改代码，而不是只在回复中显示修改**

## 工作流程

1. 理解用户的修改需求
2. 如果需要，使用 read_file 读取文件
3. 使用 search_replace 或 apply_patch 修改文件
4. 如果需要，使用 run_lint 或 run_test 验证修改
5. 告诉用户修改已完成

## 示例

用户："修改 backend/test.py，将 timeout 从 120 改为 1800"

你的步骤：
1. 调用 search_replace(file_path="backend/test.py", search="timeout = 120", replace="timeout = 1800")
2. 回复："已将 backend/test.py 中的 timeout 从 120 改为 1800"

## 禁止行为

❌ 不要只在回复中显示代码
❌ 不要说"你可以这样修改"
❌ 不要说"建议修改为"
✅ 直接使用工具修改文件
```

## 诊断步骤

### 1. 查看 Skill 配置

```bash
cat skills/chat-assistant/skill.yaml
```

检查：
- `tools` 列表中是否包含 `search_replace`
- `orchestrator` 是什么（`react` 更适合工具调用）

### 2. 查看 Prompt

```bash
cat skills/chat-assistant/prompts/chat_assistant.md
```

检查：
- 是否明确指示使用工具修改代码
- 是否有"不要只在回复中显示代码"的说明

### 3. 测试工具调用

```bash
daoyoucode chat "使用 search_replace 工具修改 backend/test.md，将 'hello' 改为 'world'"
```

观察：
- 是否看到 `🔧 执行工具: search_replace`
- 文件是否被修改

### 4. 查看日志

```bash
# 启用 DEBUG 日志
export LOG_LEVEL=DEBUG
daoyoucode chat "修改 backend/test.md"
```

查找：
- `调用工具: search_replace`
- `工具执行成功`
- 如果没有这些日志，说明 LLM 没有调用工具

## 快速修复

### 修复 1: 使用 programming Skill

```bash
# programming Skill 使用 ReAct 编排器，更适合工具调用
daoyoucode chat --skill programming "修改 backend/test.md，将 timeout 从 120 改为 1800"
```

### 修复 2: 明确要求使用工具

```bash
daoyoucode chat "使用 search_replace 工具修改 backend/test.md，将 timeout: 120 改为 timeout: 1800"
```

### 修复 3: 使用 qwen-max 模型

```bash
daoyoucode chat --model qwen-max "修改 backend/test.md"
```

## 验证修复

### 测试脚本

```bash
# 创建测试文件
echo "timeout: 120" > backend/test_modify.md

# 测试修改
daoyoucode chat --skill programming "修改 backend/test_modify.md，将 timeout: 120 改为 timeout: 1800"

# 验证结果
cat backend/test_modify.md
# 应该显示: timeout: 1800

# 清理
rm backend/test_modify.md
```

### 预期输出

```
🔧 执行工具: search_replace
   file_path  backend/test_modify.md
   search     timeout: 120
   replace    timeout: 1800
✓ 执行完成 (0.02秒)

AI > 已成功修改 backend/test_modify.md，将 timeout 从 120 改为 1800。
```

## 总结

### 问题根源

**LLM 没有调用工具，而是直接在回复中描述修改**

### 解决方案优先级

1. ✅ **立即**: 使用 `programming` Skill（使用 ReAct 编排器）
2. ✅ **短期**: 改进 Prompt，明确指示使用工具
3. ✅ **中期**: 改进工具规则，添加"何时"使用工具
4. ✅ **长期**: 创建专门的 `code-modifier` Skill

### 立即行动

```bash
# 1. 使用 programming Skill 测试
daoyoucode chat --skill programming "修改 backend/test.md，将 timeout 从 120 改为 1800"

# 2. 如果成功，说明问题在于 Skill 配置
# 3. 如果失败，检查 Skill 配置和 Prompt
```

## 相关文件

- `backend/daoyoucode/agents/core/agent.py` - Agent 执行逻辑
- `backend/daoyoucode/agents/tools/diff_tools.py` - SearchReplaceTool 实现
- `skills/chat-assistant/skill.yaml` - chat-assistant 配置
- `skills/programming/skill.yaml` - programming 配置
- `backend/config/llm_config.yaml` - LLM 配置
