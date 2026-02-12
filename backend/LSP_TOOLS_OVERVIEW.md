# LSP工具概述

## 为什么需要LSP工具？

### 问题场景

假设用户问Agent："帮我重命名`calculate_total`函数为`compute_sum`"

**没有LSP工具时**:
```python
# Agent只能用文本搜索
1. text_search("calculate_total")  # 找到所有出现的地方
2. 手动替换每个文件  # 可能漏掉一些引用
3. 可能破坏代码（字符串中的"calculate_total"也被替换了）
```

**有LSP工具时**:
```python
# Agent使用LSP工具
1. lsp_rename("calculate_total", "compute_sum")  # 一键完成
2. LSP自动找到所有引用（包括跨文件）
3. 安全重命名（不会误改字符串）
```

---

## LSP工具的6大功能

### 1. lsp_diagnostics - 诊断错误

**场景**: 用户说"帮我修复代码中的错误"

```python
# Agent调用
diagnostics = await lsp_diagnostics("src/main.py")

# 返回
[
    {
        "file": "src/main.py",
        "line": 10,
        "column": 5,
        "severity": "error",
        "message": "Undefined variable 'x'",
        "code": "undefined-variable"
    },
    {
        "file": "src/main.py",
        "line": 15,
        "column": 10,
        "severity": "warning",
        "message": "Unused import 'os'",
        "code": "unused-import"
    }
]

# Agent可以：
# 1. 看到第10行有未定义变量
# 2. 看到第15行有未使用的导入
# 3. 自动修复这些问题
```

### 2. lsp_goto_definition - 跳转定义

**场景**: 用户说"这个函数在哪里定义的？"

```python
# Agent调用
definition = await lsp_goto_definition("src/main.py", line=20, column=10)

# 返回
{
    "file": "src/utils.py",
    "line": 45,
    "column": 0,
    "name": "helper_function"
}

# Agent可以：
# 1. 找到函数定义的位置
# 2. 读取定义的代码
# 3. 理解函数的实现
```

### 3. lsp_find_references - 查找引用

**场景**: 用户说"这个函数在哪里被调用了？"

```python
# Agent调用
references = await lsp_find_references("src/utils.py", line=45, column=0)

# 返回
[
    {"file": "src/main.py", "line": 20, "column": 10},
    {"file": "src/api.py", "line": 35, "column": 5},
    {"file": "tests/test_utils.py", "line": 10, "column": 8}
]

# Agent可以：
# 1. 看到函数在3个地方被使用
# 2. 评估修改的影响范围
# 3. 决定是否需要更新调用方
```

### 4. lsp_rename - 重命名符号

**场景**: 用户说"把这个变量重命名为更清晰的名字"

```python
# Agent调用
result = await lsp_rename("src/main.py", line=10, column=5, new_name="user_count")

# LSP自动：
# 1. 找到所有引用（跨文件）
# 2. 安全重命名（不会误改字符串）
# 3. 更新所有文件

# 返回
{
    "success": True,
    "files_changed": ["src/main.py", "src/api.py", "tests/test_main.py"],
    "changes_count": 15
}
```

### 5. lsp_symbols - 符号搜索

**场景**: 用户说"找到所有的API路由定义"

```python
# Agent调用
symbols = await lsp_symbols(query="route", kind="function")

# 返回
[
    {
        "name": "get_user_route",
        "kind": "function",
        "file": "src/routes/user.py",
        "line": 10
    },
    {
        "name": "create_user_route",
        "kind": "function",
        "file": "src/routes/user.py",
        "line": 25
    }
]

# Agent可以：
# 1. 快速找到所有路由函数
# 2. 分析API结构
# 3. 生成API文档
```

### 6. lsp_code_actions - 代码操作

**场景**: 用户说"优化这段代码"

```python
# Agent调用
actions = await lsp_code_actions("src/main.py", line=10, column=5)

# 返回
[
    {
        "title": "Add missing import",
        "kind": "quickfix",
        "edit": {
            "file": "src/main.py",
            "changes": [
                {"line": 1, "text": "import os\n"}
            ]
        }
    },
    {
        "title": "Extract to function",
        "kind": "refactor",
        "edit": {...}
    }
]

# Agent可以：
# 1. 看到可用的快速修复
# 2. 自动应用修复
# 3. 重构代码
```

---

## 实际使用场景

### 场景1: 修复代码错误

```
用户: "帮我修复main.py中的所有错误"

Agent执行流程:
1. lsp_diagnostics("main.py")  # 获取所有错误
2. 对每个错误:
   - lsp_code_actions(file, line, column)  # 获取修复建议
   - 应用修复
3. 验证修复结果
```

### 场景2: 重构代码

```
用户: "把calculate_price函数重命名为compute_total_price"

Agent执行流程:
1. lsp_goto_definition("calculate_price")  # 找到定义
2. lsp_find_references(...)  # 查看影响范围
3. lsp_rename(..., "compute_total_price")  # 安全重命名
4. 验证重命名结果
```

### 场景3: 代码分析

```
用户: "分析这个项目的API结构"

Agent执行流程:
1. lsp_symbols(query="route", kind="function")  # 找到所有路由
2. 对每个路由:
   - lsp_goto_definition(...)  # 查看实现
   - 分析参数和返回值
3. 生成API文档
```

### 场景4: 依赖分析

```
用户: "这个函数被哪些地方使用了？"

Agent执行流程:
1. lsp_goto_definition("function_name")  # 找到定义
2. lsp_find_references(...)  # 找到所有引用
3. 分析调用关系
4. 生成依赖图
```

---

## LSP vs 传统工具对比

| 功能 | 传统工具 | LSP工具 | 优势 |
|------|---------|---------|------|
| 查找定义 | 文本搜索 | lsp_goto_definition | 精确、跨文件 |
| 查找引用 | grep/ripgrep | lsp_find_references | 语义级别、不会误报 |
| 重命名 | 批量替换 | lsp_rename | 安全、不会误改 |
| 错误检查 | 运行代码 | lsp_diagnostics | 实时、不需要运行 |
| 代码补全 | 无 | lsp_completion | 智能建议 |
| 快速修复 | 手动 | lsp_code_actions | 自动化 |

---

## 技术实现

### LSP服务器管理

```python
class LSPServerManager:
    """管理多个语言的LSP服务器"""
    
    def __init__(self):
        self.servers = {}  # {language: LSPServer}
    
    async def start_server(self, language: str, workspace_path: str):
        """启动LSP服务器"""
        if language == "python":
            # 启动pyright或pylsp
            server = await self._start_python_server(workspace_path)
        elif language == "javascript":
            # 启动typescript-language-server
            server = await self._start_js_server(workspace_path)
        
        self.servers[language] = server
    
    async def stop_server(self, language: str):
        """停止LSP服务器"""
        if language in self.servers:
            await self.servers[language].stop()
            del self.servers[language]
```

### LSP工具实现

```python
class LSPDiagnosticsTool(BaseTool):
    """获取诊断信息"""
    
    async def execute(self, file_path: str) -> ToolResult:
        # 1. 检测语言
        language = detect_language(file_path)
        
        # 2. 获取LSP服务器
        server = lsp_manager.get_server(language)
        
        # 3. 调用LSP
        diagnostics = await server.get_diagnostics(file_path)
        
        # 4. 返回结果
        return ToolResult(
            success=True,
            content=diagnostics
        )
```

---

## 下一步实现计划

### 第1天（2025-02-13）
- [ ] 实现LSP服务器管理器
- [ ] 实现lsp_diagnostics工具
- [ ] 实现lsp_rename工具
- [ ] 实现lsp_goto_definition工具

### 第2天（2025-02-14）
- [ ] 实现lsp_find_references工具
- [ ] 实现lsp_symbols工具
- [ ] 实现lsp_code_actions工具

### 第3天（2025-02-15）
- [ ] 编写测试用例
- [ ] 更新文档
- [ ] 集成到Agent

---

## 总结

LSP工具让Agent具备了IDE级别的代码理解能力：

1. **精确性**: 语义级别的代码分析，不是简单的文本匹配
2. **安全性**: 重命名等操作不会破坏代码
3. **效率**: 实时诊断，不需要运行代码
4. **智能**: 提供快速修复建议

这些能力让Agent能够像人类开发者一样理解和操作代码。
