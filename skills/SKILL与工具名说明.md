# Skill 与工具名说明（避免运行不稳定）

> 若 Skill 由 Kiro 等自动生成，请按本文核对：**技能 name 与 CLI 一致**、**tools 仅使用注册表真实名称**。

---

## 1. Skill 名称与 CLI 对齐

- CLI 默认 `--skill chat-assistant`，对应 skill 的 **name 必须为 `chat-assistant`**（不能是 `chat_assistant`），否则 `get_skill("chat-assistant")` 会找不到。
- 其他技能名建议与 `daoyoucode skills` 列出的一致（小写 + 连字符，如 `code-exploration`、`sisyphus-orchestrator`）。

---

## 2. 工具名必须与注册表一致

Skill 的 `tools:` 里**只能写当前已注册的工具名**。写错会导致 `Tool not found` 或该工具被静默忽略。

### 当前可用工具名（与 `daoyoucode` 注册表一致）

| 类别     | 工具名 |
|----------|--------|
| 文件     | `read_file`, `write_file`, `list_files`, `get_file_info`, `create_directory`, `delete_file` |
| 搜索     | `text_search`, `regex_search` |
| Git      | `git_status`, `git_diff`, `git_commit`, `git_log` |
| 命令     | `run_command`, `run_test`, `run_lint` |
| 编辑     | `search_replace`, `apply_patch` |
| 仓库/地图 | `repo_map`, `get_repo_structure`, `get_file_symbols` |
| 项目文档 | `discover_project_docs` |
| LSP      | `lsp_diagnostics`, `lsp_goto_definition`, `lsp_find_references`, `lsp_symbols`, `lsp_rename`, `lsp_code_actions` |
| AST      | `ast_grep_search`, `ast_grep_replace` |

### 常见错误映射（勿在 YAML 中使用左侧）

| 错误名（勿用） | 应改为 |
|----------------|--------|
| `grep_search`  | `text_search` |
| `find_function` / `find_class` / `find_imports` | `text_search`, `get_file_symbols` |
| `get_diagnostics` | `lsp_diagnostics` |
| `find_references` | `lsp_find_references` |
| `get_symbols`     | `get_file_symbols` 或 `lsp_symbols` |
| `parse_ast`       | `ast_grep_search` |
| `list_directory`  | `list_files` |

---

## 3. 运行期保护

编排器（react、simple、multi_agent）在传入 Agent 前会调用 **`filter_tool_names(skill.tools)`**：只保留已在注册表中的工具名，不存在的会**打 warning 并忽略**。这样即使 YAML 里多写了错误名称，也不会再报 `Tool not found`，但建议直接修正 YAML，使配置与本文一致。

---

## 4. Agent 名称

Skill 的 `agent:` / `agents:` 必须与内置 Agent **注册名**一致，例如：

- `MainAgent`, `programmer`, `test_expert`, `refactor_master`, `code_explorer`, `code_analyzer`
- `translator`, `sisyphus`, `oracle`, `librarian`

可用 `daoyoucode agent` 查看完整列表。
