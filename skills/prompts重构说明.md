# Skill 的 Prompt（.md）重构说明

> 基于对项目与编排器的理解，对各类 Skill 的 prompt 做了统一约定和修正，便于运行稳定、回答更智能。

---

## 1. 统一约定

### 路径规则（所有带工具的 Skill）
- **仓库/目录参数**：一律用 **`.`** 表示当前项目根（不要用 `./your-repo`、`/path/to/repo`）。
- **文件路径**：相对项目根，如 `backend/daoyoucode/agents/core/agent.py`。

### 工具名与注册表一致
- Prompt 里写到的工具名必须和 `daoyoucode` 注册表一致（见 `skills/SKILL与工具名说明.md`）。
- 错误示例：`get_diagnostics`、`find_references`、`get_symbols`、`parse_ast`、`find_function`、`grep_search`。
- 正确：`lsp_diagnostics`、`lsp_find_references`、`get_file_symbols`、`ast_grep_search`、`text_search`。

### 编排器与职责
- **chat-assistant**（react + MainAgent）：日常对话、了解项目、写/改代码、分析。强调「能做啥/了解项目」时先定性再展开、少罗列。
- **sisyphus-orchestrator**（multi_agent + sisyphus）：复杂任务分解与多 Agent 调度；简单寒暄/了解项目时简短回答即可。
- **oracle / librarian**（react，只读）：工具描述已改为注册表名称，并加路径规则。
- **programming / refactoring / testing**（simple）：在 prompt 开头加了「路径与工具」段，明确可用工具和 `.` 的用法。

---

## 2. 已改动的文件

| 文件 | 改动要点 |
|------|----------|
| `chat-assistant/prompts/chat_assistant.md` | **首轮**：首屏原则、了解项目先 repo_map 再 1～3 句、分层策略表工具名统一。**深度完善**：增加「一句话决策」表（了解项目/具体文件/找XX/其他）；「了解项目」正例/反例；项目理解工具按三层顺序排列并注明第 1/2/3 步；可用工具加注「以 Skill 配置为准」；示例1 明确错误/正确回答示例；重要原则首条为「了解项目=三层+短概括」；收尾「开始工作」四条中首条为三层调用+禁止罗列。 |
| `sisyphus-orchestrator/prompts/sisyphus.md` | 此前已含「了解项目」与寒暄的简短化要求，未改。 |
| `oracle/prompts/oracle.md` | 工具列表改为注册表名称：lsp_diagnostics、lsp_find_references、get_file_symbols、lsp_symbols、ast_grep_search；加路径规则。 |
| `librarian/prompts/librarian.md` | 同上，工具名与路径规则统一。 |
| `programming/prompts/programmer.md` | 开头增加「路径与工具」段，列出可用工具与 `.` 的用法。 |
| `refactoring/prompts/refactor.md` | 同上。 |
| `testing/prompts/test.md` | 同上，并强调 run_test/run_lint。 |
| `code-exploration/prompts/explore.md` | 增加路径规则与可用工具名说明。 |

---

## 3. 维护建议

- 新增或由 Kiro 生成 Skill 时：工具名对照 `SKILL与工具名说明.md`，prompt 里路径规则与上面一致。
- 若某 Skill 回答仍偏「机械罗列」：在该 Skill 的 prompt 顶部加「首屏原则」或「回答格式」约束（先定性、再要点、自然收尾）。
