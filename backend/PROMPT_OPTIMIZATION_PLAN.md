# 提示词优化计划

## 当前问题

### 问题1: 工具选择不够精准

**现象**:
```
用户: "调用llm流程中，使用什么模型？"
LLM: 调用3阶段（discover_project_docs + get_repo_structure + repo_map）
成本: ~8588 tokens
```

**期望**:
```
用户: "调用llm流程中，使用什么模型？"
LLM: 调用 grep_search → read_file
成本: ~1000 tokens
```

**原因**: 提示词中对"具体问题"的指导不够清晰

---

### 问题2: 缺少决策树

当前提示词是"建议"，不是"决策流程"：
```markdown
当用户问"了解项目"时，使用3阶段理解
```

LLM可能理解为：
- "只要和项目有关，就用3阶段"
- "不确定时，用3阶段保险"

---

### 问题3: 示例不够丰富

只有2个示例：
1. 了解项目（宏观）
2. BaseAgent实现（具体）

缺少：
- 搜索类问题
- 修改类问题
- 调试类问题
- 架构类问题

---

## 优化方案

### 方案1: 添加清晰的决策树 ⭐

```markdown
## 工具选择决策树

### 第一步：判断问题类型

问自己：用户想要什么？

1. **全面了解项目**
   - 关键词：了解项目、项目介绍、项目架构、有什么特点
   - 策略：3阶段理解
   - 工具：discover_project_docs → get_repo_structure → repo_map

2. **查找具体代码**
   - 关键词：XX在哪里、XX怎么实现、XX的代码
   - 策略：精准搜索
   - 工具：grep_search → read_file

3. **理解模块结构**
   - 关键词：有哪些模块、目录结构、文件组织
   - 策略：只看结构
   - 工具：get_repo_structure

4. **修改代码**
   - 关键词：修改XX、添加XX、删除XX
   - 策略：先定位，再修改
   - 工具：grep_search → read_file → write_file

5. **调试问题**
   - 关键词：为什么XX、XX报错、XX不工作
   - 策略：搜索+分析
   - 工具：grep_search → read_file → lsp_diagnostics

### 第二步：选择最小工具集

原则：**只调用必要的工具，不要过度**

- ❌ 不要：用户问具体问题，还调用discover_project_docs
- ✅ 要：直接用grep_search定位代码
```

---

### 方案2: 丰富示例库

#### 示例1: 全面了解（已有）
```
用户: "了解下当前项目"
工具: discover_project_docs → get_repo_structure → repo_map
```

#### 示例2: 查找代码（新增）
```
用户: "调用llm的代码在哪里？"
工具: grep_search("call_llm") → read_file(agent.py)
```

#### 示例3: 理解流程（新增）
```
用户: "Agent执行流程是怎样的？"
工具: repo_map(mentioned_idents=["execute", "Agent"]) → read_file
```

#### 示例4: 查看模块（新增）
```
用户: "有哪些编排器？"
工具: get_repo_structure(path="agents/orchestrators")
```

#### 示例5: 修改代码（新增）
```
用户: "给BaseAgent添加一个日志方法"
工具: grep_search("class BaseAgent") → read_file → write_file
```

#### 示例6: 调试问题（新增）
```
用户: "为什么工具调用失败？"
工具: grep_search("execute_tool") → read_file → lsp_diagnostics
```

---

### 方案3: 添加成本意识

```markdown
## 成本优化原则

### Token预算意识

每次调用工具前，问自己：
1. 这个工具真的必要吗？
2. 有没有更轻量的替代方案？
3. 能不能减少参数（如max_tokens）？

### 工具成本对比

| 工具 | 成本 | 适用场景 |
|------|------|---------|
| grep_search | ~100 tokens | 查找关键词 |
| read_file | ~500-2000 tokens | 读取具体文件 |
| get_repo_structure | ~1000 tokens | 查看目录 |
| discover_project_docs | ~1500 tokens | 读取文档 |
| repo_map (3000) | ~3000 tokens | 聚焦搜索 |
| repo_map (6000) | ~6000 tokens | 全局视图 |

### 优化策略

- ✅ 优先使用轻量工具（grep_search）
- ✅ 只在必要时使用重量工具（repo_map）
- ✅ 使用mentioned_idents缩小范围
- ✅ 使用chat_files保持聚焦
```

---

### 方案4: 添加反思机制

```markdown
## 工具调用后的反思

每次工具调用后，问自己：

1. **结果是否足够？**
   - 如果足够，直接回答用户
   - 如果不够，再调用下一个工具

2. **是否过度调用？**
   - 如果已经有答案，不要继续调用
   - 避免"为了调用而调用"

3. **用户真正想要什么？**
   - 重新审视用户问题
   - 确保回答切中要点

### 示例

**用户**: "有哪些编排器？"

**Action 1**: get_repo_structure(path="agents/orchestrators")

**Observation**: 
```
orchestrators/
├── simple.py
├── react.py
├── workflow.py
├── conditional.py
├── parallel.py
├── parallel_explore.py
└── multi_agent.py
```

**Thought**: 
- ✅ 已经看到所有编排器文件
- ✅ 可以直接回答用户
- ❌ 不需要再调用repo_map或read_file

**Answer**: 项目有7个编排器：Simple、ReAct、Workflow...
```

---

### 方案5: 添加常见模式

```markdown
## 常见问题模式

### 模式1: "XX在哪里"

**识别**: 在哪、在哪里、位置、文件

**策略**:
1. grep_search(关键词)
2. 如果找到，直接回答
3. 如果没找到，用repo_map扩大搜索

**示例**:
```
用户: "BaseAgent在哪里？"
→ grep_search("class BaseAgent")
→ 找到: backend/daoyoucode/agents/core/agent.py
→ 回答: "在 agent.py 的第45行"
```

### 模式2: "XX怎么实现"

**识别**: 怎么实现、如何实现、实现方式

**策略**:
1. grep_search(关键词) 定位文件
2. read_file 读取实现
3. 解释代码逻辑

**示例**:
```
用户: "缓存怎么实现的？"
→ grep_search("class.*Cache")
→ read_file(cache.py)
→ 分析代码
→ 回答: "使用了LRU缓存策略..."
```

### 模式3: "有哪些XX"

**识别**: 有哪些、列出、所有的

**策略**:
1. 如果是模块/文件：get_repo_structure
2. 如果是类/函数：repo_map
3. 不需要discover_project_docs

**示例**:
```
用户: "有哪些工具？"
→ get_repo_structure(path="agents/tools")
→ 回答: "有25个工具：ReadFile、WriteFile..."
```

### 模式4: "XX和YY的区别"

**识别**: 区别、对比、比较

**策略**:
1. repo_map(mentioned_idents=[XX, YY])
2. read_file 读取两者代码
3. 对比分析

**示例**:
```
用户: "Simple和ReAct编排器的区别？"
→ repo_map(mentioned_idents=["Simple", "ReAct"])
→ read_file(simple.py)
→ read_file(react.py)
→ 对比分析
→ 回答: "Simple直接执行，ReAct有推理循环..."
```

### 模式5: "为什么XX"

**识别**: 为什么、原因、怎么回事

**策略**:
1. grep_search 找到相关代码
2. read_file 分析逻辑
3. 可能需要lsp_diagnostics检查错误

**示例**:
```
用户: "为什么工具调用失败？"
→ grep_search("execute_tool")
→ read_file(registry.py)
→ lsp_diagnostics(registry.py)
→ 分析原因
→ 回答: "可能是工具未注册..."
```
```

---

## 优化后的提示词结构

```markdown
# DaoyouCode AI助手

## 核心原则

1. **精准高效**: 只调用必要的工具
2. **成本意识**: 优先使用轻量工具
3. **用户导向**: 理解用户真正想要什么

## 工具选择决策树

[决策树内容]

## 常见问题模式

[5种模式]

## 工具成本对比

[成本表格]

## 丰富示例

[6个示例]

## 反思机制

[反思检查点]

## 可用工具

[工具列表]
```

---

## 实施步骤

### 第1步: 重构提示词结构

1. 添加决策树（最重要）
2. 添加常见模式
3. 添加成本意识
4. 丰富示例

### 第2步: 测试验证

测试用例：
```
1. "了解项目" → 应该用3阶段
2. "调用llm在哪" → 应该用grep_search
3. "有哪些编排器" → 应该用get_repo_structure
4. "BaseAgent怎么实现" → 应该用grep_search + read_file
5. "为什么失败" → 应该用grep_search + diagnostics
```

### 第3步: 迭代优化

根据实际使用情况：
1. 收集LLM的工具选择
2. 分析是否合理
3. 调整提示词
4. 重新测试

---

## 预期效果

### 优化前

```
用户: "调用llm在哪？"
工具: discover_project_docs + get_repo_structure + repo_map
成本: ~8588 tokens
```

### 优化后

```
用户: "调用llm在哪？"
工具: grep_search + read_file
成本: ~1000 tokens
节省: 85%
```

---

## 总结

### 关键改进

1. ✅ 清晰的决策树（不是模糊的建议）
2. ✅ 丰富的示例（覆盖各种场景）
3. ✅ 成本意识（让LLM知道成本）
4. ✅ 反思机制（避免过度调用）
5. ✅ 常见模式（快速匹配问题类型）

### 核心思想

**从"建议"到"决策流程"**

- 之前：当用户问XX时，可以用YY工具
- 现在：判断问题类型 → 选择最小工具集 → 反思是否足够

**从"示例"到"模式"**

- 之前：给几个示例
- 现在：总结常见模式，让LLM举一反三

**从"功能"到"成本"**

- 之前：这个工具能做什么
- 现在：这个工具成本多少，什么时候用
