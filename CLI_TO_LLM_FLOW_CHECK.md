# CLI 到 LLM 调用链路检查

## 完整调用链路

```
用户输入
  ↓
CLI (chat.py)
  ↓
handle_chat() → _handle_chat_impl()
  ↓
execute_skill() [executor.py]
  ↓
_execute_skill_internal()
  ↓
orchestrator.execute() [react.py / multi_agent.py]
  ↓
agent.execute() [agent.py]
  ↓
_render_prompt() → _call_llm() / _stream_llm()
  ↓
LLM Client [llm/client_manager.py]
  ↓
API 调用
```

## 各环节检查

### 1. CLI 入口 ✅
**文件**: `backend/cli/commands/chat.py`

**关键点**:
- 初始化 Agent 系统
- 设置 tool_context（repo_path, subtree_only, cwd）
- 创建 session_id
- 构建 context（包含 enable_streaming=True）

**检查结果**: ✅ 正常
- context 正确传递
- session_id 正确生成
- enable_streaming 已启用

### 2. Skill 执行器 ✅
**文件**: `backend/daoyoucode/agents/executor.py`

**关键点**:
- 设置工具上下文（ToolContext）
- 预取 focus_repo_map（如果有 initial_files）
- 预取 semantic_code_chunks（如果 Skill 支持）
- 加载 Skill 配置
- 获取 Orchestrator
- 执行 orchestrator.execute()

**检查结果**: ✅ 正常
- 工具上下文正确设置
- 预取逻辑完整
- Skill 加载正常
- 支持流式输出（检测 isasyncgen）

### 3. Orchestrator 层 ⚠️ 需要验证
**文件**: 
- `backend/daoyoucode/agents/orchestrators/react.py`
- `backend/daoyoucode/agents/orchestrators/multi_agent.py`

**关键点**:
- 意图识别和预取（should_prefetch_project_understanding）
- 工具过滤（移除已预取的工具）
- Agent 执行

**multi_agent.py 修复**:
- ✅ 辅助 Agent 使用自己的 Skill 配置
- ✅ 通过 Skill Registry 获取 Prompt
- ✅ Agent 到 Skill 的映射关系

**潜在问题**:
1. ⚠️ **Skill Registry 是否正确加载？**
   - 需要验证 `get_skill_registry()` 能否找到 code-analysis、programming 等 Skill
   - 需要验证 Skill 的 prompt 配置是否正确

2. ⚠️ **Prompt 文件路径是否正确？**
   - code-analysis: `../oracle/prompts/oracle.md` （已修复）
   - programming: `prompts/programmer.md`
   - refactoring: `prompts/refactor.md`
   - testing: `prompts/test.md`

### 4. Agent 层 ⚠️ 关键问题
**文件**: `backend/daoyoucode/agents/core/agent.py`

**关键点**:
- 加载 Prompt（_load_prompt）
- 渲染 Prompt（_render_prompt）
- 调用 LLM（_call_llm / _stream_llm）

**已知问题**:
1. ❌ **用户输入未注入到 Prompt**
   ```
   [20:44:12] agent.code_analyzer - ERROR - [Prompt渲染] ❌ 用户输入未出现在 Prompt 中
   ```
   
   **原因**: 
   - 辅助 Agent 使用 `use_agent_default`
   - builtin agents 的 system_prompt 是空字符串
   - 渲染后的 Prompt 没有 `{{user_input}}` 占位符

   **修复**: ✅ 已修复
   - multi_agent.py 现在使用 Skill 配置中的 Prompt
   - 不再使用 `use_agent_default`

2. ⚠️ **预取内容未注入到 Prompt**
   ```
   [20:44:12] agent.code_analyzer - WARNING - [Prompt渲染] ⚠️ 预取内容未出现在渲染后的 Prompt 中
   ```
   
   **可能原因**:
   - Prompt 模板中没有 `{{project_understanding_block}}` 占位符
   - 需要检查各个 Prompt 文件

### 5. Prompt 渲染 ⚠️ 需要验证
**文件**: `backend/daoyoucode/agents/core/agent.py` (line 767-781)

**逻辑**:
```python
def _render_prompt(self, prompt: str, user_input: str, context: Dict[str, Any]) -> str:
    try:
        from jinja2 import Template
        template = Template(prompt)
        return template.render(user_input=user_input, **context)
    except Exception as e:
        self.logger.warning(f"Prompt渲染失败: {e}")
        return prompt.replace('{{user_input}}', user_input)
```

**检查点**:
1. ✅ 使用 Jinja2 渲染
2. ✅ 传入 user_input 和 context
3. ⚠️ 需要验证 Prompt 模板是否有正确的占位符

### 6. Prompt 模板检查 ⚠️

**需要检查的占位符**:

#### 必须有的占位符:
1. `{{user_input}}` - 用户输入
2. `{{repo}}` - 仓库路径

#### 可选的占位符:
1. `{{project_understanding_block}}` - 预取的项目信息
2. `{{semantic_code_chunks}}` - 语义搜索结果
3. `{{conversation_history}}` - 对话历史
4. `{{initial_files}}` - 初始文件列表
5. `{{helper_results}}` - 辅助 Agent 结果（sisyphus 专用）

**检查结果**:
- ✅ chat_assistant.md: 有所有占位符
- ✅ sisyphus.md: 有所有占位符
- ⚠️ oracle.md: 需要检查
- ⚠️ programmer.md: 需要检查
- ⚠️ refactor.md: 需要检查
- ⚠️ test.md: 需要检查

### 7. LLM 调用 ✅
**文件**: `backend/daoyoucode/agents/llm/client_manager.py`

**关键点**:
- 获取正确的 LLM Client
- 构建 LLMRequest
- 调用 chat() 或 stream_chat()

**检查结果**: ✅ 正常（假设 LLM 配置正确）

## 问题总结

### ✅ 已修复
1. 辅助 Agent 没有 Prompt - 现在使用 Skill 配置
2. code-analysis 的 prompt 路径错误 - 已修复为 `../oracle/prompts/oracle.md`
3. 各专家 Prompt 缺少"先查找再读取"规则 - 已添加

### ⚠️ 需要验证
1. **Skill Registry 是否正确工作？**
   - 测试: 在 multi_agent.py 中打印 `skill_registry.get_skill('code-analysis')`
   - 验证: Skill 是否正确加载，prompt 配置是否正确

2. **Prompt 文件是否有正确的占位符？**
   - oracle.md: 需要添加 `{{project_understanding_block}}` 等
   - programmer.md: 需要添加 `{{project_understanding_block}}` 等
   - refactor.md: 需要添加 `{{project_understanding_block}}` 等
   - test.md: 需要添加 `{{project_understanding_block}}` 等

3. **预取内容是否正确注入到 context？**
   - 检查 react.py 和 multi_agent.py 的预取逻辑
   - 验证 context['project_understanding_block'] 是否存在

## 建议的测试步骤

### 测试 1: 验证 Skill Registry
```python
# 在 multi_agent.py 的 _execute_main_with_helpers 中添加日志
from ..skills import get_skill_registry
skill_registry = get_skill_registry()

for agent_name, skill_name in agent_to_skill.items():
    helper_skill = skill_registry.get_skill(skill_name)
    if helper_skill:
        self.logger.info(f"✅ {agent_name} → {skill_name}: {helper_skill.prompt}")
    else:
        self.logger.error(f"❌ {agent_name} → {skill_name}: Skill not found")
```

### 测试 2: 验证 Prompt 渲染
```python
# 在 agent.py 的 _render_prompt 后添加日志
self.logger.info(f"[Prompt渲染] 模板长度: {len(prompt)}")
self.logger.info(f"[Prompt渲染] 渲染后长度: {len(full_prompt)}")
self.logger.info(f"[Prompt渲染] user_input 在模板中: {'{{user_input}}' in prompt}")
self.logger.info(f"[Prompt渲染] user_input 在渲染后: {user_input in full_prompt}")
```

### 测试 3: 验证预取内容
```python
# 在 multi_agent.py 的 _execute_main_with_helpers 中添加日志
if 'project_understanding_block' in context:
    self.logger.info(f"✅ context 中有 project_understanding_block: {len(context['project_understanding_block'])} 字符")
else:
    self.logger.warning(f"⚠️ context 中没有 project_understanding_block")
```

## 下一步行动

1. **添加 Prompt 占位符** ⚠️ 高优先级
   - 给 oracle.md、programmer.md、refactor.md、test.md 添加缺失的占位符
   - 确保所有 Prompt 都有 `{{user_input}}`、`{{repo}}`、`{{project_understanding_block}}`

2. **验证 Skill Registry** ⚠️ 高优先级
   - 运行测试，确认 Skill 能正确加载
   - 确认 Prompt 路径正确

3. **优化 Prompt 内容** 📝 中优先级
   - 简化 Prompt，去除冗余规则
   - 强调核心工作流程
   - 添加实战示例

4. **测试完整链路** ✅ 高优先级
   ```bash
   daoyoucode chat --skill sisyphus-orchestrator --debug
   # 输入: chat_assistant.md有啥优化建议
   ```
   
   **预期行为**:
   - 系统选择 code_analyzer 和 programmer
   - 辅助 Agent 使用自己的 Skill 配置
   - Prompt 正确渲染（包含 user_input）
   - 先调用 text_search 找文件
   - 再调用 read_file 读取
   - 返回分析结果给 sisyphus
   - sisyphus 整合并输出

## 结论

**链路整体正常** ✅，但有几个关键点需要验证和优化：

1. Skill Registry 是否正确工作
2. Prompt 模板是否有正确的占位符
3. 预取内容是否正确注入

修复这些问题后，系统应该能正常工作。然后可以专注于 Prompt 优化，充分发挥系统优势。

---

**检查时间**: Context Transfer Session
**状态**: 链路基本正常，需要验证几个关键点
**下一步**: 添加 Prompt 占位符 → 验证 Skill Registry → 测试完整链路
