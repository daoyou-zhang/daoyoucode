# daoyoucode Development Guide

> **Complete development documentation for developers**

---

## 📋 Table of Contents

1. [Development Environment Setup](#development-environment-setup)
2. [Project Structure](#project-structure)
3. [Development Workflow](#development-workflow)
4. [Coding Standards](#coding-standards)
5. [Testing Guide](#testing-guide)
6. [Debugging Tips](#debugging-tips)
7. [Contributing](#contributing)

---

## Development Environment Setup

### System Requirements

| Component | Version |
|-----------|---------|
| Python | ≥ 3.10 |
| Node.js | ≥ 18.0.0 |
| pnpm | ≥ 8.0.0 |
| Git | ≥ 2.0 |

### Quick Setup

#### 1. Clone Repository

```bash
git clone https://github.com/yourusername/daoyoucode.git
cd daoyoucode
```

#### 2. Backend Setup

```bash
# Create virtual environment
cd backend
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# Unix/macOS
source venv/bin/activate

# Install dependencies (development mode)
pip install -e ".[dev]"

# Verify installation
daoyoucode --version
```

#### 3. Frontend Setup

```bash
# Install pnpm (if not installed)
npm install -g pnpm

# Install dependencies
cd frontend
pnpm install

# Verify installation
pnpm --version
```

#### 4. Configure API Keys

Create `.env` file:

```bash
# backend/.env
DASHSCOPE_API_KEY=your_qwen_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
ANTHROPIC_API_KEY=your_claude_api_key
OPENAI_API_KEY=your_openai_api_key
```

### One-Click Setup Script

```bash
# Run from project root
bash scripts/setup.sh
```

---

## Project Structure

### Backend Structure

```
backend/
├── daoyoucode/              # Main package
│   ├── api/                # FastAPI interface layer
│   │   ├── main.py        # Application entry
│   │   ├── routes/        # Route definitions
│   │   ├── websocket/     # WebSocket handlers
│   │   └── middleware/    # Middleware
│   │
│   ├── core/              # Core services
│   │   ├── orchestrator.py    # Orchestrator
│   │   ├── router.py          # Task router
│   │   └── model_selector.py  # Model selector
│   │
│   ├── agents/            # Agent system
│   │   ├── base.py           # Base class
│   │   ├── chinese_editor.py # Chinese editor
│   │   └── ...
│   │
│   ├── tools/             # Tool collection
│   ├── llm/               # LLM integration
│   ├── plugins/           # Plugin management
│   ├── skills/            # Skill system
│   ├── hooks/             # Hook system
│   ├── storage/           # Storage layer
│   └── utils/             # Utility functions
│
├── cli/                   # CLI tools
│   ├── main.py           # CLI entry
│   ├── commands/         # Command implementations
│   └── ui/               # CLI UI
│
└── tests/                 # Tests
    ├── unit/             # Unit tests
    ├── integration/      # Integration tests
    └── e2e/              # End-to-end tests
```

### Frontend Structure

```
frontend/
└── packages/
    ├── shared/           # Shared code
    │   └── src/
    │       ├── api/      # API client
    │       ├── types/    # Type definitions
    │       ├── hooks/    # React Hooks
    │       └── utils/    # Utility functions
    │
    ├── tui/              # Terminal UI
    │   └── src/
    │       ├── App.tsx
    │       ├── components/
    │       └── screens/
    │
    ├── web/              # Web application
    │   └── src/
    │       ├── pages/
    │       ├── components/
    │       └── layouts/
    │
    └── desktop/          # Desktop application
        ├── electron/     # Electron main process
        └── src/          # React renderer process
```

---

## Development Workflow

### Start Development Servers

#### Backend

```bash
cd backend

# Method 1: Using uvicorn (recommended)
uvicorn daoyoucode.api.main:app --reload --port 8000

# Method 2: Using Python module
python -m daoyoucode.api.main

# Method 3: Using CLI
daoyoucode serve --port 8000
```

#### Frontend

```bash
cd frontend

# TUI development
pnpm dev:tui

# Web development
pnpm dev:web

# Desktop development
pnpm dev:desktop
```

### Build Project

#### Backend

```bash
cd backend

# Build Python package
python -m build

# Install local build
pip install dist/daoyoucode-*.whl
```

#### Frontend

```bash
cd frontend

# Build all packages
pnpm build

# Build specific package
pnpm --filter @daoyoucode/web build
```

### Run Tests

#### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_orchestrator.py

# Run specific test case
pytest tests/unit/test_orchestrator.py::test_task_routing

# With coverage report
pytest --cov=daoyoucode --cov-report=html

# Run tests in parallel
pytest -n auto
```

#### Frontend Tests

```bash
cd frontend

# Run all tests
pnpm test

# Run tests for specific package
pnpm --filter @daoyoucode/web test

# Watch mode
pnpm test:watch
```

### Code Quality Checks

#### Backend

```bash
cd backend

# Code formatting
black daoyoucode tests

# Linting
ruff check daoyoucode tests

# Type checking
mypy daoyoucode

# All checks
black daoyoucode tests && ruff check daoyoucode tests && mypy daoyoucode
```

#### Frontend

```bash
cd frontend

# ESLint check
pnpm lint

# TypeScript type check
pnpm typecheck

# Format code
pnpm format
```

---

## Coding Standards

### Python Coding Standards

#### Code Style

- **Follow PEP 8**, max line length 100 characters
- Use **Black** for code formatting
- Use **Ruff** for linting
- Use **isort** for import sorting

#### Naming Conventions

```python
# Class names: PascalCase
class ChineseEditor:
    pass

# Functions/methods: snake_case
def process_task():
    pass

# Constants: UPPER_SNAKE_CASE
MAX_RETRIES = 3

# Private members: prefix with underscore
def _internal_method():
    pass

# Modules: snake_case
# file: chinese_editor.py
```

#### Type Hints

```python
from typing import Optional, List, Dict, Any

def process_files(
    files: List[str],
    options: Optional[Dict[str, Any]] = None
) -> bool:
    """Process list of files
    
    Args:
        files: List of file paths
        options: Optional configuration
        
    Returns:
        Whether processing succeeded
    """
    pass
```

#### Docstrings

Use Google-style docstrings:

```python
def create_agent(
    name: str,
    model: str,
    temperature: float = 0.7
) -> Agent:
    """Create an agent instance
    
    Args:
        name: Agent name
        model: Model to use
        temperature: Temperature parameter, default 0.7
        
    Returns:
        Agent: Agent instance
        
    Raises:
        ValueError: When model is not supported
        
    Example:
        >>> agent = create_agent("editor", "qwen-max")
        >>> agent.execute("refactor code")
    """
    pass
```

### TypeScript Coding Standards

#### Code Style

- Use **ESLint** and **Prettier**
- Prefer functional programming
- Avoid `any` type

#### Naming Conventions

```typescript
// Interfaces: PascalCase, optional I prefix
interface IAgentConfig {
  name: string;
  model: string;
}

// Types: PascalCase
type TaskStatus = 'pending' | 'running' | 'completed';

// Functions: camelCase
function processTask(task: Task): void {}

// Constants: UPPER_SNAKE_CASE
const MAX_RETRIES = 3;

// Components: PascalCase
function AgentCard() {}
```

#### Type Definitions

```typescript
// Prefer interface
interface Agent {
  name: string;
  model: string;
  execute(task: string): Promise<Result>;
}

// Use type for complex types
type AgentResult = 
  | { success: true; data: string }
  | { success: false; error: Error };

// Generics
function createAgent<T extends Agent>(config: T): T {
  return config;
}
```

---

## Testing Guide

### Test Structure

```
tests/
├── unit/                  # Unit tests
│   ├── test_orchestrator.py
│   ├── test_agents.py
│   └── test_tools.py
│
├── integration/           # Integration tests
│   ├── test_api.py
│   └── test_workflow.py
│
├── e2e/                   # End-to-end tests
│   └── test_full_flow.py
│
├── fixtures/              # Test data
│   └── sample_code.py
│
└── conftest.py           # pytest configuration
```

### Writing Tests

#### Unit Test Example

```python
# tests/unit/test_orchestrator.py
import pytest
from daoyoucode.core import Orchestrator

@pytest.fixture
def orchestrator():
    """Create Orchestrator instance"""
    return Orchestrator()

def test_task_routing(orchestrator):
    """Test task routing"""
    task = "refactor code"
    agent = orchestrator.route_task(task)
    assert agent.name == "chinese-editor"

def test_task_execution(orchestrator):
    """Test task execution"""
    task = "add logging"
    result = orchestrator.execute(task)
    assert result.success is True
    assert "logging" in result.message
```

#### Integration Test Example

```python
# tests/integration/test_api.py
import pytest
from fastapi.testclient import TestClient
from daoyoucode.api.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_create_task(client):
    """Test create task API"""
    response = client.post(
        "/api/v1/tasks",
        json={"instruction": "refactor code", "files": ["main.py"]}
    )
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
```

### Test Coverage

```bash
# Generate coverage report
pytest --cov=daoyoucode --cov-report=html

# View report
open htmlcov/index.html  # macOS
start htmlcov/index.html # Windows
```

---

## Debugging Tips

### Python Debugging

#### Using pdb

```python
# Insert breakpoint in code
import pdb; pdb.set_trace()

# Or use breakpoint() (Python 3.7+)
breakpoint()
```

#### Using VS Code Debugger

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "daoyoucode.api.main:app",
        "--reload"
      ],
      "jinja": true,
      "justMyCode": false
    }
  ]
}
```

---

## Contributing

### Workflow

1. **Fork the project**
2. **Create a branch**
3. **Develop and test**
4. **Commit changes**
5. **Push branch**
6. **Create Pull Request**

### Commit Convention

Use [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Format
<type>(<scope>): <subject>

# Types
feat:     New feature
fix:      Bug fix
docs:     Documentation update
style:    Code formatting (no functional change)
refactor: Refactoring
test:     Test related
chore:    Build/tool related

# Examples
feat(agents): add chinese editor agent
fix(api): resolve task routing issue
docs: update development guide
```

---

<div align="center">

**Happy Coding! 🚀**

</div>
