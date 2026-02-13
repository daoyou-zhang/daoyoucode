# 调用链路分析 - 05 工具层

## 5. 工具层：实际执行

### 入口函数
```
📁 backend/daoyoucode/agents/tools/base.py :: ToolRegistry.execute_tool()
```

### 调用流程

#### 5.1 工具注册表

**代码**:
```python
class ToolRegistry:
    """工具注册表"""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
    
    async def execute_tool(self, name: str, **kwargs) -> ToolResult:
        """执行工具"""
        # 1. 获取工具
        tool = self.get_tool(name)
        if not tool:
            return ToolResult(
                success=False,
                content=None,
                error=f"Tool not found: {name}"
            )
        
        try:
            # 2. 执行工具
            result = await tool.execute(**kwargs)
            
            # 3. 自动截断输出
            if result.success and isinstance(result.content, str):
                original_content = result.content
                truncated_content = tool.truncate_output(original_content)
                
                if len(truncated_content) < len(original_content):
                    result.content = truncated_content
                    result.metadata['truncated'] = True
                    result.metadata['original_length'] = len(original_content)
            
            return result
        except Exception as e:
            return ToolResult(
                success=False,
                content=None,
                error=str(e)
            )
```

**职责**:
- 管理所有工具
- 执行工具
- 自动截断输出

---

#### 5.2 工具基类

**代码**:
```python
class BaseTool(ABC):
    """工具基类"""
    
    # 默认输出限制
    MAX_OUTPUT_CHARS = 8000
    MAX_OUTPUT_LINES = 500
    TRUNCATION_STRATEGY = "head_tail"
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """执行工具（子类实现）"""
        pass
    
    def truncate_output(self, content: str) -> str:
        """智能截断输出"""
        # 字符限制
        if len(content) > self.MAX_OUTPUT_CHARS:
            content = self._truncate_by_chars(content, self.MAX_OUTPUT_CHARS)
        
        # 行数限制
        lines = content.splitlines()
        if len(lines) > self.MAX_OUTPUT_LINES:
            content = self._truncate_by_lines(lines, self.MAX_OUTPUT_LINES)
        
        return content
```

---

#### 5.3 具体工具示例

##### A. RepoMapTool

**文件**: `backend/daoyoucode/agents/tools/repomap_tools.py`

**代码**:
```python
class RepoMapTool(BaseTool):
    """生成代码仓库地图"""
    
    MAX_OUTPUT_CHARS = 10000
    MAX_OUTPUT_LINES = 1000
    
    async def execute(
        self,
        repo_path: str,
        chat_files: Optional[List[str]] = None,
        mentioned_idents: Optional[List[str]] = None,
        max_tokens: int = 2000
    ) -> ToolResult:
        """
        生成RepoMap
        
        流程：
        1. 初始化缓存
        2. 扫描仓库（Tree-sitter解析）
        3. 构建引用图
        4. PageRank排序
        5. 生成地图（控制token）
        """
        # 1. 初始化缓存
        self._init_cache(repo_path)
        
        # 2. 扫描仓库
        definitions = self._scan_repository(repo_path)
        
        # 3. 构建引用图
        graph = self._build_reference_graph(definitions, repo_path)
        
        # 4. PageRank排序
        ranked = self._pagerank(
            graph,
            chat_files=chat_files,
            mentioned_idents=mentioned_idents
        )
        
        # 5. 生成地图
        repo_map = self._generate_map(ranked, definitions, max_tokens)
        
        return ToolResult(
            success=True,
            content=repo_map,
            metadata={
                'repo_path': str(repo_path),
                'file_count': len(definitions)
            }
        )
```

**关键步骤**:
1. Tree-sitter解析代码
2. 提取定义和引用
3. PageRank排序
4. Token控制

##### B. ReadFileTool

**文件**: `backend/daoyoucode/agents/tools/file_tools.py`

**代码**:
```python
class ReadFileTool(BaseTool):
    """读取文件工具"""
    
    MAX_OUTPUT_CHARS = 5000
    MAX_OUTPUT_LINES = 200
    
    async def execute(self, file_path: str, encoding: str = "utf-8") -> ToolResult:
        """读取文件"""
        try:
            path = Path(file_path)
            if not path.exists():
                return ToolResult(
                    success=False,
                    content=None,
                    error=f"File not found: {file_path}"
                )
            
            with open(path, 'r', encoding=encoding) as f:
                content = f.read()
            
            return ToolResult(
                success=True,
                content=content,
                metadata={
                    'file_path': str(path),
                    'size': len(content),
                    'lines': content.count('\n') + 1
                }
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content=None,
                error=str(e)
            )
```

##### C. TextSearchTool

**文件**: `backend/daoyoucode/agents/tools/search_tools.py`

**代码**:
```python
class TextSearchTool(BaseTool):
    """文本搜索工具"""
    
    MAX_OUTPUT_LINES = 100
    MAX_OUTPUT_CHARS = 6000
    
    async def execute(
        self,
        query: str,
        directory: str = ".",
        file_pattern: Optional[str] = None,
        case_sensitive: bool = False,
        max_results: int = 100
    ) -> ToolResult:
        """搜索文本"""
        # 搜索逻辑
        results = []
        # ... 搜索实现 ...
        
        # 格式化结果
        formatted = self._format_results(results)
        
        return ToolResult(
            success=True,
            content=formatted,
            metadata={
                'query': query,
                'count': len(results)
            }
        )
```

---

#### 5.4 工具后处理

**文件**: `backend/daoyoucode/agents/tools/postprocessor.py`

**在Agent层调用**:
```python
# Agent.py中
if tool_result.success:
    user_query = self._extract_user_query(messages)
    tool_result = await self.tool_postprocessor.process(
        tool_name=tool_name,
        result=tool_result,
        user_query=user_query,
        context=context
    )
```

**后处理器代码**:
```python
class ToolPostProcessor:
    """工具后处理器"""
    
    async def process(
        self,
        tool_name: str,
        result: ToolResult,
        user_query: str,
        context: Dict
    ) -> ToolResult:
        """
        处理工具结果
        
        流程：
        1. 提取关键词
        2. 过滤无关内容
        3. 保留最相关的结果
        """
        processor = self.processors.get(tool_name)
        if not processor:
            return result
        
        return await processor.process(result, user_query, context)
```

**示例：RepoMap后处理**:
```python
class RepoMapPostProcessor:
    async def process(self, result, user_query, context):
        # 1. 提取关键词
        keywords = self.extract_keywords(user_query)
        # 例如："Agent系统是怎么实现的？" → ['agent', '系统', '实现']
        
        # 2. 解析RepoMap
        files = self._parse_repo_map(result.content)
        
        # 3. 计算相关性
        scored_files = []
        for file_header, file_content in files:
            relevance = self.calculate_relevance(
                file_header + file_content,
                keywords
            )
            scored_files.append((file_header, file_content, relevance))
        
        # 4. 过滤低相关性的文件
        relevant_files = [
            (header, content) for header, content, score in scored_files
            if score >= 0.2  # 至少匹配20%的关键词
        ]
        
        # 5. 限制数量
        relevant_files = relevant_files[:20]
        
        # 6. 重新格式化
        result.content = self._format_repo_map(relevant_files)
        result.metadata['post_processed'] = True
        result.metadata['keywords'] = keywords
        
        return result
```

---

### 工具清单

| 工具名称 | 文件 | 功能 | 输出限制 |
|---------|------|------|---------|
| repo_map | repomap_tools.py | 生成代码地图 | 10000字符 |
| get_repo_structure | repomap_tools.py | 获取目录结构 | 8000字符 |
| read_file | file_tools.py | 读取文件 | 5000字符 |
| write_file | file_tools.py | 写入文件 | - |
| text_search | search_tools.py | 文本搜索 | 6000字符 |
| regex_search | search_tools.py | 正则搜索 | 6000字符 |
| list_files | file_tools.py | 列出文件 | - |
| ... | ... | ... | ... |

---

### 依赖关系

```
ToolRegistry
    ↓
BaseTool (基类)
    ↓
├─ RepoMapTool
│   ├─ Tree-sitter (代码解析)
│   ├─ SQLite (缓存)
│   └─ PageRank (排序)
├─ ReadFileTool
│   └─ pathlib (文件操作)
├─ TextSearchTool
│   └─ re (正则表达式)
└─ ...

ToolPostProcessor (后处理)
    ↓
├─ RepoMapPostProcessor
├─ SearchPostProcessor
├─ ReadFilePostProcessor
└─ ...
```

---

### 下一步

工具层完成后，返回到 **Agent层**，或继续到 **LLM层**

→ 继续阅读 `CALL_CHAIN_06_LLM.md`
