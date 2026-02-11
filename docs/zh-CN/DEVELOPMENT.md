# daoyoucode 开发指南

> **面向开发者的完整开发文档**

---

## 📋 目录

1. [开发环境设置](#开发环境设置)
2. [项目结构](#项目结构)
3. [开发工作流](#开发工作流)
4. [编码规范](#编码规范)
5. [测试指南](#测试指南)
6. [调试技巧](#调试技巧)
7. [贡献代码](#贡献代码)

---

## 开发环境设置

### 系统要求

| 组件 | 版本要求 |
|------|---------|
| Python | ≥ 3.10 |
| Node.js | ≥ 18.0.0 |
| pnpm | ≥ 8.0.0 |
| Git | ≥ 2.0 |

### 快速设置

#### 1. 克隆仓库

```bash
git clone https://github.com/yourusername/daoyoucode.git
cd daoyoucode
```

#### 2. 后端设置

```bash
# 创建虚拟环境
cd backend
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Unix/macOS
source venv/bin/activate

# 安装依赖（开发模式）
pip install -e ".[dev]"

# 验证安装
daoyoucode --version
```

#### 3. 前端设置

```bash
# 安装 pnpm（如果未安装）
npm install -g pnpm

# 安装依赖
cd frontend
pnpm install

# 验证安装
pnpm --version
```

#### 4. 配置 API Keys

创建 `.env` 文件：

```bash
# backend/.env
DASHSCOPE_API_KEY=your_qwen_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
ANTHROPIC_API_KEY=your_claude_api_key
OPENAI_API_KEY=your_openai_api_key
```

### 一键设置脚本

```bash
# 从项目根目录运行
bash scripts/setup.sh
```

---

## 项目结构

### 后端结构

```
backend/
├── daoyoucode/              # 主包
│   ├── api/                # FastAPI 接口层
│   │   ├── main.py        # 应用入口
│   │   ├── routes/        # 路由定义
│   │   ├── websocket/     # WebSocket 处理
│   │   └── middleware/    # 中间件
│   │
│   ├── core/              # 核心服务
│   │   ├── orchestrator.py    # 编排器
│   │   ├── router.py          # 任务路由
│   │   └── model_selector.py  # 模型选择
│   │
│   ├── agents/            # 智能体系统
│   │   ├── base.py           # 基类
│   │   ├── chinese_editor.py # 中文编辑
│   │   └── ...
│   │
│   ├── tools/             # 工具集
│   ├── llm/               # LLM 集成
│   ├── plugins/           # 插件管理
│   ├── skills/            # Skill 系统
│   ├── hooks/             # Hook 系统
│   ├── storage/           # 存储层
│   └── utils/             # 工具函数
│
├── cli/                   # CLI 工具
│   ├── main.py           # CLI 入口
│   ├── commands/         # 命令实现
│   └── ui/               # CLI UI
│
└── tests/                 # 测试
    ├── unit/             # 单元测试
    ├── integration/      # 集成测试
    └── e2e/              # 端到端测试
```

### 前端结构

```
frontend/
└── packages/
    ├── shared/           # 共享代码
    │   └── src/
    │       ├── api/      # API 客户端
    │       ├── types/    # 类型定义
    │       ├── hooks/    # React Hooks
    │       └── utils/    # 工具函数
    │
    ├── tui/              # 终端 UI
    │   └── src/
    │       ├── App.tsx
    │       ├── components/
    │       └── screens/
    │
    ├── web/              # Web 应用
    │   └── src/
    │       ├── pages/
    │       ├── components/
    │       └── layouts/
    │
    └── desktop/          # 桌面应用
        ├── electron/     # Electron 主进程
        └── src/          # React 渲染进程
```

---

## 开发工作流

### 启动开发服务器

#### 后端

```bash
cd backend

# 方式 1: 使用 uvicorn（推荐）
uvicorn daoyoucode.api.main:app --reload --port 8000

# 方式 2: 使用 Python 模块
python -m daoyoucode.api.main

# 方式 3: 使用 CLI
daoyoucode serve --port 8000
```

#### 前端

```bash
cd frontend

# TUI 开发
pnpm dev:tui

# Web 开发
pnpm dev:web

# Desktop 开发
pnpm dev:desktop
```

### 构建项目

#### 后端

```bash
cd backend

# 构建 Python 包
python -m build

# 安装本地构建
pip install dist/daoyoucode-*.whl
```

#### 前端

```bash
cd frontend

# 构建所有包
pnpm build

# 构建特定包
pnpm --filter @daoyoucode/web build
```

### 运行测试

#### 后端测试

```bash
cd backend

# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/unit/test_orchestrator.py

# 运行特定测试用例
pytest tests/unit/test_orchestrator.py::test_task_routing

# 带覆盖率报告
pytest --cov=daoyoucode --cov-report=html

# 并行运行测试
pytest -n auto
```

#### 前端测试

```bash
cd frontend

# 运行所有测试
pnpm test

# 运行特定包的测试
pnpm --filter @daoyoucode/web test

# 监听模式
pnpm test:watch
```

### 代码检查

#### 后端

```bash
cd backend

# 代码格式化
black daoyoucode tests

# 代码检查
ruff check daoyoucode tests

# 类型检查
mypy daoyoucode

# 全部检查
black daoyoucode tests && ruff check daoyoucode tests && mypy daoyoucode
```

#### 前端

```bash
cd frontend

# ESLint 检查
pnpm lint

# TypeScript 类型检查
pnpm typecheck

# 格式化
pnpm format
```

---

## 编码规范

### Python 编码规范

#### 代码风格

- **遵循 PEP 8**，最大行长度 100 字符
- 使用 **Black** 进行代码格式化
- 使用 **Ruff** 进行代码检查
- 使用 **isort** 进行导入排序

#### 命名约定

```python
# 类名：PascalCase
class ChineseEditor:
    pass

# 函数/方法：snake_case
def process_task():
    pass

# 常量：UPPER_SNAKE_CASE
MAX_RETRIES = 3

# 私有成员：前缀下划线
def _internal_method():
    pass

# 模块：snake_case
# file: chinese_editor.py
```

#### 类型提示

```python
from typing import Optional, List, Dict, Any

def process_files(
    files: List[str],
    options: Optional[Dict[str, Any]] = None
) -> bool:
    """处理文件列表
    
    Args:
        files: 文件路径列表
        options: 可选配置
        
    Returns:
        处理是否成功
    """
    pass
```

#### 文档字符串

使用 Google 风格的文档字符串：

```python
def create_agent(
    name: str,
    model: str,
    temperature: float = 0.7
) -> Agent:
    """创建智能体实例
    
    Args:
        name: 智能体名称
        model: 使用的模型
        temperature: 温度参数，默认 0.7
        
    Returns:
        Agent: 智能体实例
        
    Raises:
        ValueError: 当模型不支持时
        
    Example:
        >>> agent = create_agent("editor", "qwen-max")
        >>> agent.execute("重构代码")
    """
    pass
```

### TypeScript 编码规范

#### 代码风格

- 使用 **ESLint** 和 **Prettier**
- 优先使用函数式编程
- 避免 `any` 类型

#### 命名约定

```typescript
// 接口：PascalCase，前缀 I（可选）
interface IAgentConfig {
  name: string;
  model: string;
}

// 类型：PascalCase
type TaskStatus = 'pending' | 'running' | 'completed';

// 函数：camelCase
function processTask(task: Task): void {}

// 常量：UPPER_SNAKE_CASE
const MAX_RETRIES = 3;

// 组件：PascalCase
function AgentCard() {}
```

#### 类型定义

```typescript
// 优先使用 interface
interface Agent {
  name: string;
  model: string;
  execute(task: string): Promise<Result>;
}

// 复杂类型使用 type
type AgentResult = 
  | { success: true; data: string }
  | { success: false; error: Error };

// 泛型
function createAgent<T extends Agent>(config: T): T {
  return config;
}
```

### 通用规范

#### 文件组织

```python
# Python 文件结构
"""模块文档字符串"""

# 1. 标准库导入
import os
import sys

# 2. 第三方库导入
import click
from fastapi import FastAPI

# 3. 本地导入
from daoyoucode.core import Orchestrator
from daoyoucode.utils import logger

# 4. 常量定义
MAX_RETRIES = 3

# 5. 类和函数定义
class MyClass:
    pass

def my_function():
    pass
```

```typescript
// TypeScript 文件结构
// 1. 类型导入
import type { Agent, Task } from './types';

// 2. 库导入
import { useState, useEffect } from 'react';

// 3. 本地导入
import { api } from '@/api';
import { Button } from '@/components';

// 4. 常量定义
const MAX_RETRIES = 3;

// 5. 组件/函数定义
export function MyComponent() {}
```

#### 错误处理

```python
# Python
from daoyoucode.exceptions import AgentError

def execute_task(task: str) -> Result:
    try:
        result = agent.execute(task)
        return result
    except AgentError as e:
        logger.error(f"Agent error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise AgentError(f"Failed to execute task: {e}")
```

```typescript
// TypeScript
async function executeTask(task: string): Promise<Result> {
  try {
    const result = await agent.execute(task);
    return result;
  } catch (error) {
    if (error instanceof AgentError) {
      logger.error('Agent error:', error);
      throw error;
    }
    logger.error('Unexpected error:', error);
    throw new AgentError(`Failed to execute task: ${error}`);
  }
}
```

---

## 测试指南

### 测试结构

```
tests/
├── unit/                  # 单元测试
│   ├── test_orchestrator.py
│   ├── test_agents.py
│   └── test_tools.py
│
├── integration/           # 集成测试
│   ├── test_api.py
│   └── test_workflow.py
│
├── e2e/                   # 端到端测试
│   └── test_full_flow.py
│
├── fixtures/              # 测试数据
│   └── sample_code.py
│
└── conftest.py           # pytest 配置
```

### 编写测试

#### 单元测试示例

```python
# tests/unit/test_orchestrator.py
import pytest
from daoyoucode.core import Orchestrator

@pytest.fixture
def orchestrator():
    """创建 Orchestrator 实例"""
    return Orchestrator()

def test_task_routing(orchestrator):
    """测试任务路由"""
    task = "重构代码"
    agent = orchestrator.route_task(task)
    assert agent.name == "chinese-editor"

def test_task_execution(orchestrator):
    """测试任务执行"""
    task = "添加日志"
    result = orchestrator.execute(task)
    assert result.success is True
    assert "日志" in result.message
```

#### 集成测试示例

```python
# tests/integration/test_api.py
import pytest
from fastapi.testclient import TestClient
from daoyoucode.api.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_create_task(client):
    """测试创建任务 API"""
    response = client.post(
        "/api/v1/tasks",
        json={"instruction": "重构代码", "files": ["main.py"]}
    )
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
```

### 测试覆盖率

```bash
# 生成覆盖率报告
pytest --cov=daoyoucode --cov-report=html

# 查看报告
open htmlcov/index.html  # macOS
start htmlcov/index.html # Windows
```

### Mock 和 Fixture

```python
# tests/conftest.py
import pytest
from unittest.mock import Mock

@pytest.fixture
def mock_llm():
    """Mock LLM 客户端"""
    llm = Mock()
    llm.generate.return_value = "生成的代码"
    return llm

@pytest.fixture
def sample_code():
    """示例代码"""
    return """
def hello():
    print("Hello, World!")
"""

# 使用 fixture
def test_with_mock(mock_llm):
    result = mock_llm.generate("写一个函数")
    assert result == "生成的代码"
```

---

## 调试技巧

### Python 调试

#### 使用 pdb

```python
# 在代码中插入断点
import pdb; pdb.set_trace()

# 或使用 breakpoint()（Python 3.7+）
breakpoint()
```

#### 使用 VS Code 调试

创建 `.vscode/launch.json`：

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
    },
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal"
    }
  ]
}
```

#### 日志调试

```python
from daoyoucode.utils import logger

# 不同级别的日志
logger.debug("调试信息")
logger.info("一般信息")
logger.warning("警告信息")
logger.error("错误信息")
logger.exception("异常信息（包含堆栈）")
```

### TypeScript 调试

#### 使用浏览器开发工具

```typescript
// 在代码中插入断点
debugger;

// 使用 console
console.log('变量值:', variable);
console.table(arrayData);
console.trace('调用堆栈');
```

#### 使用 VS Code 调试

创建 `.vscode/launch.json`：

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Launch Chrome",
      "type": "chrome",
      "request": "launch",
      "url": "http://localhost:5173",
      "webRoot": "${workspaceFolder}/frontend/packages/web/src"
    }
  ]
}
```

---

## 贡献代码

### 工作流程

1. **Fork 项目**
   ```bash
   # 在 GitHub 上 Fork 项目
   git clone https://github.com/yourusername/daoyoucode.git
   ```

2. **创建分支**
   ```bash
   git checkout -b feature/amazing-feature
   ```

3. **开发和测试**
   ```bash
   # 编写代码
   # 运行测试
   pytest
   pnpm test
   ```

4. **提交代码**
   ```bash
   git add .
   git commit -m "feat: add amazing feature"
   ```

5. **推送分支**
   ```bash
   git push origin feature/amazing-feature
   ```

6. **创建 Pull Request**
   - 在 GitHub 上创建 PR
   - 填写 PR 模板
   - 等待代码审查

### Commit 规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```bash
# 格式
<type>(<scope>): <subject>

# 类型
feat:     新功能
fix:      Bug 修复
docs:     文档更新
style:    代码格式（不影响功能）
refactor: 重构
test:     测试相关
chore:    构建/工具相关

# 示例
feat(agents): add chinese editor agent
fix(api): resolve task routing issue
docs: update development guide
```

### PR 检查清单

- [ ] 代码遵循项目规范
- [ ] 所有测试通过
- [ ] 添加了必要的测试
- [ ] 更新了相关文档
- [ ] Commit 消息符合规范
- [ ] 没有合并冲突

---

## 常见问题

### Q: 如何添加新的智能体？

A: 参考 `backend/daoyoucode/agents/base.py`，创建新的智能体类：

```python
from daoyoucode.agents.base import BaseAgent

class MyAgent(BaseAgent):
    name = "my-agent"
    model = "qwen-max"
    
    async def execute(self, task: str) -> Result:
        # 实现逻辑
        pass
```

### Q: 如何添加新的工具？

A: 在 `backend/daoyoucode/tools/` 创建新文件：

```python
from daoyoucode.tools.base import BaseTool

class MyTool(BaseTool):
    name = "my-tool"
    description = "工具描述"
    
    def execute(self, params: dict) -> Any:
        # 实现逻辑
        pass
```

### Q: 如何调试 WebSocket 连接？

A: 使用浏览器开发工具或 `wscat`：

```bash
# 安装 wscat
npm install -g wscat

# 连接 WebSocket
wscat -c ws://localhost:8000/ws
```

---

## 获取帮助

- **文档**: [docs/README.md](../README.md)
- **Issues**: [GitHub Issues](https://github.com/yourusername/daoyoucode/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/daoyoucode/discussions)
- **Discord**: （待建立）

---

<div align="center">

**Happy Coding! 🚀**

</div>
