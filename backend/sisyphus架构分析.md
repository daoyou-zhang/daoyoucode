# Sisyphus-Orchestrator 架构分析

## 整体逻辑链

```
用户输入
  ↓
executor.execute_skill()
  ↓
multi_agent.execute()
  ├─ 0. 意图判断 + 项目理解预取（智能体循环前）
  │   └─ intent.should_prefetch_project_understanding()
  │       ├─ 使用LLM意图分类（如果 project_understanding_use_intent=true）
  │       ├─ 或使用关键词匹配（project_understanding_triggers）
  │       └─ 兜底：PROJECT_UNDERSTANDING_FALLBACK_KEYWORDS
  │   └─ 如果需要预取：
  │       ├─ discover_project_docs（项目文档）
  │       ├─ get_repo_structure（目录结构）
  │       └─ repo_map（代码地图）
  │       └─ 拼接成 project_understanding_block 注入 context
  │
  ├─ 1. 应用中间件（context_management, memory_integration）
  │
  ├─ 2. 过滤工具（只使用已注册的工具）
  │
  ├─ 3. 获取Agent列表（sisyphus + 4个辅助Agent）
  │
  ├─ 4. 确定协作模式（main_with_helpers）
  │
  └─ 5. 执行 main_with_helpers 模式
      ├─ 5.1 并行执行辅助Agent（code_analyzer, programmer, refactor_master, test_expert）
      │   └─ 每个Agent使用 agent_tools 配置的工具
      │
      ├─ 5.2 执行主Agent（sisyphus）
      │   ├─ 输入：user_input + context + helper_results + project_understanding_block
      │   ├─ Prompt：skills/sisyphus-orchestrator/prompts/sisyphus.md
      │   └─ 工具：repo_map, get_repo_structure, text_search, read_file
      │
      └─ 5.3 返回结果
          ├─ success
          ├─ content（主Agent的输出）
          ├─ helper_results（辅助Agent的结果）
          └─ metadata
```

## 架构评估

### ✅ 优点

#### 1. 清晰的职责分离

- **executor.py**：统一入口，处理Hook、恢复、超时
- **multi_agent.py**：编排逻辑，协调多个Agent
- **intent.py**：意图判断，统一预取逻辑
- **agent.py**：Agent执行，工具调用

每个模块职责明确，符合单一职责原则。

#### 2. 智能的预取机制

```python
# 三层预取逻辑（统一在 intent.py）
1. LLM意图分类（如果启用）
2. 关键词匹配（触发词）
3. 兜底关键词（PROJECT_UNDERSTANDING_FALLBACK_KEYWORDS）
```

**优点**：
- 避免死关键词漏掉「理解下当前项目」等说法
- 统一维护，react/multi_agent 共用
- 在智能体循环前预取，避免重复调用

#### 3. 灵活的工具分配

```yaml
agent_tools:
  sisyphus:           # 主编排：只需理解与协调
    - repo_map
    - get_repo_structure
    - text_search
    - read_file
  code_analyzer:      # 架构分析：读 + 地图 + LSP/符号
    - read_file
    - repo_map
    - ...
```

**优点**：
- 每个Agent只获得其职责所需的工具
- 避免工具泛滥，减少LLM选择困难
- 提高工具调用的准确性

#### 4. 主Agent + 辅助Agent模式

```python
# 执行流程
1. 并行执行辅助Agent（快速获取专业意见）
2. 主Agent看到辅助结果（helper_results）
3. 主Agent综合分析和决策
4. 返回聚合结果
```

**优点**：
- 充分利用并行性，提高效率
- 主Agent可以看到多个专业视角
- 避免主Agent重复工作

#### 5. 项目理解预取优化

```python
# 预取块注入到 context
context["project_understanding_block"] = header + "\n\n".join([
    "【项目文档】\n" + docs,
    "【目录结构】\n" + structure,
    "【代码地图】仅作参考\n" + repo_map
])
```

**优点**：
- 在Prompt中明确告知「已预取，请直接使用」
- 避免LLM再次调用工具
- 减少token浪费和延迟

#### 6. 路径占位符防护

```python
# 两层防护
1. Prompt开头：工具使用规则（治本）
2. BaseTool.resolve_path()：自动修正（治标）
```

**优点**：
- 引导LLM使用正确路径
- 即使LLM使用占位符，工具也能自动修正
- 提供清晰的警告信息

### ⚠️ 潜在问题

#### 1. 预取时机可能过早

**问题**：
```python
# multi_agent.execute() 开头就预取
need_project_prefetch, intents = await should_prefetch_project_understanding(...)
if need_project_prefetch and has_tools:
    # 立即预取
```

**影响**：
- 如果用户只是简单寒暄（"你好"），也会触发预取
- 浪费token和时间

**建议**：
- 在意图判断中增加"general_chat"检测
- 如果是简单寒暄，跳过预取

#### 2. 辅助Agent可能做无用功

**问题**：
```python
# 无论用户请求什么，都并行执行所有辅助Agent
helper_tasks = [
    agent.execute(...) for agent in helper_agents
]
```

**影响**：
- 用户只想"了解项目"，不需要programmer/refactor_master/test_expert
- 浪费token和时间

**建议**：
- 根据意图选择性执行辅助Agent
- 例如：
  - "understand_project" → 只执行 code_analyzer
  - "edit_or_write" → 执行 programmer
  - "重构+测试" → 执行 refactor_master + test_expert

#### 3. project_understanding_block 可能过大

**问题**：
```python
# 三层结果拼接
_DOC_CHARS, _STRUCT_CHARS, _REPOMAP_CHARS = 8000, 3500, 4500
# 总计：16000 字符
```

**影响**：
- 占用大量token
- 如果用户不需要这些信息，浪费严重

**建议**：
- 根据用户意图调整预取粒度
- 例如：
  - "了解项目" → 完整预取
  - "修复Bug" → 只预取 repo_map
  - "简单寒暄" → 不预取

#### 4. helper_results 可能被忽略

**问题**：
```python
# 主Agent的Prompt中没有强制要求使用 helper_results
# 只是说"你会在context中看到helper_results"
```

**影响**：
- LLM可能忽略辅助Agent的结果
- 辅助Agent的工作白费

**建议**：
- 在Prompt中明确要求：
  ```markdown
  ## 步骤3：整合辅助Agent的结果（必须）
  
  系统已并行执行辅助Agent，结果在 helper_results 中。
  你必须：
  1. 阅读每个辅助Agent的分析
  2. 提取关键信息
  3. 整合到你的最终答案中
  
  不要忽略辅助Agent的结果！
  ```

#### 5. 工具使用规则重复

**问题**：
```python
# agent.py 中添加了工具使用规则
tool_rules = """⚠️ 工具使用规则（必须遵守）：..."""
full_prompt = tool_rules + full_prompt

# sisyphus.md 中也有工具使用规则
## ⚠️ 重要：工具使用规则
...
```

**影响**：
- 规则重复，浪费token
- 两处维护，容易不一致

**建议**：
- 只在一处添加规则（推荐在 agent.py）
- 或者在 sisyphus.md 中简化规则

### 🔧 优化建议

#### 优化1：智能选择辅助Agent

```python
async def _execute_main_with_helpers(
    self,
    agents: List,
    user_input: str,
    context: Dict[str, Any],
    skill: 'SkillConfig'
) -> Dict[str, Any]:
    """主Agent + 辅助Agent模式（智能选择）"""
    
    main_agent = agents[0]
    helper_agents = agents[1:] if len(agents) > 1 else []
    
    # 🆕 根据意图选择辅助Agent
    intents = context.get('detected_intents', [])
    
    selected_helpers = []
    if 'understand_project' in intents:
        # 只需要架构分析
        selected_helpers = [a for a in helper_agents if a.name == 'code_analyzer']
    elif 'edit_or_write' in intents:
        # 需要编程专家
        selected_helpers = [a for a in helper_agents if a.name in ['programmer', 'code_analyzer']]
    elif 'general_chat' in intents:
        # 简单寒暄，不需要辅助Agent
        selected_helpers = []
    else:
        # 默认：执行所有辅助Agent
        selected_helpers = helper_agents
    
    self.logger.info(f"根据意图 {intents} 选择了 {len(selected_helpers)} 个辅助Agent")
    
    # 执行选中的辅助Agent
    helper_results = []
    if selected_helpers:
        # ... 并行执行
```

#### 优化2：动态调整预取粒度

```python
async def should_prefetch_project_understanding(
    skill: Any,
    user_input: str,
    context: Dict[str, Any],
) -> Tuple[bool, List[str], str]:  # 🆕 返回预取级别
    """
    返回 (need_prefetch, intents, prefetch_level)
    
    prefetch_level:
    - "full": 完整预取（文档+结构+地图）
    - "medium": 中等预取（结构+地图）
    - "light": 轻量预取（只地图）
    - "none": 不预取
    """
    
    # ... 意图判断
    
    if "understand_project" in intents:
        return True, intents, "full"
    elif "need_code_context" in intents:
        return True, intents, "medium"
    elif "edit_or_write" in intents:
        return True, intents, "light"
    else:
        return False, intents, "none"
```

#### 优化3：强化helper_results使用

在 `sisyphus.md` 中修改：

```markdown
## 步骤3：整合辅助Agent的结果（必须执行）

系统已并行执行辅助Agent，结果在 `helper_results` 中。

**你必须：**
1. ✅ 阅读每个辅助Agent的分析
2. ✅ 提取关键信息和建议
3. ✅ 整合到你的最终答案中
4. ✅ 明确标注信息来源（如"根据code_analyzer的分析..."）

**禁止：**
- ❌ 忽略辅助Agent的结果
- ❌ 重复辅助Agent已经做过的工作
- ❌ 不标注信息来源

如果 helper_results 为空，说明没有辅助Agent执行，你需要自己分析。
```

#### 优化4：统一工具使用规则

**方案A**：只在 agent.py 中添加（推荐）

```python
# agent.py
if tools:
    tool_rules = """⚠️ 工具使用规则（必须遵守）：..."""
    full_prompt = tool_rules + full_prompt
```

```markdown
# sisyphus.md
# 删除重复的工具使用规则部分
```

**方案B**：只在 sisyphus.md 中添加

```python
# agent.py
# 删除工具使用规则部分
```

```markdown
# sisyphus.md
# 保留工具使用规则
```

推荐方案A，因为：
- agent.py 是所有Agent共用的
- 规则在代码中更容易维护
- sisyphus.md 可以专注于编排逻辑

## 总结

### 架构合理性：⭐⭐⭐⭐☆ (4/5)

**优点**：
- ✅ 职责分离清晰
- ✅ 预取机制智能
- ✅ 工具分配灵活
- ✅ 并行执行高效
- ✅ 路径防护完善

**需要改进**：
- ⚠️ 辅助Agent选择可以更智能
- ⚠️ 预取粒度可以动态调整
- ⚠️ helper_results使用需要强化
- ⚠️ 工具使用规则有重复

### 优先级建议

1. **高优先级**：强化helper_results使用（优化3）
   - 影响：避免辅助Agent白费工作
   - 成本：低（只需修改Prompt）

2. **中优先级**：智能选择辅助Agent（优化1）
   - 影响：减少token浪费，提高效率
   - 成本：中（需要修改multi_agent.py）

3. **低优先级**：动态调整预取粒度（优化2）
   - 影响：进一步优化token使用
   - 成本：高（需要修改intent.py和multi_agent.py）

4. **低优先级**：统一工具使用规则（优化4）
   - 影响：减少重复，便于维护
   - 成本：低（删除重复部分）

## 测试建议

### 测试用例1：简单寒暄
```
用户："你好啊，道友"
期望：
- 不预取项目理解
- 不执行辅助Agent
- 简短回答能力介绍
```

### 测试用例2：了解项目
```
用户："理解下当前项目"
期望：
- 预取项目理解（完整）
- 只执行 code_analyzer
- 基于预取结果回答，不再调用工具
```

### 测试用例3：修复Bug
```
用户："修复登录时的500错误"
期望：
- 预取项目理解（轻量）
- 执行 code_analyzer + programmer
- 主Agent整合辅助结果
```

### 测试用例4：重构+测试
```
用户："重构登录模块，添加测试"
期望：
- 预取项目理解（中等）
- 执行 code_analyzer + refactor_master + test_expert
- 主Agent整合所有辅助结果
```
