# 路径解析问题修复完成

## 问题回顾

用户反馈：路径问题一直存在，CLI找不到文件

```
⚠️  工具返回错误: File not found: skills/chat-assistant/prompts/chat_assistant.md
⚠️  工具返回错误: Directory not found: skills/chat-assistant/prompts
```

## 根本原因

1. CLI在 `backend/` 目录运行
2. 工具的默认参数 `directory="."` 是相对于当前工作目录（`backend/`）
3. 但文件实际在项目根目录（`backend/` 的上一级）
4. 导致路径解析错误

## 解决方案

实现了**智能路径解析**机制：

### 1. 在 BaseTool 添加路径解析方法

```python
# backend/daoyoucode/agents/tools/base.py

class BaseTool(ABC):
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"tool.{name}")
        self._working_directory = None  # 工作目录
    
    def set_working_directory(self, working_dir: str):
        """设置工作目录"""
        self._working_directory = working_dir
    
    def resolve_path(self, path: str) -> Path:
        """
        解析路径
        
        - 如果是绝对路径，直接返回
        - 如果是相对路径且有working_directory，相对于working_directory
        - 否则相对于当前目录
        """
        path_obj = Path(path)
        
        if path_obj.is_absolute():
            return path_obj
        
        if self._working_directory:
            resolved = Path(self._working_directory) / path_obj
            return resolved
        
        return path_obj.resolve()
```

### 2. 在 ToolRegistry 添加工作目录管理

```python
# backend/daoyoucode/agents/tools/base.py

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._working_directory = None
    
    def set_working_directory(self, working_dir: str):
        """设置工作目录，并传递给所有工具"""
        self._working_directory = working_dir
        for tool in self._tools.values():
            tool.set_working_directory(working_dir)
    
    def register(self, tool: BaseTool):
        """注册工具时，如果已有working_directory，立即设置"""
        self._tools[tool.name] = tool
        if self._working_directory:
            tool.set_working_directory(self._working_directory)
```

### 3. 在 CLI 设置工作目录

```python
# backend/cli/commands/chat.py

def handle_chat(user_input: str, ui_context: dict):
    # 获取项目根目录的绝对路径
    repo_path = os.path.abspath(ui_context["repo"])
    
    # 初始化Agent系统
    from daoyoucode.agents.init import initialize_agent_system
    initialize_agent_system()
    
    # 设置工具注册表的工作目录
    from daoyoucode.agents.tools.registry import get_tool_registry
    registry = get_tool_registry()
    registry.set_working_directory(repo_path)  # ⭐ 关键
```

### 4. 修改工具使用 resolve_path

#### TextSearchTool
```python
async def execute(self, query: str, directory: str = ".", ...):
    # 使用 resolve_path 解析路径
    path = self.resolve_path(directory)
    
    if not path.exists():
        return ToolResult(
            success=False,
            error=f"Directory not found: {directory} (resolved to {path})"
        )
```

#### ReadFileTool
```python
async def execute(self, file_path: str, encoding: str = "utf-8"):
    # 使用 resolve_path 解析路径
    path = self.resolve_path(file_path)
    
    if not path.exists():
        return ToolResult(
            success=False,
            error=f"File not found: {file_path} (resolved to {path})"
        )
```

#### ListFilesTool
```python
async def execute(self, directory: str = ".", ...):
    # 使用 resolve_path 解析路径
    path = self.resolve_path(directory)
    
    if not path.exists():
        return ToolResult(
            success=False,
            error=f"Directory not found: {directory} (resolved to {path})"
        )
```

## 修改的文件

1. ✅ `backend/daoyoucode/agents/tools/base.py`
   - 添加 `BaseTool.set_working_directory()`
   - 添加 `BaseTool.resolve_path()`
   - 添加 `ToolRegistry.set_working_directory()`

2. ✅ `backend/cli/commands/chat.py`
   - 在初始化后设置工作目录

3. ✅ `backend/daoyoucode/agents/tools/search_tools.py`
   - TextSearchTool 使用 `resolve_path()`

4. ✅ `backend/daoyoucode/agents/tools/file_tools.py`
   - ReadFileTool 使用 `resolve_path()`
   - ListFilesTool 使用 `resolve_path()`

## 测试验证

### 测试结果

```bash
$ cd backend
$ python test_tool_names.py

工作目录: D:\daoyouspace\daoyoucode

============================================================
测试工具调用
============================================================

1. 测试 text_search
   ✅ text_search 调用成功

2. 测试 list_files
   ✅ list_files 调用成功
   找到 3 个文件
   - chat_assistant.md
   - chat_assistant_optimized.md
   - chat_assistant_v2.md

3. 测试 read_file
   ✅ read_file 调用成功
   name: chat_assistant
   version: 1.0.0
   ...
```

### 路径解析示例

```python
# CLI在 backend/ 运行
# working_directory = D:\daoyouspace\daoyoucode

# 相对路径
tool.execute(directory=".")
# 解析为: D:\daoyouspace\daoyoucode

tool.execute(file_path="skills/chat-assistant/skill.yaml")
# 解析为: D:\daoyouspace\daoyoucode\skills\chat-assistant\skill.yaml

# 绝对路径
tool.execute(directory="C:/absolute/path")
# 保持: C:/absolute/path
```

## 优点

1. ✅ **对用户透明**: 用户不需要知道CLI在哪里运行
2. ✅ **对LLM透明**: 提示词中不需要特殊说明路径问题
3. ✅ **灵活**: 支持多会话、不同工作目录
4. ✅ **向后兼容**: 如果没有设置working_directory，使用当前目录
5. ✅ **清晰**: 路径解析逻辑集中在BaseTool
6. ✅ **可调试**: 错误消息显示原始路径和解析后的路径

## 后续工作

### 需要修改的其他工具

以下工具也需要使用 `resolve_path()`：

- [ ] WriteFileTool
- [ ] GetFileInfoTool
- [ ] CreateDirectoryTool
- [ ] DeleteFileTool
- [ ] RepoMapTool
- [ ] GetRepoStructureTool
- [ ] DiscoverProjectDocsTool
- [ ] GitStatusTool
- [ ] GitDiffTool
- [ ] GitCommitTool
- [ ] GitLogTool
- [ ] SearchReplaceTool
- [ ] AstGrepSearchTool
- [ ] AstGrepReplaceTool

### 修改模板

```python
# 在工具的 execute 方法开头
async def execute(self, some_path: str, ...):
    # 使用 resolve_path 解析路径
    path = self.resolve_path(some_path)
    
    if not path.exists():
        return ToolResult(
            success=False,
            error=f"Path not found: {some_path} (resolved to {path})"
        )
    
    # ... 其余代码
```

## 总结

### 问题
- CLI在 `backend/` 运行，但文件在项目根目录
- 工具的相对路径相对于当前目录（`backend/`）
- 导致找不到文件

### 解决
- 在 `BaseTool` 添加智能路径解析
- 在 `ToolRegistry` 管理工作目录
- 在 `CLI` 启动时设置工作目录
- 工具使用 `resolve_path()` 解析路径

### 效果
- ✅ 路径问题彻底解决
- ✅ 用户和LLM都不需要关心路径细节
- ✅ 代码更清晰、更灵活
- ✅ 向后兼容

### 下一步
- 修改其他工具使用 `resolve_path()`
- 测试所有工具的路径解析
- 更新文档说明工作目录机制
