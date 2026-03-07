# 查找未使用代码工作流

## 🎯 核心原则

**repo_map 已经标记了引用计数，直接从输出中识别未使用的代码！**

不要逐个用 LSP 查找引用，repo_map 的输出已经包含了所有信息。

## 任务目标

查找项目中未使用的方法、类、函数、变量等代码。

## 执行步骤

### 1. 获取项目代码地图（必须启用 LSP）

**这是唯一需要的步骤！**

```
使用工具：repo_map
参数：
  - repo_path: "."
  - max_tokens: 6000  # 增大 token 预算，获取更多信息
  - enable_lsp: true  # 🔥 必须启用，才能看到引用计数
  - auto_scale: true

作用：
- 获取整个项目的代码地图
- 包含所有类、函数、方法的定义
- 🔥 显示每个定义的引用计数（"# X次引用"）
- 一次性获取全局信息，不需要逐个文件搜索
```

### 2. 从 repo_map 输出中识别未使用的代码

repo_map 的输出格式（启用 LSP 后）：

```
# 代码地图 (Top 50 文件)
# (LSP增强: 包含类型签名和引用计数)

backend/utils/helper.py:
  function old_function (line 10)  # 0次引用  ← 🔥 未使用！
  function active_function (line 20)  # 5次引用  ← 正在使用
  class OldClass (line 30)  # 0次引用  ← 🔥 未使用！

backend/core/user.py:
  class User (line 15)  # 10次引用  ← 正在使用
  function login (line 50)  # 3次引用  ← 正在使用
  function _internal_helper (line 80)  # 1次引用  ← 内部使用（可能需要保留）
```

**识别规则**：

1. **完全未使用**：`# 0次引用`
   - 这些代码可以安全删除
   - 示例：`old_function`, `OldClass`

2. **仅内部使用**：`# 1次引用` 且是私有方法（以 `_` 开头）
   - 可能是私有辅助方法
   - 需要判断是否必要

3. **正在使用**：`# 2次引用` 或更多
   - 这些代码正在被使用
   - 不应该删除

### 3. 排除特殊情况

以下情况不算未使用（即使引用计数为 0）：

- **入口文件**：`main.py`, `app.py`, `__main__.py`
- **测试文件**：`test_*.py`, `*_test.py`
- **公共 API**：`__init__.py` 中导出的
- **配置文件**：`settings.py`, `config.py`
- **CLI 命令**：`cli/commands/*.py`
- **Django/Flask 特殊文件**：`migrations/`, `views.py`, `models.py`

### 4. 分类未使用代码

根据引用计数分类：

#### 4.1 完全未使用（0次引用）
```
backend/utils/old_helper.py:
  function old_function (line 10)  # 0次引用
  class OldClass (line 30)  # 0次引用
```
**建议**：可以安全删除

#### 4.2 仅内部使用（1次引用，私有方法）
```
backend/core/user.py:
  function _internal_helper (line 80)  # 1次引用
```
**建议**：检查是否必要，可能可以内联

#### 4.3 低频使用（1-2次引用）
```
backend/utils/helper.py:
  function rarely_used (line 40)  # 2次引用
```
**建议**：检查是否可以简化或合并

### 5. 提供清理建议

根据分析结果，提供清理建议：

```markdown
## 未使用代码分析报告

### 可以安全删除（0次引用）

1. **backend/utils/old_helper.py**
   - `old_function` (line 10) - 完全未使用
   - `OldClass` (line 30) - 完全未使用
   - 建议：删除整个文件

2. **backend/core/legacy.py**
   - `legacy_method` (line 50) - 完全未使用
   - 建议：删除此方法

### 需要确认（1次引用，私有方法）

1. **backend/core/user.py**
   - `_internal_helper` (line 80) - 仅内部使用
   - 建议：检查是否可以内联到调用处

### 清理步骤

1. 备份代码（Git commit）
2. 删除未使用的代码
3. 运行测试确认：`pytest`
4. 提交变更
```

## ⚠️ 重要提示

### ❌ 不要这样做

```
错误示例1：逐个用 LSP 查找引用
repo_map(...)  # 获取代码地图
lsp_find_references(file_path="file1.py", line=10)  # ❌ 不需要！
lsp_find_references(file_path="file2.py", line=20)  # ❌ 不需要！
...
```

**为什么错误**：repo_map 已经包含了引用计数，不需要再逐个查找！

```
错误示例2：搜索所有函数定义
text_search(query="def", file_pattern="**/*.py")  # ❌ 不需要！
```

**为什么错误**：repo_map 已经提供了所有函数定义！

### ✅ 正确做法

```
正确示例：只用 repo_map
repo_map(repo_path=".", max_tokens=6000, enable_lsp=true)

然后直接从输出中识别：
- "# 0次引用" → 未使用
- "# 1次引用" → 可能未使用（如果是私有方法）
- "# 2次引用" 或更多 → 正在使用
```

## 工具使用原则

### 必须使用的工具

1. **repo_map**（必须，唯一需要的工具）
   - 参数：`enable_lsp=true`（必须启用）
   - 参数：`max_tokens=6000`（增大预算）
   - 作用：获取全局代码地图 + 引用计数
   - 这是最高效的方式，一次调用获取所有信息

### 不应该使用的工具

❌ **lsp_find_references**
- repo_map 已经包含引用计数
- 不需要逐个查找

❌ **text_search**
- repo_map 已经提供所有定义
- 不需要搜索

❌ **list_files**
- repo_map 已经包含所有文件
- 不需要列出

❌ **read_file**
- repo_map 已经提供定义信息
- 不需要读取文件内容

## 示例流程

### 用户请求
"查看项目，有没有没被使用的方法"

### 正确流程

```
步骤1：获取代码地图（唯一步骤）
repo_map(
    repo_path=".",
    max_tokens=6000,
    enable_lsp=true,
    auto_scale=true
)

返回结果（示例）：
# 代码地图 (Top 50 文件)
# (LSP增强: 包含类型签名和引用计数)

backend/utils/old_helper.py:
  function old_function (line 10)  # 0次引用  ← 未使用！
  class OldClass (line 30)  # 0次引用  ← 未使用！

backend/core/user.py:
  class User (line 15)  # 10次引用  ← 正在使用
  function login (line 50)  # 3次引用  ← 正在使用
  function _internal_helper (line 80)  # 1次引用  ← 可能未使用

步骤2：分析结果（直接从输出中识别）
未使用的代码：
1. old_helper.py 中的 old_function() - 0次引用
2. old_helper.py 中的 OldClass - 0次引用
3. user.py 中的 _internal_helper() - 1次引用（私有方法，可能可以内联）

步骤3：提供建议
可以安全删除：
- backend/utils/old_helper.py（整个文件都未使用）

需要确认：
- backend/core/user.py 中的 _internal_helper()（私有方法，检查是否可以内联）
```

### 错误流程（不要这样做）

```
❌ 步骤1：获取代码地图
repo_map(repo_path=".", max_tokens=3000, enable_lsp=true)

❌ 步骤2：逐个查找引用（不需要！）
lsp_find_references(file_path="backend/utils/old_helper.py", line=10)
lsp_find_references(file_path="backend/utils/old_helper.py", line=30)
lsp_find_references(file_path="backend/core/user.py", line=80)
...
→ 浪费时间，repo_map 已经包含了引用计数！
```

## 注意事项

### 1. 必须启用 LSP

```python
repo_map(
    repo_path=".",
    enable_lsp=true  # 🔥 必须启用，才能看到引用计数
)
```

如果不启用 LSP，输出中不会有引用计数，就无法识别未使用的代码。

### 2. 增大 token 预算

```python
repo_map(
    repo_path=".",
    max_tokens=6000  # 🔥 增大预算，获取更多文件
)
```

默认的 3000 tokens 可能不够，建议使用 6000 tokens。

### 3. 谨慎处理删除

不要急于删除代码：
- 可能是对外 API
- 可能是未来计划使用
- 可能是框架要求（如 Django 的 migrations）
- 可能是配置文件引用（如 settings.py）

### 4. 测试覆盖

删除代码前：
- 确保有测试覆盖
- 运行测试确认没有破坏功能
- 使用 Git 备份，方便回滚

## 成功标准

- ✅ 使用 repo_map 获取了全局代码地图（启用 LSP）
- ✅ 从输出中直接识别了未使用的代码（"# 0次引用"）
- ✅ 正确分类了未使用代码
- ✅ 提供了清晰的清理建议
- ✅ 说明了删除的风险和注意事项
- ✅ 没有使用低效的逐个查找引用方式

## 输出格式示例

```markdown
## 未使用代码分析报告

### 📊 统计
- 总文件数：50
- 总定义数：200
- 未使用定义：5 (2.5%)

### 🗑️ 可以安全删除（0次引用）

#### backend/utils/old_helper.py
- `old_function` (line 10) - 完全未使用
- `OldClass` (line 30) - 完全未使用
- **建议**：删除整个文件

#### backend/core/legacy.py
- `legacy_method` (line 50) - 完全未使用
- **建议**：删除此方法

### ⚠️ 需要确认（1次引用，私有方法）

#### backend/core/user.py
- `_internal_helper` (line 80) - 仅内部使用
- **建议**：检查是否可以内联到调用处

### 📝 清理步骤

1. 备份代码
   ```bash
   git add .
   git commit -m "备份：删除未使用代码前"
   ```

2. 删除未使用的代码
   - 删除 `backend/utils/old_helper.py`
   - 删除 `backend/core/legacy.py` 中的 `legacy_method`

3. 运行测试
   ```bash
   pytest
   ```

4. 提交变更
   ```bash
   git add .
   git commit -m "清理：删除未使用的代码"
   ```
```
