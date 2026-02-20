# 路径混淆问题修复

## 问题描述

AI 尝试访问 `daoyouCodePilot\examples\types_example.py`，但这不是当前项目的路径。

**症状**：
```
🔧 执行工具: read_file
   file_path  daoyouCodePilot\examples\types_example.py
```

## 根本原因

1. **文档中提到了 daoyouCodePilot**
   - README.md、Prompt 等多处提到 `daoyouCodePilot` 项目
   - AI 误以为这是当前项目的一个目录

2. **路径解析没有验证**
   - `abs_path()` 直接拼接路径，不检查是否存在
   - 没有警告 AI 路径不存在

## 解决方案

### 方案 1: 改进路径解析（推荐）✅

在 `resolve_path()` 中添加路径验证和智能修正：

```python
def resolve_path(self, path: str) -> Path:
    """解析路径（带智能修正）"""
    
    # 1. 检测其他项目名称
    other_projects = [
        'daoyouCodePilot',
        'daoyoucodepilot',
        'oh-my-opencode',
        'opencode',
        'aider'
    ]
    
    path_lower = path.lower()
    for project in other_projects:
        if project.lower() in path_lower:
            self.logger.warning(
                f"⚠️  检测到其他项目路径: {path}\n"
                f"   这不是当前项目的路径\n"
                f"   当前项目: {self.context.repo_path.name}\n"
                f"   提示：请使用当前项目的路径"
            )
            # 返回错误，让工具返回友好的错误消息
            raise ValueError(
                f"路径错误：'{path}' 不是当前项目的路径。\n"
                f"当前项目是 '{self.context.repo_path.name}'，"
                f"请使用相对于项目根目录的路径，如 'backend/file.py'"
            )
    
    # 2. 原有逻辑...
    return self.context.abs_path(path)
```

### 方案 2: 改进 Prompt（推荐）✅

在 Prompt 中明确说明当前项目：

```markdown
## 当前项目信息

**项目名称**: DaoyouCode
**项目根目录**: {{repo}}
**后端代码**: backend/daoyoucode/

⚠️ 重要：
- 不要使用其他项目的路径（如 daoyouCodePilot、oh-my-opencode）
- 所有路径都相对于当前项目根目录
- 示例：backend/daoyoucode/agents/core/agent.py
```

### 方案 3: 添加路径验证工具

创建一个工具来验证路径是否存在：

```python
class ValidatePathTool(BaseTool):
    """验证路径是否存在"""
    
    async def execute(self, file_path: str) -> ToolResult:
        try:
            path = self.resolve_path(file_path)
            
            if not path.exists():
                # 尝试查找相似的路径
                similar_paths = self._find_similar_paths(file_path)
                
                error_msg = f"路径不存在: {file_path}\n"
                if similar_paths:
                    error_msg += "\n你是否想要访问以下路径之一？\n"
                    for p in similar_paths[:5]:
                        error_msg += f"  - {p}\n"
                
                return ToolResult(success=False, error=error_msg)
            
            return ToolResult(
                success=True,
                content=f"路径存在: {file_path}",
                metadata={'exists': True, 'is_file': path.is_file(), 'is_dir': path.is_dir()}
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
```

## 立即修复

### 修复 1: 改进 resolve_path ✅

```python
# backend/daoyoucode/agents/tools/base.py

def resolve_path(self, path: str) -> Path:
    """解析路径（带智能修正）"""
    
    # 检测其他项目名称
    other_projects = [
        'daoyouCodePilot',
        'daoyoucodepilot', 
        'oh-my-opencode',
        'opencode',
        'aider',
        'cursor'
    ]
    
    path_parts = Path(path).parts
    if path_parts:
        first_part = path_parts[0].lower()
        for project in other_projects:
            if project.lower() == first_part:
                self.logger.error(
                    f"❌ 路径错误: {path}\n"
                    f"   '{path_parts[0]}' 不是当前项目的目录\n"
                    f"   当前项目: {self.context.repo_path.name}\n"
                    f"   提示：使用相对于项目根的路径，如 'backend/file.py'"
                )
                raise ValueError(
                    f"路径错误：'{path}' 包含其他项目名称 '{path_parts[0]}'。\n"
                    f"当前项目是 '{self.context.repo_path.name}'，"
                    f"请使用相对路径，如 'backend/daoyoucode/agents/core/agent.py'"
                )
    
    # 原有逻辑
    # ... (占位符检测等)
    
    return self.context.abs_path(path)
```

### 修复 2: 更新 Prompt ✅

```markdown
# skills/chat-assistant/prompts/chat_assistant.md

## 当前项目信息 ⚠️ 必读

**项目名称**: DaoyouCode
**项目根目录**: {{repo}}
**代码位置**: backend/daoyoucode/

**路径规则**：
1. 所有路径相对于项目根目录（不是 daoyouCodePilot 或其他项目）
2. 后端代码在 `backend/daoyoucode/` 下
3. 示例正确路径：
   - ✅ `backend/daoyoucode/agents/core/agent.py`
   - ✅ `backend/config/llm_config.yaml`
   - ❌ `daoyouCodePilot/examples/types_example.py` （错误！这是其他项目）
   - ❌ `oh-my-opencode/src/agents/` （错误！这是其他项目）

**如果你不确定文件在哪里**：
1. 使用 `text_search` 搜索文件名
2. 使用 `list_files` 列出目录
3. 使用 `get_repo_structure` 查看项目结构
```

## 测试验证

### 测试 1: 尝试访问错误路径

```bash
daoyoucode chat "读取 daoyouCodePilot/examples/types_example.py"
```

**预期结果**：
```
🔧 执行工具: read_file
   file_path  daoyouCodePilot/examples/types_example.py
⚠️  工具返回错误: 路径错误：'daoyouCodePilot/examples/types_example.py' 包含其他项目名称 'daoyouCodePilot'。
当前项目是 'daoyoucode'，请使用相对路径，如 'backend/daoyoucode/agents/core/agent.py'

AI > 抱歉，我尝试访问了错误的路径。当前项目是 DaoyouCode，不是 daoyouCodePilot。
让我使用正确的路径...
```

### 测试 2: 使用正确路径

```bash
daoyoucode chat "读取 backend/daoyoucode/agents/core/agent.py"
```

**预期结果**：
```
🔧 执行工具: read_file
   file_path  backend/daoyoucode/agents/core/agent.py
✓ 执行完成 (0.02秒)

AI > 这是 Agent 基类的实现...
```

## 实现步骤

### 步骤 1: 修改 base.py

```bash
# 编辑文件
notepad backend/daoyoucode/agents/tools/base.py

# 在 resolve_path 方法开头添加项目名称检测
```

### 步骤 2: 更新 Prompt

```bash
# 编辑文件
notepad skills/chat-assistant/prompts/chat_assistant.md

# 在开头添加"当前项目信息"部分
```

### 步骤 3: 重新安装

```bash
cd backend
pip install -e .
```

### 步骤 4: 测试

```bash
cd ..
daoyoucode chat "读取 daoyouCodePilot/examples/types_example.py"
# 应该看到错误提示

daoyoucode chat "读取 backend/daoyoucode/agents/core/agent.py"
# 应该成功
```

## 为什么会发生这个问题？

### 原因 1: 文档中的引用

README.md 和其他文档中多次提到 `daoyouCodePilot`：

```markdown
daoyoucode 融合了三个优秀项目的核心优势：
- **daoyouCodePilot** - 中文优化、国产LLM深度集成、完整工具链
```

AI 可能从这些文档中学到了这个名称。

### 原因 2: Prompt 中的提及

```markdown
### 「了解当前项目」类（必须按顺序做，才能像 daoyoucode pilot / aider 一样真正理解）
```

AI 可能误解为 `daoyoucode pilot` 是一个目录。

### 原因 3: 缺少项目上下文

Prompt 没有明确说明：
- 当前项目的名称
- 当前项目的结构
- 不要使用其他项目的路径

## 预防措施

### 1. 在 Prompt 中明确项目信息

```markdown
## 当前项目信息

你正在为 **DaoyouCode** 项目工作，不是 daoyouCodePilot 或其他项目。

项目结构：
- backend/daoyoucode/ - 核心代码
- backend/cli/ - CLI 命令
- backend/config/ - 配置文件
- skills/ - Skill 定义
```

### 2. 路径验证

在工具中添加路径验证，拒绝明显错误的路径。

### 3. 智能提示

当检测到错误路径时，提供正确的路径建议。

## 总结

### 问题

AI 尝试访问 `daoyouCodePilot\examples\types_example.py`，这不是当前项目的路径。

### 原因

1. 文档中多次提到 daoyouCodePilot
2. Prompt 没有明确当前项目信息
3. 路径解析没有验证

### 解决方案

1. ✅ 在 `resolve_path()` 中检测其他项目名称
2. ✅ 在 Prompt 中明确当前项目信息
3. ✅ 提供友好的错误消息和建议

### 立即行动

```bash
# 1. 修改 base.py（添加项目名称检测）
# 2. 更新 Prompt（添加项目信息）
# 3. 重新安装
cd backend
pip install -e .

# 4. 测试
cd ..
daoyoucode chat "读取 backend/daoyoucode/agents/core/agent.py"
```

---

**修复后，AI 将无法访问其他项目的路径，并会收到友好的错误提示。**
