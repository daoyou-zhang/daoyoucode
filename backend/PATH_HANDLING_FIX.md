# 路径处理问题修复方案

## 问题描述

当前路径处理存在严重问题：
```
repo_map 返回: daoyoucode/agents/core/llm_client.py
AI 使用: read_file("daoyoucode/agents/core/llm_client.py")
错误: File not found
实际路径: backend/daoyoucode/agents/core/llm_client.py
```

**根本原因**：
- CLI 在 `backend/` 目录运行，检测到后设置 repo 为上一级（项目根目录）
- 工具的 working_directory 设置为项目根目录
- repo_map 返回相对于项目根目录的路径（`backend/daoyoucode/...`）
- 但 AI 可能误解路径，使用了错误的路径

## daoyouCodePilot 的解决方案

### 核心设计：ToolContext

```python
@dataclass
class ToolContext:
    """工具上下文"""
    repo_path: Path  # 仓库根路径（绝对路径）
    
    def abs_root_path(self, path: str) -> str:
        """将相对路径转换为绝对路径"""
        return str(self.repo_path / path)
    
    def get_rel_fname(self, path: str) -> str:
        """获取相对于仓库根目录的文件路径"""
        try:
            return str(Path(path).relative_to(self.repo_path))
        except ValueError:
            return path
```

### 关键点

1. **所有工具都接收 ToolContext**
2. **ToolContext 包含 repo_path（绝对路径）**
3. **工具内部统一处理路径**
4. **返回的路径都是相对于 repo_path 的**

---

## 我们的修复方案

### 方案1: 标准化工具返回的路径（推荐）

**目标**：确保所有工具返回的路径都是相对于 working_directory 的标准路径。

#### 1.1 在 BaseTool 中添加路径标准化方法

```python
# backend/daoyoucode/agents/tools/base.py

class BaseTool:
    def __init__(self, ...):
        self._working_directory = None
    
    def set_working_directory(self, path: str):
        """设置工作目录"""
        self._working_directory = Path(path).resolve()
    
    def normalize_path(self, path: str) -> str:
        """
        标准化路径：返回相对于 working_directory 的路径
        
        Args:
            path: 可能是绝对路径或相对路径
        
        Returns:
            相对于 working_directory 的标准路径
        """
        if not self._working_directory:
            return path
        
        path_obj = Path(path)
        
        # 如果是绝对路径，转换为相对路径
        if path_obj.is_absolute():
            try:
                return str(path_obj.relative_to(self._working_directory))
            except ValueError:
                # 不在 working_directory 下，返回原路径
                return path
        
        # 如果是相对路径，直接返回
        return path
```

#### 1.2 修改 repo_map 工具

```python
# backend/daoyoucode/agents/tools/repomap_tools.py

class RepoMapTool(BaseTool):
    def _format_result(self, ...):
        # 在返回结果前，标准化所有文件路径
        for file_path, score in ranked:
            # 标准化路径
            normalized_path = self.normalize_path(file_path)
            file_line = f"\n{normalized_path}:"
            ...
```

#### 1.3 修改 list_files 工具

```python
# backend/daoyoucode/agents/tools/file_tools.py

class ListFilesTool(BaseTool):
    async def execute(self, ...):
        # 返回结果前，标准化路径
        results = []
        for file in files:
            results.append({
                'name': file.name,
                'path': self.normalize_path(str(file)),  # 标准化
                'type': 'file' if file.is_file() else 'directory',
                'size': file.stat().st_size if file.is_file() else 0
            })
```

### 方案2: 在 ToolRegistry 中统一处理（更彻底）

**目标**：在工具执行结果返回前，统一处理所有路径。

```python
# backend/daoyoucode/agents/tools/registry.py

class ToolRegistry:
    def _normalize_tool_result(self, result: ToolResult) -> ToolResult:
        """
        标准化工具返回结果中的路径
        
        处理：
        1. 字符串中的文件路径
        2. 字典中的 'path', 'file_path', 'file' 等字段
        3. 列表中的路径
        """
        if not result.success or not result.content:
            return result
        
        content = result.content
        
        # 如果是字符串，查找并替换路径
        if isinstance(content, str):
            content = self._normalize_paths_in_string(content)
        
        # 如果是字典，处理路径字段
        elif isinstance(content, dict):
            content = self._normalize_paths_in_dict(content)
        
        # 如果是列表，递归处理
        elif isinstance(content, list):
            content = [self._normalize_paths_in_dict(item) if isinstance(item, dict) else item 
                      for item in content]
        
        return ToolResult(
            success=result.success,
            content=content,
            error=result.error,
            metadata=result.metadata
        )
    
    def _normalize_paths_in_dict(self, data: dict) -> dict:
        """标准化字典中的路径字段"""
        path_keys = ['path', 'file_path', 'file', 'filepath', 'filename']
        
        result = data.copy()
        for key in path_keys:
            if key in result and isinstance(result[key], str):
                result[key] = self._normalize_path(result[key])
        
        return result
    
    def _normalize_path(self, path: str) -> str:
        """标准化单个路径"""
        if not self._working_directory:
            return path
        
        path_obj = Path(path)
        
        # 如果是绝对路径，转换为相对路径
        if path_obj.is_absolute():
            try:
                return str(path_obj.relative_to(self._working_directory))
            except ValueError:
                return path
        
        return path
    
    async def execute_tool(self, tool_name: str, **kwargs) -> ToolResult:
        """执行工具（添加路径标准化）"""
        result = await self._execute_tool_internal(tool_name, **kwargs)
        
        # 标准化返回结果中的路径
        return self._normalize_tool_result(result)
```

---

## 推荐实施方案

### 阶段1: 快速修复（立即）

1. **在 prompt 中明确说明**（已完成）
   - repo_map 返回的路径是完整的相对路径
   - 直接使用，不要修改

2. **添加路径验证和自动修复**
   ```python
   # 在 read_file 工具中
   async def execute(self, file_path: str):
       # 尝试直接读取
       try:
           return await self._read_file(file_path)
       except FileNotFoundError:
           # 如果失败，尝试使用 list_files 查找
           logger.warning(f"File not found: {file_path}, trying to find it...")
           correct_path = await self._find_file(Path(file_path).name)
           if correct_path:
               return await self._read_file(correct_path)
           raise
   ```

### 阶段2: 架构改进（1-2周）

1. **实现方案1：在 BaseTool 中添加 normalize_path()**
2. **修改所有返回路径的工具**
   - repo_map
   - list_files
   - text_search
   - get_repo_structure

3. **添加测试**
   ```python
   def test_path_normalization():
       tool = RepoMapTool()
       tool.set_working_directory("/project/root")
       
       # 测试绝对路径
       assert tool.normalize_path("/project/root/backend/file.py") == "backend/file.py"
       
       # 测试相对路径
       assert tool.normalize_path("backend/file.py") == "backend/file.py"
   ```

### 阶段3: 彻底解决（1个月）

1. **实现 ToolContext（类似 daoyouCodePilot）**
   ```python
   @dataclass
   class ToolContext:
       repo_path: Path
       session_id: str
       user_id: Optional[str] = None
       
       def abs_path(self, path: str) -> Path:
           """转换为绝对路径"""
           return self.repo_path / path
       
       def rel_path(self, path: str) -> str:
           """转换为相对路径"""
           return str(Path(path).relative_to(self.repo_path))
   ```

2. **所有工具接收 ToolContext**
3. **统一路径处理逻辑**

---

## 测试计划

### 测试场景1: repo_map 路径

```python
# 设置工作目录为项目根目录
registry.set_working_directory("/project/root")

# 执行 repo_map
result = await registry.execute_tool("repo_map", repo_path=".")

# 验证返回的路径
assert "backend/daoyoucode/agents/llm/clients/unified.py" in result.content

# 验证可以直接使用
result2 = await registry.execute_tool(
    "read_file",
    file_path="backend/daoyoucode/agents/llm/clients/unified.py"
)
assert result2.success
```

### 测试场景2: list_files 路径

```python
result = await registry.execute_tool("list_files", directory="backend", recursive=True)

# 验证返回的路径都是相对于工作目录的
for file in result.content:
    assert file['path'].startswith("backend/")
    
    # 验证可以直接使用
    result2 = await registry.execute_tool("read_file", file_path=file['path'])
    assert result2.success
```

### 测试场景3: 跨项目使用

```python
# 测试在不同项目中使用
projects = [
    "/project1",
    "/project2/backend",
    "/project3/src"
]

for project_path in projects:
    registry.set_working_directory(project_path)
    
    # 执行工具
    result = await registry.execute_tool("repo_map", repo_path=".")
    
    # 验证路径都是相对于 project_path 的
    # 验证可以直接使用
```

---

## 总结

### 当前状态
- ❌ 路径处理不统一
- ❌ 依赖 prompt 修补
- ❌ 跨项目使用会有问题

### 目标状态
- ✅ 所有工具返回标准化路径
- ✅ 路径相对于 working_directory
- ✅ 可以在任何项目中使用
- ✅ AI 不需要理解路径细节

### 实施优先级
1. **立即**：Prompt 修复 + read_file 自动查找
2. **1-2周**：BaseTool.normalize_path() + 修改所有工具
3. **1个月**：ToolContext 架构改进

这是一个**架构级别的改进**，不能只靠 prompt 修补！
