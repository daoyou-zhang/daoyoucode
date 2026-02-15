# 路径解析问题与解决方案

## 问题分析

### 当前问题
1. CLI在 `backend/` 目录运行
2. 工具的默认参数 `directory="."` 或 `repo_path="."` 是相对于当前工作目录
3. 当前工作目录是 `backend/`，但文件在项目根目录
4. 导致工具找不到文件：`skills/chat-assistant/prompts/chat_assistant.md`

### 问题根源
```python
# CLI运行在 backend/
$ cd backend
$ python -m cli chat

# 工具执行时
text_search(directory=".")  # "." = backend/
read_file(file_path="skills/...")  # 相对于 backend/，找不到

# 实际文件位置
项目根目录/skills/chat-assistant/prompts/chat_assistant.md
```

---

## 解决方案对比

### 方案1: 修改CLI启动目录 ❌

```bash
# 在项目根目录运行
$ python -m backend.cli chat
```

**优点**:
- 简单直接
- 不需要修改代码

**缺点**:
- 改变了用户习惯
- 需要修改文档
- 可能影响其他依赖当前目录的代码

---

### 方案2: 工具自动解析相对路径 ⭐ 推荐

让工具智能地解析路径：
1. 如果是绝对路径，直接使用
2. 如果是相对路径，相对于 `working_directory`（从context获取）
3. 如果没有 `working_directory`，使用当前目录

**实现步骤**:

#### 2.1 修改 BaseTool 添加路径解析方法

```python
# backend/daoyoucode/agents/tools/base.py

class BaseTool(ABC):
    """工具基类"""
    
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
        
        Args:
            path: 相对或绝对路径
        
        Returns:
            解析后的绝对路径
        """
        path_obj = Path(path)
        
        # 如果是绝对路径，直接返回
        if path_obj.is_absolute():
            return path_obj
        
        # 如果有工作目录，相对于工作目录
        if self._working_directory:
            return Path(self._working_directory) / path_obj
        
        # 否则相对于当前目录
        return path_obj.resolve()
```

#### 2.2 修改 ToolRegistry 传递 working_directory

```python
# backend/daoyoucode/agents/tools/base.py

class ToolRegistry:
    """工具注册表"""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._working_directory = None
    
    def set_working_directory(self, working_dir: str):
        """设置工作目录"""
        self._working_directory = working_dir
        # 传递给所有工具
        for tool in self._tools.values():
            tool.set_working_directory(working_dir)
    
    async def execute_tool(self, name: str, **kwargs) -> ToolResult:
        """执行工具"""
        tool = self.get_tool(name)
        if not tool:
            return ToolResult(
                success=False,
                content=None,
                error=f"Tool not found: {name}"
            )
        
        # 如果有working_directory，设置给工具
        if self._working_directory:
            tool.set_working_directory(self._working_directory)
        
        try:
            return await tool.execute(**kwargs)
        except Exception as e:
            logger.error(f"工具 {name} 执行失败: {e}", exc_info=True)
            return ToolResult(
                success=False,
                content=None,
                error=str(e)
            )
```

#### 2.3 修改 Agent 传递 working_directory

```python
# backend/daoyoucode/agents/core/agent.py

class BaseAgent:
    def __init__(self, config: AgentConfig):
        self.config = config
        # ...
        
        # 设置工具注册表的工作目录
        if hasattr(config, 'working_directory'):
            from ..tools.registry import get_tool_registry
            registry = get_tool_registry()
            registry.set_working_directory(config.working_directory)
```

#### 2.4 修改工具使用 resolve_path

```python
# backend/daoyoucode/agents/tools/search_tools.py

class TextSearchTool(BaseTool):
    async def execute(
        self,
        query: str,
        directory: str = ".",
        file_pattern: Optional[str] = None,
        case_sensitive: bool = False,
        max_results: int = 100
    ) -> ToolResult:
        """搜索文本"""
        try:
            # 使用 resolve_path 解析路径
            path = self.resolve_path(directory)
            
            if not path.exists():
                return ToolResult(
                    success=False,
                    content=None,
                    error=f"Directory not found: {directory} (resolved to {path})"
                )
            
            # ... 其余代码
```

```python
# backend/daoyoucode/agents/tools/file_tools.py

class ReadFileTool(BaseTool):
    async def execute(
        self,
        file_path: str,
        encoding: str = "utf-8",
        start_line: Optional[int] = None,
        end_line: Optional[int] = None
    ) -> ToolResult:
        """读取文件"""
        try:
            # 使用 resolve_path 解析路径
            path = self.resolve_path(file_path)
            
            if not path.exists():
                return ToolResult(
                    success=False,
                    content=None,
                    error=f"File not found: {file_path} (resolved to {path})"
                )
            
            # ... 其余代码
```

#### 2.5 修改 CLI 传递 working_directory

```python
# backend/cli/commands/chat.py

def handle_chat(user_input: str, ui_context: dict):
    """处理对话 - 通过Skill系统"""
    from cli.ui.console import console
    import asyncio
    import os
    
    # 准备基本上下文（传递给Skill系统）
    # 将 repo 路径转换为绝对路径
    repo_path = os.path.abspath(ui_context["repo"])
    
    # 设置工具注册表的工作目录
    from daoyoucode.agents.tools.registry import get_tool_registry
    registry = get_tool_registry()
    registry.set_working_directory(repo_path)
    
    context = {
        "session_id": ui_context["session_id"],
        "repo": repo_path,
        "model": ui_context["model"],
        "initial_files": ui_context.get("initial_files", []),
        "working_directory": repo_path,
        "repo_root": repo_path,
    }
    
    # ... 其余代码
```

---

### 方案3: 使用环境变量 ❌

```python
import os
os.environ['DAOYOUCODE_WORKING_DIR'] = '/path/to/project'
```

**缺点**:
- 不够灵活
- 多会话时可能冲突
- 不够优雅

---

## 推荐实现：方案2

### 优点
1. ✅ 对用户透明（不需要改变使用方式）
2. ✅ 灵活（支持多会话、不同工作目录）
3. ✅ 向后兼容（如果没有设置working_directory，使用当前目录）
4. ✅ 清晰（路径解析逻辑集中在BaseTool）

### 实现清单

- [ ] 修改 `BaseTool` 添加 `resolve_path` 方法
- [ ] 修改 `ToolRegistry` 添加 `set_working_directory` 方法
- [ ] 修改 `Agent` 在初始化时设置工作目录
- [ ] 修改 `CLI` 在启动时设置工作目录
- [ ] 修改所有工具使用 `resolve_path`：
  - [ ] TextSearchTool
  - [ ] ReadFileTool
  - [ ] WriteFileTool
  - [ ] ListFilesTool
  - [ ] RepoMapTool
  - [ ] GetRepoStructureTool
  - [ ] DiscoverProjectDocsTool
  - [ ] GitStatusTool
  - [ ] GitDiffTool
  - [ ] 其他文件相关工具

---

## 测试验证

### 测试用例1: 相对路径
```python
# CLI在 backend/ 运行
# working_directory = /path/to/project

tool.execute(directory=".")
# 应该解析为: /path/to/project

tool.execute(file_path="skills/chat-assistant/skill.yaml")
# 应该解析为: /path/to/project/skills/chat-assistant/skill.yaml
```

### 测试用例2: 绝对路径
```python
tool.execute(directory="/absolute/path")
# 应该保持: /absolute/path
```

### 测试用例3: 没有working_directory
```python
# 如果没有设置working_directory
tool.execute(directory=".")
# 应该使用当前目录
```

---

## 替代方案：快速修复

如果不想大改代码，可以快速修复：

### 快速修复1: 修改CLI启动脚本

```python
# backend/cli/__main__.py

import os
import sys

# 切换到项目根目录
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(project_root)

# 然后运行CLI
from cli.main import app
app()
```

### 快速修复2: 修改提示词

```markdown
## 重要提示

当前CLI在 backend/ 目录运行，但项目根目录在上一级。

调用工具时，请使用相对于项目根目录的路径：
- ❌ 错误: `directory="."`
- ✅ 正确: `directory=".."`

或使用绝对路径：
- ✅ 正确: `directory="/absolute/path/to/project"`
```

**缺点**: 这会让提示词变得复杂，且容易出错

---

## 总结

**推荐使用方案2**：在工具层面自动解析路径

这是最优雅、最灵活的解决方案，对用户和LLM都是透明的。

实现后，无论CLI在哪里运行，工具都能正确找到文件。
