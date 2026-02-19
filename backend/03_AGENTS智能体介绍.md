# Agent智能体介绍

> DaoyouCode 10个内置Agent完整介绍

---

## Agent总览

| Agent | 类型 | 工具数 | 模型 | 特点 |
|-------|------|--------|------|------|
| sisyphus | 编排 | 4 | qwen-max | 任务分解、Agent调度 |
| oracle | 咨询 | 10 | qwen-max | 架构分析、技术建议（只读） |
| librarian | 搜索 | 8 | qwen-max | 文档搜索、代码查找（只读） |
| programmer | 编程 | 11 | qwen-coder-plus | 代码编写、功能实现 |
| refactor_master | 重构 | 13 | qwen-coder-plus | 代码重构、优化 |
| test_expert | 测试 | 10 | deepseek-coder | 测试编写、修复 |
| code_analyzer | 分析 | 10 | qwen-max | 架构分析、代码审查 |
| code_explorer | 探索 | 8 | qwen-plus | 代码库搜索、探索 |
| translator | 翻译 | 6 | qwen-max | 专业翻译服务 |
| MainAgent | 主对话 | 0 | qwen-max | 日常对话、代码咨询 |

---

## 核心Agent详解

### 1. Sisyphus - 主编排Agent

**职责**：
- 分析用户请求
- 分解复杂任务
- 选择合适的专业Agent
- 验证执行结果
- 聚合最终答案

**特点**：
- Todo驱动工作流
- 智能Agent选择
- 结果验证
- 只使用4个基础工具（快速探索）

**工具**（4个）：
- repo_map - 项目理解
- get_repo_structure - 项目理解
- text_search - 搜索
- read_file - 文件操作

**使用场景**：
- 复杂任务（重构+测试）
- 多文件修改
- 需要多个专业Agent协作

**配置**：
- 模型：qwen-max（最强模型）
- 温度：0.1（低温度，更准确）
- Prompt：skills/sisyphus-orchestrator/prompts/sisyphus.md

**使用方式**：
```bash
python backend/daoyoucode.py chat --skill sisyphus-orchestrator
```

---

### 2. Oracle - 高IQ咨询Agent

**职责**：
- 架构分析和决策
- 代码审查和建议
- 性能分析
- 安全审查
- 技术咨询

**特点**：
- 只读权限（不修改代码）
- 使用最强模型
- 专注于高质量分析
- 适合复杂决策

**工具**（10个）：
- repo_map - 项目理解
- get_repo_structure - 项目理解
- read_file - 文件操作
- list_files - 文件操作
- text_search - 搜索
- regex_search - 搜索
- lsp_diagnostics - LSP
- lsp_goto_definition - LSP
- lsp_symbols - LSP
- discover_project_docs - 项目文档

**使用场景**：
- ✅ 架构决策
- ✅ 完成重要工作后的自我审查
- ✅ 2次以上修复失败后
- ✅ 不熟悉的代码模式
- ✅ 安全/性能问题

**避免使用**：
- ❌ 简单文件操作
- ❌ 第一次尝试修复
- ❌ 从已读代码可以回答的问题
- ❌ 琐碎决策（变量命名、格式化）

**配置**：
- 模型：qwen-max
- 温度：0.1
- Prompt：skills/oracle/prompts/oracle.md

**使用方式**：
```bash
python backend/daoyoucode.py chat --skill oracle
```

---

### 3. Librarian - 文档搜索Agent

**职责**：
- 搜索项目文档
- 搜索代码实现
- 查找相关示例
- 提供参考资料

**特点**：
- 只读权限
- 专注于搜索和检索
- 快速定位信息
- 可以集成外部搜索（websearch MCP）

**工具**（8个）：
- repo_map - 项目理解
- get_repo_structure - 项目理解
- read_file - 文件操作
- text_search - 搜索
- regex_search - 搜索
- ast_grep_search - AST搜索
- lsp_symbols - LSP
- discover_project_docs - 项目文档

**使用场景**：
- 查找文档
- 搜索代码示例
- 了解最佳实践
- 学习新技术

**配置**：
- 模型：qwen-max
- 温度：0.1
- Prompt：skills/librarian/prompts/librarian.md

**使用方式**：
```bash
python backend/daoyoucode.py chat --skill librarian
```

---

### 4. Programmer - 编程专家

**职责**：
- 代码编写
- 功能实现
- Bug修复
- 代码优化

**工具**（11个）：
- read_file - 文件操作
- write_file - 文件操作
- list_files - 文件操作
- text_search - 搜索
- search_replace - 代码编辑
- lsp_diagnostics - LSP
- lsp_goto_definition - LSP
- lsp_find_references - LSP
- repo_map - 项目理解
- run_test - 命令执行
- git_status - Git

**使用场景**：
- 编写新功能
- 修复Bug
- 实现需求

**配置**：
- 模型：qwen-coder-plus
- 温度：0.1
- Prompt：skills/programming/prompts/programmer.md

**使用方式**：
```bash
python backend/daoyoucode.py chat --skill programming
```

---

### 5. RefactorMaster - 重构专家

**职责**：
- 代码重构
- 代码优化
- 架构改进
- 技术债务清理

**特点**：
- 安全渐进式重构
- 保持功能不变
- 提高代码质量

**工具**（13个）：
- read_file - 文件操作
- write_file - 文件操作
- list_files - 文件操作
- text_search - 搜索
- search_replace - 代码编辑
- lsp_diagnostics - LSP
- lsp_goto_definition - LSP
- lsp_find_references - LSP
- lsp_rename - LSP
- ast_grep_search - AST
- ast_grep_replace - AST
- repo_map - 项目理解
- run_test - 命令执行

**使用场景**：
- 代码重构
- 提取函数/类
- 重命名符号
- 优化结构

**配置**：
- 模型：qwen-coder-plus
- 温度：0.2
- Prompt：skills/refactoring/prompts/refactor.md

**使用方式**：
```bash
python backend/daoyoucode.py chat --skill refactoring
```

---

### 6. TestExpert - 测试专家

**职责**：
- 测试编写
- 测试修复
- 测试策略
- TDD工作流

**工具**（10个）：
- read_file - 文件操作
- write_file - 文件操作
- list_files - 文件操作
- text_search - 搜索
- search_replace - 代码编辑
- lsp_diagnostics - LSP
- lsp_goto_definition - LSP
- repo_map - 项目理解
- run_test - 命令执行
- git_status - Git

**使用场景**：
- 编写单元测试
- 修复失败的测试
- 提高测试覆盖率
- TDD开发

**配置**：
- 模型：deepseek-coder
- 温度：0.3
- Prompt：skills/testing/prompts/test.md

**使用方式**：
```bash
python backend/daoyoucode.py chat --skill testing
```

---

## 辅助Agent

### 7. CodeAnalyzer - 代码分析Agent

**职责**：
- 架构分析
- 代码审查
- 技术咨询

**工具**（10个）：
- repo_map、get_repo_structure、read_file、list_files
- text_search、regex_search
- lsp_diagnostics、lsp_goto_definition、lsp_symbols
- discover_project_docs

**配置**：
- 模型：qwen-max
- 温度：0.1

---

### 8. CodeExplorer - 代码探索Agent

**职责**：
- 代码库搜索
- 代码探索
- 查找实现

**工具**（8个）：
- repo_map、get_repo_structure、read_file
- text_search、regex_search、ast_grep_search
- lsp_symbols、discover_project_docs

**配置**：
- 模型：qwen-plus
- 温度：0.1

---

### 9. Translator - 翻译Agent

**职责**：
- 专业翻译
- 文档翻译
- 代码注释翻译

**工具**（6个）：
- read_file、write_file、list_files
- text_search、search_replace、repo_map

**配置**：
- 模型：qwen-max
- 温度：0.3

---

### 10. MainAgent - 主对话Agent

**职责**：
- 日常对话
- 代码咨询
- 问题解答

**工具**（0个）：
- 不使用工具，纯对话

**配置**：
- 模型：qwen-max
- 温度：0.7

---

## Agent选择指南

### 按任务类型选择

| 任务类型 | 推荐Agent | 原因 |
|---------|----------|------|
| 复杂任务 | sisyphus | 智能分解和调度 |
| 架构决策 | oracle | 高质量分析（只读） |
| 文档搜索 | librarian | 专注搜索（只读） |
| 编写代码 | programmer | 代码编写专家 |
| 代码重构 | refactor_master | 安全重构 |
| 编写测试 | test_expert | 测试专家 |
| 代码分析 | code_analyzer | 架构分析 |
| 代码探索 | code_explorer | 搜索探索 |
| 翻译 | translator | 专业翻译 |
| 日常对话 | MainAgent | 通用对话 |

### 按权限选择

| 权限 | Agent | 说明 |
|------|-------|------|
| 只读 | oracle, librarian | 不修改代码，只分析 |
| 读写 | programmer, refactor_master, test_expert | 可以修改代码 |
| 编排 | sisyphus | 调度其他Agent |

### 按模型选择

| 模型 | Agent | 特点 |
|------|-------|------|
| qwen-max | sisyphus, oracle, librarian, code_analyzer, translator, MainAgent | 最强模型，适合复杂任务 |
| qwen-coder-plus | programmer, refactor_master | 代码专用模型 |
| deepseek-coder | test_expert | 测试专用模型 |
| qwen-plus | code_explorer | 通用模型 |

---

## Agent协作模式

### 模式1: Sisyphus编排
```
用户请求 → Sisyphus分解任务 → 调度专业Agent → 聚合结果
```

### 模式2: Oracle咨询
```
用户请求 → Oracle分析 → 提供建议（不修改代码）
```

### 模式3: 专业Agent直接执行
```
用户请求 → Programmer/RefactorMaster/TestExpert → 直接执行
```

---

## 相关文档

- [CLI命令参考.md](./CLI命令参考.md) - CLI使用指南
- [ORCHESTRATORS.md](./ORCHESTRATORS.md) - 编排器详细介绍
- [TOOLS工具参考.md](./TOOLS工具参考.md) - 工具参考手册
