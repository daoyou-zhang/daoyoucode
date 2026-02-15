# DaoyouCode 快速参考指南

> 快速查找关键信息和常用操作

## 📖 文档导航

### 从哪里开始？

```
1. 想了解整体架构？
   → 阅读 CALL_CHAIN_FLOWCHART.md（流程图）
   → 阅读 CALL_CHAIN_ANALYSIS.md（总索引）

2. 想了解某一层的实现？
   → 入口层：CALL_CHAIN_01_ENTRY.md
   → 命令层：CALL_CHAIN_02_COMMAND.md
   → Skill层：CALL_CHAIN_03_SKILL.md
   → Agent层：CALL_CHAIN_04_AGENT.md
   → 工具层：CALL_CHAIN_05_TOOL.md
   → LLM层：CALL_CHAIN_06_LLM.md
   → Memory层：CALL_CHAIN_07_MEMORY.md

3. 想了解设计决策？
   → 上下文分离：CONTEXT_SEPARATION_EXPLAINED.md
   → Typer注册：TYPER_REGISTRATION_EXPLAINED.md
   → Agent架构：AGENT_ARCHITECTURE.md

4. 想了解当前状态？
   → 项目状态：PROJECT_STATUS.md
   → 项目概览：PROJECT_OVERVIEW.md
```

---

## 🎯 核心概念速查

### 调用链路

```
用户输入
  ↓
CLI入口 (cli/__main__.py)
  ↓
Typer应用 (cli/app.py)
  ↓
Chat命令 (cli/commands/chat.py)
  ↓
Skill执行器 (daoyoucode/agents/executor.py)
  ↓
Agent执行 (daoyoucode/agents/core/agent.py)
  ↓
工具调用 (daoyoucode/agents/tools/)
  ↓
LLM调用 (daoyoucode/agents/llm/)
  ↓
Memory系统 (daoyoucode/agents/memory/)
```

### 上下文流转

```
UI上下文 (ui_context)
  - 在命令层（chat.py）
  - 包含：session_id, model, repo, initial_files
  - 用途：管理CLI交互状态
  ↓
业务上下文 (context)
  - 从ui_context提取
  - 传递给Skill/Agent/工具层
  - 用途：执行业务逻辑
```

### Function Calling循环

```
1. Agent调用LLM（带工具定义）
   ↓
2. LLM决策：调用工具 or 返回答案？
   ↓
3a. 如果调用工具：
    - 执行工具
    - 截断输出（减少93%）
    - 智能后处理（再减少30-50%）
    - 添加到消息历史
    - 回到步骤1
   ↓
3b. 如果返回答案：
    - 返回最终响应
    - 保存到Memory
    - 显示给用户
```

---

## 🔧 常用命令

### 运行CLI

```bash
cd backend
python -m cli chat
```

### 测试功能

```bash
# 测试工具注册
python test_tool_registry.py

# 测试Function Calling
python test_function_calling.py

# 测试Memory系统
python test_memory_integration.py

# 测试工具截断
python test_tool_truncation.py

# 测试智能后处理
python test_postprocessing.py
```

### CLI命令

```
/help           查看所有命令
/exit           退出对话
/model [name]   查看或切换模型
/session        查看会话ID
/add <file>     添加文件到上下文
/files          查看已加载的文件
```

---

## 📁 关键文件速查

### 入口和命令

```
cli/__main__.py          Python模块入口
cli/app.py               Typer应用（装饰器注册）
cli/commands/chat.py     Chat命令处理
```

### 核心系统

```
daoyoucode/agents/init.py              统一初始化
daoyoucode/agents/executor.py          Skill执行器
daoyoucode/agents/core/agent.py        Agent基类
daoyoucode/agents/core/orchestrator.py 编排器注册表
```

### 工具系统

```
daoyoucode/agents/tools/base.py           工具基类和注册表
daoyoucode/agents/tools/postprocessor.py  智能后处理
daoyoucode/agents/tools/repomap_tools.py  RepoMap工具
daoyoucode/agents/tools/file_tools.py     文件操作工具
daoyoucode/agents/tools/search_tools.py   搜索工具
```

### LLM系统

```
daoyoucode/agents/llm/client_manager.py  客户端管理器
daoyoucode/agents/llm/config_loader.py   配置加载
daoyoucode/agents/llm/clients/unified.py 统一客户端
config/llm_config.yaml                   LLM配置
```

### Memory系统

```
daoyoucode/agents/memory/__init__.py  Memory管理器
```

### Skill配置

```
skills/chat-assistant/skill.yaml                Skill配置
skills/chat-assistant/prompts/chat_assistant.md Prompt模板
```

---

## 🎨 代码模式速查

### 注册工具

```python
from daoyoucode.agents.tools.base import BaseTool, ToolResult

class MyTool(BaseTool):
    name = "my_tool"
    description = "工具描述"
    
    # 配置输出限制
    MAX_OUTPUT_CHARS = 5000
    MAX_OUTPUT_LINES = 200
    
    async def execute(self, **kwargs) -> ToolResult:
        # 实现工具逻辑
        result = do_something()
        
        return ToolResult(
            success=True,
            content=result,
            metadata={"key": "value"}
        )

# 注册工具
from daoyoucode.agents.tools.base import get_tool_registry
registry = get_tool_registry()
registry.register(MyTool())
```

### 注册Agent

```python
from daoyoucode.agents.core.agent import BaseAgent, AgentConfig

config = AgentConfig(
    name="MyAgent",
    description="Agent描述",
    model="qwen-plus",
    temperature=0.7,
    system_prompt="你是..."
)

agent = BaseAgent(config)

from daoyoucode.agents.core.agent import register_agent
register_agent(agent)
```

### 执行Skill

```python
from daoyoucode.agents.executor import execute_skill

result = await execute_skill(
    skill_name="chat_assistant",
    user_input="用户输入",
    session_id="session-id",
    context={
        "repo": "./backend",
        "model": "qwen-plus"
    }
)

if result.get('success'):
    print(result.get('content'))
else:
    print(result.get('error'))
```

### 调用LLM

```python
from daoyoucode.agents.llm.client_manager import get_client_manager

client_manager = get_client_manager()
client = client_manager.get_client("qwen-plus")

response = await client.chat(
    messages=[
        {"role": "user", "content": "你好"}
    ],
    tools=tools,  # 可选
    temperature=0.7
)

print(response.content)
```

---

## 🐛 调试技巧

### 查看日志

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 断点调试

```python
# 在关键位置设置断点
import pdb; pdb.set_trace()

# 或使用VSCode的调试功能
```

### 查看工具调用

```python
# 在Agent执行后查看
result = await agent.execute(...)
print(f"工具调用: {result.tools_used}")
print(f"Token使用: {result.tokens_used}")
print(f"成本: {result.cost}")
```

### 查看Memory

```python
from daoyoucode.agents.memory import get_memory_manager

memory = get_memory_manager()
history = memory.get_conversation_history("session-id")
print(history)
```

---

## 💡 最佳实践

### 1. 工具开发

- ✅ 继承`BaseTool`
- ✅ 设置合适的`MAX_OUTPUT_CHARS`和`MAX_OUTPUT_LINES`
- ✅ 返回`ToolResult`对象
- ✅ 添加详细的`description`（用于LLM理解）
- ✅ 使用`metadata`传递额外信息

### 2. Agent开发

- ✅ 使用`AgentConfig`配置
- ✅ 编写清晰的`system_prompt`
- ✅ 注册到`agent_registry`
- ✅ 使用Memory系统保存状态

### 3. Skill开发

- ✅ 创建`skill.yaml`配置文件
- ✅ 编写`prompt.md`模板
- ✅ 选择合适的编排器（Simple、ReAct等）
- ✅ 选择合适的Agent

### 4. 上下文管理

- ✅ UI状态留在UI层（`ui_context`）
- ✅ 业务信息传递到业务层（`context`）
- ✅ 不要混合UI状态和业务信息
- ✅ 使用Memory系统管理长期状态

---

## 🔍 问题排查

### 工具未注册？

```python
# 检查工具注册
from daoyoucode.agents.tools.base import get_tool_registry
registry = get_tool_registry()
print(registry.list_tools())
```

### Agent未注册？

```python
# 检查Agent注册
from daoyoucode.agents.core.agent import get_agent_registry
registry = get_agent_registry()
print(registry.list_agents())
```

### LLM配置错误？

```python
# 检查LLM配置
from daoyoucode.agents.llm.client_manager import get_client_manager
client_manager = get_client_manager()
print(client_manager.provider_configs)
```

### Memory不工作？

```python
# 检查Memory配置
from daoyoucode.agents.memory import get_memory_manager
memory = get_memory_manager()
print(memory.db_path)
```

---

## 📊 性能优化

### 工具输出优化

```
原始输出 → 截断（减少93%） → 后处理（再减少30-50%）
```

**配置**:
```python
class MyTool(BaseTool):
    MAX_OUTPUT_CHARS = 5000  # 字符限制
    MAX_OUTPUT_LINES = 200   # 行数限制
```

### Memory优化

- 使用索引加速查询
- 定期清理旧数据
- 限制历史记录数量

### LLM调用优化

- 使用流式输出
- 批量处理请求
- 缓存常用结果

---

## 🎓 学习路径

### 初学者

1. 阅读`PROJECT_STATUS.md`了解当前状态
2. 阅读`CALL_CHAIN_FLOWCHART.md`了解整体流程
3. 运行`python -m cli chat`体验功能
4. 阅读`CALL_CHAIN_01_ENTRY.md`了解入口层

### 进阶

1. 阅读所有`CALL_CHAIN_*.md`文档
2. 阅读`CONTEXT_SEPARATION_EXPLAINED.md`了解设计
3. 阅读`AGENT_ARCHITECTURE.md`了解架构
4. 尝试开发自己的工具和Agent

### 高级

1. 研究工具输出优化系统
2. 研究Memory系统实现
3. 研究Function Calling循环
4. 优化性能和扩展功能

---

## 🔗 相关资源

- [项目状态](PROJECT_STATUS.md)
- [调用链路分析](CALL_CHAIN_ANALYSIS.md)
- [完整流程图](CALL_CHAIN_FLOWCHART.md)
- [可插拔架构设计](PLUGGABLE_ARCHITECTURE.md) ⭐
- [上下文分离设计](CONTEXT_SEPARATION_EXPLAINED.md)
- [Typer注册说明](TYPER_REGISTRATION_EXPLAINED.md)
- [Agent架构](AGENT_ARCHITECTURE.md)
- [项目概览](PROJECT_OVERVIEW.md)

---

**提示**: 这是一个快速参考指南，详细信息请查看相应的完整文档。

