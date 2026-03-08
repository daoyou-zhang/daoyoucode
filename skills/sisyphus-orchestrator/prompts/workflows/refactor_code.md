# 代码重构工作流

## 工具使用原则

⚠️ **必读**：请先阅读 [工具使用指南](tool_usage_guide.md)，了解工具优先级和最佳实践。

**核心原则：优先使用 repo_map、LSP、AST 等高效工具，避免逐个文件搜索！**

## 任务目标

重构代码，改进代码结构、可读性、可维护性，但不改变功能。

## 核心原则

**重构的黄金法则**：
1. 小步快跑：每次只做一个小改动
2. 保持测试通过：每次改动后确保测试通过
3. 不改变行为：重构不改变代码的外部行为
4. 有明确目标：知道为什么要重构

## 执行步骤

### 1. 理解现有代码

**⚠️ 重要：优先使用 repo_map 和 LSP 工具获取全局视图！**

参考：[工具使用指南](tool_usage_guide.md)

#### 1.1 获取项目代码地图（推荐，第一步）
```
使用工具：repo_map
参数：
  - repo_path: "."
  - max_tokens: 5000（可选，获取更多信息）
  - enable_lsp: true（可选，启用LSP增强）

作用：
- ✅ 了解要重构的代码在项目中的位置
- ✅ 查看模块之间的依赖关系
- ✅ 识别重复代码和可以合并的部分
- ✅ 评估重构的影响范围
```

#### 1.2 读取目标代码
```
使用工具：read_file
参数：
  - file_path: "要重构的文件"

作用：了解代码内容
```

#### 1.3 分析代码结构（AST 优先）
```
使用工具：get_file_symbols
参数：
  - file_path: "要重构的文件"

作用：
- ✅ 快速获取类、函数结构
- ✅ 了解代码组织方式
- ✅ 比手动阅读更高效
```

#### 1.4 查找依赖关系（LSP 优先）

**⚠️ 重要：使用 LSP 工具前，必须先确认文件存在**

```
步骤1：确认文件存在
使用工具：read_file
参数：
  - file_path: "要检查的文件"

作用：确认文件确实存在，避免 LSP 工具报错

步骤2：查找引用关系（文件存在时）
使用工具：lsp_find_references
参数：
  - file_path: "要重构的文件"
  - line: 关键函数的行号
  - character: 列号

作用：
- ✅ 了解哪些地方使用了这个代码
- ✅ 评估重构的影响范围
- ✅ 确保不会遗漏需要更新的地方
```

#### 1.5 检查现有问题（LSP 优先）
```
使用工具：lsp_diagnostics
参数：
  - file_path: "要重构的文件"

作用：
- ✅ 了解现有的语法、类型错误
- ✅ 重构时一并修复这些问题
```

### 2. 确定重构目标

明确重构的目标：

#### 2.1 常见重构目标
- **提取函数**：将长函数拆分为小函数
- **提取类**：将相关功能组织到类中
- **重命名**：使用更清晰的命名
- **消除重复**：提取公共代码
- **简化条件**：简化复杂的 if/else
- **优化结构**：改进代码组织

#### 2.2 评估影响范围
- 影响哪些文件？
- 影响哪些调用方？
- 是否需要更新测试？
- 是否需要更新文档？

### 3. 制定重构计划

**将大的重构拆分为小步骤**：

#### 3.1 列出重构步骤
例如，重构一个大函数：
1. 提取第一个子功能为函数
2. 提取第二个子功能为函数
3. 简化主函数逻辑
4. 重命名函数和变量
5. 添加文档字符串

#### 3.2 确定顺序
- 先做简单的（如重命名）
- 再做复杂的（如提取类）
- 每步都要保持代码可运行

### 4. 执行重构

**一次只做一个改动**：

#### 4.1 使用搜索替换（推荐）
```
使用工具：search_replace
参数：
  - file_path: "目标文件"
  - search: "要替换的代码"
  - replace: "替换后的代码"
  - is_regex: false

作用：精确替换代码片段
```

#### 4.2 或者重写文件
```
使用工具：write_file
参数：
  - file_path: "目标文件"
  - content: "重构后的完整代码"

作用：重写整个文件（适合大改动）
```

#### 4.3 验证改动
```
步骤1：检查语法
使用工具：lsp_diagnostics
参数：
  - file_path: "重构的文件"

步骤2：查看变更
使用工具：git_diff
参数：
  - file_path: "重构的文件"

步骤3：运行测试（如果有）
使用工具：run_test
参数：
  - test_path: "相关测试文件"
```

### 5. 更新相关代码

**如果重构影响了其他文件**：

#### 5.1 查找所有引用
```
使用工具：lsp_find_references
参数：
  - file_path: "重构的文件"
  - line: 修改的函数行号
  - character: 列号

作用：找到所有调用方
```

#### 5.2 更新调用方
```
使用工具：search_replace 或 batch_write_files
参数：根据具体情况

作用：更新所有受影响的代码
```

### 6. 验证重构结果

**确保重构没有破坏功能**：

#### 6.1 检查所有修改的文件
```
使用工具：git_diff
参数：无（查看所有变更）

作用：确认所有改动都是预期的
```

#### 6.2 运行测试
```
使用工具：run_test
参数：
  - test_path: "."（运行所有测试）

作用：确保功能没有被破坏
```

#### 6.3 检查代码质量
```
使用工具：lsp_diagnostics
参数：
  - file_path: "重构的文件"

作用：确保没有引入新的错误
```

### 7. 说明重构

简要说明重构的内容和改进点，根据用户需求灵活调整说明的详细程度。

## 常见重构模式

### 模式1：提取函数

**场景**：函数太长，难以理解

```
步骤：
1. 识别可以提取的代码块
2. 确定函数名和参数
3. 提取为新函数
4. 替换原代码为函数调用
5. 验证功能不变
```

### 模式2：提取类

**场景**：相关功能分散在多个函数中

```
步骤：
1. 识别相关的函数和数据
2. 设计类的接口
3. 创建新类
4. 移动函数到类中
5. 更新调用方
6. 验证功能不变
```

### 模式3：拆分大类 ⭐⭐⭐（重要）

**场景**：一个类太大，承担了太多职责（如 agent.py 超过 1000 行）

**⚠️ 关键原则**：
1. **小步快跑** - 一次只拆一个职责
2. **先创建后移动** - 先创建新文件，再移动代码
3. **保持可运行** - 每步都要保持代码可运行
4. **验证再继续** - 每步都要验证，失败就回退
5. **动态获取路径** - 永远不要硬编码路径，必须先搜索定位

## 路径处理规则 ⚠️⚠️⚠️

### 核心原则：永远不要硬编码路径

❌ **错误做法**：
```
write_file(file_path="backend/daoyoucode/agents/core/config.py", ...)
read_file(file_path="daoyoucode/agents/core/agent.py")
```

✅ **正确做法**：
```
1. 使用 text_search 定位文件
2. 从搜索结果提取路径
3. 使用 read_file 验证路径
4. 基于已知路径构造新路径
5. 所有后续步骤使用提取的路径
```

### 路径传递流程

```
步骤1：搜索定位
text_search(query="class BaseAgent", file_pattern="**/*.py") 
→ 结果：找到 backend/daoyoucode/agents/core/agent.py:50

步骤2：提取路径
从搜索结果中提取：
- target_file = "backend/daoyoucode/agents/core/agent.py"
- target_dir = "backend/daoyoucode/agents/core"

步骤3：验证路径
read_file(file_path=target_file)
→ 成功：路径正确，继续
→ 失败：重新搜索或调整路径

步骤4：构造新路径
基于 target_dir 构造新文件路径：
- config_file = target_dir + "/config.py"
- llm_caller_file = target_dir + "/llm_caller.py"

步骤5：使用路径
所有后续工具调用都使用这些变量：
- read_file(file_path=target_file)
- write_file(file_path=config_file, ...)
- lsp_diagnostics(file_path=target_file)
```

**详细步骤**：

#### 步骤0：定位目标文件（必须第一步）⭐⭐⭐
```
⚠️ 重要：这是最关键的一步，必须先执行

工具序列：

1. 搜索目标文件
   text_search(
       query="用户提到的类名或文件特征",
       file_pattern="**/*.py"
   )
   
   输出示例：
   找到 1 个匹配:
   - backend/daoyoucode/agents/core/agent.py:50: class BaseAgent
   
2. 提取路径信息
   从搜索结果中提取：
   → target_file = "backend/daoyoucode/agents/core/agent.py"
   → target_dir = "backend/daoyoucode/agents/core"
   
   ⚠️ 注意：
   - 路径可能包含或不包含 backend 前缀
   - 取决于当前工作目录
   - 不要假设路径格式
   
3. 验证文件存在
   read_file(file_path=target_file)
   
   → 成功：确认路径正确，记住这个路径
   → 失败：调整路径或重新搜索

⚠️ 关键：将 target_file 和 target_dir 记住，后续所有步骤都使用这些变量
```

#### 步骤1：分析类的职责（5分钟）
```
⚠️ 使用步骤0获取的 target_file

工具：
1. read_file(file_path=target_file)
   → 读取完整代码

2. get_file_symbols(file_path=target_file)
   → 分析类结构，列出所有方法

3. 手动分析：
   → 识别不同的职责（如：LLM调用、工具管理、记忆管理）
   → 每个职责包含哪些方法
   → 方法之间的依赖关系

输出：拆分计划
- 职责1 → 新类A（包含方法1、2、3）
- 职责2 → 新类B（包含方法4、5、6）
- 职责3 → 新类C（包含方法7、8、9）
```

#### 步骤2：创建配置文件（3分钟）⭐
```
⚠️ 重要：先创建独立的配置文件，避免循环导入

⚠️ 路径构造：基于步骤0获取的 target_dir

构造新文件路径：
config_file = target_dir + "/config.py"

示例：
如果 target_dir = "backend/daoyoucode/agents/core"
则 config_file = "backend/daoyoucode/agents/core/config.py"

工具：write_file
参数：
  - file_path: config_file（使用构造的路径变量）
  - content: 配置类代码

内容示例：
```python
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List

@dataclass
class AgentConfig:
    """Agent配置"""
    name: str
    description: str
    model: str
    temperature: float = 0.7
    system_prompt: str = ""

@dataclass
class AgentResult:
    """Agent执行结果"""
    success: bool
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
```

验证：
lsp_diagnostics(file_path=config_file)

⚠️ 如果验证失败：
- 检查路径是否正确
- 使用 read_file(file_path=config_file) 确认文件已创建
- 修复语法错误后再继续
```

#### 步骤3：创建第一个新类（10分钟）⭐
```
⚠️ 重要：一次只创建一个新类，不要同时创建多个

⚠️ 路径构造：基于步骤0获取的 target_dir

构造新文件路径：
llm_caller_file = target_dir + "/llm_caller.py"

示例：
如果 target_dir = "backend/daoyoucode/agents/core"
则 llm_caller_file = "backend/daoyoucode/agents/core/llm_caller.py"

工具：write_file
参数：
  - file_path: llm_caller_file（使用构造的路径变量）
  - content: 新类代码

内容要求：
1. 从原类复制相关方法
2. 添加必要的导入
3. 确保类可以独立运行

验证：
lsp_diagnostics(file_path=llm_caller_file)

⚠️ 如果有错误：
- 修复导入问题
- 修复类型问题
- 不要继续下一步，直到这个类没有错误
```

#### 步骤4：更新原类使用新类（10分钟）⭐
```
⚠️ 重要：使用 search_replace，不要用 intelligent_diff_edit
⚠️ 使用步骤0获取的 target_file

工具：search_replace（多次调用）

第1次：添加导入
search_replace(
    file_path=target_file,  # 使用步骤0的路径变量
    search="from dataclasses import dataclass, field",
    replace="""from dataclasses import dataclass, field
from .config import AgentConfig, AgentResult
from .llm_caller import LLMCaller"""
)

第2次：修改 __init__
search_replace(
    file_path=target_file,  # 使用相同的路径变量
    search="def __init__(self, config: AgentConfig):",
    replace="""def __init__(self, config: AgentConfig):
        self.config = config
        self.llm_caller = LLMCaller()"""
)

第3次：删除已移动的方法（一个一个删）
search_replace(
    file_path=target_file,  # 使用相同的路径变量
    search="def _call_llm(self, ...):\n    完整的方法体",
    replace="# 已移至 LLMCaller"
)

验证：
lsp_diagnostics(file_path=target_file)

⚠️ 如果有错误：
- 检查导入是否正确
- 检查方法调用是否更新
- 不要继续下一步
```

#### 步骤5：查找并更新引用（10分钟）
```
⚠️ 使用步骤0获取的 target_file

工具：lsp_find_references

步骤：
1. 先确认文件存在（应该已经确认过）
   read_file(file_path=target_file)
   
2. 查找原类的所有引用
   lsp_find_references(
       file_path=target_file,  # 使用步骤0的路径变量
       line=类定义行号,
       character=0
   )
   
   输出示例：
   找到 3 个引用:
   - backend/daoyoucode/orchestrators/core.py:25
   - backend/daoyoucode/cli/main.py:10
   - backend/tests/test_agent.py:5

3. 对每个引用文件：
   提取引用文件路径：
   → ref_file_1 = "backend/daoyoucode/orchestrators/core.py"
   → ref_file_2 = "backend/daoyoucode/cli/main.py"
   → ref_file_3 = "backend/tests/test_agent.py"
   
   对每个文件使用 search_replace：
   search_replace(
       file_path=ref_file_1,  # 使用提取的路径
       search="agent._call_llm(...)",
       replace="agent.llm_caller.call(...)"
   )

4. 验证每个文件：
   lsp_diagnostics(file_path=ref_file_1)
   lsp_diagnostics(file_path=ref_file_2)
   lsp_diagnostics(file_path=ref_file_3)
```

#### 步骤6：验证整体（5分钟）
```
1. 查看所有变更
git_diff()

2. 运行测试（如果有）
run_test(test_path=".")

3. 确认功能没有被破坏
```

#### 步骤7：重复步骤2-6（拆分下一个职责）
```
⚠️ 重要：
- 一次只拆一个职责
- 每次都要完整走完步骤2-6
- 不要同时拆多个职责
- 继续使用步骤0获取的 target_file 和 target_dir
```

**完整示例（拆分 agent.py）**：

```
第0步：定位文件（必须）
text_search(query="class BaseAgent", file_pattern="**/*.py")
→ target_file = "backend/daoyoucode/agents/core/agent.py"
→ target_dir = "backend/daoyoucode/agents/core"

第1轮：拆分配置类
1. 构造路径：config_file = target_dir + "/config.py"
2. 创建 config.py（AgentConfig, AgentResult）
3. 更新 agent.py 导入（使用 target_file）
4. 验证

第2轮：拆分 LLM 调用
1. 构造路径：llm_caller_file = target_dir + "/llm_caller.py"
2. 创建 llm_caller.py（LLMCaller 类）
3. 移动 _call_llm, _call_llm_with_functions 等方法
4. 更新 agent.py 使用 LLMCaller（使用 target_file）
5. 查找并更新所有引用（使用 target_file）
6. 验证

第3轮：拆分工具管理
1. 构造路径：tool_manager_file = target_dir + "/tool_manager.py"
2. 创建 tool_manager.py（ToolManager 类）
3. 移动工具相关方法
4. 更新 agent.py 使用 ToolManager（使用 target_file）
5. 查找并更新所有引用（使用 target_file）
6. 验证

第4轮：拆分记忆管理
1. 构造路径：memory_manager_file = target_dir + "/memory_manager.py"
2. 创建 memory_manager.py（MemoryManager 类）
3. 移动记忆相关方法
4. 更新 agent.py 使用 MemoryManager（使用 target_file）
5. 查找并更新所有引用（使用 target_file）
6. 验证
```

**常见错误和解决方案**：

❌ **错误1：硬编码路径（最严重）**
```
# 错误做法
write_file(file_path="backend/daoyoucode/agents/core/config.py", ...)
read_file(file_path="daoyoucode/agents/core/agent.py")
→ 路径可能不正确，无法应用于其他项目

# 正确做法
# 步骤1：搜索定位
text_search(query="class BaseAgent", file_pattern="**/*.py")
→ 提取：target_file = "搜索结果中的路径"
→ 提取：target_dir = "文件所在目录"

# 步骤2：验证路径
read_file(file_path=target_file)

# 步骤3：构造新路径
config_file = target_dir + "/config.py"

# 步骤4：使用路径
write_file(file_path=config_file, ...)
→ 路径动态获取，可应用于任何项目
```

❌ **错误2：同时创建多个文件**
```
# 错误做法
batch_write_files(files=[
    {path: llm_caller_file, content: "..."},
    {path: tool_manager_file, content: "..."},
    {path: memory_manager_file, content: "..."}
])
→ 难以定位问题

# 正确做法
write_file(file_path=llm_caller_file, content="...")
验证
write_file(file_path=tool_manager_file, content="...")
验证
write_file(file_path=memory_manager_file, content="...")
验证
```

❌ **错误3：使用 intelligent_diff_edit 修改大文件**
```
# 错误做法
intelligent_diff_edit(
    file_path=target_file,
    search_block="很长的代码块",
    replace_block="修改后的代码块"
)
→ 容易失败，验证错误多

# 正确做法
search_replace(
    file_path=target_file,
    search="具体的一个方法",
    replace="# 已移至新类"
)
→ 精确、安全
```

❌ **错误4：忘记先创建 config.py**
```
# 错误做法
直接创建 llm_caller.py，导入 AgentConfig
→ 循环导入错误

# 正确做法
1. 先创建 config.py（独立的配置文件）
2. 再创建 llm_caller.py（导入 config.py）
3. 最后更新 agent.py（导入 config.py）
```

❌ **错误5：一次移动太多方法**
```
# 错误做法
一次性移动 10 个方法到新类
→ 验证失败，难以定位问题

# 正确做法
一次移动 2-3 个相关方法
验证通过后再移动下一批
```

❌ **错误6：跳过步骤0（定位文件）**
```
# 错误做法
直接假设文件路径，开始创建新文件
→ 路径错误，后续步骤全部失败

# 正确做法
1. 必须先执行步骤0：搜索定位目标文件
2. 提取并验证路径
3. 基于已知路径进行后续操作
```

### 模式4：消除重复

**场景**：多处代码重复

```
步骤：
1. 查找重复代码
2. 提取为公共函数
3. 替换所有重复处
4. 验证功能不变
```

### 模式4：简化条件

**场景**：复杂的 if/else 嵌套

```
步骤：
1. 识别条件逻辑
2. 提前返回（减少嵌套）
3. 提取条件为函数
4. 使用多态替代条件
5. 验证功能不变
```

### 模式5：重命名

**场景**：命名不清晰

```
步骤：
1. 确定新名称
2. 使用 search_replace 全局替换
3. 检查所有引用
4. 验证功能不变
```

## 工具使用原则

### 重构前

1. **必须理解代码**：完全理解要重构的代码
2. **必须查找引用**：了解影响范围
3. **必须检查测试**：确保有测试覆盖

### 重构时

1. **小步快跑**：每次只做一个小改动
2. **优先使用 search_replace**：精确替换，减少错误
3. **及时验证**：每步都要验证

### 重构后

1. **必须运行测试**：确保功能不变
2. **必须查看变更**：确认改动正确
3. **必须检查语法**：确保没有错误

## 注意事项

### 安全重构

1. **有测试覆盖**：重构前确保有测试
2. **小步前进**：不要一次改太多
3. **频繁验证**：每步都要验证
4. **保留备份**：Git 是你的朋友

### 避免的错误

❌ **不要硬编码路径（最重要）**
- 永远不要写死文件路径
- 必须先搜索定位文件
- 从搜索结果提取路径
- 基于已知路径构造新路径
- 所有步骤使用提取的路径变量

❌ **不要改变行为**
- 重构只改结构，不改功能
- 如果要改功能，那不是重构

❌ **不要一次改太多**
- 大的重构要拆分为小步骤
- 每步都要保持代码可运行

❌ **不要推测文件路径**
- 永远不要根据类名或模块名推测文件路径
- 必须使用 text_search 或 repo_map 查找实际路径
- 必须使用 read_file 确认文件存在
- 然后再使用 LSP 工具

❌ **不要忽略测试**
- 重构后必须运行测试
- 如果没有测试，先写测试

❌ **不要忽略调用方**
- 修改接口要更新所有调用方
- 使用 lsp_find_references 查找

### 何时停止重构

- ✅ 代码已经足够清晰
- ✅ 没有明显的改进空间
- ✅ 进一步重构收益递减
- ✅ 用户需求已经满足

## 成功标准

- ✅ 代码结构更清晰
- ✅ 代码更易理解和维护
- ✅ 功能没有被破坏
- ✅ 所有测试通过
- ✅ 没有引入新的错误
- ✅ Git 变更清晰可追溯
