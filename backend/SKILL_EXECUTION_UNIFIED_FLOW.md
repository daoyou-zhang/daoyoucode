# Skill执行的统一流程

> 从Skill配置看核心调用链路

## 🎯 核心理解

**你的理解完全正确！**

```
一个Skill从头到尾，核心调用流程是统一的。
不同的只是各个组件的内部实现差异。
```

---

## 📋 从Skill配置开始

### Skill配置文件（skill.yaml）

```yaml
# skills/chat-assistant/skill.yaml

name: chat_assistant
orchestrator: react      # ← 决定使用哪个编排器
agent: MainAgent         # ← 决定使用哪个Agent
tools:                   # ← 决定可用哪些工具
  - repo_map
  - read_file
  - text_search
```

**这个配置文件就是整个执行流程的"蓝图"！**

---

## 🔄 统一的执行流程

### 无论使用什么编排器/Agent，流程都是一样的：

```
用户输入
    ↓
execute_skill(skill_name="chat_assistant", user_input="...")
    ↓
1. 加载Skill配置（skill.yaml）
    ↓
2. 根据配置获取编排器（orchestrator: react）
    ↓
3. 编排器执行（orchestrator.execute()）
    ↓
4. 编排器内部：获取Agent（agent: MainAgent）
    ↓
5. Agent执行（agent.execute()）
    ↓
6. Agent内部：调用LLM + 工具（tools: [repo_map, read_file, ...]）
    ↓
7. 返回结果
```

---

## 💡 关键代码验证

### 1. Skill执行器（统一入口）

```python
# backend/daoyoucode/agents/executor.py

async def _execute_skill_internal(skill_name, user_input, context):
    # 1. 加载Skill配置
    skill = skill_loader.get_skill(skill_name)
    # skill.orchestrator = "react"
    # skill.agent = "MainAgent"
    # skill.tools = ["repo_map", "read_file", ...]
    
    # 2. 获取编排器（根据配置）
    orchestrator = get_orchestrator(skill.orchestrator)
    
    # 3. 执行（统一接口）
    result = await orchestrator.execute(skill, user_input, context)
    
    return result
```

**关键点**：
- ✅ 所有Skill都走这个统一入口
- ✅ 根据配置动态获取编排器
- ✅ 调用统一的`execute()`接口

---

### 2. 编排器执行（统一接口）

```python
# backend/daoyoucode/agents/core/orchestrator.py

class BaseOrchestrator(ABC):
    @abstractmethod
    async def execute(self, skill, user_input, context):
        """统一的执行接口"""
        pass
```

**所有编排器都实现这个接口**：

```python
# SimpleOrchestrator
async def execute(self, skill, user_input, context):
    agent = get_agent(skill.agent)  # ← 从配置获取Agent
    result = await agent.execute(...)
    return result

# ReActOrchestrator
async def execute(self, skill, user_input, context):
    agent = get_agent(skill.agent)  # ← 从配置获取Agent
    result = await agent.execute(...)
    return result

# ParallelOrchestrator
async def execute(self, skill, user_input, context):
    agents = [get_agent(name) for name in skill.agents]  # ← 从配置获取多个Agent
    results = await asyncio.gather(*[agent.execute(...) for agent in agents])
    return merge_results(results)
```

**关键点**：
- ✅ 统一的`execute()`接口
- ✅ 都从Skill配置获取Agent
- ✅ 都调用Agent的`execute()`
- ❌ 不同的是内部实现逻辑

---

### 3. Agent执行（统一接口）

```python
# backend/daoyoucode/agents/core/agent.py

class BaseAgent:
    async def execute(self, prompt_source, user_input, context, llm_config, tools):
        # 1. 准备prompt
        prompt = self._prepare_prompt(...)
        
        # 2. 调用LLM（带工具）
        response = await self._call_llm_with_tools(
            messages=[...],
            tool_names=tools,  # ← 从Skill配置传入
            llm_config=llm_config
        )
        
        return response
```

**关键点**：
- ✅ 统一的`execute()`接口
- ✅ 接收Skill配置的工具列表
- ✅ 调用LLM和工具
- ❌ 不同Agent的差异在于prompt和决策逻辑

---

## 🎨 不同组件的差异

### 编排器的差异（流程控制）

```python
# SimpleOrchestrator（简单执行）
async def execute(self, skill, user_input, context):
    agent = get_agent(skill.agent)
    result = await agent.execute(...)  # ← 直接执行
    return result

# ReActOrchestrator（推理循环）
async def execute(self, skill, user_input, context):
    agent = get_agent(skill.agent)
    result = await agent.execute(...)  # ← Agent内部有循环
    return result

# ParallelOrchestrator（并行执行）
async def execute(self, skill, user_input, context):
    agents = [get_agent(name) for name in skill.agents]
    results = await asyncio.gather(...)  # ← 并行执行多个Agent
    return merge_results(results)
```

**差异**：
- Simple：直接执行
- ReAct：依赖Agent的Function Calling循环
- Parallel：并行执行多个Agent

---

### Agent的差异（决策逻辑）

```python
# MainAgent（通用Agent）
class MainAgent(BaseAgent):
    def _prepare_prompt(self, ...):
        return "你是一个通用助手..."  # ← 通用prompt

# CodeAgent（代码专家）
class CodeAgent(BaseAgent):
    def _prepare_prompt(self, ...):
        return "你是一个代码专家..."  # ← 专业prompt

# AnalysisAgent（分析专家）
class AnalysisAgent(BaseAgent):
    def _prepare_prompt(self, ...):
        return "你是一个分析专家..."  # ← 分析prompt
```

**差异**：
- 主要是prompt不同
- 决策逻辑可能不同
- 但执行流程相同

---

### 工具的差异（具体操作）

```python
# RepoMapTool（生成代码地图）
class RepoMapTool(BaseTool):
    async def execute(self, repo_path):
        # 使用tree-sitter解析代码
        return code_map

# ReadFileTool（读取文件）
class ReadFileTool(BaseTool):
    async def execute(self, file_path):
        # 读取文件内容
        return file_content

# SearchTool（搜索）
class SearchTool(BaseTool):
    async def execute(self, pattern):
        # 搜索文件
        return search_results
```

**差异**：
- 每个工具的具体实现不同
- 但都实现`execute()`接口
- 都返回`ToolResult`

---

## 📊 完整流程图

```
用户输入: "这个项目的结构是什么？"
    ↓
execute_skill(
    skill_name="chat_assistant",
    user_input="这个项目的结构是什么？"
)
    ↓
┌─────────────────────────────────────────┐
│ 1. 加载Skill配置                         │
│    skill.yaml:                          │
│    - orchestrator: react                │
│    - agent: MainAgent                   │
│    - tools: [repo_map, read_file, ...]  │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 2. 获取编排器                            │
│    orchestrator = get_orchestrator("react") │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 3. 编排器执行                            │
│    orchestrator.execute(skill, ...)     │
│    ↓                                    │
│    内部：获取Agent                       │
│    agent = get_agent("MainAgent")       │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 4. Agent执行                             │
│    agent.execute(                       │
│        tools=["repo_map", "read_file", ...]  │
│    )                                    │
│    ↓                                    │
│    内部：Function Calling循环            │
│    - LLM决策：调用repo_map工具           │
│    - 执行工具：repo_map.execute()        │
│    - 获取结果：代码地图                  │
│    - LLM决策：返回答案                   │
└─────────────────────────────────────────┘
    ↓
返回结果: "项目包含以下模块..."
```

---

## 🎯 核心结论

### 1. 统一的接口

```python
# 所有编排器
class BaseOrchestrator:
    async def execute(self, skill, user_input, context):
        pass

# 所有Agent
class BaseAgent:
    async def execute(self, prompt_source, user_input, context, llm_config, tools):
        pass

# 所有工具
class BaseTool:
    async def execute(self, **kwargs):
        pass
```

**统一接口 = 可替换 = 可插拔**

---

### 2. 配置驱动

```yaml
# Skill配置决定一切
orchestrator: react      # ← 决定流程控制
agent: MainAgent         # ← 决定决策逻辑
tools: [...]             # ← 决定可用工具
```

**配置 = 蓝图 = 执行流程**

---

### 3. 差异在内部

```
相同：
✅ 执行流程（execute_skill → orchestrator → agent → tools）
✅ 接口定义（execute()）
✅ 数据流转（skill → context → result）

不同：
❌ 编排器的流程控制逻辑
❌ Agent的prompt和决策逻辑
❌ 工具的具体实现
```

---

## 💡 实际例子

### 例子1：使用Simple编排器

```yaml
# skill.yaml
orchestrator: simple
agent: MainAgent
tools: [repo_map]
```

**执行流程**：
```
execute_skill
    ↓
SimpleOrchestrator.execute()
    ↓ 直接执行
MainAgent.execute()
    ↓ 调用LLM
LLM决策 → 调用repo_map → 返回结果
```

---

### 例子2：使用ReAct编排器

```yaml
# skill.yaml
orchestrator: react
agent: MainAgent
tools: [repo_map, read_file]
```

**执行流程**：
```
execute_skill
    ↓
ReActOrchestrator.execute()
    ↓ 直接执行（循环在Agent内部）
MainAgent.execute()
    ↓ Function Calling循环
LLM决策 → 调用repo_map → 获取结果
    ↓
LLM决策 → 调用read_file → 获取结果
    ↓
LLM决策 → 返回答案
```

---

### 例子3：使用Parallel编排器

```yaml
# skill.yaml
orchestrator: parallel
agents:
  - CodeAgent
  - AnalysisAgent
tools: [repo_map, read_file]
```

**执行流程**：
```
execute_skill
    ↓
ParallelOrchestrator.execute()
    ↓ 并行执行
┌─────────────────┬─────────────────┐
│ CodeAgent       │ AnalysisAgent   │
│ .execute()      │ .execute()      │
│     ↓           │     ↓           │
│ LLM + 工具      │ LLM + 工具      │
└─────────────────┴─────────────────┘
    ↓
合并结果 → 返回
```

---

## 📚 如何梳理逻辑？

### 方法1：从Skill配置开始（推荐）

```
1. 看skill.yaml
   ↓
2. 找到orchestrator（如：react）
   ↓
3. 看orchestrators/react.py的execute()方法
   ↓
4. 找到agent（如：MainAgent）
   ↓
5. 看agents/main_agent.py的execute()方法
   ↓
6. 找到tools（如：repo_map）
   ↓
7. 看tools/repomap_tools.py的execute()方法
```

**优势**：
- ✅ 清晰直观
- ✅ 配置即文档
- ✅ 快速定位

---

### 方法2：从文档开始

```
1. 看CALL_CHAIN_ANALYSIS.md（总览）
   ↓
2. 看CALL_CHAIN_03_SKILL.md（Skill层）
   ↓
3. 看CALL_CHAIN_04_AGENT.md（Agent层）
   ↓
4. 看CALL_CHAIN_05_TOOL.md（工具层）
```

**优势**：
- ✅ 系统全面
- ✅ 理解设计
- ✅ 掌握原理

---

### 方法3：从代码开始

```
1. 看executor.py（执行入口）
   ↓
2. 看orchestrator.py（编排器基类）
   ↓
3. 看orchestrators/react.py（具体编排器）
   ↓
4. 看agent.py（Agent基类）
   ↓
5. 看tools/base.py（工具基类）
```

**优势**：
- ✅ 深入细节
- ✅ 理解实现
- ✅ 便于调试

---

## 🎨 设计精髓

### 1. 统一接口 + 多态实现

```python
# 统一接口
class BaseOrchestrator:
    async def execute(self, skill, user_input, context):
        pass

# 多态实现
class SimpleOrchestrator(BaseOrchestrator):
    async def execute(self, skill, user_input, context):
        # 简单实现
        pass

class ReActOrchestrator(BaseOrchestrator):
    async def execute(self, skill, user_input, context):
        # ReAct实现
        pass
```

**效果**：
- 调用方不需要知道具体实现
- 可以随时替换实现
- 易于扩展新实现

---

### 2. 配置驱动 + 动态加载

```python
# 配置驱动
skill = load_skill("chat_assistant")
orchestrator = get_orchestrator(skill.orchestrator)  # ← 动态获取

# 执行
result = await orchestrator.execute(skill, ...)
```

**效果**：
- 不需要修改代码
- 只需修改配置
- 灵活组合

---

### 3. 分层解耦 + 职责单一

```
Skill层：定义任务（配置）
    ↓
编排器层：控制流程（Simple/ReAct/Parallel）
    ↓
Agent层：智能决策（LLM + 工具）
    ↓
工具层：具体操作（repo_map/read_file/...）
```

**效果**：
- 每层职责清晰
- 修改影响小
- 易于测试

---

## 🚀 总结

### 你的理解完全正确！

```
✅ 核心调用流程是统一的
✅ 不同的是各个组件的内部实现
✅ 从Skill配置就能看出整个执行流程
✅ 配置 = 蓝图 = 执行路径
```

### 梳理逻辑的最佳方式

```
1. 看skill.yaml（配置）
   ↓
2. 找orchestrator（流程控制）
   ↓
3. 找agent（决策逻辑）
   ↓
4. 找tools（具体操作）
```

### 核心设计原则

```
统一接口 + 多态实现 = 可插拔
配置驱动 + 动态加载 = 灵活
分层解耦 + 职责单一 = 可维护
```

---

**这就是DaoyouCode的核心设计！简单、统一、强大！** 🎉
