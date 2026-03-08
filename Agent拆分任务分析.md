# Agent 拆分任务分析

## 任务描述

将一个大的 Agent 类拆分为多个小的、职责单一的 Agent 类。

## 任务特点

1. **重构性质** - 改变代码结构，但功能不变
2. **多文件操作** - 需要创建新文件，修改现有文件
3. **依赖关系复杂** - 需要更新所有引用
4. **影响范围大** - 可能影响多个模块

## 应该用哪个工作流？

### 选项1：write_code.md ❌

**不适合的原因**：
- ❌ write_code 侧重于"编写新代码"
- ❌ 不强调"保持功能不变"
- ❌ 不强调"小步快跑"
- ❌ 缺少"查找引用"和"更新调用方"的指导

### 选项2：refactor_code.md ✅

**适合的原因**：
- ✅ 强调"不改变行为"
- ✅ 强调"小步快跑"
- ✅ 包含"查找引用"和"更新调用方"
- ✅ 包含验证步骤

**但需要优化**：
- ⚠️ 缺少"类拆分"的具体指导
- ⚠️ 缺少"多文件重构"的流程
- ⚠️ 缺少"依赖关系分析"的详细步骤

## 现有 refactor_code.md 的不足

### 1. 缺少"类拆分"模式

现有的重构模式：
- ✅ 提取函数
- ✅ 提取类
- ✅ 消除重复
- ✅ 简化条件
- ✅ 重命名

**缺少**：
- ❌ 拆分大类为多个小类
- ❌ 重新组织类的职责
- ❌ 处理类之间的依赖

### 2. 缺少"多文件重构"流程

现有流程侧重于单文件重构，对于多文件重构：
- ⚠️ 没有明确的步骤顺序
- ⚠️ 没有依赖关系分析
- ⚠️ 没有文件创建和组织的指导

### 3. 缺少"依赖分析"工具使用

虽然提到了 `lsp_find_references`，但：
- ⚠️ 没有强调在拆分前必须分析依赖
- ⚠️ 没有提供依赖关系可视化的方法
- ⚠️ 没有提供批量更新引用的策略

## 建议的优化

### 优化1：添加"类拆分"模式

```markdown
### 模式6：拆分大类

**场景**：一个类承担了太多职责

**步骤**：
1. 分析类的职责（使用 get_file_symbols）
2. 识别可以独立的职责
3. 设计新的类结构
4. 创建新类文件
5. 移动方法到新类
6. 更新原类，使用新类
7. 查找并更新所有引用
8. 验证功能不变

**工具使用**：
1. repo_map - 了解类在项目中的位置
2. get_file_symbols - 分析类的结构
3. lsp_find_references - 查找所有引用
4. write_file - 创建新类文件
5. search_replace - 更新引用
6. lsp_diagnostics - 验证语法
7. run_test - 验证功能
```

### 优化2：添加"多文件重构"流程

```markdown
## 多文件重构流程

### 阶段1：分析和规划
1. 使用 repo_map 了解项目结构
2. 使用 read_file 读取目标类
3. 使用 get_file_symbols 分析类结构
4. 使用 lsp_find_references 查找所有引用
5. 制定拆分计划（哪些职责拆到哪些类）

### 阶段2：创建新类
1. 设计新类的接口
2. 使用 write_file 创建新类文件
3. 实现新类的方法
4. 使用 lsp_diagnostics 验证语法

### 阶段3：更新原类
1. 使用 search_replace 移除已拆分的方法
2. 添加对新类的引用
3. 使用 lsp_diagnostics 验证语法

### 阶段4：更新调用方
1. 使用 lsp_find_references 查找所有调用
2. 使用 search_replace 批量更新引用
3. 使用 lsp_diagnostics 验证每个文件

### 阶段5：验证和清理
1. 使用 git_diff 查看所有变更
2. 使用 run_test 运行所有测试
3. 确认功能没有被破坏
```

### 优化3：强化依赖分析

```markdown
## 依赖关系分析

### 步骤1：使用 repo_map 获取全局视图
```
repo_map(
    repo_path=".",
    max_depth=3,
    include_tests=false
)
```
- 了解类在项目中的位置
- 查看模块之间的依赖关系
- 识别可能受影响的模块

### 步骤2：使用 lsp_find_references 查找引用
```
# 对每个要移动的方法
lsp_find_references(
    file_path="原类文件",
    line=方法行号,
    character=0
)
```
- 找到所有调用方
- 评估影响范围
- 制定更新策略

### 步骤3：使用 text_search 查找字符串引用
```
text_search(
    query="类名",
    file_pattern="**/*.py"
)
```
- 查找字符串形式的引用
- 查找配置文件中的引用
- 查找文档中的引用
```

## 完整的 Agent 拆分流程示例

### 场景：拆分 BaseAgent 类

假设 BaseAgent 有以下职责：
1. LLM 调用
2. 工具管理
3. 记忆管理
4. Prompt 构建

**目标**：拆分为 4 个独立的类

### 阶段1：分析（5-10分钟）

```
1. repo_map(repo_path=".")
   → 了解 BaseAgent 在项目中的位置

2. read_file(file_path="backend/daoyoucode/agents/core/agent.py")
   → 读取 BaseAgent 代码

3. get_file_symbols(file_path="backend/daoyoucode/agents/core/agent.py")
   → 分析类结构，识别方法

4. lsp_find_references(file_path="...", line=50, character=0)
   → 查找 BaseAgent 的所有引用

5. text_search(query="BaseAgent", file_pattern="**/*.py")
   → 查找字符串引用

分析结果：
- BaseAgent 被 10 个文件引用
- 主要方法：execute, _call_llm, _load_tools, _load_memory, _build_prompt
- 可以拆分为：LLMCaller, ToolManager, MemoryManager, PromptBuilder
```

### 阶段2：创建新类（10-15分钟）

```
1. write_file(
     file_path="backend/daoyoucode/agents/core/llm_caller.py",
     content="class LLMCaller: ..."
   )
   → 创建 LLMCaller 类

2. write_file(
     file_path="backend/daoyoucode/agents/core/tool_manager.py",
     content="class ToolManager: ..."
   )
   → 创建 ToolManager 类

3. write_file(
     file_path="backend/daoyoucode/agents/core/memory_manager.py",
     content="class MemoryManager: ..."
   )
   → 创建 MemoryManager 类

4. write_file(
     file_path="backend/daoyoucode/agents/core/prompt_builder.py",
     content="class PromptBuilder: ..."
   )
   → 创建 PromptBuilder 类

5. lsp_diagnostics(file_path="backend/daoyoucode/agents/core/llm_caller.py")
   → 验证每个新类的语法
```

### 阶段3：更新 BaseAgent（5-10分钟）

```
1. search_replace(
     file_path="backend/daoyoucode/agents/core/agent.py",
     search="def _call_llm(self, ...):\n    ...",
     replace="# 已移至 LLMCaller"
   )
   → 移除已拆分的方法

2. search_replace(
     file_path="backend/daoyoucode/agents/core/agent.py",
     search="def __init__(self, config):",
     replace="""
     def __init__(self, config):
         self.llm_caller = LLMCaller()
         self.tool_manager = ToolManager()
         self.memory_manager = MemoryManager()
         self.prompt_builder = PromptBuilder()
     """
   )
   → 添加对新类的引用

3. lsp_diagnostics(file_path="backend/daoyoucode/agents/core/agent.py")
   → 验证语法
```

### 阶段4：更新调用方（10-20分钟）

```
1. 对每个引用 BaseAgent 的文件：
   
   search_replace(
     file_path="引用文件",
     search="agent._call_llm(...)",
     replace="agent.llm_caller.call(...)"
   )
   
2. lsp_diagnostics(file_path="引用文件")
   → 验证每个文件
```

### 阶段5：验证（5-10分钟）

```
1. git_diff()
   → 查看所有变更

2. run_test(test_path=".")
   → 运行所有测试

3. 确认功能没有被破坏
```

### 总耗时：35-65分钟

## 对比：手工 vs daoyoucode

### 手工拆分
- 时间：2-4 小时
- 容易遗漏引用
- 容易出错
- 难以追踪变更

### 使用 daoyoucode
- 时间：35-65 分钟（节省 60-80%）
- 自动查找所有引用
- 自动验证语法
- Git 记录所有变更

## 结论

### 1. 应该用 refactor_code.md ✅

但需要添加：
- "类拆分"模式
- "多文件重构"流程
- 强化依赖分析

### 2. 现有工作流可以完成，但不够优化 ⚠️

可以完成的原因：
- ✅ 有基本的重构流程
- ✅ 有工具使用指导
- ✅ 有验证步骤

需要优化的原因：
- ⚠️ 缺少"类拆分"的具体指导
- ⚠️ 缺少"多文件重构"的流程
- ⚠️ 缺少"依赖分析"的详细步骤

### 3. 建议优化方向

**优先级1：添加"类拆分"模式**
- 提供具体的步骤
- 提供工具使用示例
- 提供完整的流程

**优先级2：添加"多文件重构"流程**
- 分阶段执行
- 明确每个阶段的目标
- 提供验证点

**优先级3：强化依赖分析**
- 强调使用 repo_map
- 强调使用 lsp_find_references
- 提供批量更新策略

## 下一步

你想让我：
1. 优化 refactor_code.md，添加"类拆分"模式？
2. 创建一个专门的 split_class.md 工作流？
3. 直接测试现有工作流，看看效果如何？
