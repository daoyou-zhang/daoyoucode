# 查找硬编码配置工作流

## 工具使用原则

⚠️ **必读**：请先阅读 [工具使用指南](tool_usage_guide.md)，了解工具优先级和最佳实践。

**核心原则：使用批量搜索工具，避免逐个文件检查！**

## 任务目标

分析代码库，找出所有应该可配置但被硬编码的参数，并提供配置化建议。

## 执行步骤

### 1. 理解需求

确认用户想要：
- 查找所有硬编码配置？
- 查找特定类型的硬编码（如超时、重试次数）？
- 分析某个模块的硬编码？

### 2. 批量搜索硬编码模式

**使用 grep_search 工具批量搜索常见硬编码模式**：

#### 2.1 数值类硬编码

```
搜索模式：
1. max_iterations\s*=\s*\d+
2. max_retries\s*=\s*\d+
3. timeout\s*=\s*[\d\.]+
4. max_tokens\s*=\s*\d+
5. temperature\s*=\s*[\d\.]+
6. max_length\s*=\s*\d+
7. max_size\s*=\s*\d+
8. max_history\s*=\s*\d+
9. cache_size\s*=\s*\d+
10. ttl\s*=\s*\d+

工具调用：
grep_search(
    query="max_iterations\\s*=\\s*\\d+",
    include_pattern="**/*.py",
    exclude_pattern="**/tests/**"
)

注意：
- 使用 \\ 转义特殊字符
- exclude_pattern 排除测试代码
- 一次搜索一个模式，不要合并
```

#### 2.2 字符串类硬编码

```
搜索模式：
1. model\s*=\s*["']qwen|model\s*=\s*["']gpt
2. path\s*=\s*["']\.daoyoucode
3. dir\s*=\s*["']\.cache

工具调用：
grep_search(
    query='model\\s*=\\s*["\']qwen',
    include_pattern="**/*.py",
    exclude_pattern="**/tests/**"
)
```

#### 2.3 路径类硬编码

```
搜索模式：
1. \.daoyoucode
2. \.cache
3. skills/

工具调用：
grep_search(
    query="\\.daoyoucode",
    include_pattern="**/*.py"
)
```

### 3. 分析搜索结果

对每个搜索结果：

#### 3.1 读取上下文

```
使用 read_file 读取文件，查看前后代码：

read_file(
    file_path="搜索到的文件路径",
    start_line=1100,
    end_line=1120
)

⚠️ 注意：
- 先使用 text_search 或 repo_map 查找文件
- 使用相对于当前工作目录的路径
- 不要硬编码 backend 前缀

目的：
- 理解这个值的用途
- 判断是否在测试代码中
- 判断是否在配置类中
- 判断是否已经可配置
```

#### 3.2 分类判断

**必须配置化（高优先级）**：
- ✅ 核心功能参数（工具调用次数、超时时间）
- ✅ 影响所有用户的参数
- ✅ 环境相关参数（路径、模型名称）
- ✅ 性能调优参数（缓存大小、并发数）

**应该配置化（中优先级）**：
- ✅ 历史记录限制
- ✅ 重试策略参数
- ✅ UI 显示参数

**可以忽略（低优先级）**：
- ❌ 测试代码中的硬编码
- ❌ 配置类的默认值（已经是配置的一部分）
- ❌ 数学常量、协议版本号
- ❌ HTTP 状态码、标准端口号

#### 3.3 判断依据

**检查文件路径**：
```python
# 测试代码 - 忽略
if "tests/" in file_path or "test_" in file_path:
    → IGNORE

# 配置类 - 检查是否在 @dataclass 中
if "@dataclass" in context or "class.*Config" in context:
    → IGNORE（如果是默认值）
```

**检查变量名**：
```python
# 核心参数 - 必须配置
if variable in ["timeout", "max_iterations", "max_retries"]:
    → MUST_CONFIG (high priority)

# 缓存参数 - 应该配置
if variable in ["cache_size", "max_history", "ttl"]:
    → SHOULD_CONFIG (medium priority)

# UI 参数 - 可以配置
if variable in ["max_length", "display_limit"]:
    → COULD_CONFIG (low priority)
```

### 4. 分析影响范围

对于需要配置化的硬编码：

#### 4.1 查找使用频率

```
使用 grep_search 查找变量在代码库中的使用：

grep_search(
    query="\\btimeout\\b",
    include_pattern="**/*.py",
    exclude_pattern="**/tests/**"
)

统计：
- 使用次数
- 涉及文件数
- 是否跨模块使用
```

#### 4.2 查找所在类和函数

```
使用 find_class 和 find_function：

find_class(
    class_name="UnifiedLLMClient",
    file_path="搜索到的文件路径"
)

find_function(
    function_name="chat",
    file_path="搜索到的文件路径"
)

⚠️ 注意：使用相对于当前工作目录的路径

目的：
- 理解调用链路
- 评估影响范围
```

#### 4.3 检查是否已有配置

```
搜索配置文件：

grep_search(
    query="timeout",
    include_pattern="**/*.yaml"
)

grep_search(
    query="timeout",
    include_pattern="**/config.py"
)

判断：
- 是否已经有相关配置？
- 配置是否完整？
- 是否需要补充？
```

### 5. 生成配置建议

对每个需要配置化的硬编码，提供：

#### 5.1 配置文件建议

```yaml
# 建议的配置文件结构
# config/llm_config.yaml
llm:
  timeout:
    default: 1800  # 默认30分钟
    simple_task: 300  # 简单任务5分钟
    complex_task: 3600  # 复杂任务1小时
    streaming: 1800  # 流式请求
```

#### 5.2 代码修改建议

```python
# 修改前
timeout=1800.0

# 修改后
from .config_manager import get_config_manager
config = get_config_manager()
timeout = config.get('llm_config.llm.timeout.default', 1800)
```

#### 5.3 优先级和影响评估

```
优先级: HIGH
影响范围: 所有 LLM 调用
风险级别: HIGH
建议配置文件: config/llm_config.yaml
配置路径: llm.timeout.default
```

### 6. 生成分析报告

使用 write_file 生成详细报告：

```
write_file(
    file_path="硬编码配置分析报告.md",
    content=report_content
)

报告结构：
1. 概述
   - 发现的硬编码总数
   - 按优先级分类统计
   - 按类型分类统计

2. 高优先级配置项
   - 详细列表
   - 影响分析
   - 配置建议

3. 中优先级配置项
   - 详细列表
   - 配置建议

4. 低优先级配置项
   - 简要列表

5. 实施建议
   - 分阶段实施计划
   - 配置文件结构
   - 配置管理器实现示例
```

## 工具使用示例

### 完整流程示例

```
用户："检查一下有没有需要配置文件，却给写死了的代码"

执行流程：

1. 搜索超时配置
   grep_search(query="timeout\\s*=\\s*[\\d\\.]+", include_pattern="**/*.py", exclude_pattern="**/tests/**")
   → 发现 15 处

2. 搜索重试配置
   grep_search(query="max_retries\\s*=\\s*\\d+", include_pattern="**/*.py", exclude_pattern="**/tests/**")
   → 发现 8 处

3. 搜索迭代次数
   grep_search(query="max_iterations\\s*=\\s*\\d+", include_pattern="**/*.py", exclude_pattern="**/tests/**")
   → 发现 5 处

4. 搜索缓存配置
   grep_search(query="cache_size\\s*=\\s*\\d+|max_cache\\s*=\\s*\\d+", include_pattern="**/*.py", exclude_pattern="**/tests/**")
   → 发现 3 处

5. 分析第一个发现（LLM 超时）
   read_file(file_path="搜索到的文件路径", start_line=110, end_line=115)
   → 读取上下文
   → 判断：MUST_CONFIG (high priority)

6. 查找使用频率
   grep_search(query="timeout=1800", include_pattern="**/*.py")
   → 发现 2 处使用（同步和流式）

7. 查找所在类

⚠️ 注意：使用相对于当前工作目录的路径
   find_class(class_name="UnifiedLLMClient", file_path="backend/daoyoucode/agents/llm/clients/unified.py")
   → 理解调用链路

8. 检查现有配置
   grep_search(query="timeout", include_pattern="**/*.yaml")
   → 未发现相关配置

9. 重复步骤 5-8 处理其他发现...

10. 生成报告
    write_file(file_path="硬编码配置分析报告.md", content=...)
    → 包含所有发现、分析和建议
```

## 注意事项

### 1. 批量搜索优化

✅ **正确做法**：
```
# 一次搜索一个模式
grep_search(query="timeout\\s*=\\s*[\\d\\.]+", ...)
grep_search(query="max_retries\\s*=\\s*\\d+", ...)
grep_search(query="max_iterations\\s*=\\s*\\d+", ...)
```

❌ **错误做法**：
```
# 不要尝试合并多个模式（正则表达式可能失败）
grep_search(query="timeout|max_retries|max_iterations", ...)
```

### 2. 排除测试代码

✅ **始终排除测试代码**：
```
exclude_pattern="**/tests/**"
```

### 3. 转义特殊字符

✅ **正确转义**：
```
query="max_iterations\\s*=\\s*\\d+"  # 使用 \\
query="\\.daoyoucode"  # 转义点号
```

### 4. 上下文分析

✅ **读取足够的上下文**：
```
# 读取前后 10-20 行
read_file(file_path=..., start_line=line-10, end_line=line+10)
```

### 5. 避免误判

检查以下情况，避免误报：
- 测试代码中的硬编码（合理）
- 配置类的默认值（已经可配置）
- 数学常量（不需要配置）
- 临时调试代码（标注 TODO）

### 6. 提供可操作的建议

不要只列出问题，要提供：
- 具体的配置文件结构
- 代码修改示例
- 实施优先级
- 风险评估

## 成功标准

- ✅ 找出所有需要配置化的硬编码
- ✅ 正确分类和优先级排序
- ✅ 提供详细的配置建议
- ✅ 生成完整的分析报告
- ✅ 没有误报（测试代码、配置类等）
- ✅ 报告清晰、可操作

## 输出格式

生成的报告应包含：

```markdown
# 硬编码配置分析报告

## 概述
- 总计发现: X 个硬编码配置
- 高优先级: X 个
- 中优先级: X 个
- 低优先级: X 个

## 🔴 高优先级（影响核心功能）

### 1. LLM 请求超时
**位置**: [文件路径]:112
**当前值**: timeout=1800.0

⚠️ 注意：文件路径相对于当前工作目录
**问题**: 硬编码，无法根据任务类型调整
**影响**: 所有 LLM 调用
**建议配置**:
```yaml
# config/llm_config.yaml
llm:
  timeout:
    default: 1800
    simple_task: 300
    complex_task: 3600
```

## 🟡 中优先级（影响性能）
...

## 🟢 低优先级（影响较小）
...

## 实施建议
1. 创建配置文件
2. 实现配置管理器
3. 修改代码使用配置
4. 测试验证
```
