# DaoyouCode 工具参考手册

## 工具总览

系统共有 **34个** 内置工具，分为8大类。

---

## 1. 文件操作工具（8个）

### read_file
- **功能**：读取单个文件内容
- **参数**：`file_path` (相对路径)
- **用途**：查看文件内容

### write_file
- **功能**：写入单个文件（支持流式显示）
- **参数**：`file_path`, `content`
- **用途**：创建或覆盖文件

### batch_read_files
- **功能**：批量读取多个文件
- **参数**：`file_paths` (列表)
- **用途**：一次性读取多个文件，提高效率

### batch_write_files
- **功能**：批量写入多个文件（支持流式显示）
- **参数**：`files` (列表，每项包含 path 和 content)
- **用途**：一次性写入多个文件

### list_files
- **功能**：列出目录中的文件
- **参数**：`directory`, `pattern` (可选)
- **用途**：浏览目录结构

### get_file_info
- **功能**：获取文件元信息
- **参数**：`file_path`
- **用途**：查看文件大小、修改时间等

### create_directory
- **功能**：创建目录
- **参数**：`directory_path`
- **用途**：创建新目录

### delete_file
- **功能**：删除文件或目录
- **参数**：`file_path`
- **用途**：删除不需要的文件

---

## 2. 搜索工具（3个）

### text_search
- **功能**：文本搜索（类似 ripgrep）
- **参数**：`query`, `file_pattern` (可选)
- **用途**：在代码中搜索关键词

### regex_search
- **功能**：正则表达式搜索
- **参数**：`pattern`, `file_pattern` (可选)
- **用途**：使用正则表达式搜索

### semantic_code_search
- **功能**：语义代码搜索（类似 Cursor @codebase）
- **参数**：`query`, `top_k`, `repo_path`
- **用途**：用自然语言描述搜索相关代码

---

## 3. 项目理解工具（3个）

### discover_project_docs
- **功能**：自动发现并读取项目文档
- **参数**：`repo_path`, `max_doc_length` (可选)
- **用途**：了解项目的 README、文档等

### get_repo_structure
- **功能**：获取仓库目录结构
- **参数**：`repo_path`, `max_depth` (可选)
- **用途**：查看项目的文件组织

### repo_map
- **功能**：生成代码仓库地图
- **参数**：`repo_path`, `chat_files` (可选)
- **用途**：查看项目的代码结构、类、函数等

---

## 4. 代码分析工具（3个）

### get_file_symbols
- **功能**：获取文件符号表（类、函数、方法等）
- **参数**：`file_path`
- **用途**：分析文件的代码结构

### ast_grep_search
- **功能**：AST 级别的代码搜索
- **参数**：`pattern`, `language`, `file_pattern` (可选)
- **用途**：基于语法树搜索代码模式

### ast_grep_replace
- **功能**：AST 级别的代码替换
- **参数**：`pattern`, `replacement`, `language`, `file_pattern` (可选)
- **用途**：基于语法树替换代码

---

## 5. 代码编辑工具（3个）

### search_replace
- **功能**：搜索替换编辑
- **参数**：`file_path`, `search`, `replace`
- **用途**：在文件中查找并替换内容

### apply_patch
- **功能**：应用 Unified Diff 补丁
- **参数**：`file_path`, `patch`
- **用途**：应用细粒度的代码变更

### intelligent_diff_edit
- **功能**：智能 Diff 编辑（支持流式显示）
- **参数**：`file_path`, `original_snippet`, `new_snippet`
- **用途**：智能地替换代码片段

---

## 6. Git 工具（4个）

### git_status
- **功能**：查看 Git 仓库状态
- **参数**：`repo_path`
- **用途**：查看未提交的变更

### git_diff
- **功能**：查看 Git 差异
- **参数**：`repo_path`, `file_path` (可选)
- **用途**：查看代码变更详情

### git_commit
- **功能**：Git 提交（占位符，待实现）
- **参数**：`repo_path`, `message`
- **用途**：提交代码变更

### git_log
- **功能**：查看 Git 日志（占位符，待实现）
- **参数**：`repo_path`, `max_count` (可选)
- **用途**：查看提交历史

---

## 7. LSP 工具（6个）

### lsp_diagnostics
- **功能**：获取诊断信息（错误、警告等）
- **参数**：`file_path`
- **用途**：检查代码问题

### lsp_goto_definition
- **功能**：跳转到定义
- **参数**：`file_path`, `line`, `character`
- **用途**：查找符号定义位置

### lsp_find_references
- **功能**：查找引用
- **参数**：`file_path`, `line`, `character`
- **用途**：查找符号被使用的地方

### lsp_symbols
- **功能**：获取符号列表
- **参数**：`file_path`
- **用途**：列出文件中的所有符号

### lsp_rename
- **功能**：重命名符号
- **参数**：`file_path`, `line`, `character`, `new_name`
- **用途**：安全地重命名变量、函数等

### lsp_code_actions
- **功能**：获取代码操作（快速修复等）
- **参数**：`file_path`, `line`, `character`
- **用途**：获取可用的代码修复建议

---

## 8. 命令执行工具（4个）

### run_command
- **功能**：运行 shell 命令
- **参数**：`command`, `cwd` (可选)
- **用途**：执行任意命令

### run_test
- **功能**：运行测试
- **参数**：`test_path` (可选), `test_name` (可选)
- **用途**：执行测试用例

### run_lint
- **功能**：运行 Lint 检查
- **参数**：`file_path` (可选)
- **用途**：检查代码风格和质量

### code_snippet_validation
- **功能**：验证代码片段
- **参数**：`code`, `language`
- **用途**：检查代码片段是否有语法错误

---

## 工具使用建议

### 了解项目的标准流程
1. `discover_project_docs` - 读取文档
2. `get_repo_structure` - 查看目录
3. `repo_map` - 查看代码地图

### 查找代码的推荐方式
1. 先用 `text_search` 或 `semantic_code_search` 找到文件
2. 再用 `read_file` 读取内容
3. 如需分析结构，用 `get_file_symbols`

### 修改代码的推荐流程
1. 用搜索工具找到目标文件
2. 用 `read_file` 读取当前内容
3. 用 `search_replace` 或 `intelligent_diff_edit` 修改
4. 用 `lsp_diagnostics` 或 `run_lint` 验证

### 批量操作的优势
- 使用 `batch_read_files` 代替多次 `read_file`
- 使用 `batch_write_files` 代替多次 `write_file`
- 可以显著提高效率，减少工具调用次数

---

## 路径规则

- **仓库路径**：始终使用 `.` 表示当前项目根目录
- **文件路径**：使用相对于项目根的相对路径，如 `backend/agent.py`
- **不要使用绝对路径**：如 `/home/user/project/file.py`

---

**工具总数**：34个
**最后更新**：2026-02-26
