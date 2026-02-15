# 两阶段执行模式

## 问题背景

用户提出："是不是业务编排问题？在skill中，控制llm第一次做意图理解？"

**核心问题**：
- LLM 直接调用工具，缺乏规划
- 搜索失败后立即误判，没有备选方案
- 缺乏"先思考再行动"的机制

**示例**：
```
用户: "需要超时恢复策略"
AI: text_search("timeout") → 没结果 → "代码库中没有超时处理"
实际: 应该先理解意图，制定多重搜索计划
```

---

## 解决方案：两阶段执行模式

### 核心思想

**不需要改代码**，只需要在 Skill 的 prompt 中添加"两阶段执行"指导：

1. **阶段1: 意图理解与规划**（不调用工具）
   - 理解用户真正想要什么
   - 分析任务复杂度
   - 制定执行计划
   - 预判风险和备选方案

2. **阶段2: 执行与验证**（调用工具）
   - 按计划执行
   - 验证结果
   - 如果失败，执行备选方案

---

## 实现方式

### 在 Skill Prompt 中添加

```markdown
## 执行流程：两阶段模式 ⭐⭐⭐

### 阶段1: 意图理解与规划（不调用工具）

**在调用任何工具之前，先在脑海中完成以下分析：**

1. 理解用户意图
   - 用户真正想要什么？
   - 是查询、修改、创建、还是理解？
   - 有没有隐含的需求？

2. 分析任务复杂度
   - 简单任务（单文件、已知位置）→ 直接执行
   - 中等任务（需要搜索、多文件）→ 制定计划
   - 复杂任务（需要理解、设计）→ 分步执行

3. 制定执行计划
   - 需要哪些信息？
   - 用什么工具获取？
   - 如果失败怎么办？（备选方案）
   - 如何验证结果？

4. 预判风险
   - 搜索可能失败 → 准备多种搜索方式
   - 文件可能不存在 → 准备创建方案
   - 理解可能不足 → 准备深入分析

### 阶段2: 执行与验证（调用工具）

**基于计划执行，并验证结果**
```

---

## 对比

### 改进前（单阶段）

```
用户: "需要超时恢复策略"
↓
AI: text_search("timeout")
↓
结果: 没找到
↓
AI: "代码库中没有超时处理逻辑"
```

**问题**：
- 没有规划
- 单次搜索失败就放弃
- 没有备选方案

### 改进后（两阶段）

```
用户: "需要超时恢复策略"
↓
[阶段1: 意图理解]
- 理解：用户想实现 LLM 超时恢复
- 复杂度：中等（需要搜索 + 可能设计）
- 计划：
  1. 多方式搜索现有代码
  2. 如果找到 → 分析
  3. 如果没找到 → 设计方案
- 风险：搜索可能失败 → 准备多种搜索词
↓
[阶段2: 执行]
- text_search("timeout")
- text_search("超时")
- text_search("TimeoutError")
- list_files("**/timeout*.py")
- get_repo_structure(annotate=True)
↓
结果: 综合判断是否存在
```

**优势**：
- 有规划
- 多重验证
- 有备选方案
- 更准确的判断

---

## 为什么不需要改代码？

### 1. ReAct 编排器已经支持

ReAct 编排器有预留方法：
- `_plan()`: 生成执行计划
- `_reflect()`: 反思失败原因
- `_verify()`: 验证结果

但当前简化版本不使用这些方法，而是让 LLM 通过 Function Calling 自主控制。

### 2. Prompt 可以控制 LLM 行为

通过在 prompt 中明确要求"两阶段执行"，LLM 会：
1. 先在内部思考（不调用工具）
2. 制定计划
3. 再调用工具执行

这是 **Prompt Engineering** 的力量。

### 3. 成本更低

如果通过代码实现：
- 需要额外的 LLM 调用（规划阶段）
- 需要解析计划结果
- 需要管理状态

通过 Prompt 实现：
- 0 额外成本
- LLM 内部完成规划
- 更灵活

---

## 与 ReAct 预留方法的关系

### 当前方案（Prompt 驱动）

```
用户输入
↓
LLM 读取 Prompt（包含两阶段指导）
↓
LLM 内部：
  - 阶段1: 理解意图、制定计划
  - 阶段2: 调用工具执行
↓
返回结果
```

**优势**：
- 简单、灵活
- 0 额外成本
- 适合大多数场景

### 未来方案（代码驱动）

如果需要更强的控制，可以实现 `AdvancedReActOrchestrator`：

```python
class AdvancedReActOrchestrator(ReActOrchestrator):
    async def execute(self, skill, user_input, context):
        # 阶段1: 显式规划
        plan = await self._plan(user_input, context)
        
        # 阶段2: 执行计划
        result = await self._execute_plan(plan, context)
        
        # 阶段3: 验证结果
        if not await self._verify(result, context):
            # 阶段4: 反思并重新规划
            new_instruction = await self._reflect(
                user_input, result, context
            )
            return await self.execute(skill, new_instruction, context)
        
        return result
```

**优势**：
- 更强的控制
- 可以记录计划
- 可以人工审核
- 适合关键任务

**劣势**：
- 更多 LLM 调用
- 更高成本
- 更复杂

---

## 测试建议

### 测试场景1: 搜索失败处理

```
用户: "看看有没有超时处理"

期望行为:
[阶段1: 规划]
- 理解：查找超时相关代码
- 计划：多方式搜索
- 风险：可能搜索不到

[阶段2: 执行]
- text_search("timeout")
- text_search("超时")
- list_files("**/timeout*.py")
- 综合判断

结果: "尝试了多种方式，确实没有找到" 或 "找到了相关代码"
```

### 测试场景2: 复杂任务

```
用户: "实现一个缓存系统"

期望行为:
[阶段1: 规划]
- 理解：需要设计和实现缓存
- 复杂度：高
- 计划：
  1. 搜索现有缓存实现
  2. 设计方案
  3. 实现代码
  4. 测试

[阶段2: 执行]
- 按计划逐步执行
- 每步验证结果
```

---

## 总结

### 核心价值

**通过 Prompt 实现"先思考再行动"**：
- ✅ 不需要改代码
- ✅ 0 额外成本
- ✅ 更准确的判断
- ✅ 更好的用户体验

### 实施步骤

1. ✅ 在 `chat_assistant.md` 中添加"两阶段执行"指导
2. ✅ 添加示例说明正确和错误的做法
3. 🔄 测试效果
4. 🔄 根据反馈调整

### 未来扩展

如果需要更强的控制：
- 实现 `AdvancedReActOrchestrator`
- 使用 ReAct 预留方法
- 添加人工审核机制

但对于大多数场景，**Prompt 驱动的两阶段模式已经足够**。

---

## 参考

- `backend/daoyoucode/agents/orchestrators/react.py` - ReAct 编排器和预留方法
- `backend/REACT_RESERVED_METHODS_GUIDE.md` - 预留方法详细说明
- `skills/chat-assistant/prompts/chat_assistant.md` - Skill Prompt（已更新）
