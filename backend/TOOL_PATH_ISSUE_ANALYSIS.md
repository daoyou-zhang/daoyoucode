# 工具路径处理问题分析

## 问题描述

AI 在使用 `search_replace` 工具时遇到错误：
```
⚠️  工具返回错误: File not found: backend/daoyoucode/agents/core/timeout_recovery.py
```

## 问题根源

### 1. 路径解析不一致

不同工具对路径的处理方式不同：

#### ✅ ReadFileTool（正确）
```python
# backend/daoyoucode/agents/tools/file_tools.py
async def execute(self, file_path: str, encoding: str = "utf-8") -> ToolResult:
    # 使用 resolve_path 解析路径
    path = self.resolve_path(file_path)  # ✅ 正确
    
    if not path.exists():
        return ToolResult(
            success=False,
            error=f"File not found: {file_path} (resolved to {path})"
        )
```

#### ❌ SearchReplaceTool（错误）
```python
# backend/daoyoucode/agents/tools/diff_tools.py
async def execute(self, file_path: str, search: str, replace: str, replace_all: bool = False) -> ToolResult:
    path = Path(file_path)  # ❌ 直接使用 Path，没有解析
    
    if not path.exists():
        return ToolResult(
            success=False,
            error=f"File not found: {file_path}"  # ❌ 没有显示解析后的路径
        )
```

### 2. 工作目录问题

当 AI 在项目根目录运行时：
- **当前目录**: `/path/to/daoyoucode/`
- **AI 提供的路径**: `backend/daoyoucode/agents/core/timeout_recovery.py`
- **期望的绝对路径**: `/path/to/daoyoucode/backend/daoyoucode/agents/core/timeout_recovery.py`

但 `SearchReplaceTool` 直接使用 `Path(file_path)`，会相对于当前工作目录解析，可能导致路径错误。

### 3. 上下文缺失

`SearchReplaceTool` 没有正确使用 `ToolContext`：
- 没有调用 `self.resolve_path()`
- 没有使用 `self.context.repo_path`
- 错误信息不够详细

## 影响范围

### 受影响的工具

需要检查所有文件操作工具：

1. ❌ **SearchReplaceTool** - 路径解析问题
2. ✅ **ReadFileTool** - 正确使用 `resolve_path`
3. ❓ **WriteFileTool** - 需要检查
4. ❓ **ListFilesTool** - 需要检查
5. ❓ **GetFileInfoTool** - 需要检查

### 影响场景

1. **AI 自主修改代码** - 最常见的场景
2. **跨目录操作** - 当工作目录不是项目根目录时
3. **相对路径处理** - AI 提供相对路径时

## 解决方案

### 方案 1: 修复 SearchReplaceTool（推荐）

```python
# backend/daoyoucode/agents/tools/diff_tools.py
class SearchReplaceTool(BaseTool):
    async def execute(
        self,
        file_path: str,
        search: str,
        replace: str,
        replace_all: bool = False
    ) -> ToolResult:
        try:
            # ✅ 使用 resolve_path 解析路径
            path = self.resolve_path(file_path)
            
            if not path.exists():
                return ToolResult(
                    success=False,
                    content=None,
                    # ✅ 显示原始路径和解析后的路径
                    error=f"File not found: {file_path} (resolved to {path})"
                )
            
            # 读取文件
            content = path.read_text(encoding='utf-8', errors='ignore')
            
            # 执行替换
            from . import diff_tools
            new_content = diff_tools.replace(content, search, replace, replace_all)
            
            # 写入文件
            path.write_text(new_content, encoding='utf-8')
            
            return ToolResult(
                success=True,
                content=f"Successfully replaced in {file_path}",
                metadata={
                    'file_path': str(path),
                    'old_size': len(content),
                    'new_size': len(new_content),
                    'replace_all': replace_all
                }
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content=None,
                error=str(e)
            )
```

### 方案 2: 统一路径处理（长期）

创建一个路径处理混入类：

```python
# backend/daoyoucode/agents/tools/mixins.py
class PathResolutionMixin:
    """路径解析混入类"""
    
    def resolve_and_validate_path(self, file_path: str) -> tuple[Path, Optional[str]]:
        """
        解析并验证路径
        
        Returns:
            (resolved_path, error_message)
        """
        try:
            path = self.resolve_path(file_path)
            
            if not path.exists():
                error = f"File not found: {file_path} (resolved to {path})"
                return path, error
            
            return path, None
        except Exception as e:
            return None, f"Path resolution error: {e}"
```

### 方案 3: 改进错误提示（辅助）

在工具描述中明确说明路径格式：

```python
def get_function_schema(self) -> Dict[str, Any]:
    return {
        "name": self.name,
        "description": self.description,
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": (
                        "文件的相对路径（相对于项目根目录）。"
                        "例如: 'backend/config.py' 或 'README.md'。"
                        "不要使用绝对路径或占位符！"
                    )
                },
                # ...
            },
            "required": ["file_path"]
        }
    }
```

## 修复优先级

### 高优先级（立即修复）
1. ✅ **SearchReplaceTool** - 最常用的编辑工具
2. ⚠️ **WriteFileTool** - 检查是否有同样问题
3. ⚠️ **其他文件工具** - 统一检查

### 中优先级（后续优化）
1. 创建路径处理混入类
2. 统一所有工具的路径处理
3. 改进错误提示

### 低优先级（长期改进）
1. 添加路径验证测试
2. 文档化路径处理规范
3. AI 提示词优化

## 测试建议

### 1. 单元测试

```python
# backend/tests/test_search_replace_path.py
import pytest
from pathlib import Path
from daoyoucode.agents.tools.diff_tools import SearchReplaceTool
from daoyoucode.agents.tools.base import ToolContext

@pytest.mark.asyncio
async def test_search_replace_with_relative_path():
    """测试相对路径处理"""
    tool = SearchReplaceTool()
    
    # 设置上下文
    repo_path = Path(__file__).parent.parent
    context = ToolContext(repo_path=repo_path)
    tool.set_context(context)
    
    # 测试相对路径
    result = await tool.execute(
        file_path="backend/config/llm_config.yaml",
        search="timeout: 1800",
        replace="timeout: 3600"
    )
    
    assert result.success
```

### 2. 集成测试

```python
@pytest.mark.asyncio
async def test_ai_modify_code():
    """测试 AI 修改代码的完整流程"""
    # 模拟 AI 调用 search_replace
    # 验证路径解析正确
    # 验证文件修改成功
```

## 临时解决方案

在修复之前，可以通过以下方式避免问题：

### 1. 使用绝对路径

```python
# AI 应该使用绝对路径
file_path = "/full/path/to/file.py"
```

### 2. 确保工作目录正确

```python
# 在项目根目录运行
cd /path/to/daoyoucode
daoyoucode chat
```

### 3. 使用其他工具

```python
# 使用 read_file + write_file 代替 search_replace
content = read_file("backend/file.py")
new_content = content.replace("old", "new")
write_file("backend/file.py", new_content)
```

## 相关问题

### 1. 为什么 ReadFileTool 没问题？

因为它正确使用了 `self.resolve_path()`：
```python
path = self.resolve_path(file_path)  # ✅
```

### 2. 其他工具是否有同样问题？

需要逐个检查：
- WriteFileTool
- ListFilesTool
- GetFileInfoTool
- GitStatusTool
- GitDiffTool

### 3. 如何防止类似问题？

1. **代码审查** - 确保所有工具使用 `resolve_path`
2. **单元测试** - 测试路径解析
3. **文档规范** - 明确路径处理标准
4. **Linter 规则** - 检测直接使用 `Path(file_path)`

## 总结

### 问题
- `SearchReplaceTool` 没有使用 `resolve_path()` 解析路径
- 导致 AI 提供的相对路径无法正确解析
- 错误信息不够详细

### 解决
1. 修改 `SearchReplaceTool.execute()` 使用 `self.resolve_path()`
2. 改进错误信息，显示原始路径和解析后的路径
3. 检查其他工具是否有同样问题

### 影响
- 修复后 AI 可以正确修改代码
- 提高工具的健壮性
- 改善用户体验

## 下一步

1. ✅ 创建此分析文档
2. ⏳ 修复 SearchReplaceTool
3. ⏳ 检查其他文件工具
4. ⏳ 添加单元测试
5. ⏳ 更新文档
