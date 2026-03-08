# DaoyouCode

<div align="center">

**Next-Generation AI Programming Assistant - CoreOrchestrator + Workflow Driven**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-active-success.svg)]()

[English](README.en.md) • [中文文档](README.md)

</div>

---

## 📖 Overview

**DaoyouCode** is a next-generation AI programming assistant based on CoreOrchestrator architecture, featuring intelligent intent recognition, tiered prefetch mechanism, and workflow-driven execution to provide developers with powerful support for code analysis, writing, and refactoring.

### ✨ Key Features

- 🎯 **Intelligent Intent Recognition** - Fast intent recognition using small model (qwen-turbo) with 95%+ accuracy
- 📊 **Tiered Prefetch Mechanism** - Dynamically load context based on task complexity (Full/Medium/Light/None)
- � **Workflow Driven** - Define task execution through Markdown files without writing code
- 🛠️ **Complete Toolchain** - 34+ professional tools with deep LSP/AST integration and Git operations support
- 🧠 **Smart Memory System** - Conversation history, long-term memory, user profiles, and intelligent context loading
- 🌐 **Chinese LLM Optimized** - Deep support for Qwen and DeepSeek with multi-key rotation
- ⚙️ **Configuration as Service** - Configure via YAML + Markdown with hot reload support
- 🎨 **Context Auto-Management** - Automatic path management, search history, and target file protection

### 🎯 Technical Highlights

**CoreOrchestrator Architecture**
```
User Input
  ↓
Intent Recognition (qwen-turbo, fast & accurate)
  ↓
Tiered Prefetch (load context on demand)
  ├─ Full: Directory structure + Code map + Project docs
  ├─ Medium: Directory structure + Code map
  ├─ Light: Code map only
  └─ None: No prefetch
  ↓
Workflow Loading (dynamically load based on intent)
  ↓
Agent Execution (dynamically created, no Python class needed)
  ↓
Return Results (streaming support)
```

**Deep Code Understanding**
- **LSP Integration** - Type information, reference relationships, code diagnostics, intelligent renaming
- **AST Analysis** - Syntax tree parsing, structured code understanding
- **Semantic Search** - Vector-based code retrieval, understanding code intent
- **Smart Code Map** - Automatic project structure overview generation (with LSP enhancement)

**Context Auto-Management** 🆕
- **target_file** - Automatically set on first search, protected from overwriting
- **search_history** - Record all search operations, traceable
- **last_search_paths** - Always updated to latest search results
- **Multi-file support** - Automatically save all file paths

**Configuration as Service**
- **skill.yaml** - Unified configuration entry (Agent name, role, tools, prefetch parameters)
- **workflow.md** - Define task execution (goals, steps, principles)
- **intents.yaml** - Intent configuration (keywords, workflows, prefetch levels)
- **prompt_template.md** - Base Prompt template

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/daoyou-zhang/daoyoucode.git
cd daoyoucode

# Install dependencies
cd backend
pip install -r requirements.txt
```

### Configuration

Edit `backend/.env`:

```bash
# Copy configuration file
cp .env.example .env

# Edit .env and fill in your API Key
DASHSCOPE_API_KEY=your_key_here
```

Or edit `backend/config/llm_config.yaml`:

```yaml
providers:
  qwen:
    api_key: ["your-api-key-here"]
    enabled: true

default:
  model: "qwen-max"
  temperature: 0.7
  max_tokens: 4000
  timeout: 1800
```

### Usage

```bash
# Interactive chat (default sisyphus-orchestrator)
daoyoucode chat

# Use specific skill
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

### Example 1: Intelligent Code Analysis

```bash
daoyoucode chat

You > Analyze the design of backend/daoyoucode/agents/core/agent.py

AI will automatically:
1. Recognize intent: code_analysis
2. Prefetch: Medium level (directory structure + code map)
3. Load workflow: analyze_code.md
4. Execute analysis: Use repo_map, read_file, get_file_symbols
5. Return complete analysis report
```

### Example 2: Code Refactoring

```bash
You > Refactor agent.py to improve maintainability

AI will:
1. Recognize intent: refactor_code
2. Prefetch: Full level (complete context)
3. Load workflow: refactor_code.md
4. Execute refactoring:
   - Search target file
   - Read and understand code
   - Propose refactoring plan
   - Execute modifications
5. Display diff and summary
```

### Example 3: Bug Fixing

```bash
You > Fix the login functionality bug

AI will:
1. Recognize intent: debug_code
2. Prefetch: Medium level
3. Load workflow: debug_code.md
4. Execute debugging:
   - Locate problem code
   - Analyze root cause
   - Provide fix solution
   - Execute fix
5. Verify fix with lsp_diagnostics
```

### Example 4: Understanding Project

```bash
You > Understand this project

AI will automatically:
1. Recognize intent: understand_project
2. Prefetch: Full level
3. Load workflow: understand_project.md
4. Execute understanding:
   - Call discover_project_docs to read README
   - Call get_repo_structure to view directory structure
   - Call repo_map to generate code map
5. Summarize project features concisely
```

## 🏗️ Project Structure

```
daoyoucode/
├── backend/                    # Python core implementation
│   ├── daoyoucode.py          # CLI entry point
│   ├── cli/                   # CLI commands
│   ├── daoyoucode/
│   │   └── agents/
│   │       ├── core/          # Agent core
│   │       │   ├── agent.py           # Agent base class
│   │       │   ├── context.py         # Context management 🆕
│   │       │   ├── core_orchestrator.py  # Core orchestrator
│   │       │   └── skill_loader.py    # Skill loader
│   │       ├── tools/         # Tool system (35+ tools)
│   │       │   ├── file_tools.py      # File operations
│   │       │   ├── search_tools.py    # Search tools
│   │       │   ├── lsp_tools.py       # LSP tools
│   │       │   ├── diff_tools.py      # Diff editing
│   │       │   ├── repomap_tools.py   # Code map
│   │       │   └── ...
│   │       ├── llm/           # LLM client
│   │       ├── memory/        # Memory system
│   │       └── middleware/    # Middleware
│   ├── config/                # Configuration files
│   └── tests/                 # Tests
├── skills/                    # Skill configurations and Prompts
│   ├── sisyphus-orchestrator/ # Main orchestrator
│   │   ├── skill.yaml         # Skill configuration
│   │   ├── intents.yaml       # Intent configuration
│   │   ├── prompts/
│   │   │   ├── base_template.md      # Base template
│   │   │   └── workflows/            # Workflow definitions
│   │   │       ├── write_code.md     # Write code
│   │   │       ├── refactor_code.md  # Refactor code
│   │   │       ├── analyze_code.md   # Analyze code
│   │   │       ├── search_code.md    # Search code
│   │   │       ├── context_usage_guide.md  # Context guide 🆕
│   │   │       └── ...
│   ├── programming/           # Programming expert
│   ├── code-analysis/         # Code analysis
│   ├── refactoring/           # Refactoring expert
│   └── ...
└── docs/                      # Documentation
```

## 🤖 Core Concepts

### CoreOrchestrator

The core orchestrator responsible for:
- **Intent Recognition** - Fast recognition using small model (qwen-turbo)
- **Tiered Prefetch** - Dynamically load context based on task complexity
- **Workflow Loading** - Load appropriate workflow based on intent
- **Agent Execution** - Dynamically create and execute Agent
- **Result Synthesis** - Synthesize and return results

### Workflows

Define task execution through Markdown files:

| Workflow | Purpose | Prefetch Level |
|----------|---------|----------------|
| **write_code.md** | Write new code | Medium |
| **refactor_code.md** | Refactor code | Full |
| **analyze_code.md** | Analyze code | Medium |
| **search_code.md** | Search code | Light |
| **debug_code.md** | Debug code | Medium |
| **run_test.md** | Run tests | Light |
| **understand_project.md** | Understand project | Full |

### Context Auto-Management 🆕

System automatically manages file paths and search history:

**Core Variables**:
- `target_file` - Main target file (set on first search, protected)
- `target_files` - Multiple file list (for batch operations)
- `target_dir` - Target directory
- `last_search_paths` - Latest search results (always updated)
- `search_history` - All search history (traceable)

**Usage Example**:
```
1. text_search("agent.py")
   → target_file = "agent.py" (auto-set)

2. read_file(path="{{target_file}}")
   → Read agent.py

3. text_search("config.yaml")  # Search other files
   → target_file remains unchanged (still agent.py)
   → last_search_paths = ["config.yaml"]

4. write_file(path="{{target_file}}", content="...")
   → Modify agent.py (correct file)
```

### Tool System (35+ Tools)

**Project Understanding** (3 tools)
- `discover_project_docs` - Discover project documentation
- `get_repo_structure` - Get directory structure
- `repo_map` - Smart code map (with LSP enhancement)

**Code Search** (4 tools)
- `text_search` - Text search
- `regex_search` - Regex search (formerly grep_search)
- `semantic_code_search` - Semantic retrieval
- `ast_grep_search` - AST search

**LSP Tools** (6 tools)
- `lsp_diagnostics` - Code diagnostics
- `lsp_goto_definition` - Jump to definition
- `lsp_find_references` - Find references
- `lsp_symbols` - Get symbols
- `lsp_rename` - Rename
- `lsp_code_actions` - Code actions

**File Operations** (9 tools)
- `read_file` / `batch_read_files` - Read files
- `write_file` / `batch_write_files` - Write files
- `search_replace` - Search and replace
- `intelligent_diff_edit` - Intelligent diff editing
- `apply_patch` - Apply patch
- `list_files` - List files
- `delete_file` / `batch_delete_files` - Delete files

**Git Tools** (4 tools)
- `git_status` - Git status
- `git_diff` - Git diff
- `git_commit` - Git commit
- `git_log` - Git log

**Other Tools** (9+ tools)
- `run_command` - Execute command
- `run_test` - Run tests
- `run_lint` - Run lint
- `get_file_symbols` - Get file symbols
- `code_snippet_validation` - Code validation
- ...

## 🔧 Advanced Features

### Intelligent Context Management

- **Auto-prefetch** - Automatically load relevant information based on task type
- **Tiered loading** - Full/Medium/Light/None four levels
- **Conversation History** - Intelligent compression, retaining key information
- **Long-term Memory** - User preferences and project knowledge persistence
- **Semantic Retrieval** - Vector-based relevant code retrieval

### Context Auto-Management 🆕

- **Automatic path management** - No need to hardcode paths
- **Target file protection** - target_file won't be overwritten by subsequent searches
- **Search history** - Record all search operations, traceable
- **Multi-file support** - Automatically save all file paths
- **Simplified workflows** - Reduce repetitive code, improve readability

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
| [Context Usage Guide](skills/sisyphus-orchestrator/prompts/workflows/context_usage_guide.md) | Context variable usage guide 🆕 |

## 🎯 Tech Stack

- **Python 3.10+** - Core programming language
- **Typer** - CLI framework
- **Tree-sitter** - Code parsing
- **LSP** - Language Server Protocol
- **Qwen** - Chinese LLM
- **DeepSeek** - Code-specialized LLM
- **Rich** - Terminal beautification
- **Jinja2** - Prompt templates

## 🆕 Recent Updates

### Context Integration (Latest)

- ✅ **Context auto-management** - Automatic path management, no hardcoding needed
- ✅ **Search history** - Record all search operations, traceable
- ✅ **Target file protection** - target_file won't be overwritten
- ✅ **Multi-file support** - Automatically save all file paths
- ✅ **Workflow optimization** - Added Context usage guide and examples
- ✅ **Tool name fixes** - Unified correct tool names (grep_search → regex_search)
- ✅ **Complete test suite** - 24/24 tests passed

### CoreOrchestrator Architecture

- ✅ **Intent recognition** - Fast recognition using small model (qwen-turbo)
- ✅ **Tiered prefetch** - Dynamically load context based on task complexity
- ✅ **Workflow driven** - Define task execution through Markdown files
- ✅ **Configuration as service** - Configure via YAML + Markdown

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
