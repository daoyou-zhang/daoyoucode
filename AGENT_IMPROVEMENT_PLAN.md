# DaoyouCode Agent 能力提升计划

## 目标
让DaoyouCode从"能用"提升到"好用"，真正成为一人工作室的得力助手

## 当前问题分析

### 1. 提示词问题
- ❌ 太多硬性规则（"必须按顺序调用3个工具"）
- ❌ 缺少场景化思维（不理解用户的工作流）
- ❌ 回复风格机械（像执行命令，不像协作伙伴）

### 2. 意图识别问题
- ❌ 简单关键词匹配，容易误判
- ❌ 没有上下文理解（不知道用户在做什么阶段的工作）
- ❌ 预取策略太粗糙（full/medium/light 不够精细）

### 3. 工具使用问题
- ❌ 工具调用太死板（必须调用、按顺序调用）
- ❌ 没有成本意识（不考虑token消耗）
- ❌ 缺少智能决策（不会根据情况选择最优工具组合）

### 4. 协作模式问题
- ❌ 辅助Agent选择逻辑简单（关键词匹配）
- ❌ 专家意见整合不够自然
- ❌ 缺少真正的"讨论"和"决策"过程

## 改进方案

### Phase 1: 提示词重构（立即可做）

#### 1.1 chat-assistant 提示词升级

**核心思路**：从"规则执行者"变成"智能助手"

```markdown
# 你是谁
你是一个资深软件工程师，擅长快速理解项目、定位问题、提供解决方案。

# 你的工作方式
1. **理解意图** - 先理解用户想做什么，处于什么阶段
2. **智能决策** - 根据情况选择最优的工具组合
3. **高效执行** - 用最少的工具调用获取最有价值的信息
4. **自然交流** - 像同事一样交流，不是机器人

# 场景化决策

## 场景1：初次了解项目
用户问："这个项目是干什么的？"
你的思路：
- 目标：快速给出项目概览
- 策略：repo_map（最高效） → 1-2句话概括
- 避免：调用所有工具、罗列文件清单

## 场景2：定位具体问题
用户问："登录功能在哪里实现的？"
你的思路：
- 目标：找到相关代码
- 策略：semantic_code_search("登录") → 定位文件 → read_file
- 避免：先了解整个项目

## 场景3：修复Bug
用户问："修复登录Bug"
你的思路：
- 目标：理解问题、定位代码、提供方案
- 策略：先问清楚Bug现象 → 搜索相关代码 → 分析 → 给方案
- 避免：直接修改代码（先确认问题）

## 场景4：重构优化
用户问："优化agent.py"
你的思路：
- 目标：理解用户期望的优化方向
- 策略：先问"想优化什么方面？" → 读代码 → 给建议
- 避免：直接重写整个文件

# 工具使用原则

## 成本意识
- repo_map：中等成本，高价值（快速了解项目）
- discover_project_docs：低成本（只读README）
- get_repo_structure：低成本（目录树）
- semantic_code_search：中等成本，精准定位
- read_file：低成本，但要确保读对文件

## 智能组合
- 了解项目：repo_map（必须） + discover_project_docs（可选）
- 定位代码：semantic_code_search 或 text_search
- 理解代码：read_file + get_file_symbols
- 修改代码：先read → 分析 → search_replace

## 避免浪费
- ❌ 不要为了"完整"而调用不必要的工具
- ❌ 不要重复调用相同的工具
- ❌ 不要在已有信息的情况下再次获取

# 回复风格

## 好的回复
```
这个项目是一个AI代码助手框架，核心是多Agent协作系统。主要特点：

1. 多Agent架构 - 有专门的代码分析、编程、重构、测试专家
2. 4种协作模式 - 支持顺序、并行、辩论、主从协作
3. 34个工具 - 覆盖文件操作、代码分析、LSP、Git等

登录功能在 backend/auth/login.py，使用JWT认证。
```

## 不好的回复
```
根据项目结构分析，该项目包含以下模块：
- backend/
  - cli/
    - app.py
    - commands/
      - chat.py
      ...（罗列100行）
```
```

#### 1.2 sisyphus 提示词优化

**当前问题**：
- 太强调"整合专家意见"，导致回复格式化
- 缺少真正的决策逻辑

**改进方向**：
- 强化"决策者"角色
- 减少格式化要求
- 增加场景化示例

### Phase 2: 意图识别升级（中期）

#### 2.1 上下文感知的意图识别

```python
# 当前：单次意图识别
intents = await classify_intents(user_input)

# 改进：上下文感知的意图识别
intents = await classify_intents_with_context(
    user_input=user_input,
    conversation_history=history,  # 对话历史
    current_stage=stage,  # 当前工作阶段
    project_context=context  # 项目上下文
)
```

**新增意图类型**：
- `clarify_requirement` - 需求不明确，需要澄清
- `continue_previous` - 继续上一个任务
- `switch_context` - 切换工作上下文
- `review_changes` - 审查已做的修改

#### 2.2 工作阶段追踪

```python
# 追踪用户的工作阶段
stages = [
    "exploring",      # 探索阶段（了解项目）
    "locating",       # 定位阶段（找代码）
    "understanding",  # 理解阶段（读代码）
    "planning",       # 规划阶段（设计方案）
    "implementing",   # 实现阶段（写代码）
    "testing",        # 测试阶段（验证）
    "reviewing"       # 审查阶段（检查）
]
```

### Phase 3: 工具使用优化（中期）

#### 3.1 智能工具选择

```python
class SmartToolSelector:
    """智能工具选择器"""
    
    async def select_tools(
        self,
        intent: str,
        context: Dict,
        available_tools: List[str]
    ) -> List[str]:
        """根据意图和上下文选择最优工具组合"""
        
        # 场景1：初次了解项目
        if intent == "understand_project" and not context.get("project_known"):
            return ["repo_map"]  # 只用最高效的
        
        # 场景2：深入了解项目
        if intent == "understand_project" and context.get("need_details"):
            return ["repo_map", "discover_project_docs", "get_repo_structure"]
        
        # 场景3：定位代码
        if intent == "locate_code":
            return ["semantic_code_search"]  # 最精准的
        
        # 场景4：理解代码
        if intent == "understand_code":
            return ["read_file", "get_file_symbols", "lsp_find_references"]
```

#### 3.2 工具调用成本优化

```python
# 记录工具调用成本
TOOL_COSTS = {
    "repo_map": {"tokens": 2000, "time": 3.0, "value": 9},
    "discover_project_docs": {"tokens": 500, "time": 1.0, "value": 7},
    "semantic_code_search": {"tokens": 1000, "time": 2.0, "value": 8},
    "read_file": {"tokens": 200, "time": 0.5, "value": 6},
}

# 选择最优工具组合（价值/成本比）
def select_optimal_tools(intent, budget):
    tools = get_candidate_tools(intent)
    return optimize_by_value_cost_ratio(tools, budget)
```

### Phase 4: 协作模式升级（长期）

#### 4.1 真正的多Agent讨论

```python
# 当前：并行执行 → 主Agent整合
# 问题：没有真正的"讨论"

# 改进：引入讨论机制
class AgentDiscussion:
    async def discuss(self, topic, agents):
        # Round 1: 各Agent提出初步意见
        opinions = await self.gather_opinions(topic, agents)
        
        # Round 2: 针对分歧点讨论
        conflicts = self.identify_conflicts(opinions)
        if conflicts:
            refined = await self.discuss_conflicts(conflicts, agents)
        
        # Round 3: 达成共识
        consensus = await self.reach_consensus(refined, agents)
        
        return consensus
```

#### 4.2 动态Agent选择

```python
# 当前：基于关键词选择Agent
# 改进：基于任务复杂度和Agent能力匹配

class DynamicAgentSelector:
    async def select_agents(self, task):
        # 分析任务复杂度
        complexity = await self.analyze_complexity(task)
        
        # 分解子任务
        subtasks = await self.decompose_task(task)
        
        # 匹配最合适的Agent
        agents = []
        for subtask in subtasks:
            best_agent = self.match_agent(subtask)
            agents.append(best_agent)
        
        return agents
```

### Phase 5: 记忆系统增强（长期）

#### 5.1 工作上下文记忆

```python
# 记住用户的工作流
class WorkflowMemory:
    def remember_workflow(self, session_id, action):
        """记住用户的工作流程"""
        workflow = self.get_workflow(session_id)
        workflow.append({
            "action": action,
            "timestamp": now(),
            "context": current_context
        })
    
    def predict_next_action(self, session_id):
        """预测用户下一步可能的操作"""
        workflow = self.get_workflow(session_id)
        return self.ml_model.predict(workflow)
```

#### 5.2 项目知识图谱

```python
# 构建项目知识图谱
class ProjectKnowledgeGraph:
    def build_graph(self, repo_path):
        """构建项目知识图谱"""
        graph = {
            "modules": [],      # 模块
            "functions": [],    # 函数
            "classes": [],      # 类
            "dependencies": [], # 依赖关系
            "call_graph": [],   # 调用图
        }
        return graph
    
    def query(self, question):
        """基于知识图谱回答问题"""
        # "登录功能在哪里？" → 查询图谱 → 返回相关节点
        return self.graph_query(question)
```

## 实施优先级

### 🔥 立即可做（本周）
1. ✅ 重写 chat-assistant 提示词（场景化、智能化）
2. ✅ 优化 sisyphus 提示词（减少格式化）
3. ✅ 添加成本意识到工具选择逻辑
4. ✅ 改进意图识别（增加上下文）

### 📅 中期目标（本月）
1. 实现智能工具选择器
2. 实现工作阶段追踪
3. 优化预取策略（更精细的分级）
4. 改进辅助Agent选择逻辑

### 🎯 长期目标（下季度）
1. 实现真正的多Agent讨论机制
2. 构建项目知识图谱
3. 实现工作流预测
4. 动态Agent能力匹配

## 衡量标准

### 用户体验指标
- ⏱️ 响应速度：首次回复 < 3秒
- 🎯 准确率：意图识别准确率 > 90%
- 💰 成本效率：平均token消耗降低30%
- 😊 满意度：用户觉得"聪明"、"懂我"

### 技术指标
- 🔧 工具调用次数：平均减少40%
- 🎯 工具选择准确率：> 85%
- 🧠 上下文理解：能记住3轮以上对话
- 🤝 协作效率：多Agent任务完成时间减少50%

## 下一步行动

1. **今天**：重写 chat-assistant.md 提示词
2. **明天**：测试新提示词，收集反馈
3. **本周**：实现智能工具选择器原型
4. **下周**：优化意图识别，增加上下文感知

---

**目标**：让DaoyouCode成为真正的"工作室合伙人"，而不只是"命令执行器"
