# 多Agent协调时的Skill配置和Prompt传递机制

## 你的问题

> 多agent协调时，skill配置哪个可以看到？因为要传递多个prompt??

## 简短答案

**每个Agent使用自己的Prompt，不是传递多个Prompt！**

- **主Skill配置**：只有主Agent使用
- **辅助Agent**：使用各自Agent的默认Prompt（`use_agent_default: True`）
- **不需要传递多个Prompt**：每个Agent独立加载自己的Prompt

---

## 详细解释

### 1. Skill配置的结构

```yaml
# skills/sisyphus-orchestrator/skill.yaml
name: sisyphus-orchestrator
orchestrator: multi_agent
collaboration_mode: main_with_helpers

# Agent列表
agents:
  - sisyphus          # 主Agent
  - code_analyzer     # 辅助Agent 1
  - programmer        # 辅助Agent 2
  - test_expert       # 辅助Agent 3

# Prompt配置（只给主Agent用）
prompt:
  file: prompts/sisyphus.md

# 工具配置（只给主Agent用）
tools:
  - repo_map
  - text_search
  - read_file

# LLM配置（只给主Agent用）
llm:
  model: qwen-max
  temperature: 0.1
```

**关键点**：
- `prompt` 配置只给**主Agent**（第一个Agent）使用
- 辅助Agent使用各自的**默认Prompt**

---

### 2. 多Agent执行流程

#### 代码实现（`multi_agent.py`）

```python
async def _execute_main_with_helpers(
    self,
    agents: List,
    user_input: str,
    context: Dict[str, Any],
    skill: 'SkillConfig'
) -> Dict[str, Any]:
    """主Agent + 辅助Agent模式"""
    
    main_agent = agents[0]          # 第一个是主Agent
    helper_agents = agents[1:]      # 其他是辅助Agent
    
    # 1. 先执行辅助Agent（并行）
    helper_results = []
    if helper_agents:
        for agent in helper_agents:
            result = await agent.execute(
                prompt_source={'use_agent_default': True},  # ← 使用Agent默认Prompt
                user_input=user_input,
                context=context,
                tools=skill.tools if skill.tools else None
            )
            helper_results.append({
                'agent': agent.name,
                'content': result.content
            })
    
    # 2. 执行主Agent（可以看到辅助Agent的结果）
    main_context = {
        **context,
        'helper_results': helper_results  # ← 辅助Agent的结果
    }
    
    main_result = await main_agent.execute(
        prompt_source=skill.prompt,  # ← 使用Skill配置的Prompt
        user_input=user_input,
        context=main_context,
        llm_config=skill.llm,
        tools=skill.tools
    )
    
    return {
        'success': main_result.success,
        'content': main_result.content,
        'helper_results': helper_results
    }
```

---

### 3. Prompt加载机制

#### Agent的`_load_prompt`方法

```python
async def _load_prompt(
    self,
    prompt_source: Dict[str, Any],
    context: Dict[str, Any]
) -> str:
    """加载Prompt"""
    
    # 方式1：从文件加载（Skill配置）
    if 'file' in prompt_source:
        return await self._load_prompt_from_file(prompt_source['file'])
    
    # 方式2：内联Prompt
    elif 'inline' in prompt_source:
        return prompt_source['inline']
    
    # 方式3：使用Agent默认Prompt（辅助Agent用这个）
    elif prompt_source.get('use_agent_default'):
        return self.config.system_prompt
    
    else:
        raise ValueError(f"Invalid prompt source: {prompt_source}")
```

---

### 4. 实际例子

#### 场景：Sisyphus编排多个Agent

**用户请求**："重构登录模块并添加测试"

**执行流程**：

```
1. CLI加载Skill配置
   ↓
   skills/sisyphus-orchestrator/skill.yaml
   
2. 多Agent编排器执行
   ↓
   agents: [sisyphus, code_analyzer, programmer, test_expert]
   
3. 并行执行辅助Agent
   ↓
   code_analyzer.execute(
       prompt_source={'use_agent_default': True},  # ← 使用code_analyzer的默认Prompt
       user_input="重构登录模块并添加测试"
   )
   → 使用 code_analyzer.config.system_prompt
   → 返回：架构分析结果
   
   programmer.execute(
       prompt_source={'use_agent_default': True},  # ← 使用programmer的默认Prompt
       user_input="重构登录模块并添加测试"
   )
   → 使用 programmer.config.system_prompt
   → 返回：代码实现建议
   
   test_expert.execute(
       prompt_source={'use_agent_default': True},  # ← 使用test_expert的默认Prompt
       user_input="重构登录模块并添加测试"
   )
   → 使用 test_expert.config.system_prompt
   → 返回：测试策略
   
4. 执行主Agent（看到辅助Agent的结果）
   ↓
   sisyphus.execute(
       prompt_source={'file': 'skills/sisyphus-orchestrator/prompts/sisyphus.md'},
       user_input="重构登录模块并添加测试",
       context={
           'helper_results': [
               {'agent': 'code_analyzer', 'content': '架构分析...'},
               {'agent': 'programmer', 'content': '代码建议...'},
               {'agent': 'test_expert', 'content': '测试策略...'}
           ]
       }
   )
   → 使用 skills/sisyphus-orchestrator/prompts/sisyphus.md
   → 可以看到辅助Agent的结果（在context中）
   → 返回：综合的任务分解和执行计划
```

---

### 5. 每个Agent的Prompt在哪里？

#### 主Agent（Sisyphus）

**Prompt来源**：Skill配置
```yaml
# skills/sisyphus-orchestrator/skill.yaml
prompt:
  file: prompts/sisyphus.md
```

**Prompt内容**：`skills/sisyphus-orchestrator/prompts/sisyphus.md`
```markdown
# Sisyphus - 主编排Agent

你是Sisyphus，负责任务分解和Agent调度。

## 可用的辅助Agent
- code_analyzer：架构分析
- programmer：代码编写
- test_expert：测试编写

## 你可以看到辅助Agent的结果
在context中有 `helper_results`：
- [{'agent': 'code_analyzer', 'content': '...'}]
- [{'agent': 'programmer', 'content': '...'}]
- [{'agent': 'test_expert', 'content': '...'}]

## 你的任务
综合辅助Agent的建议，形成完整的执行计划。
```

#### 辅助Agent（code_analyzer）

**Prompt来源**：Agent默认配置
```python
# backend/daoyoucode/agents/builtin/code_analyzer.py
class CodeAnalyzerAgent(BaseAgent):
    def __init__(self):
        config = AgentConfig(
            name="code_analyzer",
            description="代码分析Agent",
            model="qwen-max",
            temperature=0.1,
            system_prompt="""
你是代码分析专家。

你的职责：
- 分析代码架构
- 识别问题
- 提供改进建议

你的工具：
- repo_map
- read_file
- text_search
- get_diagnostics
- parse_ast
"""
        )
        super().__init__(config)
```

**Prompt内容**：直接在Agent类中定义（`system_prompt`）

---

### 6. 为什么这样设计？

#### 优势

1. **解耦**：每个Agent有自己的Prompt，互不干扰
2. **复用**：辅助Agent可以在多个Skill中复用
3. **简单**：不需要在Skill中配置多个Prompt
4. **灵活**：主Agent可以看到辅助Agent的结果

#### 示例：同一个辅助Agent，不同的Skill

```yaml
# skills/sisyphus-orchestrator/skill.yaml
agents:
  - sisyphus
  - code_analyzer  # ← 使用code_analyzer的默认Prompt
  - programmer

---

# skills/oracle/skill.yaml
agents:
  - oracle
  - code_analyzer  # ← 同一个Agent，同样的Prompt
  - librarian
```

**code_analyzer在两个Skill中都使用相同的Prompt！**

---

### 7. 如果想自定义辅助Agent的Prompt怎么办？

#### 方案1：创建新的Agent（推荐）

```python
# backend/daoyoucode/agents/builtin/code_analyzer_strict.py
class CodeAnalyzerStrictAgent(BaseAgent):
    def __init__(self):
        config = AgentConfig(
            name="code_analyzer_strict",
            description="严格的代码分析Agent",
            system_prompt="""
你是严格的代码分析专家。

要求：
- 必须指出所有问题
- 不允许任何警告
- 强制最佳实践
"""
        )
        super().__init__(config)
```

然后在Skill中使用：
```yaml
agents:
  - sisyphus
  - code_analyzer_strict  # ← 使用新Agent
  - programmer
```

#### 方案2：使用内联Prompt（不推荐）

修改编排器代码，传递内联Prompt：
```python
result = await agent.execute(
    prompt_source={'inline': '自定义Prompt...'},
    user_input=user_input
)
```

**不推荐**：破坏了Agent的复用性

---

### 8. 主Agent如何看到辅助Agent的结果？

#### 通过Context传递

```python
# 编排器代码
main_context = {
    **context,
    'helper_results': [
        {'agent': 'code_analyzer', 'content': '架构分析结果...'},
        {'agent': 'programmer', 'content': '代码建议...'},
        {'agent': 'test_expert', 'content': '测试策略...'}
    ]
}

main_result = await main_agent.execute(
    prompt_source=skill.prompt,
    user_input=user_input,
    context=main_context  # ← 包含辅助Agent的结果
)
```

#### 主Agent的Prompt中引用

```markdown
# skills/sisyphus-orchestrator/prompts/sisyphus.md

你是Sisyphus，主编排Agent。

## 辅助Agent的结果

{% if helper_results %}
{% for result in helper_results %}
### {{ result.agent }}
{{ result.content }}
{% endfor %}
{% endif %}

## 你的任务
基于以上辅助Agent的分析，制定执行计划。
```

**使用Jinja2模板**：自动渲染`helper_results`

---

### 9. 完整的数据流

```
用户请求："重构登录模块并添加测试"
    ↓
CLI加载Skill
    ↓
skills/sisyphus-orchestrator/skill.yaml
    agents: [sisyphus, code_analyzer, programmer, test_expert]
    prompt: {file: prompts/sisyphus.md}
    ↓
多Agent编排器
    ↓
┌─────────────────────────────────────────────────────┐
│ 步骤1：并行执行辅助Agent                              │
├─────────────────────────────────────────────────────┤
│ code_analyzer.execute(                              │
│     prompt_source={'use_agent_default': True}       │
│ )                                                   │
│ → 使用 code_analyzer.config.system_prompt          │
│ → 返回："架构分析：登录模块耦合度高..."              │
│                                                     │
│ programmer.execute(                                 │
│     prompt_source={'use_agent_default': True}       │
│ )                                                   │
│ → 使用 programmer.config.system_prompt             │
│ → 返回："建议：拆分为3个模块..."                     │
│                                                     │
│ test_expert.execute(                                │
│     prompt_source={'use_agent_default': True}       │
│ )                                                   │
│ → 使用 test_expert.config.system_prompt            │
│ → 返回："测试策略：单元测试 + 集成测试..."           │
└─────────────────────────────────────────────────────┘
    ↓
    helper_results = [
        {'agent': 'code_analyzer', 'content': '架构分析...'},
        {'agent': 'programmer', 'content': '建议...'},
        {'agent': 'test_expert', 'content': '测试策略...'}
    ]
    ↓
┌─────────────────────────────────────────────────────┐
│ 步骤2：执行主Agent                                   │
├─────────────────────────────────────────────────────┤
│ sisyphus.execute(                                   │
│     prompt_source={'file': 'prompts/sisyphus.md'},  │
│     context={'helper_results': [...]}               │
│ )                                                   │
│ → 加载 skills/sisyphus-orchestrator/prompts/       │
│          sisyphus.md                                │
│ → 渲染Prompt（包含helper_results）                  │
│ → 调用LLM                                           │
│ → 返回："综合分析：                                  │
│          1. 架构问题：...                            │
│          2. 重构方案：...                            │
│          3. 测试计划：..."                           │
└─────────────────────────────────────────────────────┘
    ↓
返回给用户
```

---

## 总结

### 核心要点

1. **每个Agent使用自己的Prompt**
   - 主Agent：使用Skill配置的Prompt
   - 辅助Agent：使用各自的默认Prompt

2. **不需要传递多个Prompt**
   - 编排器自动处理
   - 每个Agent独立加载

3. **主Agent可以看到辅助Agent的结果**
   - 通过`context['helper_results']`传递
   - 在Prompt中使用Jinja2模板引用

4. **Skill配置只配置主Agent**
   - `prompt`：主Agent的Prompt
   - `tools`：主Agent的工具
   - `llm`：主Agent的LLM配置

5. **辅助Agent使用默认配置**
   - Prompt：`agent.config.system_prompt`
   - 工具：从`tool_groups.py`获取
   - LLM：`agent.config.model`

### 配置示例

```yaml
# skills/sisyphus-orchestrator/skill.yaml
name: sisyphus-orchestrator
orchestrator: multi_agent
collaboration_mode: main_with_helpers

# Agent列表
agents:
  - sisyphus          # 主Agent（使用下面的prompt配置）
  - code_analyzer     # 辅助Agent（使用默认Prompt）
  - programmer        # 辅助Agent（使用默认Prompt）
  - test_expert       # 辅助Agent（使用默认Prompt）

# 主Agent的Prompt配置
prompt:
  file: prompts/sisyphus.md

# 主Agent的工具配置
tools:
  - repo_map
  - text_search
  - read_file

# 主Agent的LLM配置
llm:
  model: qwen-max
  temperature: 0.1
```

### 代码位置

- **编排器**：`backend/daoyoucode/agents/orchestrators/multi_agent.py`
- **Prompt加载**：`backend/daoyoucode/agents/core/agent.py` (`_load_prompt`)
- **Skill配置**：`backend/daoyoucode/agents/core/skill.py`
- **Agent定义**：`backend/daoyoucode/agents/builtin/*.py`

---

**简单来说**：Skill配置只管主Agent，辅助Agent自己管自己！
