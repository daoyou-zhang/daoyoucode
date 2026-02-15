# 可插拔架构设计详解

> DaoyouCode 的扩展能力极强的插件化架构

## 🎯 核心设计理念

**一切皆可插拔，一切皆可扩展**

```
注册表模式 + 单例模式 + 工厂模式 = 强大的可插拔架构
```

---

## 📐 架构概览

### 三大注册表系统

```
┌─────────────────────────────────────────────────────────┐
│                    Agent系统初始化                       │
│                 initialize_agent_system()               │
└─────────────────────────────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │ 工具注册表    │ │ Agent注册表  │ │ 编排器注册表  │
    │ToolRegistry  │ │AgentRegistry │ │Orchestrator  │
    │              │ │              │ │Registry      │
    │ 25个工具     │ │ 7个Agent     │ │ 3个编排器    │
    └──────────────┘ └──────────────┘ └──────────────┘
```

---

## 🔧 1. 工具注册表（ToolRegistry）

### 设计特点

✅ **单例模式** - 全局唯一实例  
✅ **自动注册** - 初始化时自动注册所有内置工具  
✅ **延迟加载** - 只在需要时创建实例  
✅ **类型安全** - 所有工具继承`BaseTool`  
✅ **易于扩展** - 添加新工具只需3步

### 实现代码

```python
# backend/daoyoucode/agents/tools/registry.py

# 全局单例
_tool_registry = None

def get_tool_registry() -> ToolRegistry:
    """获取工具注册表单例"""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
        _register_builtin_tools()  # 自动注册内置工具
    return _tool_registry

def _register_builtin_tools():
    """注册内置工具"""
    # 文件操作工具（6个）
    _tool_registry.register(ReadFileTool())
    _tool_registry.register(WriteFileTool())
    _tool_registry.register(ListFilesTool())
    _tool_registry.register(GetFileInfoTool())
    _tool_registry.register(CreateDirectoryTool())
    _tool_registry.register(DeleteFileTool())
    
    # 搜索工具（2个）
    _tool_registry.register(TextSearchTool())
    _tool_registry.register(RegexSearchTool())
    
    # Git工具（4个）
    _tool_registry.register(GitStatusTool())
    _tool_registry.register(GitDiffTool())
    _tool_registry.register(GitCommitTool())
    _tool_registry.register(GitLogTool())
    
    # 命令执行工具（2个）
    _tool_registry.register(RunCommandTool())
    _tool_registry.register(RunTestTool())
    
    # Diff工具（1个）
    _tool_registry.register(SearchReplaceTool())
    
    # RepoMap工具（2个）
    _tool_registry.register(RepoMapTool())
    _tool_registry.register(GetRepoStructureTool())
    
    # LSP工具（6个）
    _tool_registry.register(LSPDiagnosticsTool())
    _tool_registry.register(LSPGotoDefinitionTool())
    _tool_registry.register(LSPFindReferencesTool())
    _tool_registry.register(LSPSymbolsTool())
    _tool_registry.register(LSPRenameTool())
    _tool_registry.register(LSPCodeActionsTool())
    
    # AST工具（2个）
    _tool_registry.register(AstGrepSearchTool())
    _tool_registry.register(AstGrepReplaceTool())
```

### 如何添加新工具？

**只需3步**：

```python
# 步骤1: 创建工具类
from daoyoucode.agents.tools.base import BaseTool, ToolResult

class MyNewTool(BaseTool):
    name = "my_new_tool"
    description = "我的新工具"
    
    async def execute(self, **kwargs) -> ToolResult:
        # 实现工具逻辑
        return ToolResult(success=True, content="结果")

# 步骤2: 在registry.py中导入
from .my_tools import MyNewTool

# 步骤3: 在_register_builtin_tools()中注册
_tool_registry.register(MyNewTool())
```

**就这么简单！** 🎉

---

## 🤖 2. Agent注册表（AgentRegistry）

### 设计特点

✅ **单例模式** - 全局唯一实例  
✅ **集中注册** - 所有Agent在`builtin/__init__.py`中注册  
✅ **按需加载** - Agent实例在需要时创建  
✅ **类型安全** - 所有Agent继承`BaseAgent`  
✅ **职责清晰** - 每个Agent有明确的职责

### 实现代码

```python
# backend/daoyoucode/agents/builtin/__init__.py

def register_builtin_agents():
    """注册所有内置Agent"""
    
    # 主Agent
    register_agent(MainAgent())
    
    # 基础Agent
    register_agent(TranslatorAgent())
    register_agent(ProgrammerAgent())
    
    # 编程辅助Agent（借鉴oh-my-opencode）
    register_agent(CodeAnalyzerAgent())      # Oracle - 架构顾问
    register_agent(CodeExplorerAgent())      # Explore - 代码搜索
    register_agent(RefactorMasterAgent())    # 重构专家
    register_agent(TestExpertAgent())        # 测试专家
```

### 当前注册的Agent

| Agent | 职责 | 灵感来源 |
|-------|------|----------|
| MainAgent | 主对话Agent | - |
| TranslatorAgent | 翻译Agent | - |
| ProgrammerAgent | 编程Agent | - |
| CodeAnalyzerAgent | 架构顾问 | oh-my-opencode Oracle |
| CodeExplorerAgent | 代码搜索 | oh-my-opencode Explore |
| RefactorMasterAgent | 重构专家 | - |
| TestExpertAgent | 测试专家 | - |

### 如何添加新Agent？

**只需3步**：

```python
# 步骤1: 创建Agent类
from daoyoucode.agents.core.agent import BaseAgent, AgentConfig

class MyNewAgent(BaseAgent):
    def __init__(self):
        config = AgentConfig(
            name="MyNewAgent",
            description="我的新Agent",
            model="qwen-plus",
            system_prompt="你是..."
        )
        super().__init__(config)

# 步骤2: 在builtin/__init__.py中导入
from .my_agent import MyNewAgent

# 步骤3: 在register_builtin_agents()中注册
register_agent(MyNewAgent())
```

**就这么简单！** 🎉

---

## 🎭 3. 编排器注册表（OrchestratorRegistry）

### 设计特点

✅ **单例模式** - 全局唯一实例  
✅ **工厂模式** - 按需创建编排器实例  
✅ **策略模式** - 不同编排器实现不同策略  
✅ **类型安全** - 所有编排器继承`BaseOrchestrator`  
✅ **灵活组合** - Skill可以选择不同的编排器

### 实现代码

```python
# backend/daoyoucode/agents/core/orchestrator.py

class OrchestratorRegistry:
    """编排器注册表"""
    
    def __init__(self):
        self._orchestrators: Dict[str, type] = {}
        self._instances: Dict[str, BaseOrchestrator] = {}
    
    def register(self, name: str, orchestrator_class: type):
        """注册编排器"""
        self._orchestrators[name] = orchestrator_class
    
    def get(self, name: str) -> Optional[BaseOrchestrator]:
        """获取编排器实例（单例）"""
        if name not in self._instances:
            self._instances[name] = self._orchestrators[name]()
        return self._instances[name]

# 全局注册表
_orchestrator_registry = OrchestratorRegistry()

def get_orchestrator_registry() -> OrchestratorRegistry:
    return _orchestrator_registry
```

### 当前注册的编排器

| 编排器 | 策略 | 用途 |
|--------|------|------|
| SimpleOrchestrator | 简单执行 | 单Agent直接执行 |
| ReActOrchestrator | ReAct循环 | 推理-行动循环 |
| MultiAgentOrchestrator | 多Agent协作 | 复杂任务分解 |

### 如何添加新编排器？

**只需3步**：

```python
# 步骤1: 创建编排器类
from daoyoucode.agents.core.orchestrator import BaseOrchestrator

class MyNewOrchestrator(BaseOrchestrator):
    async def execute(self, skill, user_input, context):
        # 实现编排逻辑
        agent = self._get_agent(skill.agent)
        result = await agent.execute(...)
        return result

# 步骤2: 在orchestrators/__init__.py中导入
from .my_orchestrator import MyNewOrchestrator

# 步骤3: 注册编排器
from daoyoucode.agents.core.orchestrator import register_orchestrator
register_orchestrator("my_new", MyNewOrchestrator)
```

**就这么简单！** 🎉

---

## 🚀 统一初始化系统

### 幂等初始化

```python
# backend/daoyoucode/agents/init.py

_initialized = False

def initialize_agent_system():
    """
    初始化Agent系统（幂等操作）
    
    这个函数可以被多次调用，不会重复初始化
    """
    global _initialized
    
    if _initialized:
        return get_tool_registry()
    
    # 1. 初始化工具注册表
    tool_registry = get_tool_registry()
    
    # 2. 注册内置Agent
    register_builtin_agents()
    
    # 3. 注册内置编排器
    orchestrator_registry = get_orchestrator_registry()
    
    _initialized = True
    return tool_registry
```

### 调用位置

```python
# backend/cli/commands/chat.py

def handle_chat(user_input: str, ui_context: dict):
    """处理对话"""
    
    # 初始化Agent系统（幂等，可以多次调用）
    from daoyoucode.agents.init import initialize_agent_system
    initialize_agent_system()
    
    # 执行Skill
    from daoyoucode.agents.executor import execute_skill
    result = await execute_skill(...)
```

---

## 💡 设计模式分析

### 1. 注册表模式（Registry Pattern）

**用途**: 管理所有可插拔组件

**优点**:
- ✅ 集中管理
- ✅ 易于查找
- ✅ 避免硬编码

**实现**:
```python
class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
    
    def register(self, tool: BaseTool):
        self._tools[tool.name] = tool
    
    def get(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)
```

---

### 2. 单例模式（Singleton Pattern）

**用途**: 确保全局唯一实例

**优点**:
- ✅ 避免重复创建
- ✅ 全局访问点
- ✅ 节省资源

**实现**:
```python
_tool_registry = None

def get_tool_registry() -> ToolRegistry:
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    return _tool_registry
```

---

### 3. 工厂模式（Factory Pattern）

**用途**: 按需创建对象

**优点**:
- ✅ 延迟创建
- ✅ 解耦创建逻辑
- ✅ 易于扩展

**实现**:
```python
class OrchestratorRegistry:
    def get(self, name: str) -> BaseOrchestrator:
        if name not in self._instances:
            self._instances[name] = self._orchestrators[name]()
        return self._instances[name]
```

---

### 4. 策略模式（Strategy Pattern）

**用途**: 不同的编排策略

**优点**:
- ✅ 算法可替换
- ✅ 易于扩展
- ✅ 避免条件语句

**实现**:
```python
class BaseOrchestrator(ABC):
    @abstractmethod
    async def execute(self, skill, user_input, context):
        pass

class SimpleOrchestrator(BaseOrchestrator):
    async def execute(self, skill, user_input, context):
        # 简单执行策略
        pass

class ReActOrchestrator(BaseOrchestrator):
    async def execute(self, skill, user_input, context):
        # ReAct循环策略
        pass
```

---

## 🎨 扩展能力展示

### 扩展1: 添加新工具

```python
# 1. 创建工具文件: backend/daoyoucode/agents/tools/my_tools.py
class DatabaseQueryTool(BaseTool):
    name = "database_query"
    description = "查询数据库"
    
    async def execute(self, query: str) -> ToolResult:
        # 实现数据库查询
        return ToolResult(success=True, content=result)

# 2. 在registry.py中注册
from .my_tools import DatabaseQueryTool
_tool_registry.register(DatabaseQueryTool())

# 3. 完成！工具立即可用
```

---

### 扩展2: 添加新Agent

```python
# 1. 创建Agent文件: backend/daoyoucode/agents/builtin/database_expert.py
class DatabaseExpertAgent(BaseAgent):
    def __init__(self):
        config = AgentConfig(
            name="DatabaseExpert",
            description="数据库专家",
            model="qwen-plus",
            system_prompt="你是数据库专家..."
        )
        super().__init__(config)

# 2. 在builtin/__init__.py中注册
from .database_expert import DatabaseExpertAgent
register_agent(DatabaseExpertAgent())

# 3. 完成！Agent立即可用
```

---

### 扩展3: 添加新编排器

```python
# 1. 创建编排器文件: backend/daoyoucode/agents/orchestrators/parallel.py
class ParallelOrchestrator(BaseOrchestrator):
    async def execute(self, skill, user_input, context):
        # 实现并行执行逻辑
        agents = [self._get_agent(name) for name in skill.agents]
        results = await asyncio.gather(*[
            agent.execute(...) for agent in agents
        ])
        return merge_results(results)

# 2. 注册编排器
register_orchestrator("parallel", ParallelOrchestrator)

# 3. 在Skill配置中使用
# skill.yaml:
# orchestrator: parallel
```

---

## 📊 架构优势

### 1. 高度解耦

```
工具 ← 注册表 → Agent ← 注册表 → 编排器
  ↓                ↓                ↓
独立开发        独立开发        独立开发
独立测试        独立测试        独立测试
独立部署        独立部署        独立部署
```

### 2. 易于测试

```python
# 测试工具
def test_my_tool():
    tool = MyNewTool()
    result = await tool.execute(param="value")
    assert result.success

# 测试Agent
def test_my_agent():
    agent = MyNewAgent()
    result = await agent.execute(...)
    assert result.success

# 测试编排器
def test_my_orchestrator():
    orchestrator = MyNewOrchestrator()
    result = await orchestrator.execute(...)
    assert result.success
```

### 3. 易于扩展

**添加新功能的成本**:
- 新工具: 1个文件 + 1行注册代码
- 新Agent: 1个文件 + 1行注册代码
- 新编排器: 1个文件 + 1行注册代码

**不需要修改**:
- ❌ 核心框架代码
- ❌ 其他工具/Agent/编排器
- ❌ 配置文件（除了Skill配置）

### 4. 易于维护

**职责清晰**:
- 工具: 只负责执行具体操作
- Agent: 只负责决策和调用工具
- 编排器: 只负责协调执行流程
- 注册表: 只负责管理组件

**修改影响小**:
- 修改工具: 只影响使用该工具的Agent
- 修改Agent: 只影响使用该Agent的Skill
- 修改编排器: 只影响使用该编排器的Skill

---

## 🔍 实际应用示例

### 示例1: 添加Slack通知工具

```python
# 1. 创建工具
class SlackNotifyTool(BaseTool):
    name = "slack_notify"
    description = "发送Slack通知"
    
    async def execute(self, channel: str, message: str) -> ToolResult:
        # 调用Slack API
        await slack_client.send_message(channel, message)
        return ToolResult(success=True, content="通知已发送")

# 2. 注册工具
_tool_registry.register(SlackNotifyTool())

# 3. Agent自动可以使用
# LLM会看到这个工具，并在需要时调用
```

---

### 示例2: 添加代码审查Agent

```python
# 1. 创建Agent
class CodeReviewerAgent(BaseAgent):
    def __init__(self):
        config = AgentConfig(
            name="CodeReviewer",
            description="代码审查专家",
            model="qwen-plus",
            system_prompt="""你是代码审查专家。
            
            你的职责：
            1. 检查代码质量
            2. 发现潜在问题
            3. 提供改进建议
            
            可用工具：
            - read_file: 读取代码文件
            - ast_grep_search: 搜索代码模式
            - lsp_diagnostics: 获取诊断信息
            """
        )
        super().__init__(config)

# 2. 注册Agent
register_agent(CodeReviewerAgent())

# 3. 创建Skill配置
# skills/code-review/skill.yaml:
# name: code_review
# agent: CodeReviewer
# orchestrator: simple
```

---

### 示例3: 添加并行执行编排器

```python
# 1. 创建编排器
class ParallelOrchestrator(BaseOrchestrator):
    async def execute(self, skill, user_input, context):
        # 并行执行多个Agent
        tasks = []
        for agent_name in skill.agents:
            agent = self._get_agent(agent_name)
            task = agent.execute(user_input, context)
            tasks.append(task)
        
        # 等待所有Agent完成
        results = await asyncio.gather(*tasks)
        
        # 合并结果
        return self._merge_results(results)

# 2. 注册编排器
register_orchestrator("parallel", ParallelOrchestrator)

# 3. 在Skill中使用
# skill.yaml:
# orchestrator: parallel
# agents:
#   - CodeAnalyzer
#   - CodeExplorer
#   - RefactorMaster
```

---

## 🎯 最佳实践

### 1. 工具开发

✅ **单一职责**: 每个工具只做一件事  
✅ **清晰描述**: description要详细，LLM才能理解  
✅ **错误处理**: 捕获异常，返回友好的错误信息  
✅ **输出限制**: 设置MAX_OUTPUT_CHARS避免输出过长  
✅ **元数据**: 使用metadata传递额外信息

```python
class GoodTool(BaseTool):
    name = "good_tool"
    description = "详细的工具描述，包括参数说明和使用场景"
    MAX_OUTPUT_CHARS = 5000
    
    async def execute(self, param: str) -> ToolResult:
        try:
            result = do_something(param)
            return ToolResult(
                success=True,
                content=result,
                metadata={"execution_time": 0.5}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"执行失败: {str(e)}"
            )
```

---

### 2. Agent开发

✅ **清晰的system_prompt**: 说明Agent的职责和能力  
✅ **合适的模型**: 根据任务复杂度选择模型  
✅ **合适的temperature**: 创造性任务用高温度，精确任务用低温度  
✅ **工具说明**: 在prompt中说明可用工具

```python
class GoodAgent(BaseAgent):
    def __init__(self):
        config = AgentConfig(
            name="GoodAgent",
            description="清晰的Agent描述",
            model="qwen-plus",
            temperature=0.7,
            system_prompt="""你是XXX专家。
            
            你的职责：
            1. ...
            2. ...
            
            可用工具：
            - tool1: 用途说明
            - tool2: 用途说明
            
            工作流程：
            1. ...
            2. ...
            """
        )
        super().__init__(config)
```

---

### 3. 编排器开发

✅ **清晰的执行流程**: 明确的步骤和逻辑  
✅ **错误处理**: 处理Agent执行失败的情况  
✅ **上下文传递**: 正确传递和更新context  
✅ **结果合并**: 合理合并多个Agent的结果

```python
class GoodOrchestrator(BaseOrchestrator):
    async def execute(self, skill, user_input, context):
        try:
            # 1. 准备上下文
            context = await self._prepare_context(context)
            
            # 2. 执行Agent
            agent = self._get_agent(skill.agent)
            result = await agent.execute(user_input, context)
            
            # 3. 后处理
            result = await self._post_process(result)
            
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
```

---

## 📝 总结

### 核心优势

1. ✅ **可插拔**: 所有组件都可以独立添加/移除
2. ✅ **可扩展**: 添加新功能成本极低
3. ✅ **可测试**: 每个组件都可以独立测试
4. ✅ **可维护**: 职责清晰，修改影响小
5. ✅ **易理解**: 注册表模式简单直观

### 扩展成本

| 操作 | 文件数 | 代码行数 | 修改核心代码 |
|------|--------|----------|--------------|
| 添加工具 | 1 | ~30 | ❌ 否 |
| 添加Agent | 1 | ~20 | ❌ 否 |
| 添加编排器 | 1 | ~50 | ❌ 否 |

### 设计模式

- 注册表模式: 管理组件
- 单例模式: 全局唯一实例
- 工厂模式: 按需创建对象
- 策略模式: 可替换的算法

---

## 🚀 未来扩展方向

### 1. 插件系统

```python
# 支持外部插件
class PluginManager:
    def load_plugin(self, plugin_path: str):
        # 动态加载插件
        module = importlib.import_module(plugin_path)
        
        # 自动注册工具
        for tool in module.get_tools():
            get_tool_registry().register(tool)
        
        # 自动注册Agent
        for agent in module.get_agents():
            register_agent(agent)
```

### 2. 热重载

```python
# 支持运行时重载
class HotReloader:
    def reload_tool(self, tool_name: str):
        # 重新加载工具
        registry = get_tool_registry()
        registry.unregister(tool_name)
        registry.register(new_tool)
```

### 3. 远程工具

```python
# 支持远程工具调用
class RemoteTool(BaseTool):
    async def execute(self, **kwargs):
        # 通过RPC调用远程工具
        result = await rpc_client.call(self.name, kwargs)
        return result
```

---

**这就是DaoyouCode的可插拔架构！扩展能力极强，开发成本极低！** 🎉

