# Agents系统

统一的、可插拔的Agent执行框架。

## 架构

```
Skill (配置) → Orchestrator (编排) → Agent (执行) → LLM (基础设施)
     ↓              ↓                    ↓
  可插拔          可插拔               可插拔
```

## 目录结构

```
agents/
├── core/                  # 核心组件
│   ├── skill.py          # Skill配置和加载
│   ├── agent.py          # Agent基类和注册表
│   ├── orchestrator.py   # 编排器基类和注册表
│   └── middleware.py     # 中间件基类和注册表
├── orchestrators/        # 编排器实现
│   ├── simple.py         # 简单编排器（单Agent）
│   └── multi_agent.py    # 多Agent编排器
├── middleware/           # 中间件实现
│   ├── followup.py       # 追问判断
│   └── context.py        # 上下文管理
├── builtin/              # 内置Agent
│   ├── translator.py     # 翻译Agent
│   └── programmer.py     # 编程Agent
├── llm/                  # LLM基础设施
│   ├── base.py           # LLM基类
│   ├── client_manager.py # 客户端管理器
│   ├── clients/          # LLM客户端实现
│   ├── context/          # 上下文管理
│   └── utils/            # 工具函数
├── executor.py           # 执行入口
└── __init__.py           # 模块导出
```

## 快速开始

### 1. 执行Skill

```python
from daoyoucode.agents import execute_skill

result = await execute_skill(
    skill_name='translation',
    user_input='把这段话翻译成英文：你好世界',
    session_id='session_123'
)

print(result['content'])
```

### 2. 创建自定义Agent

```python
from daoyoucode.agents import BaseAgent, AgentConfig, register_agent

class MyAgent(BaseAgent):
    def __init__(self):
        config = AgentConfig(
            name="my_agent",
            description="我的Agent",
            model="qwen-max",
            system_prompt="你是..."
        )
        super().__init__(config)

register_agent(MyAgent())
```

### 3. 创建Skill配置

在 `skills/my-skill/skill.yaml`:

```yaml
name: my-skill
version: 1.0.0
description: 我的Skill

orchestrator: simple
agent: my_agent

prompt:
  use_agent_default: true

llm:
  model: qwen-max
  temperature: 0.7

middleware:
  - followup_detection
  - context_management
```

## 核心概念

### Skill
任务的配置定义，指定编排器、Agent、Prompt和中间件。

### Orchestrator（编排器）
协调Skill的执行流程，可插拔。
- `simple`: 单Agent执行
- `multi_agent`: 多Agent协作

### Agent（执行者）
执行具体任务的专家，Prompt可插拔（文件/内联/默认）。

### Middleware（中间件）
提供可选的能力增强（追问判断、上下文管理等）。

### LLM
提供LLM基础设施（客户端管理、连接池、上下文管理）。

## 优势

1. **完全可插拔**: Skill、Orchestrator、Agent、Prompt都可插拔
2. **配置驱动**: YAML配置，无需修改代码
3. **灵活组合**: 中间件机制，按需组合能力
4. **领域无关**: 不限于编程，支持任何领域
5. **统一管理**: 所有组件在一个目录下

## 详细文档

参见 `backend/README.md` 获取完整使用指南。
