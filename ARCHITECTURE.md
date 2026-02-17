# DaoyouCode 代码级架构一览

> 面向人类与 AI（Cursor / aider / DaoyouCode 内置 Agent）的**一页式**项目理解文档。用于在代码级快速建立整体心智模型。

---

## 1. 项目是什么（一句话）

**DaoyouCode** 是 CLI 优先的 AI 编程助手：用户通过命令行发起请求 → 由 **Skill** 决定用哪个编排器与哪些工具 → **编排器** 协调 **Agent** → **Agent** 调用 **工具** 与 **LLM** 完成代码理解、编辑、分析。核心实现为 **Python**，位于 `backend/`。

---

## 2. 主数据流（必记）

```
用户输入
  → CLI (backend/cli/ 或 backend/daoyoucode.py)
  → Skill 配置 (skills/<skill>/skill.yaml：orchestrator、agent、tools、llm)
  → 编排器 (backend/daoyoucode/agents/orchestrators/)
  → Agent (backend/daoyoucode/agents/core/agent.py 等)
  → 工具 (backend/daoyoucode/agents/tools/) + LLM (backend/daoyoucode/agents/llm/)
  → 结果回显
```

- **入口**：`backend/daoyoucode.py` 或 `backend/cli/app.py`；常用命令 `chat` / `edit` 在 `backend/cli/commands/`。
- **配置驱动**：行为由 `skills/*/skill.yaml` 决定（哪个编排器、哪些 Agent、哪些工具、哪个模型），不是写死在代码里。

---

## 3. 关键目录（代码级）

| 目录 | 含义 |
|------|------|
| `backend/daoyoucode/agents/` | 核心：agent 基类、编排器、工具注册、LLM 客户端、记忆与上下文。 |
| `backend/daoyoucode/agents/core/` | Agent、Skill 加载、编排器接口、上下文管理、路由/规划。 |
| `backend/daoyoucode/agents/orchestrators/` | 编排器实现：react、simple、multi_agent 等。 |
| `backend/daoyoucode/agents/tools/` | 所有工具实现：repo_map、read_file、text_search、LSP、AST、Git 等。 |
| `backend/daoyoucode/agents/llm/` | LLM 统一客户端、多厂商、配置加载。 |
| `backend/daoyoucode/agents/memory/` | 会话历史、长期记忆、用户画像。 |
| `backend/cli/` | 命令行入口与子命令：chat、edit、doctor、skills 等。 |
| `skills/` | 各 Skill 的 skill.yaml 与 prompts；CLI 的 `--skill` 对应此处 name。 |
| `config/` | 全局配置示例（如 llm_config.yaml、agent_router_config.yaml）。 |

---

## 4. 核心概念对应关系

- **Skill**：一份 YAML（名称、编排器、Agent 列表、工具列表、LLM 配置）。CLI 通过 `--skill <name>` 指定。
- **编排器**：决定多 Agent 如何协作（顺序/并行/辩论/主从），以及单 Agent 的 ReAct/Simple 循环。
- **Agent**：执行单位，持有一组工具与 LLM，按编排器调度执行。
- **工具**：在 `agents/tools/` 注册；Skill 的 `tools` 列表决定当前会话可用哪些。路径类参数统一用 **`.`** 表示项目根。

---

## 5. 如何“快速理解整个项目”（Cursor vs aider vs DaoyouCode）

### Cursor

- **方式**：对工作区做**语义索引**（文件扫描 → AST 分块 → 向量嵌入 → 本地向量库）。你通过 **@codebase** / @文件 把相关片段注入上下文；没有单独的“项目介绍文档”步骤，理解依赖检索到的代码块。
- **建议**：本仓库中优先读 **ARCHITECTURE.md**（本文）和 **backend/README.md**，再用 @ 引用具体目录（如 `backend/daoyoucode/agents`）可更快建立整体观。

### aider

- **方式**：维护一份 **repo map**（tree-sitter 等提取的符号/签名），在每次请求时按 token 预算把“最相关”的 map 片段发给模型；配合用户把需要编辑的文件加入会话。
- **特点**：单 Coder、单轮流、repo map 即主要“项目理解”载体；无多 Agent/编排层。

### DaoyouCode（本仓库）

- **方式**：**三层理解**，由 Agent 在“了解项目”类请求时按顺序调用工具：
  1. **discover_project_docs(repo_path=".")** — 读 README、ARCHITECTURE 等文档（即本文会被读）；
  2. **get_repo_structure(repo_path=".")** — 看目录树；
  3. **repo_map(repo_path=".")** — 看代码地图（符号/结构摘要）。
- **特点**：文档 + 结构 + 代码地图 组合，再让 LLM 用 1～3 句话概括；避免只靠单层（如仅 repo_map）导致“罗列文件/类名”式的浅理解。

### 对比小结

| 维度 | Cursor | aider | DaoyouCode |
|------|--------|-------|------------|
| 项目理解载体 | 向量检索到的代码块 | repo map（符号/签名） | 文档 + 目录树 + repo_map |
| 是否显式读 README/架构 | 依赖是否 @ 引用 | 无专门步骤 | 有（discover_project_docs） |
| 建议“快速理解”用法 | 先读 ARCHITECTURE.md + backend/README，再 @ 目录 | 加文件 + 依赖 repo map | 直接问“了解下项目”，Agent 跑三层工具 |

---

## 6. 基于代码级快速理解的本仓库实践

1. **人类 / Cursor**：先读本文 + `backend/README.md`，再按需用 @ 指向 `backend/daoyoucode/agents`、`backend/cli`、`skills`。
2. **DaoyouCode 内置 Agent**：用户说“了解项目/看看项目”时，按 prompt 依次调用 `discover_project_docs` → `get_repo_structure` → `repo_map`，再 1～3 句概括；本文会被 `discover_project_docs` 发现并注入上下文。
3. **aider 用户**：若用本仓库做参考，可把 `ARCHITECTURE.md` 和 `backend/README.md` 加入会话，等价于“先看文档再看代码”。

---

## 7. 延伸阅读

- **backend/README.md** — 后端文档导航、CLI 用法、Skill/编排器/Agent 概念。
- **backend/CLI命令参考.md** — 完整命令与示例。
- **backend/TOOLS工具参考.md** — 工具列表与组合方式。
- **skills/SKILL与工具名说明.md** — Skill 与工具名约定。
- **[docs/CODEBASE_UNDERSTANDING_DESIGN.md](docs/CODEBASE_UNDERSTANDING_DESIGN.md)** — Cursor / aider / DaoyouCode 对比，以及如何吸收「指向性」与「按问检索」做到 Cursor 水平。

---

*本文档旨在被 Cursor 索引、被 discover_project_docs 读取，并与 README 一起构成“代码级快速理解”的入口。*
