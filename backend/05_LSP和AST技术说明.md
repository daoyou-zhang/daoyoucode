# LSP和AST技术说明

## LSP（Language Server Protocol）

### 什么是LSP？

**LSP是一个协议**，定义了编辑器/IDE和语言服务器之间的通信标准。

```
┌─────────────┐         LSP协议          ┌──────────────────┐
│   编辑器    │ ◄──────────────────────► │  语言服务器       │
│  (客户端)   │   JSON-RPC over stdio   │  (本地进程)       │
└─────────────┘                          └──────────────────┘
     │                                            │
     │                                            │
     ▼                                            ▼
  显示结果                                   分析代码
  (错误、补全等)                            (类型检查、跳转等)
```

### LSP是服务吗？

**是的，LSP服务器是本地服务**：

1. **本地进程**
   - 语言服务器运行在本地机器上
   - 通过stdin/stdout或socket通信
   - 不需要网络连接

2. **常见的LSP服务器**
   ```bash
   # Python
   pyright-langserver --stdio
   
   # TypeScript/JavaScript
   typescript-language-server --stdio
   
   # Rust
   rust-analyzer
   
   # Go
   gopls
   ```

3. **生命周期**
   ```
   启动 → 初始化 → 工作 → 关闭
     ↓       ↓        ↓       ↓
   spawn  initialize  请求   shutdown
   ```

### daoyoucode中的LSP实现

```python
# backend/daoyoucode/agents/tools/lsp_tools.py

class LSPServerManager:
    """LSP服务器管理器（本地）"""
    
    def __init__(self):
        self.servers = {}  # 运行中的服务器进程
    
    async def start_server(self, config: LSPServerConfig):
        """启动本地LSP服务器进程"""
        # 1. 检查是否已安装
        if not self._is_installed(config):
            await self._install_server(config)
        
        # 2. 启动进程
        process = await asyncio.create_subprocess_exec(
            config.command,
            *config.args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # 3. 初始化LSP连接
        client = LSPClient(process)
        await client.initialize(workspace_path)
        
        return client
```

**关键点**：
- ✅ 本地进程（不是远程服务）
- ✅ 通过stdin/stdout通信
- ✅ 自动安装和管理
- ✅ 支持多种语言

## AST（Abstract Syntax Tree）

### 什么是AST？

**AST是一种数据结构**，表示代码的语法结构。

```python
# 源代码
def hello(name):
    print(f"Hello, {name}!")

# AST表示
FunctionDef(
    name='hello',
    args=arguments(
        args=[arg(arg='name')]
    ),
    body=[
        Expr(
            value=Call(
                func=Name(id='print'),
                args=[
                    JoinedStr(
                        values=[
                            Constant(value='Hello, '),
                            FormattedValue(value=Name(id='name')),
                            Constant(value='!')
                        ]
                    )
                ]
            )
        )
    ]
)
```

### AST是工具吗？

**AST是数据结构，但我们使用AST工具来操作它**：

1. **解析器（Parser）**
   - 将源代码转换为AST
   - 例如：tree-sitter、ast-grep

2. **查询工具**
   - 在AST上进行模式匹配
   - 例如：ast-grep search

3. **转换工具**
   - 修改AST并生成新代码
   - 例如：ast-grep replace

### daoyoucode中的AST实现

#### 1. Tree-sitter（解析器）

```python
# backend/daoyoucode/agents/tools/repomap_tools.py

from tree_sitter import Parser, Language

class RepoMapTool:
    def parse_file(self, file_path: Path):
        """使用tree-sitter解析文件"""
        # 1. 创建解析器
        parser = Parser()
        parser.set_language(Language('python'))
        
        # 2. 解析代码
        tree = parser.parse(content.encode())
        
        # 3. 遍历AST节点
        for node in tree.root_node.children:
            if node.type == 'function_definition':
                # 提取函数信息
                name = self._get_node_name(node)
                start_line = node.start_point[0]
                end_line = node.end_point[0]
```

**特点**：
- ✅ 本地库（不是服务）
- ✅ 支持25+种语言
- ✅ 增量解析（快速）
- ✅ 错误容忍（部分代码也能解析）

#### 2. ast-grep（查询和替换工具）

```python
# backend/daoyoucode/agents/tools/ast_tools.py

class AstGrepSearchTool:
    async def execute(self, pattern: str, language: str = "python"):
        """使用ast-grep搜索代码模式"""
        # 1. 调用ast-grep命令行工具
        cmd = [
            binary_path,
            'search',
            '--pattern', pattern,
            '--language', language,
            '--json'
        ]
        
        # 2. 执行并解析结果
        result = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
```

**特点**：
- ✅ 命令行工具（本地）
- ✅ 结构化模式匹配
- ✅ 精确替换
- ✅ 支持25+种语言

## LSP vs AST 对比

| 特性 | LSP | AST |
|------|-----|-----|
| **本质** | 协议 + 服务器进程 | 数据结构 + 解析工具 |
| **运行方式** | 本地服务进程 | 本地库/命令行工具 |
| **通信方式** | JSON-RPC (stdin/stdout) | 函数调用/命令行 |
| **生命周期** | 长期运行（守护进程） | 按需调用（短暂） |
| **状态** | 有状态（维护工作区） | 无状态（每次重新解析） |
| **能力** | 类型检查、补全、跳转、重命名 | 结构分析、模式匹配、代码转换 |
| **依赖** | 需要安装语言服务器 | 需要安装解析器库 |
| **性能** | 首次启动慢，后续快 | 每次解析，但增量快 |

## 在daoyoucode中的使用

### LSP使用场景

```python
# 1. 获取诊断信息（错误、警告）
diagnostics = await lsp_diagnostics("file.py")

# 2. 跳转到定义
definition = await lsp_goto_definition("file.py", line=10, character=5)

# 3. 查找所有引用
references = await lsp_find_references("file.py", line=10, character=5)

# 4. 获取符号列表
symbols = await lsp_symbols("file.py")

# 5. 重命名符号
await lsp_rename("file.py", line=10, character=5, new_name="new_name")
```

**优势**：
- 理解代码语义（类型、引用）
- 跨文件分析
- 实时反馈

### AST使用场景

```python
# 1. 结构化搜索
matches = await ast_grep_search(
    pattern="def $FUNC($ARGS): $BODY",
    language="python"
)

# 2. 精确替换
await ast_grep_replace(
    pattern="print($MSG)",
    replacement="logger.info($MSG)",
    language="python"
)

# 3. 提取代码结构（tree-sitter）
tree = parser.parse(content)
functions = [node for node in tree.root_node.children 
             if node.type == 'function_definition']
```

**优势**：
- 结构化匹配（不会误匹配字符串中的代码）
- 精确边界（知道每个节点的确切位置）
- 快速解析（增量更新）

## 深度融合的价值

### 为什么要融合？

**LSP的优势**：
- 理解语义（类型、引用关系）
- 跨文件分析
- 实时验证

**AST的优势**：
- 精确的结构信息
- 快速的模式匹配
- 完整的代码边界

**融合后**：
```python
# 示例：智能代码搜索
async def smart_search(query: str):
    # 1. 使用向量检索找到候选
    candidates = await semantic_search(query)
    
    # 2. 使用AST提取精确结构
    for candidate in candidates:
        tree = parse_with_treesitter(candidate['file'])
        candidate['structure'] = extract_structure(tree)
    
    # 3. 使用LSP获取类型信息
    for candidate in candidates:
        symbols = await lsp_symbols(candidate['file'])
        candidate['types'] = extract_types(symbols)
    
    # 4. 综合排序
    return rerank(candidates, query)
```

**效果**：
- 更准确的搜索（结合语义和结构）
- 更丰富的信息（类型、引用、结构）
- 更好的用户体验

## 总结

### LSP
- ✅ 本地服务进程
- ✅ 长期运行
- ✅ 理解语义
- ✅ 跨文件分析

### AST
- ✅ 本地库/工具
- ✅ 按需调用
- ✅ 精确结构
- ✅ 快速解析

### 融合
- ✅ 发挥各自优势
- ✅ 互补不足
- ✅ 1+1>2的效果

现在可以开始深度优化了！
