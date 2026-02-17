# 如何添加新Agent - 超简单！

## 你的理解完全正确 ✅

Agent本身**没有独属的逻辑**，只是一个配置容器！

真正的逻辑在：
- **Skill配置**（指定工具、Prompt）
- **BaseAgent**（通用的执行逻辑）

---

## 添加新Agent只需3步

### 步骤1：创建Agent文件

**位置**：`backend/daoyoucode/agents/builtin/`

**示例**：创建 `sisyphus.py`

```python
"""
Sisyphus - 主编排Agent

负责任务分解和Agent调度
Prompt配置在 skills/sisyphus/prompts/sisyphus.md
"""

from ..core.agent import BaseAgent, AgentConfig


class SisyphusAgent(BaseAgent):
    """主编排Agent"""
    
    def __init__(self):
        config = AgentConfig(
            name="sisyphus",
            description="主编排Agent，负责任务分解和Agent调度",
            model="qwen-max",
            temperature=0.1,
            system_prompt=""  # Prompt由Skill配置
        )
        super().__init__(config)
```

**就这么简单！** 只需要：
- 继承 `BaseAgent`
- 配置 `AgentConfig`（名称、描述、模型）
- `system_prompt` 留空（由Skill配置）

---

### 步骤2：注册Agent

**位置**：`backend/daoyoucode/agents/builtin/__init__.py`

**修改**：

```python
# 1. 导入新Agent
from .sisyphus import SisyphusAgent

# 2. 在register_builtin_agents()中注册
def register_builtin_agents():
    """注册所有内置Agent"""
    
    # 主Agent
    register_agent(MainAgent())
    
    # 编排Agent（新增）
    register_agent(SisyphusAgent())  # ← 添加这一行
    
    # 其他Agent...
    register_agent(TranslatorAgent())
    register_agent(ProgrammerAgent())
    # ...

# 3. 添加到__all__
__all__ = [
    'register_builtin_agents',
    'MainAgent',
    'SisyphusAgent',  # ← 添加这一行
    # ...
]
```

**就这么简单！** 只需要：
- 导入Agent类
- 调用 `register_agent()`
- 添加到 `__all__`

---

### 步骤3：创建Skill配置

**位置**：`skills/sisyphus/skill.yaml`

```yaml
name: sisyphus
orchestrator: multi_agent
collaboration_mode: main_with_helpers

agents:
  - sisyphus  # ← 使用新Agent
  - code_analyzer
  - programmer

tools:  # ← 配置工具
  - repo_map
  - text_search
  - read_file

prompt:  # ← 配置Prompt
  file: prompts/sisyphus.md

llm:  # ← 配置LLM
  model: qwen-max
  temperature: 0.1
```

**就这么简单！** Skill配置了：
- 使用哪个Agent
- 使用哪些工具
- 使用什么Prompt
- 使用什么LLM配置

---

## 完整示例：添加Oracle Agent

### 1. 创建Agent文件

```python
# backend/daoyoucode/agents/builtin/oracle.py
"""
Oracle - 高IQ咨询Agent

只读分析，提供架构建议和技术咨询
Prompt配置在 skills/oracle/prompts/oracle.md
"""

from ..core.agent import BaseAgent, AgentConfig


class OracleAgent(BaseAgent):
    """Oracle - 高IQ咨询Agent"""
    
    def __init__(self):
        config = AgentConfig(
            name="oracle",
            description="高IQ咨询Agent，提供架构分析和技术建议",
            model="qwen-max",
            temperature=0.1,
            system_prompt=""  # Prompt由Skill配置
        )
        super().__init__(config)
```

### 2. 注册Agent

```python
# backend/daoyoucode/agents/builtin/__init__.py

# 导入
from .oracle import OracleAgent

# 注册
def register_builtin_agents():
    register_agent(MainAgent())
    register_agent(OracleAgent())  # ← 新增
    # ...

# 导出
__all__ = [
    'register_builtin_agents',
    'MainAgent',
    'OracleAgent',  # ← 新增
    # ...
]
```

### 3. 创建Skill配置

```yaml
# skills/oracle/skill.yaml
name: oracle
orchestrator: react
agent: oracle  # ← 使用Oracle Agent

tools:  # ← 只读工具
  - repo_map
  - read_file
  - text_search
  - get_diagnostics

prompt:
  file: prompts/oracle.md

llm:
  model: qwen-max
  temperature: 0.1
```

### 4. 创建Prompt

```markdown
# skills/oracle/prompts/oracle.md

你是Oracle，高IQ咨询Agent。

## 你的职责
提供架构分析和技术建议（只读，不修改代码）

## 你的工具
- repo_map - 生成代码地图
- read_file - 读取文件
- text_search - 搜索代码
- get_diagnostics - 获取诊断信息

## 使用场景
- 架构决策
- 代码审查
- 性能分析
- 安全审查

## 重要
- 你是只读的，不能修改代码
- 提供高质量的分析和建议
- 使用工具深入理解代码
```

---

## 核心理解

### Agent本身没有独属逻辑 ✅

```python
class MyAgent(BaseAgent):
    def __init__(self):
        config = AgentConfig(
            name="my_agent",
            description="我的Agent",
            model="qwen-max",
            temperature=0.1,
            system_prompt=""  # ← 空的！
        )
        super().__init__(config)
    
    # ← 没有其他方法！
    # ← 所有逻辑都在BaseAgent中！
```

**Agent只是一个配置容器**：
- 名称
- 描述
- 默认模型
- 默认温度

---

### 真正的逻辑在哪里？

#### 1. BaseAgent（通用执行逻辑）

```python
# backend/daoyoucode/agents/core/agent.py
class BaseAgent:
    async def execute(self, prompt_source, user_input, tools, llm_config):
        # 1. 加载Prompt（从Skill）
        prompt = load_prompt(prompt_source)
        
        # 2. 调用LLM（使用Skill的配置）
        response = await llm.chat(
            prompt=prompt,
            tools=tools,  # ← 从Skill
            model=llm_config.model  # ← 从Skill
        )
        
        # 3. 工具调用循环
        for iteration in range(15):
            if response.has_tool_call:
                tool_result = execute_tool(...)
                response = await llm.chat(...)
            else:
                break
        
        return response
```

**所有Agent共享这个逻辑！**

---

#### 2. Skill配置（差异化配置）

```yaml
# skills/my-skill/skill.yaml
agent: my_agent  # ← 选择Agent

tools:  # ← 配置工具（差异化）
  - read_file
  - write_file

prompt:  # ← 配置Prompt（差异化）
  file: prompts/my-prompt.md

llm:  # ← 配置LLM（差异化）
  model: qwen-max
  temperature: 0.1
```

**Skill配置决定了Agent的行为！**

---

## 数据流

```
用户请求
    ↓
Skill配置（YAML）
    ↓
编排器读取
    ↓
编排器调用Agent.execute(
    tools=skill.tools,      # ← 从Skill
    prompt_source=skill.prompt,  # ← 从Skill
    llm_config=skill.llm    # ← 从Skill
)
    ↓
BaseAgent.execute()
    ↓
使用Skill配置执行任务
```

---

## 为什么这样设计？

### 优势

1. **简单**：添加Agent只需要3步
2. **灵活**：同一个Agent可以用在不同Skill中
3. **可配置**：通过Skill配置差异化行为
4. **可维护**：逻辑集中在BaseAgent

### 示例

**同一个Agent，不同的Skill**：

```yaml
# skills/simple-chat/skill.yaml
agent: MainAgent
tools:
  - read_file
  - text_search
prompt:
  file: prompts/simple.md

---

# skills/advanced-chat/skill.yaml
agent: MainAgent  # ← 同一个Agent
tools:  # ← 不同的工具
  - repo_map
  - read_file
  - write_file
  - git_commit
prompt:  # ← 不同的Prompt
  file: prompts/advanced.md
```

**同一个Agent，不同的行为！**

---

## 总结

### 你的理解完全正确 ✅

1. **添加Agent**：在 `builtin/` 目录创建文件
2. **注册Agent**：在 `__init__.py` 中注册
3. **Agent没有独属逻辑**：只是配置容器
4. **真正的逻辑**：
   - BaseAgent（通用执行）
   - Skill配置（差异化配置）

### 添加新Agent超简单

```python
# 1. 创建文件
class MyAgent(BaseAgent):
    def __init__(self):
        config = AgentConfig(name="my_agent", ...)
        super().__init__(config)

# 2. 注册
register_agent(MyAgent())

# 3. 创建Skill配置
# skills/my-skill/skill.yaml
agent: my_agent
tools: [...]
prompt: {...}
```

**就这么简单！** 🎉

---

## 快速添加Sisyphus Agent

### 1. 创建文件

```bash
# 创建文件
touch backend/daoyoucode/agents/builtin/sisyphus.py
```

```python
# backend/daoyoucode/agents/builtin/sisyphus.py
from ..core.agent import BaseAgent, AgentConfig

class SisyphusAgent(BaseAgent):
    def __init__(self):
        config = AgentConfig(
            name="sisyphus",
            description="主编排Agent",
            model="qwen-max",
            temperature=0.1,
            system_prompt=""
        )
        super().__init__(config)
```

### 2. 注册

```python
# backend/daoyoucode/agents/builtin/__init__.py
from .sisyphus import SisyphusAgent

def register_builtin_agents():
    register_agent(MainAgent())
    register_agent(SisyphusAgent())  # ← 添加
    # ...

__all__ = [
    'register_builtin_agents',
    'MainAgent',
    'SisyphusAgent',  # ← 添加
    # ...
]
```

### 3. 使用

```yaml
# skills/sisyphus/skill.yaml
agent: sisyphus
tools: [repo_map, text_search, read_file]
prompt:
  file: prompts/sisyphus.md
```

**完成！** 🚀

---

## 下一步

1. 添加Sisyphus Agent（5分钟）
2. 添加Oracle Agent（5分钟）
3. 添加Librarian Agent（5分钟）
4. 创建对应的Skill配置
5. 测试效果

**添加Agent真的很简单！** 😊


---

## ✅ 已完成：新增3个Agent

### 1. Sisyphus - 主编排Agent

**文件**：
- Agent：`backend/daoyoucode/agents/builtin/sisyphus.py`
- Skill：`skills/sisyphus-orchestrator/skill.yaml`
- Prompt：`skills/sisyphus-orchestrator/prompts/sisyphus.md`

**特点**：
- 4个基础工具（repo_map, get_repo_structure, text_search, read_file）
- 负责任务分解和Agent调度
- 使用多Agent编排器（main_with_helpers模式）

**使用**：
```bash
python backend/daoyoucode.py --skill sisyphus-orchestrator "重构登录模块并添加测试"
```

---

### 2. Oracle - 高IQ咨询Agent

**文件**：
- Agent：`backend/daoyoucode/agents/builtin/oracle.py`
- Skill：`skills/oracle/skill.yaml`
- Prompt：`skills/oracle/prompts/oracle.md`

**特点**：
- 10个只读分析工具
- 提供架构分析和技术建议
- 只读权限（不修改代码）

**使用**：
```bash
python backend/daoyoucode.py --skill oracle "分析登录模块的架构设计"
```

---

### 3. Librarian - 文档搜索Agent

**文件**：
- Agent：`backend/daoyoucode/agents/builtin/librarian.py`
- Skill：`skills/librarian/skill.yaml`
- Prompt：`skills/librarian/prompts/librarian.md`

**特点**：
- 8个搜索和读取工具
- 专注于信息检索和知识搜索
- 只读权限

**使用**：
```bash
python backend/daoyoucode.py --skill librarian "如何使用Agent的工具？"
```

---

## 验证测试

运行测试验证新Agent：

```bash
python backend/tests/test_new_agents.py
```

**测试结果**：
```
✓ 所有新Agent注册成功
✓ 工具映射配置正确
✓ Skill配置文件完整
```

---

## Agent总览

### 当前所有Agent（10个）

| Agent | 工具数 | 类型 | 职责 |
|-------|--------|------|------|
| main_agent | 4 | 通用 | 通用任务处理 |
| sisyphus | 4 | 编排 | 任务分解和Agent调度 |
| oracle | 10 | 咨询 | 架构分析和技术建议（只读） |
| librarian | 8 | 搜索 | 文档和代码搜索（只读） |
| code_analyzer | 10 | 分析 | 代码分析和架构理解 |
| code_explorer | 8 | 探索 | 代码探索和导航 |
| programmer | 11 | 编程 | 代码编写和Bug修复 |
| refactor_master | 13 | 重构 | 代码重构和优化 |
| test_expert | 10 | 测试 | 测试编写和修复 |
| translator | 6 | 翻译 | 文档和代码翻译 |

---

## 工具分组总结

### 编排Agent（4个工具）
- sisyphus, main_agent
- 快速探索，任务分解

### 只读Agent（8-10个工具）
- oracle（10个）- 深度分析
- librarian（8个）- 信息检索
- code_analyzer（10个）- 代码分析
- code_explorer（8个）- 代码探索

### 编程Agent（11-13个工具）
- programmer（11个）- 代码编写
- refactor_master（13个）- 代码重构
- test_expert（10个）- 测试编写

### 专用Agent（6个工具）
- translator（6个）- 翻译

---

## 下一步计划

### 1. 测试新Agent
- 测试Sisyphus的任务分解能力
- 测试Oracle的架构分析能力
- 测试Librarian的搜索能力

### 2. 优化编排器
- 改进多Agent协作
- 优化任务分解算法
- 提升并行执行效率

### 3. 添加更多Agent（可选）
- Prometheus - 规划Agent
- Multimodal Looker - 多模态Agent

---

## 参考文档

- [Agent对比分析](AGENT_COMPARISON_AND_RECOMMENDATIONS.md)
- [工具参考手册](TOOLS_REFERENCE.md)
- [工具快速参考](TOOLS_QUICK_REFERENCE.md)
- [Agent工具映射](AGENT_TOOL_MAPPING.md)
- [多Agent实施指南](MULTI_AGENT_IMPLEMENTATION_GUIDE.md)
- [架构总结](ARCHITECTURE_SUMMARY.md)

---

**添加Agent真的很简单！现在我们有10个专业Agent了！** 🎉
