# Diff 显示功能实现总结

## 用户需求

**问题**："修改成功了，但是我怎么看修改后代码呢？diff？之前 aider 是咋做的"

## aider 的做法

aider 在修改代码后会：

1. **自动显示 diff**：每次修改后立即显示 unified diff
2. **询问确认**：问用户是否接受修改
3. **支持撤销**：用户可以拒绝修改，aider 会回滚

示例：
```
aider> 修改 test.py，将 timeout 从 120 改为 1800

Applied edit to test.py

--- a/test.py
+++ b/test.py
@@ -1,1 +1,1 @@
-timeout = 120
+timeout = 1800

Accept these changes? (Y)es/(N)o/(U)ndo/(S)kip: 
```

## 实现方案

### 方案 1: search_replace 工具自动生成 diff ✅ 已实现

**修改内容**：

1. **改进 SearchReplaceTool**（`backend/daoyoucode/agents/tools/diff_tools.py`）
   - 在修改文件前保存原始内容
   - 修改后生成 unified diff
   - 在返回结果中包含 diff
   - 格式化输出，包含 emoji 和代码块

2. **实现 GitDiffTool**（`backend/daoyoucode/agents/tools/git_tools.py`）
   - 支持查看单个文件或所有文件的 diff
   - 支持查看已暂存的修改
   - 返回标准的 git diff 格式

3. **改进 Prompt**（`skills/chat-assistant/prompts/chat_assistant.md`）
   - 指示 AI 在修改后显示 diff
   - 提供正确的回复格式示例

### 实现细节

#### 1. SearchReplaceTool 改进

```python
async def execute(self, file_path: str, search: str, replace: str, replace_all: bool = False):
    # 读取原始内容
    old_content = path.read_text(encoding='utf-8', errors='ignore')
    
    # 执行替换
    new_content = diff_tools.replace(old_content, search, replace, replace_all)
    
    # 生成 diff
    import difflib
    diff_lines = list(difflib.unified_diff(
        old_content.splitlines(keepends=True),
        new_content.splitlines(keepends=True),
        fromfile=f"a/{file_path}",
        tofile=f"b/{file_path}",
        lineterm=''
    ))
    
    diff_text = ''.join(diff_lines) if diff_lines else "No changes"
    
    # 写入文件
    path.write_text(new_content, encoding='utf-8')
    
    # 构建结果消息（包含 diff）
    result_message = f"✅ Successfully modified {file_path}\n\n"
    result_message += "📝 Changes:\n"
    result_message += "```diff\n"
    result_message += diff_text
    result_message += "\n```"
    
    return ToolResult(
        success=True,
        content=result_message,
        metadata={
            'file_path': str(path),
            'diff': diff_text,
            'changes_count': len([line for line in diff_lines if line.startswith('+') or line.startswith('-')])
        }
    )
```

#### 2. GitDiffTool 实现

```python
async def execute(self, file_path: str = None, staged: bool = False):
    import subprocess
    
    # 构建 git diff 命令
    cmd = ["git", "diff"]
    
    if staged:
        cmd.append("--staged")
    
    if file_path:
        path = self.resolve_path(file_path)
        cmd.append(str(path))
    
    # 执行命令
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    
    if result.returncode != 0:
        return ToolResult(success=False, error=f"Git diff failed: {result.stderr}")
    
    diff_output = result.stdout
    
    if not diff_output.strip():
        return ToolResult(success=True, content="No changes")
    
    return ToolResult(
        success=True,
        content=diff_output,
        metadata={'has_changes': True, 'file_path': file_path}
    )
```

#### 3. Prompt 改进

```markdown
### 代码修改工具 ⚠️ 重要：必须真正调用工具修改文件

**search_replace** - 修改现有文件 ⭐⭐⭐
- **⚠️ 重要**：当用户要求修改代码时，**必须调用此工具**，不要只在回复中显示修改后的代码

**✅ 正确做法**：
用户："修改 backend/test.py，将 timeout 从 120 改为 1800"
你的行动：
1. 调用 search_replace(...)
2. 工具返回包含 diff 的结果
3. 你的回复：
   "✅ 已修改 backend/test.py
   
   📝 Changes:
   ```diff
   -    timeout = 120
   +    timeout = 1800
   ```
   
   将超时时间从 120 秒增加到 1800 秒（30 分钟）。"

**重要**：search_replace 工具会自动生成 diff，你应该在回复中显示这个 diff。
```

## 使用示例

### 示例 1: 修改代码后自动显示 diff

```
用户："修改 backend/test.py，将 timeout 从 120 改为 1800"

🔧 执行工具: search_replace
   file_path  backend/test.py
   search     timeout = 120
   replace    timeout = 1800
✓ 执行完成 (0.02秒)

AI > ✅ Successfully modified backend/test.py

📝 Changes:
```diff
--- a/backend/test.py
+++ b/backend/test.py
@@ -10,7 +10,7 @@
 
 def main():
-    timeout = 120
+    timeout = 1800
     print(f"Timeout: {timeout}")
```

将超时时间从 120 秒增加到 1800 秒（30 分钟）。
```

### 示例 2: 手动查看 diff

```
用户："显示 backend/test.py 的修改"

🔧 执行工具: git_diff
   file_path  backend/test.py
✓ 执行完成 (0.01秒)

AI > backend/test.py 的修改：

```diff
diff --git a/backend/test.py b/backend/test.py
index 1234567..abcdefg 100644
--- a/backend/test.py
+++ b/backend/test.py
@@ -10,7 +10,7 @@
-    timeout = 120
+    timeout = 1800
```
```

### 示例 3: 查看所有修改

```
用户："显示所有修改"

🔧 执行工具: git_diff
✓ 执行完成 (0.01秒)

AI > 当前所有修改：

```diff
diff --git a/backend/test.py b/backend/test.py
--- a/backend/test.py
+++ b/backend/test.py
@@ -10,7 +10,7 @@
-    timeout = 120
+    timeout = 1800

diff --git a/backend/config.yaml b/backend/config.yaml
--- a/backend/config.yaml
+++ b/backend/config.yaml
@@ -5,7 +5,7 @@
-  max_tokens: 4000
+  max_tokens: 8000
```
```

## 验证测试

### 测试步骤

```bash
# 1. 重新安装
cd backend
pip install -e .

# 2. 创建测试文件
cd ..
echo "timeout = 120" > backend/test_diff.py

# 3. 测试修改和 diff 显示
daoyoucode chat "修改 backend/test_diff.py，将 timeout = 120 改为 timeout = 1800"

# 4. 验证结果
# 应该看到：
# - 工具调用提示
# - diff 显示
# - 文件被修改

# 5. 清理
rm backend/test_diff.py
```

### 预期输出

```
AI正在思考...

🔧 执行工具: search_replace
   file_path  backend/test_diff.py
   search     timeout = 120
   replace    timeout = 1800
✓ 执行完成 (0.02秒)

AI > ✅ Successfully modified backend/test_diff.py

📝 Changes:
```diff
--- a/backend/test_diff.py
+++ b/backend/test_diff.py
@@ -1,1 +1,1 @@
-timeout = 120
+timeout = 1800
```

已将超时时间从 120 秒修改为 1800 秒。
```

## 与 aider 的对比

| 功能 | aider | DaoyouCode |
|------|-------|------------|
| 自动显示 diff | ✅ | ✅ 已实现 |
| 格式化输出 | ✅ | ✅ 已实现 |
| 询问确认 | ✅ | ⏳ 待实现 |
| 支持撤销 | ✅ | ⏳ 使用 git |
| 彩色 diff | ✅ | ⏳ 待实现 |
| 交互式审查 | ✅ | ⏳ 待实现 |

## 已修改的文件

1. `backend/daoyoucode/agents/tools/diff_tools.py`
   - SearchReplaceTool.execute() - 添加 diff 生成和格式化输出

2. `backend/daoyoucode/agents/tools/git_tools.py`
   - GitDiffTool.execute() - 实现 git diff 功能

3. `skills/chat-assistant/prompts/chat_assistant.md`
   - 添加修改后显示 diff 的指示

## 相关文档

1. `backend/HOW_TO_VIEW_CHANGES.md` - 如何查看修改指南
2. `backend/AI_TOOL_CALLING_FIX_SUMMARY.md` - 工具调用修复
3. `backend/DIFF_DISPLAY_IMPLEMENTATION.md` - 本文档

## 未来改进

### 短期（1-2 周）

1. ⏳ **彩色 diff 输出**
   - 使用 Rich 库显示彩色 diff
   - 红色表示删除，绿色表示添加

2. ⏳ **改进 diff 格式**
   - 显示修改的行号
   - 显示修改统计（+X -Y）
   - 支持并排 diff

### 中期（1-2 月）

1. ⏳ **询问确认机制**
   - 修改前显示将要做的修改
   - 询问用户是否继续
   - 支持 Y/N/U/S 选项

2. ⏳ **撤销功能**
   - 记录修改历史
   - 支持一键撤销
   - 支持撤销到任意版本

### 长期（3-6 月）

1. ⏳ **交互式审查**
   - 逐个修改点审查
   - 支持接受/拒绝单个修改
   - 类似 git add -p

2. ⏳ **修改历史管理**
   - 记录所有 AI 修改
   - 支持查看历史
   - 支持回滚

## 故障排查

### 问题：没有看到 diff

**检查**：
1. 是否使用了 search_replace 工具
2. AI 是否在回复中显示了 diff
3. 终端是否支持 markdown 代码块

**解决**：
```bash
# 手动查看
git diff backend/test.py

# 或要求 AI 显示
daoyoucode chat "显示 backend/test.py 的修改"
```

### 问题：diff 格式不清晰

**原因**：
- 终端不支持彩色输出
- diff 太长被截断

**解决**：
```bash
# 使用 git diff（支持彩色）
git diff backend/test.py

# 或使用 IDE 的 Git 功能
```

### 问题：想撤销修改

**解决**：
```bash
# 撤销单个文件
git checkout backend/test.py

# 撤销所有修改
git checkout .

# 或使用 git restore（Git 2.23+）
git restore backend/test.py
```

## 总结

### 已实现 ✅

1. search_replace 工具自动生成并返回 diff
2. git_diff 工具可以查看任何文件的修改
3. AI 会在回复中显示格式化的 diff
4. 支持查看单个文件或所有文件的修改

### 使用方法

1. **自动显示**：修改后 AI 自动显示 diff
2. **手动查看**：使用 `git diff` 命令
3. **要求显示**：明确要求 AI 显示 diff

### 立即行动

```bash
# 1. 重新安装
cd backend
pip install -e .

# 2. 测试
cd ..
daoyoucode chat "修改 backend/test.md，将 hello 改为 world"

# 3. 查看 diff（应该自动显示）
```

---

**现在 AI 修改代码后会自动显示 diff，就像 aider 一样！**
