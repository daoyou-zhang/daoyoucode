# 工具参考手册

> DaoyouCode 26个工具完整参考

---

## 工具总览

| 类别 | 工具数 | 使用频率 |
|------|--------|---------|
| 文件操作 | 6 | ⭐⭐⭐⭐⭐ |
| 搜索 | 2 | ⭐⭐⭐⭐⭐ |
| Git | 4 | ⭐⭐⭐⭐ |
| 命令执行 | 2 | ⭐⭐⭐⭐ |
| 代码编辑 | 1 | ⭐⭐⭐⭐⭐ |
| LSP | 6 | ⭐⭐⭐⭐ |
| AST | 2 | ⭐⭐⭐ |
| 代码地图 | 2 | ⭐⭐⭐⭐ |
| 项目文档 | 1 | ⭐⭐⭐ |

---

## 快速查找表

| 工具 | 功能 | 常用参数 |
|------|------|---------|
| **文件操作** | | |
| `read_file` | 读取文件 | file_path |
| `write_file` | 写入文件 | file_path, content |
| `list_files` | 列出目录 | directory, recursive |
| `get_file_info` | 文件信息 | path |
| `create_directory` | 创建目录 | directory |
| `delete_file` | 删除文件 | path, recursive |
| **搜索** | | |
| `text_search` | 文本搜索 | query, directory |
| `regex_search` | 正则搜索 | pattern, directory |
| **Git** | | |
| `git_status` | Git状态 | repo_path |
| `git_diff` | Git差异 | 🚧 未实现 |
| `git_commit` | Git提交 | 🚧 未实现 |
| `git_log` | Git日志 | 🚧 未实现 |
| **命令执行** | | |
| `run_command` | 执行命令 | command, cwd |
| `run_test` | 运行测试 | test_path, test_framework |
| **代码编辑** | | |
| `search_replace` | 精确替换 | file_path, search, replace |
| **LSP** | | |
| `lsp_diagnostics` | 诊断信息 | file_path, severity |
| `lsp_goto_definition` | 跳转定义 | file_path, line, character |
| `lsp_find_references` | 查找引用 | file_path, line, character |
| `lsp_symbols` | 符号列表 | file_path, scope |
| `lsp_rename` | 重命名符号 | file_path, line, character, new_name |
| `lsp_code_actions` | 代码操作 | file_path, line, character |
| **AST** | | |
| `ast_grep_search` | AST搜索 | pattern, lang |
| `ast_grep_replace` | AST替换 | pattern, rewrite, lang |
| **代码地图** | | |
| `repo_map` | 代码地图 | repo_path, chat_files |
| `get_repo_structure` | 仓库结构 | repo_path, max_depth |
| **项目文档** | | |
| `discover_project_docs` | 项目文档 | repo_path |

---

## 按场景选择工具

### 理解新项目
```
discover_project_docs → get_repo_structure → repo_map
```

### 查找代码
```
text_search / ast_grep_search → read_file
```

### 修改代码
```
read_file → search_replace → lsp_diagnostics → run_test
```

### 重构代码
```
lsp_find_references → lsp_rename / ast_grep_replace → run_test
```

### 调试错误
```
lsp_diagnostics → lsp_goto_definition → read_file → search_replace
```

---

## 核心工具详解

### 1. read_file - 读取文件
```python
read_file(file_path="src/main.py")
```
- 读取单个文件的完整内容
- 大文件会被截断（最大5000字符或200行）

### 2. write_file - 写入文件
```python
write_file(file_path="src/new.py", content="def hello(): pass")
```
- 创建新文件或覆盖现有文件
- 自动创建目录

### 3. search_replace - 精确替换
```python
search_replace(
    file_path="src/main.py",
    search="def old():\n    pass",
    replace="def new():\n    return True"
)
```
- 支持9种智能匹配策略
- 精确替换代码块

### 4. text_search - 文本搜索
```python
text_search(query="def main", directory="src", file_pattern="*.py")
```
- 类似grep的文本搜索
- 支持文件模式过滤

### 5. lsp_diagnostics - 诊断信息
```python
lsp_diagnostics(file_path="src/main.py", severity="error")
```
- 获取语法错误、类型错误、警告
- 支持Python、JavaScript、TypeScript等

### 6. lsp_find_references - 查找引用
```python
lsp_find_references(file_path="src/main.py", line=10, character=5)
```
- 查找符号的所有引用位置
- 重构前的影响分析

### 7. lsp_rename - 重命名符号
```python
lsp_rename(file_path="src/main.py", line=10, character=5, new_name="new_func")
```
- 安全重命名函数、类、变量
- 自动更新所有引用

### 8. ast_grep_search - AST搜索
```python
ast_grep_search(pattern="console.log($MSG)", lang="javascript")
```
- 使用AST模式匹配搜索代码
- 支持25种语言

### 9. ast_grep_replace - AST替换
```python
ast_grep_replace(
    pattern="console.log($MSG)",
    rewrite="logger.info($MSG)",
    lang="javascript",
    dry_run=true
)
```
- 批量重构代码
- 支持预览模式

### 10. repo_map - 代码地图
```python
repo_map(
    repo_path=".",
    chat_files=["src/main.py"],
    mentioned_idents=["Config"]
)
```
- 智能排序最相关的代码
- PageRank算法 + 个性化权重
- 快速了解项目结构

### 11. git_status - Git状态
```python
git_status(repo_path=".")
```
- 查看当前分支、修改的文件、暂存的文件
- 了解工作目录状态

### 12. run_test - 运行测试
```python
run_test(test_path="tests/test_main.py", test_framework="pytest")
```
- 支持pytest、unittest、jest
- 返回测试结果统计

---

## 工具组合模式

### 模式1: 理解新项目
```
1. discover_project_docs(repo_path=".")  # 读文档
2. get_repo_structure(repo_path=".")     # 看结构
3. repo_map(repo_path=".")               # 生成地图
```

### 模式2: 查找和修改代码
```
1. text_search(query="function_name")    # 找到位置
2. read_file(file_path="src/main.py")    # 读取文件
3. search_replace(...)                   # 精确修改
4. lsp_diagnostics(file_path="...")      # 检查错误
```

### 模式3: 重构代码
```
1. lsp_find_references(...)              # 查找所有引用
2. lsp_rename(...)                       # 重命名符号
3. run_test()                            # 运行测试
4. git_status()                          # 检查更改
```

### 模式4: 批量修改
```
1. ast_grep_search(pattern="...")        # 找到所有匹配
2. ast_grep_replace(dry_run=true, ...)   # 预览替换
3. ast_grep_replace(dry_run=false, ...)  # 实际替换
4. run_test()                            # 验证更改
```

---

## 性能提示

| 工具 | 首次运行 | 后续运行 | 优化建议 |
|------|---------|---------|---------|
| `repo_map` | 慢（解析文件） | 快（缓存） | 提供chat_files聚焦 |
| `lsp_*` | 慢（启动服务器） | 快（复用） | 批量操作 |
| `ast_grep_*` | 慢（首次下载） | 快 | 限制搜索路径 |
| `text_search` | 快 | 快 | 使用file_pattern过滤 |

---

## 安全提示

| 工具 | 风险 | 注意事项 |
|------|------|---------|
| `write_file` | 🔴 高 | 会覆盖现有文件 |
| `delete_file` | 🔴 高 | 不可逆操作 |
| `search_replace` | 🟡 中 | 直接修改文件 |
| `lsp_rename` | 🟡 中 | 修改多个文件 |
| `ast_grep_replace` | 🟡 中 | 批量修改 |
| `run_command` | 🟡 中 | 执行任意命令 |
| `read_file` | 🟢 低 | 只读操作 |
| `text_search` | 🟢 低 | 只读操作 |

---

## 最佳实践

1. **修改前先读取** - 使用 `read_file` 确认内容
2. **修改后检查** - 使用 `lsp_diagnostics` 检查错误
3. **测试验证** - 使用 `run_test` 验证更改
4. **Git管理** - 使用 `git_status` 查看更改
5. **预览模式** - AST替换先用 `dry_run=true`

---

## 相关文档

- [CLI命令参考.md](./CLI命令参考.md) - CLI使用指南
- [AGENTS.md](./AGENTS.md) - Agent详细介绍
- [ORCHESTRATORS.md](./ORCHESTRATORS.md) - 编排器详细介绍
