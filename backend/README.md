# daoyoucode Backend

Python后端服务，统一的Agent执行框架。

## 目录结构

```
backend/
├── daoyoucode/          # 主包
│   ├── agents/         # ✅ Agent系统（统一）
│   │   ├── core/       # 核心组件
│   │   ├── orchestrators/  # 编排器
│   │   ├── middleware/     # 中间件
│   │   ├── builtin/        # 内置Agent
│   │   ├── llm/            # LLM基础设施
│   │   └── executor.py     # 执行入口
│   ├── api/            # FastAPI接口
│   ├── hooks/          # Hook系统
│   ├── tools/          # 工具集
│   ├── storage/        # 存储层
│   └── utils/          # 工具函数
└── cli/                # CLI工具
```

## 快速开始

### 安装

```bash
cd backend
pip install -e ".[dev]"
```

### 使用

```python
from daoyoucode.agents import execute_skill

# 执行Skill
result = await execute_skill(
    skill_name='translation',
    user_input='把这段话翻译成英文：你好世界',
    session_id='session_123'
)

print(result['content'])
```

## 核心架构

```
Skill (配置) → Orchestrator (编排) → Agent (执行) → LLM (基础设施)
     ↓              ↓                    ↓
  可插拔          可插拔               可插拔
```

### 核心组件

1. **Skill**: YAML配置定义任务
2. **Orchestrator**: 编排执行流程（simple/multi_agent）
3. **Agent**: 执行具体任务（translator/programmer等）
4. **Middleware**: 能力增强（追问判断/上下文管理）
5. **LLM**: 基础设施（客户端管理/连接池）

## 创建自定义组件

### 1. 自定义Agent

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

### 2. 自定义Orchestrator

```python
from daoyoucode.agents import BaseOrchestrator, register_orchestrator

class MyOrchestrator(BaseOrchestrator):
    async def execute(self, skill, user_input, context):
        # 自定义编排逻辑
        ...

register_orchestrator('my_orchestrator', MyOrchestrator)
```

### 3. Skill配置

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

## 优势

- ✅ **完全可插拔**: 所有组件都可自定义
- ✅ **配置驱动**: YAML配置，无需修改代码
- ✅ **领域无关**: 不限于编程，支持任何领域
- ✅ **统一管理**: 清晰的目录结构
- ✅ **智能优化**: 追问判断、上下文管理、连接池

## 开发

```bash
# 运行测试
pytest

# 启动服务
uvicorn daoyoucode.api.main:app --reload
```

## 详细文档

- `agents/README.md` - Agent系统详细文档
- `AGENT_COMPARISON_ANALYSIS.md` - 与其他项目对比分析
