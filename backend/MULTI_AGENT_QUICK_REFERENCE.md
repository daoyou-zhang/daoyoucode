# 多Agent快速参考

## 一句话总结

**Skill配置只管主Agent，辅助Agent自己管自己！**

---

## 快速问答

### Q1: Skill配置的Prompt给谁用？

**A**: 只给主Agent（第一个Agent）用

```yaml
agents:
  - sisyphus          # ← 主Agent，使用下面的prompt
  - code_analyzer     # ← 辅助Agent，使用默认Prompt
  - programmer        # ← 辅助Agent，使用默认Prompt

prompt:
  file: prompts/sisyphus.md  # ← 只给sisyphus用
```

---

### Q2: 辅助Agent的Prompt在哪里？

**A**: 在Agent定义文件中（`builtin/*.py`）

```python
# backend/daoyoucode/agents/builtin/code_analyzer.py
class CodeAnalyzerAgent(BaseAgent):
    def __init__(self):
        config = AgentConfig(
            name="code_analyzer",
            system_prompt="""
你是代码分析专家...
"""  # ← 辅助Agent的Prompt在这里
        )
```

---

### Q3: 需要传递多个Prompt吗？

**A**: 不需要！每个Agent自己加载自己的Prompt

```python
# 编排器代码
# 辅助Agent
await agent.execute(
    prompt_source={'use_agent_default': True}  # ← 使用默认Prompt
)

# 主Agent
await agent.execute(
    prompt_source={'file': 'prompts/sisyphus.md'}  # ← 使用Skill配置
)
```

---

### Q4: 主Agent如何看到辅助Agent的结果？

**A**: 通过Context传递

```python
# 编排器代码
main_context = {
    **context,
    'helper_results': [  # ← 辅助Agent的结果
        {'agent': 'code_analyzer', 'content': '...'},
        {'agent': 'programmer', 'content': '...'}
    ]
}

await main_agent.execute(
    context=main_context  # ← 传递给主Agent
)
```

主Agent的Prompt中可以引用：
```markdown
{% if helper_results %}
{% for result in helper_results %}
### {{ result.agent }}
{{ result.content }}
{% endfor %}
{% endif %}
```

---

### Q5: 如何自定义辅助Agent的Prompt？

**A**: 创建新的Agent（推荐）

```python
# 方案1：创建新Agent（推荐）
class CodeAnalyzerStrictAgent(BaseAgent):
    def __init__(self):
        config = AgentConfig(
            name="code_analyzer_strict",
            system_prompt="自定义Prompt..."
        )

# 方案2：修改现有Agent的system_prompt（不推荐）
# 会影响所有使用该Agent的Skill
```

---

## 配置模板

### 单Agent Skill

```yaml
name: my-skill
orchestrator: react
agent: my_agent  # ← 单个Agent

prompt:
  file: prompts/my_agent.md

tools:
  - tool1
  - tool2
```

### 多Agent Skill

```yaml
name: my-skill
orchestrator: multi_agent
collaboration_mode: main_with_helpers

agents:
  - main_agent        # ← 主Agent
  - helper_agent_1    # ← 辅助Agent
  - helper_agent_2    # ← 辅助Agent

prompt:               # ← 只给主Agent用
  file: prompts/main_agent.md

tools:                # ← 只给主Agent用
  - tool1
  - tool2
```

---

## 执行流程

```
1. 加载Skill配置
   ↓
2. 并行执行辅助Agent
   - 使用各自的默认Prompt
   - 返回结果
   ↓
3. 执行主Agent
   - 使用Skill配置的Prompt
   - 可以看到辅助Agent的结果（在context中）
   - 返回综合结果
   ↓
4. 返回给用户
```

---

## Prompt来源对比

| Agent类型 | Prompt来源 | 配置位置 |
|----------|-----------|---------|
| 主Agent | Skill配置 | `skills/*/prompts/*.md` |
| 辅助Agent | Agent默认 | `builtin/*.py`的`system_prompt` |

---

## 代码位置

| 功能 | 文件 |
|-----|------|
| 多Agent编排 | `backend/daoyoucode/agents/orchestrators/multi_agent.py` |
| Prompt加载 | `backend/daoyoucode/agents/core/agent.py` |
| Skill配置 | `backend/daoyoucode/agents/core/skill.py` |
| Agent定义 | `backend/daoyoucode/agents/builtin/*.py` |

---

## 常见错误

### ❌ 错误1：为每个Agent配置Prompt

```yaml
# 错误示例
agents:
  - name: main_agent
    prompt: prompts/main.md
  - name: helper_agent
    prompt: prompts/helper.md  # ← 不支持！
```

**正确做法**：
```yaml
agents:
  - main_agent
  - helper_agent  # ← 使用默认Prompt

prompt:
  file: prompts/main.md  # ← 只配置主Agent
```

---

### ❌ 错误2：在辅助Agent中配置工具

```yaml
# 错误示例
agents:
  - main_agent
  - helper_agent:
      tools: [tool1, tool2]  # ← 不支持！
```

**正确做法**：
```yaml
agents:
  - main_agent
  - helper_agent  # ← 工具从tool_groups.py获取

tools:  # ← 只配置主Agent的工具
  - tool1
  - tool2
```

---

### ❌ 错误3：期望辅助Agent看到主Agent的结果

```python
# 错误理解
# 辅助Agent先执行，看不到主Agent的结果
```

**正确理解**：
```python
# 执行顺序：
# 1. 辅助Agent并行执行（互相看不到）
# 2. 主Agent执行（可以看到辅助Agent的结果）
```

---

## 调试技巧

### 查看Agent使用的Prompt

```python
# 在agent.py的_load_prompt方法中添加日志
async def _load_prompt(self, prompt_source, context):
    prompt = ...
    self.logger.info(f"Agent {self.name} 使用Prompt: {prompt[:100]}...")
    return prompt
```

### 查看辅助Agent的结果

```python
# 在multi_agent.py中添加日志
helper_results = [...]
self.logger.info(f"辅助Agent结果: {helper_results}")
```

### 查看Context内容

```python
# 在agent.py的execute方法中添加日志
self.logger.info(f"Context keys: {context.keys()}")
if 'helper_results' in context:
    self.logger.info(f"Helper results count: {len(context['helper_results'])}")
```

---

## 最佳实践

### 1. 主Agent的Prompt应该

- ✅ 说明可用的辅助Agent
- ✅ 引用helper_results
- ✅ 提供综合分析
- ✅ 给出执行计划

### 2. 辅助Agent的Prompt应该

- ✅ 专注于单一职责
- ✅ 简洁明了
- ✅ 不需要知道其他Agent
- ✅ 提供清晰的输出

### 3. Skill配置应该

- ✅ 只配置主Agent的Prompt
- ✅ 列出所有需要的Agent
- ✅ 选择合适的协作模式
- ✅ 配置主Agent的工具

---

## 示例对比

### 单Agent Skill（简单）

```yaml
# skills/oracle/skill.yaml
name: oracle
orchestrator: react
agent: oracle

prompt:
  file: prompts/oracle.md

tools:
  - repo_map
  - read_file
```

**特点**：
- 一个Agent
- 一个Prompt
- 简单直接

---

### 多Agent Skill（复杂）

```yaml
# skills/sisyphus-orchestrator/skill.yaml
name: sisyphus-orchestrator
orchestrator: multi_agent
collaboration_mode: main_with_helpers

agents:
  - sisyphus
  - code_analyzer
  - programmer
  - test_expert

prompt:
  file: prompts/sisyphus.md

tools:
  - repo_map
  - text_search
```

**特点**：
- 多个Agent
- 一个Prompt（主Agent）
- 辅助Agent使用默认Prompt
- 主Agent可以看到辅助Agent的结果

---

## 记忆口诀

```
Skill配置一个Prompt，
只给主Agent来使用。
辅助Agent用默认，
各自管理不混淆。

主Agent看到辅助结果，
通过Context来传递。
不需要传多个Prompt，
编排器自动来处理。
```

---

## 相关文档

- [多Agent Prompt机制详解](MULTI_AGENT_PROMPT_MECHANISM.md) - 完整解释
- [多Agent Prompt流转图](MULTI_AGENT_PROMPT_FLOW.md) - 可视化流程
- [如何添加新Agent](HOW_TO_ADD_NEW_AGENT.md) - Agent开发指南
- [新增Agent总结](NEW_AGENTS_SUMMARY.md) - 新Agent总结

---

**记住**：Skill配置只管主Agent，辅助Agent自己管自己！
