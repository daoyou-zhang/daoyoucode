# DaoyouCode 工具快速参考

> **快速查找工具能力**

## 📋 工具总览（26个）

| 工具名称 | 功能 | 常用参数 | 使用频率 |
|---------|------|---------|---------|
| **文件操作** | | | |
| `read_file` | 读取文件内容 | file_path | ⭐⭐⭐⭐⭐ |
| `write_file` | 写入/创建文件 | file_path, content | ⭐⭐⭐⭐⭐ |
| `list_files` | 列出目录 | directory, recursive, pattern | ⭐⭐⭐⭐ |
| `get_file_info` | 获取文件信息 | path | ⭐⭐⭐ |
| `create_directory` | 创建目录 | directory | ⭐⭐ |
| `delete_file` | 删除文件/目录 | path, recursive | ⭐⭐ |
| **搜索** | | | |
| `text_search` | 文本搜索 | query, directory, file_pattern | ⭐⭐⭐⭐⭐ |
| `regex_search` | 正则搜索 | pattern, directory | ⭐⭐⭐ |
| **Git** | | | |
| `git_status` | Git状态 | repo_path | ⭐⭐⭐⭐⭐ |
| `git_diff` | Git差异 | - | 🚧 未实现 |
| `git_commit` | Git提交 | - | 🚧 未实现 |
| `git_log` | Git日志 | - | 🚧 未实现 |
| **命令执行** | | | |
| `run_command` | 执行命令 | command, cwd, timeout | ⭐⭐⭐⭐ |
| `run_test` | 运行测试 | test_path, test_framework | ⭐⭐⭐⭐ |
| **代码编辑** | | | |
| `search_replace` | SEARCH/REPLACE编辑 | file_path, search, replace | ⭐⭐⭐⭐⭐ |
| **LSP** | | | |
| `lsp_diagnostics` | 获取诊断信息 | file_path, severity | ⭐⭐⭐⭐⭐ |
| `lsp_goto_definition` | 跳转到定义 | file_path, line, character | ⭐⭐⭐⭐ |
| `lsp_find_references` | 查找引用 | file_path, line, character | ⭐⭐⭐⭐ |
| `lsp_symbols` | 获取符号列表 | file_path, scope, query | ⭐⭐⭐ |
| `lsp_rename` | 重命名符号 | file_path, line, character, new_name | ⭐⭐⭐ |
| `lsp_code_actions` | 获取代码操作 | file_path, line, character | ⭐⭐ |
| **AST** | | | |
| `ast_grep_search` | AST搜索 | pattern, lang, paths | ⭐⭐⭐ |
| `ast_grep_replace` | AST替换 | pattern, rewrite, lang, dry_run | ⭐⭐ |
| **代码地图** | | | |
| `repo_map` | 生成代码地图 | repo_path, chat_files, mentioned_idents | ⭐⭐⭐⭐ |
| `get_repo_structure` | 获取仓库结构 | repo_path, max_depth | ⭐⭐⭐ |
| **项目文档** | | | |
| `discover_project_docs` | 发现项目文档 | repo_path, include_changelog | ⭐⭐⭐ |

---

## 🎯 按场景选择工具

### 场景1: 理解新项目
```
discover_project_docs → get_repo_structure → repo_map
```

### 场景2: 查找代码
```
text_search / ast_grep_search → read_file
```

### 场景3: 修改代码
```
read_file → search_replace → lsp_diagnostics → run_test
```

### 场景4: 重构代码
```
lsp_find_references → lsp_rename / ast_grep_replace → run_test
```

### 场景5: 调试错误
```
lsp_diagnostics → lsp_goto_definition → read_file → search_replace
```

---

## 💡 工具选择决策树

```
需要修改代码？
├─ 是 → 精确位置已知？
│  ├─ 是 → search_replace
│  └─ 否 → text_search → search_replace
└─ 否 → 需要查找信息？
   ├─ 是 → 查找什么？
   │  ├─ 文本 → text_search
   │  ├─ 代码模式 → ast_grep_search
   │  ├─ 符号定义 → lsp_goto_definition
   │  ├─ 符号引用 → lsp_find_references
   │  └─ 项目结构 → repo_map / get_repo_structure
   └─ 否 → 需要检查？
      ├─ 错误 → lsp_diagnostics
      ├─ 测试 → run_test
      └─ Git状态 → git_status
```

---

## ⚡ 性能提示

| 工具 | 首次运行 | 后续运行 | 优化建议 |
|------|---------|---------|---------|
| `repo_map` | 慢（解析所有文件） | 快（使用缓存） | 提供chat_files聚焦 |
| `lsp_*` | 慢（启动服务器） | 快（复用服务器） | 批量操作 |
| `ast_grep_*` | 慢（首次下载） | 快 | 限制搜索路径 |
| `text_search` | 快 | 快 | 使用file_pattern过滤 |

---

## ⚠️ 安全提示

| 工具 | 风险等级 | 注意事项 |
|------|---------|---------|
| `write_file` | 🔴 高 | 会覆盖现有文件 |
| `delete_file` | 🔴 高 | 不可逆操作 |
| `search_replace` | 🟡 中 | 直接修改文件 |
| `lsp_rename` | 🟡 中 | 修改多个文件 |
| `ast_grep_replace` | 🟡 中 | 批量修改 |
| `run_command` | 🟡 中 | 执行任意命令 |
| `read_file` | 🟢 低 | 只读操作 |
| `text_search` | 🟢 低 | 只读操作 |

---

## 📖 详细文档

完整的工具说明请查看：[TOOLS_REFERENCE.md](TOOLS_REFERENCE.md)
