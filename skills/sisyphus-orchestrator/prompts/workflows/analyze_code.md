# 代码分析工作流

## 工具使用原则

⚠️ **必读**：请先阅读 [工具使用指南](tool_usage_guide.md)，了解工具优先级和最佳实践。

⚠️ **Context 变量**：请阅读 [Context 使用指南](context_usage_guide.md)，了解如何使用 Context 变量。

**核心原则：优先使用 repo_map、LSP、AST 等高效工具，避免逐个文件搜索！**

## 🎯 Context 变量简化分析流程

系统会自动保存搜索结果，简化多文件分析：

- **target_file**: 首次搜索时自动设置（主要分析的文件）
- **last_search_paths**: 最新搜索结果（参考文件）
- **search_history**: 所有搜索历史（回溯查找）

**使用示例**：
```
1. text_search("agent.py")
   → target_file = "agent.py"

2. read_file(path="{{target_file}}")
   → 分析主文件

3. text_search("context.py")
   → target_file 保持不变
   → last_search_paths = ["context.py"]

4. read_file(path="{{last_search_paths[0]}}")
   → 分析参考文件
```

详细说明请参考：[Context 使用指南](context_usage_guide.md)

## 任务目标

分析代码的架构、逻辑、实现方式，帮助用户理解代码。

## 执行步骤

### 1. 确定分析范围

根据用户请求，确定需要分析的内容：
- 整个项目的架构？
- 某个模块的实现？
- 某个功能的逻辑？
- 某个文件的代码？

### 2. 收集代码信息

**按优先级使用工具**：

#### 2.1 项目级分析（整体架构）
```
使用工具：repo_map
参数：
  - repo_path: "."
  - max_depth: 3
  - include_tests: false

作用：获取项目的代码地图，了解整体结构
```

#### 2.2 目录级分析（模块结构）
```
使用工具：get_repo_structure
参数：
  - repo_path: "目标目录"
  - max_depth: 2
  - show_files: true

作用：了解目录结构和文件组织
```

#### 2.3 文件级分析（代码实现）

**⚠️ 重要：使用 LSP 工具前，必须先确认文件存在**

```
步骤1：确认文件存在
使用工具：read_file
参数：
  - file_path: "具体文件路径"

作用：读取文件内容，同时确认文件存在

步骤2：获取文件符号（类、函数等）
使用工具：get_file_symbols
参数：
  - file_path: "具体文件路径"

步骤3（可选）：LSP 符号查询（获取类型信息）
⚠️ 只有在步骤1成功读取文件后才使用
使用工具：lsp_symbols
参数：
  - file_path: "具体文件路径"（必须是文件，不能是目录）
  - scope: "file"（不要使用 "workspace"）
  - query: ""（可选，用于过滤）

⚠️ 重要：lsp_symbols 只能用于具体的文件路径
- ✅ 正确：file_path="backend/main.py"
- ❌ 错误：file_path="."（目录）
- ❌ 错误：file_path="backend"（目录）
- ❌ 错误：file_path="*"（通配符）

如果不确定文件路径，先用 list_files 或 text_search 找到文件。
如果文件不存在，不要使用 LSP 工具。
```

#### 2.4 依赖分析（引用关系）
```
使用工具：lsp_find_references
参数：
  - file_path: "具体文件路径"
  - line: 行号
  - character: 列号

作用：查找某个符号的所有引用
```

#### 2.5 代码搜索（查找相关代码）
```
使用工具：text_search 或 regex_search
参数：
  - query: "搜索关键词"
  - file_pattern: "*.py"（可选）

作用：查找相关的代码片段
```

### 3. 分析代码

根据收集的信息，分析：

#### 3.1 架构分析
- 项目的整体结构
- 模块之间的关系
- 设计模式的使用
- 代码组织方式

#### 3.2 逻辑分析
- 核心流程
- 数据流向
- 控制流程
- 异常处理

#### 3.3 实现分析
- 关键函数的实现
- 算法的选择
- 数据结构的使用
- 性能考虑

#### 3.4 质量分析
- 代码可读性
- 可维护性
- 潜在问题
- 改进建议

### 4. 提供分析结果

根据用户的具体问题，灵活组织分析结果：
- 如果用户问整体架构，重点说明架构设计
- 如果用户问具体实现，重点说明实现逻辑
- 如果用户问某个功能，重点说明该功能的实现
- 用清晰的语言解释，不要过于技术化

## 工具使用原则

### 优先级

1. **先整体后局部**：先用 repo_map 了解整体，再深入具体文件
2. **先简单后复杂**：先用 get_file_symbols，需要类型信息时再用 lsp_symbols
3. **先搜索后读取**：不确定文件位置时，先搜索再读取

### 避免的错误

❌ **不要对不存在的文件使用 LSP 工具**
```
错误示例：
text_search 找到了文件路径 → 直接使用 lsp_symbols
正确做法：
text_search 找到了文件路径 → read_file 确认存在 → 再使用 lsp_symbols
```

❌ **不要对目录使用 lsp_symbols**
```
错误示例：
lsp_symbols(file_path=".", scope="workspace")
lsp_symbols(file_path="backend", scope="workspace")
```

❌ **不要过度使用工具**
- 如果 repo_map 已经提供了足够信息，不需要再读取每个文件
- 如果 get_file_symbols 已经足够，不需要再用 lsp_symbols

❌ **不要忽略用户的具体问题**
- 用户问"登录功能怎么实现"，重点分析登录相关代码
- 不要分析整个项目的所有代码

### 正确的工具使用示例

#### 示例1：分析整个项目
```
1. repo_map(repo_path=".")
2. 根据代码地图，识别核心模块
3. 对核心模块使用 get_repo_structure
4. 总结项目架构
```

#### 示例2：分析某个功能
```
1. text_search(query="登录", file_pattern="**/*.py")
2. 找到相关文件（如 auth.py）
3. read_file(file_path="backend/auth.py")
4. get_file_symbols(file_path="backend/auth.py")
5. 分析登录逻辑
```

#### 示例3：分析某个文件
```
1. read_file(file_path="backend/main.py")
2. get_file_symbols(file_path="backend/main.py")
3. 如果需要类型信息：
   lsp_symbols(file_path="backend/main.py", scope="file")
4. 分析文件内容
```

## 注意事项

1. **聚焦用户问题**：不要分析无关的代码
2. **控制分析深度**：根据用户需求决定分析的详细程度
3. **提供可操作的建议**：如果发现问题，给出改进建议
4. **使用清晰的语言**：避免过于技术化的术语
5. **突出重点**：先说最重要的发现，再说细节

### 文件路径处理

⚠️ **永远不要推测文件路径**

错误做法：
- ❌ 根据类名推测文件路径（如 `ContextSnapshot` → `context.py`）
- ❌ 根据模块名推测文件路径
- ❌ 假设文件一定存在

正确做法：
- ✅ 使用 `text_search` 查找类名或函数名
- ✅ 从搜索结果中获取实际的文件路径
- ✅ 使用 `read_file` 确认文件存在
- ✅ 然后再使用 LSP 工具

示例：
```
用户："分析 ContextSnapshot 类"

错误流程：
1. 推测文件路径（如：backend/daoyoucode/agents/core/context.py）
2. lsp_symbols(file_path="推测的路径")
3. 失败：文件不存在或路径错误

⚠️ 注意：
- 不要推测路径
- 路径相对于当前工作目录
- backend 前缀可能不需要（取决于运行位置）

正确流程：
1. text_search(query="class ContextSnapshot")
   → 返回：找到 1 个匹配，在 backend/core/snapshot.py
2. read_file(file_path="backend/core/snapshot.py")
   → 确认文件存在，读取内容
3. get_file_symbols(file_path="backend/core/snapshot.py")
   → 获取类的符号信息
```

## 成功标准

- ✅ 用户理解了代码的核心逻辑
- ✅ 用户知道了代码的组织方式
- ✅ 用户得到了有价值的见解
- ✅ 分析结果清晰、有条理
- ✅ 没有工具调用错误
