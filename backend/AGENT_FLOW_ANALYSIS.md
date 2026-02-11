# Agent系统完整流程分析

> 分析日期: 2026-02-12  
> 当前状态: Phase 1完成，工具系统待实现

---

## 一、整体架构流程

```
用户请求
    ↓
execute_skill (executor.py)
    ↓
Hook系统 (before hooks)
    ↓
Skill加载 (skill.yaml)
    ↓
Orchestrator选择 (simple/multi_agent/workflow/conditional/parallel)
    ↓
Agent执行 (BaseAgent.execute)
    ↓
    ├─ 加载Prompt (file/inline/default)
    ├─ 渲染Prompt (Jinja2)
    └─ 调用LLM (client_manager)
    ↓
Hook系统 (after hooks)
    ↓
返回结果
```

---

## 二、核心组件详解

### 1. 执行入口 (executor.py)

**文件**: `backend/daoyoucode/agents/executor.py`

**功能**:
- 统一的Skill执行入口
- 集成Hook系统
- 集成失败恢复
- 错误处理

**流程**:
```python
async def execute_skill(
    skill_name: str,
    user_input: str,
    session_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    recovery_config: Optional[RecoveryConfig] = None,
    validator: Optional[Callable] = None,
    analyzer: Optional[Callable] = None
) -> Dict[str, Any]:
    # 1. 运行before hooks
    # 2. 加载Skill配置
    # 3. 获取Orchestrator
    # 4. 执行
    # 5. 运行after hooks
    # 6. 返回结果
```

---

### 2. Skill系统 (core/skill.py)

**文件**: `backend/daoyoucode/agents/core/skill.py`

**功能**:
- 加载YAML配置
- 管理Skill注册表
- 解析Prompt路径

**Skill配置结构**:
```yaml
name: skill-name
version: 1.0.0
description: 描述

orchestrator: simple
agent: agent_name

prompt:
  file: prompts/prompt.md

llm:
  model: qwen-max
  temperature: 0.7

middleware:
  - context_management

permissions:
  read: [...]
  write: [...]

hooks:
  - logging
  - metrics
```

---

### 3. Orchestrator系统 (core/orchestrator.py)

**文件**: `backend/daoyoucode/agents/core/orchestrator.py`

**已实现的编排器**:

#### 3.1 SimpleOrchestrator
- 单Agent执行
- 应用中间件
- 最基础的编排

#### 3.2 MultiAgentOrchestrator
- 多Agent顺序执行
- 结果聚合
- 适合多专家协作

#### 3.3 WorkflowOrchestrator ✨新增
- 按步骤执行工作流
- 支持条件分支
- 步骤间数据传递
- 变量替换 `${variable}`

#### 3.4 ConditionalOrchestrator ✨新增
- 根据条件选择执行路径
- if_path / else_path
- 条件表达式评估

#### 3.5 ParallelOrchestrator ✨新增
- 并行执行多个Agent
- 智能结果聚合
- 提升响应速度

---

### 4. Agent系统 (core/agent.py)

**文件**: `backend/daoyoucode/agents/core/agent.py`

**核心类**:
- `AgentConfig`: Agent配置
- `AgentResult`: 执行结果
- `BaseAgent`: Agent基类
- `AgentRegistry`: Agent注册表

**执行流程**:
```python
async def execute(prompt_source, user_input, context, llm_config):
    # 1. 加载Prompt
    prompt = await self._load_prompt(prompt_source, context)
    
    # 2. 渲染Prompt (Jinja2)
    full_prompt = self._render_prompt(prompt, user_input, context)
    
    # 3. 调用LLM
    response = await self._call_llm(full_prompt, llm_config)
    
    # 4. 返回结果
    return AgentResult(success=True, content=response)
```

**Prompt加载方式**:
1. **文件**: `{'file': 'skills/xxx/prompts/xxx.md'}`
2. **内联**: `{'inline': 'prompt text'}`
3. **默认**: `{'use_agent_default': True}`

---

### 5. Hook系统 (core/hook.py)

**文件**: `backend/daoyoucode/agents/core/hook.py`

**生命周期**:
- `before_execute`: 执行前
- `after_execute`: 执行后
- `on_error`: 错误时

**内置Hook**:
1. **LoggingHook**: 记录执行日志
2. **MetricsHook**: 收集性能指标
3. **ValidationHook**: 输入验证
4. **RetryHook**: 自动重试

---

### 6. 权限系统 (core/permission.py)

**文件**: `backend/daoyoucode/agents/core/permission.py`

**功能**:
- 权限规则匹配
- 三种权限: allow/deny/ask
- 用户确认回调
- 装饰器支持

---

### 7. 失败恢复系统 (core/recovery.py)

**文件**: `backend/daoyoucode/agents/core/recovery.py`

**功能**:
- 自动重试（可配置次数）
- 结果验证
- 错误分析
- 修复建议生成
- 执行历史记录

---

### 8. LLM基础设施 (agents/llm/)

**功能**:
- 客户端管理器
- 连接池管理
- 上下文管理
- 智能加载策略

---

## 三、已实现的Agent

### 当前状态

| Agent | 文件 | Skill | Prompt | 状态 |
|-------|------|-------|--------|------|
| **TranslatorAgent** | translator.py | translation | translator.md | ✅ |
| **ProgrammerAgent** | programmer.py | programming | programmer.md | ✅ |
| **CodeAnalyzerAgent** | code_analyzer.py | code-analysis | oracle.md | ✅ |
| **CodeExplorerAgent** | code_explorer.py | code-exploration | explore.md | ✅ |
| **RefactorMasterAgent** | refactor_master.py | refactoring | refactor.md | ✅ |
| **TestExpertAgent** | test_expert.py | testing | test.md | ✅ |

**总计**: 6个Agent，全部实现 ✅

---

## 四、工具调用系统（待实现）

### 当前状态

**问题**: 工具调用系统尚未实现 ❌

**现状**:
- `AgentResult.tools_used` 字段已定义，但未使用
- `backend/daoyoucode/tools/` 目录为空
- Agent执行流程中没有工具调用逻辑

### 需要实现的工具系统

根据`完整功能清单.md`和`核心设计文档.md`，需要实现：

#### 4.1 LSP工具（借鉴oh-my-opencode）

**功能**:
- `lsp_diagnostics`: 获取错误/警告
- `lsp_rename`: 跨工作区重命名
- `lsp_goto_definition`: 跳转定义
- `lsp_find_references`: 查找引用
- `lsp_symbols`: 符号搜索
- `lsp_code_actions`: 代码操作

**实现位置**: `backend/daoyoucode/tools/lsp/`

#### 4.2 AST工具（借鉴oh-my-opencode）

**功能**:
- `ast_grep_search`: AST级搜索（25种语言）
- `ast_grep_replace`: AST级替换

**实现位置**: `backend/daoyoucode/tools/ast/`

#### 4.3 Git工具

**功能**:
- 自动提交
- 智能commit message
- 原子提交
- 历史分析
- Git状态查询

**实现位置**: `backend/daoyoucode/tools/git/`

#### 4.4 文件操作工具

**功能**:
- `read_file`: 读取文件
- `write_file`: 写入文件
- `list_files`: 列出目录
- `get_file_info`: 文件信息
- `create_directory`: 创建目录
- `delete_file`: 删除文件

**实现位置**: `backend/daoyoucode/tools/file/`

#### 4.5 代码搜索工具

**功能**:
- 文本搜索（ripgrep）
- 正则搜索
- AST搜索
- 语义搜索（LSP）

**实现位置**: `backend/daoyoucode/tools/search/`

#### 4.6 测试工具

**功能**:
- `run_test`: 运行测试
- 测试失败修复
- 测试结果分析

**实现位置**: `backend/daoyoucode/tools/test/`

---

## 五、工具调用流程设计

### 5.1 工具注册系统

```python
# backend/daoyoucode/tools/registry.py

class Tool:
    """工具基类"""
    name: str
    description: str
    parameters: Dict[str, Any]
    
    async def execute(self, **kwargs) -> Any:
        """执行工具"""
        pass

class ToolRegistry:
    """工具注册表"""
    
    def register(self, tool: Tool):
        """注册工具"""
        pass
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """获取工具"""
        pass
    
    def list_tools(self) -> List[str]:
        """列出所有工具"""
        pass
```

### 5.2 Agent集成工具

```python
# backend/daoyoucode/agents/core/agent.py

class BaseAgent(ABC):
    
    async def execute(self, ...):
        # 1. 加载Prompt
        prompt = await self._load_prompt(...)
        
        # 2. 获取可用工具
        tools = self._get_available_tools()
        
        # 3. 渲染Prompt（包含工具描述）
        full_prompt = self._render_prompt_with_tools(prompt, tools, ...)
        
        # 4. 调用LLM（支持Function Calling）
        response = await self._call_llm_with_tools(full_prompt, tools, ...)
        
        # 5. 解析工具调用
        tool_calls = self._parse_tool_calls(response)
        
        # 6. 执行工具
        tool_results = await self._execute_tools(tool_calls)
        
        # 7. 返回结果
        return AgentResult(
            success=True,
            content=response,
            tools_used=[call['name'] for call in tool_calls]
        )
```

### 5.3 LLM Function Calling

```python
# backend/daoyoucode/agents/llm/clients/unified.py

class UnifiedLLMClient:
    
    async def chat_with_tools(
        self,
        messages: List[Dict],
        tools: List[Tool],
        temperature: float = 0.7
    ) -> Dict:
        """支持工具调用的对话"""
        
        # 转换工具为Function Calling格式
        functions = [tool.to_function_schema() for tool in tools]
        
        # 调用LLM
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            functions=functions,
            temperature=temperature
        )
        
        # 解析响应
        if response.function_call:
            return {
                'type': 'function_call',
                'name': response.function_call.name,
                'arguments': response.function_call.arguments
            }
        else:
            return {
                'type': 'text',
                'content': response.content
            }
```

---

## 六、完整执行流程示例

### 示例1: 代码分析（无工具）

```python
# 用户请求
result = await execute_skill(
    skill_name='code-analysis',
    user_input='分析这个模块的架构',
    context={'code_content': code}
)

# 执行流程
1. executor.py: execute_skill()
2. Hook: before_execute (logging, metrics)
3. Skill: 加载 code-analysis/skill.yaml
4. Orchestrator: SimpleOrchestrator
5. Agent: CodeAnalyzerAgent.execute()
   - 加载 prompts/oracle.md
   - 渲染 Prompt + code_content
   - 调用 LLM (qwen-max)
6. Hook: after_execute (logging, metrics)
7. 返回: AgentResult
```

### 示例2: 代码搜索（需要工具）

```python
# 用户请求
result = await execute_skill(
    skill_name='code-exploration',
    user_input='在哪里实现了用户认证？',
    context={'search_scope': 'src/'}
)

# 执行流程（工具系统实现后）
1. executor.py: execute_skill()
2. Hook: before_execute
3. Skill: 加载 code-exploration/skill.yaml
4. Orchestrator: SimpleOrchestrator
5. Agent: CodeExplorerAgent.execute()
   - 加载 prompts/explore.md
   - 获取可用工具: [grep, ast_grep, lsp_symbols]
   - 渲染 Prompt + 工具描述
   - 调用 LLM (支持Function Calling)
   - LLM返回: 调用 grep("user.*auth")
   - 执行工具: grep.execute(pattern="user.*auth")
   - 获取结果: [file1.py, file2.py]
   - 再次调用 LLM: 分析结果
6. Hook: after_execute
7. 返回: AgentResult (tools_used=['grep'])
```

---

## 七、待实现功能清单

### Phase 2: 工具系统（高优先级）

- [ ] **工具注册系统** - Tool基类、ToolRegistry
- [ ] **LSP工具集成** - 6个LSP工具
- [ ] **文件操作工具** - 6个文件工具
- [ ] **代码搜索工具** - 4种搜索方式
- [ ] **Git工具** - 基础Git操作
- [ ] **Function Calling** - LLM工具调用支持
- [ ] **Agent工具集成** - 修改BaseAgent支持工具

### Phase 3: 高级功能（中优先级）

- [ ] **后台任务执行** - BackgroundTaskManager
- [ ] **动态Prompt构建** - DynamicPromptBuilder
- [ ] **AST工具集成** - ast-grep
- [ ] **测试工具** - 运行测试、自动修复

### Phase 4: 扩展功能（低优先级）

- [ ] **浏览器自动化** - Playwright集成
- [ ] **MCP集成** - 外部工具协议
- [ ] **Commands系统** - 自定义命令
- [ ] **更多Agent** - Librarian、Sisyphus等

---

## 八、总结

### 当前完成度

| 模块 | 完成度 | 状态 |
|------|--------|------|
| **核心架构** | 100% | ✅ 完成 |
| **Skill系统** | 100% | ✅ 完成 |
| **Agent系统** | 100% | ✅ 6个Agent |
| **Orchestrator** | 100% | ✅ 5种编排器 |
| **Hook系统** | 100% | ✅ 4个Hook |
| **权限系统** | 100% | ✅ 完成 |
| **失败恢复** | 100% | ✅ 完成 |
| **工具系统** | 0% | ❌ 待实现 |
| **LLM基础设施** | 80% | ⚠️ 缺Function Calling |

### 核心优势

1. ✅ **完全可插拔架构** - Skill/Agent/Prompt/Orchestrator
2. ✅ **配置驱动** - YAML配置，无需修改代码
3. ✅ **强大的编排能力** - 5种编排器
4. ✅ **完善的扩展机制** - Hook/权限/恢复
5. ❌ **工具调用能力** - 待实现

### 下一步重点

**优先实现工具系统**，这是编程辅助Agent发挥作用的关键！

1. 工具注册系统
2. 文件操作工具（最基础）
3. 代码搜索工具（CodeExplorer需要）
4. LSP工具（高级功能）
5. Function Calling支持

---

**当前状态**: Phase 1完成，Phase 2（工具系统）待实现 🚀
