# DaoyouCode

<div align="center">

**Next-Generation AI Programming Assistant - Multi-Agent Collaboration + Intelligent Orchestration**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-active-success.svg)]()

[English](README.en.md) • [中文文档](README.md)

</div>

---

## 📖 Overview

**DaoyouCode** is a next-generation AI programming assistant based on multi-agent collaboration architecture, featuring intelligent orchestration systems, comprehensive toolchains, and deep code understanding capabilities to provide developers with powerful support for code analysis, writing, and refactoring.

### ✨ Key Features

- 🤖 **Multi-Agent Collaboration** - 6 specialized agents (Code Analysis, Programming, Refactoring, Testing, etc.) working together intelligently
- 🎯 **Intelligent Orchestration** - 7 orchestration strategies (ReAct, Multi-Agent, Parallel, etc.) automatically selecting optimal solutions
- 🛠️ **Complete Toolchain** - 34+ professional tools with deep LSP/AST integration and Git operations support
- 🧠 **Smart Memory System** - Conversation history, long-term memory, user profiles, and intelligent context loading
- 🌐 **Chinese LLM Optimized** - Deep support for Qwen and DeepSeek with multi-key rotation
- 📝 **Skill System** - 14+ preset skills, flexible configuration, and extensible

### 🎯 Technical Highlights

**Multi-Agent Collaboration Architecture**
- **Sisyphus Orchestrator** - Main agent responsible for task understanding, expert scheduling, and result synthesis
- **Code Analyzer** - Architecture analysis, code review, technology selection
- **Programmer** - Code writing, bug fixing, feature implementation
- **Refactor Master** - Code refactoring, performance optimization, design improvement
- **Test Expert** - Test writing, test fixing, quality assurance
- **4 Collaboration Modes** - Sequential, Parallel, Debate, Main-with-Helpers

**Deep Code Understanding**
- **LSP Integration** - Type information, reference relationships, code diagnostics, intelligent renaming
- **AST Analysis** - Syntax tree parsing, structured code understanding
- **Semantic Search** - Vector-based code retrieval, understanding code intent
- **Smart Code Map** - Automatic project structure overview generation

**Intelligent Orchestration System**
- **ReAct Mode** - Reasoning-action loop supporting complex tool invocations
- **Multi-Agent Mode** - Multi-expert parallel analysis and comprehensive decision-making
- **Conditional Mode** - Conditional branching and dynamic routing
- **Workflow Mode** - Workflow orchestration and complex task decomposition

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/daoyou-zhang/daoyoucode.git
cd daoyoucode

# Install dependencies
cd backend
pip install -e .
```

### Configuration

Edit `backend/config/llm_config.yaml`:

```yaml
providers:
  qwen:
    api_key: ["your-api-key-here"]  # Replace with your API Key
    enabled: true

default:
  model: "qwen-max"
  temperature: 0.7
  max_tokens: 4000
  timeout: 1800
```

### Usage

```bash
# Interactive chat (default chat-assistant)
daoyoucode chat

# Use multi-agent orchestration (Sisyphus)
daoyoucode chat --skill sisyphus-orchestrator

# Use specific expert
daoyoucode chat --skill programming      # Programming expert
daoyoucode chat --skill code-analysis    # Code analysis
daoyoucode chat --skill refactoring      # Refactoring expert

# Single edit
daoyoucode edit "change timeout to 60"

# List all skills
daoyoucode skills list

# Health check
daoyoucode doctor
```

## 🎓 Usage Examples

### Example 1: Multi-Agent Collaborative Code Analysis

```bash
daoyoucode chat --skill sisyphus-orchestrator

You > Analyze the design of backend/daoyoucode/agents/core/agent.py

AI will automatically:
1. Code Analyzer analyzes architecture design
2. Programmer evaluates code quality
3. Sisyphus synthesizes both experts' opinions
4. Provides complete analysis report and improvement suggestions
```

### Example 2: Intelligent Code Refactoring

```bash
You > Refactor agent.py to improve maintainability

AI will:
1. Code Analyzer identifies excessive responsibilities
2. Refactor Master proposes splitting plan
3. Programmer provides specific implementation steps
4. Sisyphus integrates the plan and provides execution plan
```

### Example 3: Bug Fixing

```bash
You > Fix the login functionality bug

AI will:
1. Code Analyzer locates problem code
2. Programmer provides fix solution
3. Test Expert suggests test cases
4. Sisyphus makes comprehensive decision and executes fix
```

### Example 4: Understanding Project

```bash
You > Understand this project

AI will automatically:
1. Call discover_project_docs to read README
2. Call get_repo_structure to view directory structure
3. Call repo_map to generate code map
4. Summarize project features concisely
```

## 🏗️ Project Structure

```
daoyoucode/
├── backend/                    # Python core implementation
│   ├── daoyoucode.py          # CLI entry point
│   ├── cli/                   # CLI commands
│   ├── daoyoucode/
│   │   └── agents/
│   │       ├── core/          # Agent core (execution, Prompt, Skill)
│   │       ├── orchestrators/ # Orchestrators (Simple, ReAct, Multi-Agent, etc.)
│   │       ├── tools/         # Tool system (34+ tools)
│   │       ├── llm/           # LLM client
│   │       ├── memory/        # Memory system
│   │       └── middleware/    # Middleware
│   ├── config/                # Configuration files
│   └── tests/                 # Tests
├── skills/                    # Skill configurations and Prompts
│   ├── sisyphus-orchestrator/ # Multi-agent orchestration
│   ├── chat-assistant/        # Interactive chat
│   ├── programming/           # Programming expert
│   ├── code-analysis/         # Code analysis
│   ├── refactoring/           # Refactoring expert
│   ├── testing/               # Testing expert
│   └── ...
└── docs/                      # Documentation
```

## 🤖 Core Concepts

### Agents

6 specialized agents, each with distinct responsibilities:

| Agent | Responsibility | Expertise |
|-------|---------------|-----------|
| **Sisyphus** | Task orchestration, expert scheduling, result synthesis | Complex task decomposition, multi-expert collaboration |
| **Code Analyzer** | Architecture analysis, code review | Technology selection, design evaluation |
| **Programmer** | Code writing, bug fixing | Feature implementation, problem solving |
| **Refactor Master** | Code refactoring, performance optimization | Design improvement, code quality |
| **Test Expert** | Test writing, quality assurance | Test strategy, use case design |
| **Librarian** | Code search, quick location | Information retrieval, code navigation |

### Orchestrators

7 orchestration strategies for different scenarios:

| Orchestrator | Features | Use Cases |
|-------------|----------|-----------|
| **Simple** | Single agent execution | Simple tasks |
| **ReAct** | Reasoning-action loop | Tasks requiring tool invocations |
| **Multi-Agent** | Multi-agent collaboration | Complex tasks requiring multiple experts |
| **Parallel** | Parallel execution | Independent subtasks |
| **Conditional** | Conditional branching | Dynamic decision-making |
| **Workflow** | Workflow orchestration | Fixed processes |
| **Sisyphus** | Iterative optimization | Continuous improvement |

### Collaboration Modes

**Main-with-Helpers Mode**
```
1. System automatically selects helper agents based on user intent
2. Helper agents execute analysis in parallel
3. Main agent (Sisyphus) synthesizes all expert opinions
4. Provides complete solution
```

**Sequential Mode**
```
Agent1 → Agent2 → Agent3
Each agent processes the output of the previous one
```

**Parallel Mode**
```
Agent1 ↘
Agent2 → Aggregate results
Agent3 ↗
```

**Debate Mode**
```
Multiple rounds of debate, shared memory, reaching consensus
```

### Tool System (34+ Tools)

**Project Understanding** (3 tools)
- `discover_project_docs` - Discover project documentation
- `get_repo_structure` - Get directory structure
- `repo_map` - Smart code map

**Code Search** (4 tools)
- `text_search` - Text search
- `regex_search` - Regex search
- `semantic_code_search` - Semantic retrieval
- `ast_grep_search` - AST search

**LSP Tools** (8 tools)
- `lsp_diagnostics` - Code diagnostics
- `lsp_goto_definition` - Jump to definition
- `lsp_find_references` - Find references
- `lsp_symbols` - Get symbols
- `lsp_rename` - Rename
- `lsp_hover` - Hover information
- `lsp_completion` - Code completion
- `lsp_signature_help` - Signature help

**File Operations** (6 tools)
- `read_file` / `batch_read_files` - Read files
- `write_file` / `batch_write_files` - Write files
- `search_replace` - Search and replace
- `apply_patch` - Apply patch

**Git Tools** (3 tools)
- `git_status` - Git status
- `git_diff` - Git diff
- `git_log` - Git log

**Other Tools** (10+ tools)
- `execute_command` - Execute command
- `list_files` - List files
- `get_file_symbols` - Get symbols
- ...

## 🔧 Advanced Features

### Intelligent Context Management

- **Auto-prefetch** - Automatically load relevant information based on task type
- **Conversation History** - Intelligent compression, retaining key information
- **Long-term Memory** - User preferences and project knowledge persistence
- **Semantic Retrieval** - Vector-based relevant code retrieval

### Auto Display Diff

Automatically display unified diff after code modification:

```diff
✅ Successfully modified backend/test.py

📝 Changes:
--- a/backend/test.py
+++ b/backend/test.py
@@ -10,7 +10,7 @@
-    timeout = 120
+    timeout = 1800
```

### Timeout Recovery Mechanism

Automatically handle timeout issues:
1. First attempt: Normal execution
2. Second attempt: Increase timeout
3. Third attempt: Simplify Prompt + increase timeout
4. Fourth attempt: Switch to backup model

### Tool Invocation Optimization

- **Same-round deduplication** - Avoid duplicate tool calls
- **Result caching** - Cache tool execution results
- **Batch operations** - Support batch file read/write
- **Smart post-processing** - Automatically format tool output

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Code-level architecture overview |
| [backend/README.md](backend/README.md) | Backend documentation navigation |
| [backend/01_CLI命令参考.md](backend/01_CLI命令参考.md) | CLI command reference |
| [backend/02_ORCHESTRATORS编排器介绍.md](backend/02_ORCHESTRATORS编排器介绍.md) | Orchestrator introduction |
| [backend/03_AGENTS智能体介绍.md](backend/03_AGENTS智能体介绍.md) | Agent introduction |
| [backend/04_TOOLS工具参考.md](backend/04_TOOLS工具参考.md) | Tool reference |
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | Quick reference card |

## 🎯 Tech Stack

- **Python 3.10+** - Core programming language
- **Typer** - CLI framework
- **Tree-sitter** - Code parsing
- **LSP** - Language Server Protocol
- **Qwen** - Chinese LLM
- **DeepSeek** - Code-specialized LLM
- **Rich** - Terminal beautification
- **Jinja2** - Prompt templates

## 🤝 Contributing

Contributions are welcome! The project is under active development.

- Submit Issues: [GitHub Issues](https://github.com/daoyou-zhang/daoyoucode/issues)
- Submit PRs: [Pull Requests](https://github.com/daoyou-zhang/daoyoucode/pulls)

## 📄 License

[MIT License](LICENSE)

## 🙏 Acknowledgments

Thanks to the following technologies and tools:
- Python ecosystem
- Tree-sitter community
- LSP protocol
- Qwen, DeepSeek and other LLM providers

---

<div align="center">

**Intelligent Programming with AI Companions**

Made with ❤️ by [daoyou-zhang](https://github.com/daoyou-zhang)

⭐ If this project helps you, please give it a Star!

</div>
