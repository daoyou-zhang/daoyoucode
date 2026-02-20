# AI 工具调用问题修复总结

## 问题描述

**核心问题**：AI 只是在回复中显示了修改后的代码，但没有真正调用工具去修改文件

**症状**：
- 用户看到 AI 回复："你可以将代码修改为：timeout = 1800"
- 但没有看到工具调用提示：`🔧 执行工具: search_replace`
- 文件没有被修改

## 根本原因

**LLM 没有调用工具，而是直接回复**

原因分析：
1. ❌ **chat-assistant Skill 缺少修改工具**：工具列表中没有 `search_replace`
2. ❌ **Prompt 指示不够明确**：没有强调"必须调用工具"而不是"只描述修改"
3. ❌ **programming Skill 使用 simple 编排器**：不如 react 适合工具调用

## 修复方案

### 修复 1: 添加修改工具到 chat-assistant ✅

**文件**: `skills/chat-assistant/skill.yaml`

**修改**:
```yaml
tools:
  - discover_project_docs
  - get_repo_structure
  - repo_map
  - semantic_code_search
  - read_file
  - text_search
  - regex_search
  - write_file
  - search_replace        # 🆕 添加
  - apply_patch           # 🆕 添加
  - list_files
  - get_file_symbols      # 🆕 添加
  - run_lint              # 🆕 添加
  - git_diff              # 🆕 添加
```

### 修复 2: 改进 Prompt 指示 ✅

**文件**: `skills/chat-assistant/prompts/chat_assistant.md`

**添加**:
```markdown
### 代码修改工具 ⚠️ 重要：必须真正调用工具修改文件

**search_replace** - 修改现有文件 ⭐⭐⭐
- **⚠️ 重要**：当用户要求修改代码时，**必须调用此工具**，不要只在回复中显示修改后的代码

**❌ 错误做法**：
用户："修改 backend/test.py，将 timeout 从 120 改为 1800"
你的回复："你可以将代码修改为：timeout = 1800"  ← 错误！没有真正修改文件

**✅ 正确做法**：
用户："修改 backend/test.py，将 timeout 从 120 改为 1800"
你的行动：
1. 调用 search_replace(file_path="backend/test.py", search="timeout = 120", replace="timeout = 1800")
2. 系统显示：🔧 执行工具: search_replace ✓ 执行完成
3. 你的回复："已将 backend/test.py 中的 timeout 从 120 改为 1800"
```

### 修复 3: programming Skill 使用 ReAct 编排器 ✅

**文件**: `skills/programming/skill.yaml`

**修改**:
```yaml
# 使用 ReAct 编排器（更适合工具调用）
orchestrator: react
```

## 验证修复

### 测试步骤

```bash
# 1. 重新安装
cd backend
pip install -e .

# 2. 创建测试文件
cd ..
echo "timeout: 120" > backend/test_modify.md

# 3. 测试修改（使用 chat-assistant）
daoyoucode chat "修改 backend/test_modify.md，将 timeout: 120 改为 timeout: 1800"

# 4. 验证结果
cat backend/test_modify.md
# 应该显示: timeout: 1800

# 5. 清理
rm backend/test_modify.md
```

### 预期输出

```
AI正在思考...

🔧 执行工具: search_replace
   file_path  backend/test_modify.md
   search     timeout: 120
   replace    timeout: 1800
✓ 执行完成 (0.02秒)

AI > 已成功修改 backend/test_modify.md，将 timeout 从 120 改为 1800。
```

### 如果仍然失败

尝试使用 programming Skill：

```bash
daoyoucode chat --skill programming "修改 backend/test_modify.md，将 timeout: 120 改为 timeout: 1800"
```

或明确要求使用工具：

```bash
daoyoucode chat "使用 search_replace 工具修改 backend/test_modify.md，将 timeout: 120 改为 timeout: 1800"
```

## 技术细节

### 工具调用流程

```
用户输入
  ↓
execute_skill()
  ↓
orchestrator.execute() (react)
  ↓
agent.execute()
  ↓
_call_llm_with_tools()
  ↓
LLM 返回 function_call
  ↓
tool_registry.execute_tool("search_replace", ...)
  ↓
SearchReplaceTool.execute()
  ↓
path.write_text(new_content)  ← 文件被修改
  ↓
返回 ToolResult(success=True)
  ↓
显示：🔧 执行工具: search_replace ✓ 执行完成
```

### 为什么 LLM 不调用工具？

1. **工具不在列表中**：Skill 的 `tools` 列表中没有该工具
2. **Prompt 没有指示**：Prompt 没有明确说"必须调用工具"
3. **模型能力不足**：某些模型的 Function Calling 能力较弱
4. **编排器不适合**：simple 编排器不如 react 适合工具调用

### ReAct vs Simple 编排器

| 特性 | ReAct | Simple |
|------|-------|--------|
| 工具调用 | ✅ 优秀 | ⚠️ 一般 |
| 多轮推理 | ✅ 支持 | ❌ 不支持 |
| 自动重试 | ✅ 支持 | ✅ 支持 |
| 适用场景 | 复杂任务、工具调用 | 简单对话 |

**结论**：需要工具调用的 Skill 应该使用 ReAct 编排器

## 相关文件

### 已修改的文件

1. `skills/chat-assistant/skill.yaml` - 添加修改工具
2. `skills/chat-assistant/prompts/chat_assistant.md` - 改进 Prompt 指示
3. `skills/programming/skill.yaml` - 改用 ReAct 编排器

### 相关文档

1. `backend/AI_NOT_CALLING_TOOLS_DIAGNOSIS.md` - 问题诊断
2. `backend/ENSURE_AI_CAN_MODIFY_CODE.md` - 测试指南
3. `backend/TOOL_PATH_FIX_SUMMARY.md` - 工具路径修复
4. `backend/AI_MODIFICATION_REVIEW.md` - AI 修改评审

### 核心代码

1. `backend/daoyoucode/agents/core/agent.py` - Agent 执行逻辑
2. `backend/daoyoucode/agents/tools/diff_tools.py` - SearchReplaceTool 实现
3. `backend/daoyoucode/agents/orchestrators/react.py` - ReAct 编排器
4. `backend/daoyoucode/agents/orchestrators/simple.py` - Simple 编排器

## 最佳实践

### 1. Skill 配置

```yaml
# 需要修改代码的 Skill
orchestrator: react  # 使用 ReAct 编排器

tools:
  - read_file
  - search_replace  # 必须包含
  - apply_patch
  - write_file
  - run_lint        # 验证修改
```

### 2. Prompt 编写

```markdown
## 代码修改规则

当用户要求修改代码时，你**必须**使用工具：

✅ 正确：调用 search_replace(file_path="...", search="...", replace="...")
❌ 错误：只在回复中显示修改后的代码
```

### 3. 用户提示

```bash
# 明确要求使用工具
daoyoucode chat "使用 search_replace 工具修改 ..."

# 使用适合的 Skill
daoyoucode chat --skill programming "修改 ..."

# 使用强模型
daoyoucode chat --model qwen-max "修改 ..."
```

## 故障排查

### 问题：LLM 仍然不调用工具

**检查**:
1. Skill 的 `tools` 列表中是否包含 `search_replace`
2. Skill 的 `orchestrator` 是否为 `react`
3. Prompt 是否明确指示"必须调用工具"
4. 模型是否支持 Function Calling（qwen-max 支持）

**解决**:
```bash
# 查看 Skill 配置
cat skills/chat-assistant/skill.yaml

# 查看 Prompt
cat skills/chat-assistant/prompts/chat_assistant.md

# 使用 programming Skill
daoyoucode chat --skill programming "修改 ..."
```

### 问题：工具调用了但文件没有修改

**检查**:
1. 是否看到 `🔧 执行工具: search_replace`
2. 是否看到 `✓ 执行完成`
3. 是否有错误提示

**解决**:
```bash
# 查看详细日志
export LOG_LEVEL=DEBUG
daoyoucode chat "修改 ..."

# 检查文件权限
ls -l backend/test_modify.md

# 检查路径是否正确
# 使用完整相对路径：backend/test_modify.md
```

### 问题：找不到文件

**检查**:
1. 路径是否相对于项目根目录
2. 路径是否完整（包含 backend/ 前缀）

**解决**:
```bash
# ❌ 错误
daoyoucode chat "修改 test_modify.md"

# ✅ 正确
daoyoucode chat "修改 backend/test_modify.md"
```

## 总结

### 问题根源

**LLM 没有调用工具，而是直接在回复中描述修改**

### 修复内容

1. ✅ chat-assistant 添加修改工具（search_replace, apply_patch 等）
2. ✅ Prompt 明确指示"必须调用工具"而不是"只描述修改"
3. ✅ programming 改用 ReAct 编排器

### 验证方法

```bash
# 创建测试文件
echo "timeout: 120" > backend/test_modify.md

# 测试修改
daoyoucode chat "修改 backend/test_modify.md，将 timeout: 120 改为 timeout: 1800"

# 验证结果（应该显示 timeout: 1800）
cat backend/test_modify.md

# 清理
rm backend/test_modify.md
```

### 预期结果

- ✅ 看到工具调用提示：`🔧 执行工具: search_replace`
- ✅ 看到执行完成：`✓ 执行完成 (0.02秒)`
- ✅ 文件被修改：`cat backend/test_modify.md` 显示 `timeout: 1800`
- ✅ AI 回复确认：`已成功修改 backend/test_modify.md`

### 立即行动

```bash
# 1. 重新安装
cd backend
pip install -e .

# 2. 运行测试
cd ..
backend\test_ai_modify.bat

# 3. 如果成功，开始使用
daoyoucode chat "修改 backend/config/llm_config.yaml，将 max_tokens 从 4000 改为 8000"
```

---

**修复完成！AI 现在应该能够真正调用工具修改文件了。**
