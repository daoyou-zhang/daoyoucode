# Prompt占位符问题深度分析

## 问题现象

LLM在调用工具时，仍然使用占位符路径：
- `repo_map(repo_path="./your-repo-path")`
- `read_file(file_path="path/to/your/file.txt")`
- `text_search(directory="./src")`

## 根本原因

### 1. LLM训练数据的影响

LLM在训练时看到了大量使用占位符的示例代码：
```python
# 常见的占位符模式（来自文档、教程、Stack Overflow）
repo_path = "./your-repo-path"
file_path = "path/to/your/file.txt"
directory = "./src"
```

这些模式已经深深嵌入到模型的权重中，形成了强烈的"先验知识"。

### 2. Prompt权重问题

当前的防护措施权重不够：

| 位置 | 权重 | 当前状态 |
|------|------|----------|
| System Prompt | ⭐⭐⭐⭐⭐ | ❌ 未添加规则 |
| User Prompt开头 | ⭐⭐⭐⭐ | ✅ 已添加规则 |
| Few-shot示例 | ⭐⭐⭐⭐ | ❌ 未添加 |
| Function描述 | ⭐⭐ | ✅ 已添加警告 |

**问题**：System Prompt权重最高，但我们没有在那里添加规则！

### 3. Function Calling的特殊性

Function Calling有自己的处理流程：
1. LLM生成Function Call（JSON格式）
2. 系统解析JSON，提取参数
3. 执行工具

在步骤1中，LLM可能会"自动补全"参数，使用训练数据中的常见模式。

## 解决方案

### 方案1：在System Prompt中添加规则（推荐）⭐⭐⭐⭐⭐

**优点**：
- 权重最高，LLM最重视
- 对所有工具调用生效
- 不会被长文本稀释

**实施**：
在`backend/daoyoucode/agents/core/agent.py`的`_build_system_prompt()`中添加：

```python
def _build_system_prompt(self) -> str:
    """构建系统提示"""
    base_prompt = self.config.get('system_prompt', '')
    
    # 🆕 添加工具使用规则（最高优先级）
    tool_rules = """
⚠️ 工具使用规则（必须遵守）：

1. 路径参数使用 '.' 表示当前工作目录
   - ✅ 正确：repo_map(repo_path=".")
   - ❌ 错误：repo_map(repo_path="./your-repo-path")

2. 文件路径使用相对路径
   - ✅ 正确：read_file(file_path="backend/config.py")
   - ❌ 错误：read_file(file_path="path/to/your/file.txt")

3. 搜索目录使用 '.' 或省略
   - ✅ 正确：text_search(query="example", directory=".")
   - ❌ 错误：text_search(query="example", directory="./src")

记住：当前工作目录就是项目根目录，不需要猜测路径！
"""
    
    return tool_rules + "\n\n" + base_prompt
```

### 方案2：添加Few-shot示例 ⭐⭐⭐⭐

**优点**：
- 直接展示正确用法
- LLM善于模仿示例
- 可以覆盖训练数据的影响

**实施**：
在Prompt中添加示例对话：

```markdown
## 工具使用示例

### 示例1：探索项目结构

用户："帮我看看这个项目的结构"

助手思考：我需要先了解项目结构
```json
{
  "tool": "repo_map",
  "arguments": {
    "repo_path": "."
  }
}
```

### 示例2：搜索代码

用户："搜索所有的login函数"

助手思考：我需要搜索代码
```json
{
  "tool": "text_search",
  "arguments": {
    "query": "def login",
    "directory": ".",
    "file_pattern": "*.py"
  }
}
```

### 示例3：读取文件

用户："读取配置文件"

助手思考：我需要先找到配置文件
```json
{
  "tool": "text_search",
  "arguments": {
    "query": "config",
    "file_pattern": "*.yaml"
  }
}
```

然后读取找到的文件：
```json
{
  "tool": "read_file",
  "arguments": {
    "file_path": "backend/config/llm_config.yaml"
  }
}
```
```

### 方案3：工具层面的路径验证和自动修正 ⭐⭐⭐

**优点**：
- 最后一道防线
- 自动修正常见错误
- 不依赖LLM

**实施**：
在`BaseTool.resolve_path()`中添加：

```python
def resolve_path(self, path: str) -> Path:
    """
    解析路径（支持自动修正常见错误）
    
    自动修正：
    - "./your-repo-path" → "."
    - "path/to/your/file.txt" → 抛出错误（无法自动修正）
    - "./src" → "src"（去掉./前缀）
    """
    # 检测占位符路径
    placeholder_patterns = [
        'your-repo-path',
        'your-project',
        'path/to/your',
        'path/to/file',
        'example/path'
    ]
    
    for pattern in placeholder_patterns:
        if pattern in path.lower():
            logger.warning(
                f"⚠️  检测到占位符路径: {path}\n"
                f"   自动修正为: .\n"
                f"   提示：请使用 '.' 表示当前工作目录"
            )
            return self.context.working_directory
    
    # 去掉 ./ 前缀（如果路径不存在）
    if path.startswith('./'):
        clean_path = path[2:]
        full_path = self.context.working_directory / clean_path
        if not full_path.exists():
            logger.warning(
                f"⚠️  路径不存在: {path}\n"
                f"   尝试去掉 ./ 前缀: {clean_path}"
            )
            path = clean_path
    
    # 原有逻辑
    if path == '.':
        return self.context.working_directory
    
    # ...
```

### 方案4：在LLM响应后添加验证 ⭐⭐

**优点**：
- 可以拦截错误的工具调用
- 给LLM第二次机会

**实施**：
在`Agent._call_llm_with_functions()`中添加：

```python
async def _call_llm_with_functions(self, ...):
    response = await client.chat(request)
    
    # 🆕 验证工具调用
    if response.function_call:
        validated = self._validate_function_call(response.function_call)
        if not validated['valid']:
            # 重新调用LLM，提供错误提示
            error_msg = validated['error']
            messages.append({
                'role': 'assistant',
                'content': None,
                'function_call': response.function_call
            })
            messages.append({
                'role': 'user',
                'content': f"⚠️ 工具调用错误: {error_msg}\n请修正参数后重试。"
            })
            response = await client.chat(request)
    
    return response

def _validate_function_call(self, function_call):
    """验证工具调用"""
    args = json.loads(function_call['arguments'])
    
    # 检查路径参数
    for key in ['repo_path', 'directory', 'file_path', 'path']:
        if key in args:
            value = args[key]
            if self._is_placeholder(value):
                return {
                    'valid': False,
                    'error': f"参数 {key}='{value}' 是占位符路径，请使用实际路径"
                }
    
    return {'valid': True}

def _is_placeholder(self, path: str) -> bool:
    """检测是否是占位符路径"""
    placeholders = [
        'your-repo-path',
        'your-project',
        'path/to/your',
        'path/to/file',
        'example/path'
    ]
    return any(p in path.lower() for p in placeholders)
```

## 推荐实施顺序

1. **立即实施**：方案1（System Prompt）+ 方案3（路径验证）
   - 方案1：最高权重，治本
   - 方案3：最后防线，治标

2. **后续优化**：方案2（Few-shot示例）
   - 需要更多测试和调优
   - 可以根据实际效果调整

3. **可选**：方案4（LLM验证）
   - 增加了复杂度
   - 可能导致额外的LLM调用
   - 只在前3个方案效果不佳时考虑

## 测试计划

### 测试用例

1. **基础测试**：
   ```bash
   python daoyoucode.py chat --skill sisyphus-orchestrator
   > 你好，帮我看看项目结构
   ```
   期望：`repo_map(repo_path=".")`

2. **搜索测试**：
   ```bash
   > 搜索所有的Agent定义
   ```
   期望：`text_search(query="class.*Agent", directory=".")`

3. **文件读取测试**：
   ```bash
   > 读取LLM配置文件
   ```
   期望：`read_file(file_path="backend/config/llm_config.yaml")`

### 成功标准

- ✅ 所有工具调用都使用正确的路径格式
- ✅ 没有占位符路径（如`./your-repo-path`）
- ✅ 没有错误的相对路径（如`./src`应该是`src`）

## 附录：为什么`./src`是错误的？

用户的项目结构：
```
D:\daoyouspace\daoyoucode\
├── backend/          # 当前工作目录
│   ├── daoyoucode/
│   ├── config/
│   └── ...
├── frontend/
├── docs/
└── ...
```

当LLM使用`directory="./src"`时：
- 实际路径：`D:\daoyouspace\daoyoucode\backend\src`
- 但这个目录不存在！

正确的做法：
- 如果要搜索backend目录：`directory="."`
- 如果要搜索daoyoucode目录：`directory="daoyoucode"`
- 如果要搜索整个项目：需要先用`get_repo_structure`了解结构

## 总结

占位符问题的根源是LLM训练数据的影响，需要通过多层防护来解决：
1. System Prompt（最高权重）
2. Few-shot示例（模仿学习）
3. 工具层验证（最后防线）

建议立即实施方案1+3，这样可以快速解决问题。
