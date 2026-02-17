# 代码库理解设计：Cursor / aider / DaoyouCode 对比与可吸收方案

> 回答三个问题：哪个好？DaoyouCode 能从 Cursor/aider 吸收什么？文档 + 目录树 + repo_map + tree-sitter 能否做到 Cursor 水平？

---

## 1. 三者对比（谁好、好在哪）

| 维度 | Cursor | aider | DaoyouCode（当前） |
|------|--------|-------|---------------------|
| **理解载体** | 代码块向量索引 + 按问检索 | 单一大 repo map（符号/签名） | 文档 + 目录树 + repo_map（三层） |
| **指向性** | 强：@file / @folder / @codebase 显式注入 | 弱：用户把文件加入会话 | 有但弱：initial_files / chat_files 靠 prompt 提示模型用 |
| **是否按「当前问题」检索** | 是：query → 向量相似度 → 注入相关代码块 | 否：整份 map 或按 token 截断 | 否：先三层固定内容再总结 |
| **代码解析** | AST 分块 + 向量化 | tree-sitter 符号/签名 | tree-sitter（grep_ast）+ PageRank |
| **树/结构** | 隐含在索引与 @ 中 | 无单独目录树步骤 | 有：get_repo_structure |
| **文档** | 需用户 @ 文档 | 无专门步骤 | 有：discover_project_docs 先读 README/ARCHITECTURE |

**结论（哪个好）**：

- **Cursor**：指向性最好、按问检索最准，适合「我正看这几处，你只关心这些」；依赖本地索引与算力。
- **aider**：实现简单、单 repo map 稳定，适合「整仓感知 + 编辑」；没有「按问题找代码」。
- **DaoyouCode**：三层（文档→结构→代码）全局观最好，多 Agent/多编排可扩展；缺「按问检索」和「强指向性」。

没有绝对谁更好，而是场景不同：**Cursor 偏「聚焦当前任务」**，**aider 偏「整仓 + 编辑」**，**DaoyouCode 偏「先建立全局再动手」**。要接近 Cursor 的体验，需要吸收其**指向性**和**按问检索**。

---

## 2. DaoyouCode 当前实现（已有 / 缺口）

### 已有能力

- **tree-sitter**：`repomap_tools.py` 已用 **grep_ast**（tree-sitter-language-pack / tree-sitter-languages）解析多语言，提取定义/引用，建引用图，PageRank 排序；与 aider 的 repo map 思路一致且已落地。
- **三层理解**：`discover_project_docs`（README、ARCHITECTURE 等）→ `get_repo_structure` → `repo_map`，顺序固定、可配置。
- **弱指向**：`initial_files`（CLI/IDE 传入）、repo_map 的 `chat_files` / `mentioned_idents` 权重；prompt 里写「打开的文件优先」「可作 chat_files」——但未强制绑定，依赖模型自己传。

### 缺口（相对 Cursor）

1. **按问检索代码块**：没有「把代码库 chunk → embed → 存向量库 → 用户/Agent 提问时取 top-k 注入」。现有 `VectorRetriever` 只用于**对话历史**语义检索，且默认关闭。
2. **强指向性**：没有像 Cursor 的 @ 那样，显式、可配置的「焦点文件/目录」协议；`initial_files` 未自动注入到 repo_map 或首轮 context，效果依赖模型是否记得用。

---

## 3. 可吸收的设计（Cursor + aider）

### 3.1 吸收 Cursor 的「指向性」

**思路**：把「用户/IDE 指定的焦点」变成一等公民，并自动参与代码库理解。

- **统一焦点上下文**：在 context 里明确 `focus_files` / `focus_dirs`（可由 `initial_files` 与未来「@path」解析得到）。在 prompt 中固定一句：「当前焦点文件/目录：…，调用 repo_map 时请将 focus_files 作为 chat_files 传入。」
- **自动注入 repo_map**（推荐）：若 `initial_files` 非空，在首轮或「了解项目」时，由执行层**自动**调一次 `repo_map(repo_path=".", chat_files=initial_files)`，把结果注入上下文，模型无需再猜；或由编排器在调用 Agent 前预填「已根据焦点文件生成 repo_map 摘要」。
- **未来扩展**：支持用户输入中的 `@path` 或 CLI 的 `--focus`，写入 `focus_files`，与上面同一套逻辑。

这样 DaoyouCode 就具备「指向性」：指定了文件/目录，就一定会被优先用于 repo_map 和上下文。

### 3.2 吸收 Cursor 的「按问检索」

**思路**：在「回答具体问题」时，不只靠三层固定内容，而是多一步「按问题检索相关代码块」。

- **代码库向量索引（可选功能）**：
  - 对仓库做 **chunk**（按文件/函数/类，与 Cursor 类似），用现有或新 embedding 模型生成向量，写入本地向量库（如 FAISS、Chroma、本地 SQLite+向量）。
  - 增量更新：用 mtime 或 Merkle 思路，只对变更文件重算 chunk+embed，与 repo_map 的缓存策略可复用思路。
- **检索流程**：用户/Agent 发出问题 → 问题文本 embed → 在代码向量库中取 top-k 代码块 → 与「文档 + 目录树 + repo_map」一起注入 LLM。这样就有「和 Cursor 类似的按问检索」。
- **实现**：可复用 `VectorRetriever` 的 encode/相似度，数据源从「对话历史」改为「代码块」；或单独建 `CodebaseVectorIndex`，与记忆模块解耦。

先做「指向性 + 自动注入 repo_map」，再做「代码库向量检索」，性价比更高。

### 3.3 继续用好 tree-sitter 与三层

- **tree-sitter**：已在 repo_map 中使用，保持即可；若后续有「只取某目录」的 subtree 需求，在 repo_map 的扫描阶段按 `focus_dirs` 过滤即可。
- **文档 + 目录树 + repo_map**：保持为默认「了解项目」流程；若启用代码库向量检索，可在「回答具体问题」时作为**第四步**：query → 检索代码块 → 与三层结果一起给模型。这样既有 Cursor 的「按问聚焦」，又保留 DaoyouCode 的「全局观」。

---

## 4. 能否做到和 Cursor 一样水平？

- **仅靠「文档 + 目录树 + repo_map」**：已经能接近 **aider** 的「整仓感知」水平，且多出文档与目录树两层；tree-sitter 在 repo_map 里已用，和 aider 同级。
- **加上「指向性」与「自动注入 repo_map」**：能明显接近 Cursor 的「指向性」体验——用户/IDE 指定了文件或目录，就会优先被纳入代码地图与上下文，而不是依赖模型自己传参。
- **再加上「代码库向量检索」**：就能在「按当前问题检索相关代码」这一点上对齐 Cursor 的能力，整体达到「Cursor 水平」的代码库理解：既有全局（三层），又有聚焦（指向 + 按问检索）。

实施顺序与当前实现状态：

1. **短期（已实现）**：**指向性**——executor 在存在 `initial_files` 时预调 `repo_map(chat_files=initial_files)`，结果写入 `context['focus_repo_map_content']`，并在 chat-assistant prompt 中展示；同时 prompt 要求「焦点文件必须作为 chat_files 传入」。
2. **中期（已实现）**：**代码库向量索引 + 按问检索**——`memory/codebase_index.py` 提供 chunk、embed（可选 sentence-transformers）、持久化与 `search(query, top_k)`；工具 `semantic_code_search` 供 Agent 显式调用；chat-assistant 启用该工具且每轮自动将 `semantic_code_search(user_input)` 结果注入 `context['semantic_code_chunks']`，实现 Cursor 同级的「按问注入相关代码」。
3. **长期**：增量索引（按 mtime 只重算变更文件）、.cursorignore 风格排除、与 IDE 的 @path 协议等，按需迭代。

---

## 5. 小结

| 问题 | 结论 |
|------|------|
| 哪个好？ | Cursor 指向性+按问检索强；aider 简单稳；DaoyouCode 三层全局观好。各有优劣，按场景选。 |
| DaoyouCode 能吸收什么？ | **Cursor**：指向性（@ → focus_files + 自动注入 repo_map）、按问检索（代码向量索引）。**aider**：已有 tree-sitter + repo map，可继续借鉴 token 预算与排序策略。 |
| 文档+树+repo_map+tree-sitter 能否到 Cursor 水平？ | **能**：在保留三层的的基础上，加上「指向性」和「代码库按问检索」，即可达到与 Cursor 同等级别的代码库理解能力。 |

---

## 6. 全流程对比：检索 → 理解 → 修改 → 验证（还能从 Cursor 吸收什么）

### 6.1 流程分段对比

| 阶段 | Cursor | DaoyouCode（当前） | 可吸收点 |
|------|--------|---------------------|----------|
| **检索** | 向量索引 + @ 显式注入；.cursorignore 控制范围 | 三层（文档/结构/repo_map）+ 指向性预取 + 按问 semantic_code_search | 已对齐；可加 .cursorignore 风格排除（见下） |
| **理解** | 注入的代码块 + 对话历史，模型直接读 | 同上 + 焦点 repo_map + semantic_code_chunks 预注入 | 已对齐 |
| **修改** | Chat 内 Apply：整文件重写或 diff，用户点「应用」才写盘；Accept/Reject 单块 | Agent 直接 search_replace / write_file / apply_patch 写盘；edit 命令一次跑完 | Cursor 是「先展示再决定」；我们是「先改再确认」——可做：edit 若用户拒绝则 git checkout 回滚 |
| **验证** | 无强制；用户自行看 diff / 跑测试 | chat-assistant prompt 要求「修改后 lsp_diagnostics」；edit-single **未**配 run_lint/lsp_diagnostics | 在 edit-single 中加上修改后验证（见下） |
| **UX** | IDE 内嵌、diff 高亮、Accept/Reject 按钮 | CLI：文字输出、可选 confirm；无 diff 回滚 | 形态不同；CLI 可做：edit 后输出「已修改文件」+ 建议 `git diff`，拒绝时回滚 |

### 6.2 还能从 Cursor 吸收的具体点

1. **修改后必验证**：edit-single 当前无 run_lint/lsp_diagnostics，模型可能改完不检查。→ 为 edit-single 增加工具 run_lint、lsp_diagnostics，并在 prompt 中写「修改后必须调用 lsp_diagnostics 或 run_lint 验证，若有错误需修复」。
2. **拒绝即回滚**：edit 命令在用户选择「不应用」时，当前仅提示取消，文件已被 Agent 改过。→ 若用户拒绝，对本次修改过的文件执行 `git checkout -- <files>`（或记录修改前版本并还原），实现「先改再确认、拒绝则回滚」。
3. **.cursorignore 风格排除**：代码库索引/ repo_map 扫描时忽略 node_modules、.git 等。→ 在 codebase_index（及可选 repo_map）中支持读取 `.cursorignore` 或沿用 .gitignore，排除列表与 Cursor 一致，减少噪音、加快索引。
4. **Apply 前预览**（可选）：Cursor 是「生成 diff → 用户 Accept 再写盘」。我们 CLI 可做成「Agent 先只返回 diff，由 CLI 用 patch 应用」——实现复杂且与当前「工具直接写盘」不一致，可作为后续选项，不列入当前必做。

### 6.3 成熟度概览

| 维度 | 成熟度 | 说明 |
|------|--------|------|
| **检索** | 高 | 三层 + 指向性 + 按问检索已实现；索引可持久、可关键词回退；缺 .cursorignore 与增量更新。 |
| **理解** | 高 | 文档/结构/repo_map + 焦点预取 + semantic_code_chunks 预注入；与 Cursor 心智模型对齐。 |
| **修改** | 中高 | search_replace / write_file / apply_patch 齐全；edit 走 Skill、一次跑完；缺「拒绝即回滚」与强制验证。 |
| **验证** | 中 | chat-assistant 有「修改后 lsp_diagnostics」要求；edit-single 未配验证工具与 prompt 约束。 |
| **整体** | 中高 | 从检索到修改的链路完整，与 Cursor 在「理解+聚焦」上已同级；编辑侧补上「验证」与「拒绝回滚」即可视为与 Cursor 同成熟度。 |

---

*本文档与 [ARCHITECTURE.md](../ARCHITECTURE.md) 配套，作为「代码库理解」设计与发展参考。*
