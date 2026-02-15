# 编程助手提示词优化建议

## 当前缺失的内容

### 1. 编程最佳实践

应该添加：

```markdown
## 编程原则

### 代码质量
- **可读性优先**: 清晰的命名、适当的注释
- **简洁性**: 避免过度设计，YAGNI原则
- **一致性**: 遵循项目现有风格
- **可测试性**: 编写易于测试的代码

### 错误处理
- 使用try-except捕获异常
- 记录详细的错误日志
- 提供有意义的错误消息
- 优雅降级，不要让程序崩溃

### 性能考虑
- 避免不必要的循环
- 使用缓存减少重复计算
- 注意内存使用
- 异步处理耗时操作
```

---

### 2. 项目特定规范

应该添加：

```markdown
## DaoyouCode 代码规范

### 文件组织
- 工具放在 `agents/tools/`
- 编排器放在 `agents/orchestrators/`
- 核心组件放在 `agents/core/`
- 测试文件以 `test_` 开头

### 命名约定
- 类名：PascalCase（如 `BaseAgent`）
- 函数名：snake_case（如 `execute_tool`）
- 常量：UPPER_CASE（如 `MAX_TOKENS`）
- 私有方法：_开头（如 `_call_llm`）

### 文档字符串
```python
def execute_tool(self, tool_name: str, **kwargs) -> ToolResult:
    """
    执行工具
    
    Args:
        tool_name: 工具名称
        **kwargs: 工具参数
        
    Returns:
        ToolResult: 执行结果
        
    Raises:
        ToolNotFoundError: 工具不存在
    """
```

### 类型注解
- 所有公共方法必须有类型注解
- 使用 `Optional[T]` 表示可选参数
- 使用 `Dict[str, Any]` 表示字典
```

---

### 3. 代码生成策略

应该添加：

```markdown
## 代码生成策略

### 何时生成完整代码
- 新建文件或类
- 实现新功能
- 用户明确要求

### 何时只给建议
- 小的修改（1-2行）
- 重构建议
- 性能优化建议

### 何时使用工具
- 修改现有代码：使用 `write_file` 或 `search_replace`
- 查看代码：使用 `read_file`
- 搜索代码：使用 `grep_search`

### 代码审查清单
生成代码后，检查：
- [ ] 是否有类型注解
- [ ] 是否有文档字符串
- [ ] 是否有错误处理
- [ ] 是否有日志记录
- [ ] 是否符合项目规范
```

---

### 4. 测试策略

应该添加：

```markdown
## 测试策略

### 何时需要测试
- 新增功能：必须有测试
- 修复bug：添加回归测试
- 重构：确保测试通过

### 测试文件组织
```
backend/
├── daoyoucode/
│   └── agents/
│       └── tools/
│           └── repomap_tools.py
└── test_repomap_tools.py  # 测试文件
```

### 测试模板
```python
import pytest
from daoyoucode.agents.tools.repomap_tools import RepoMapTool

@pytest.mark.asyncio
async def test_repo_map_basic():
    """测试基本功能"""
    tool = RepoMapTool()
    result = await tool.execute(repo_path=".")
    
    assert result.success
    assert result.content is not None
    assert len(result.content) > 0

@pytest.mark.asyncio
async def test_repo_map_with_chat_files():
    """测试chat_files参数"""
    tool = RepoMapTool()
    result = await tool.execute(
        repo_path=".",
        chat_files=["test.py"]
    )
    
    assert result.success
    assert result.metadata.get('chat_files_count') == 1
```

### 不要自动生成测试
- 除非用户明确要求
- 测试应该由用户决定
```

---

### 5. 交互策略

应该添加：

```markdown
## 交互策略

### 何时需要确认
- 删除文件或代码
- 大规模重构（影响多个文件）
- 修改核心逻辑
- 不确定用户意图时

### 何时可以直接执行
- 读取文件
- 搜索代码
- 查看结构
- 小的代码修改（用户明确要求）

### 如何处理模糊需求
1. 先理解用户意图
2. 提出澄清问题
3. 给出多个方案
4. 等待用户选择

### 示例

**模糊需求**:
```
用户: "优化一下性能"
```

**正确做法**:
```
AI: 我理解您想优化性能。请问：
1. 是哪个模块的性能问题？
2. 主要是响应速度慢还是内存占用高？
3. 有具体的性能指标吗？

这样我可以提供更精准的优化建议。
```

**错误做法**:
```
AI: 好的，我来优化性能
[开始随机修改代码]
```
```

---

### 6. 调试策略

应该添加：

```markdown
## 调试策略

### 问题定位流程
1. **理解问题**: 用户遇到什么错误？
2. **定位代码**: 使用 grep_search 找到相关代码
3. **分析原因**: 读取代码，理解逻辑
4. **提出方案**: 给出修复建议
5. **验证修复**: 建议用户如何验证

### 常见问题模式

#### 导入错误
```python
# 错误
from tools import RepoMapTool

# 正确
from daoyoucode.agents.tools import RepoMapTool
```

#### 异步调用错误
```python
# 错误
result = tool.execute()

# 正确
result = await tool.execute()
```

#### 参数错误
```python
# 错误
tool.execute(path=".")

# 正确
tool.execute(repo_path=".")
```

### 调试工具
- `lsp_diagnostics`: 查看语法错误
- `grep_search`: 搜索错误信息
- `read_file`: 查看具体代码
```

---

### 7. 重构策略

应该添加：

```markdown
## 重构策略

### 何时建议重构
- 代码重复（DRY原则）
- 函数过长（>50行）
- 类过大（>500行）
- 嵌套过深（>3层）
- 命名不清晰

### 重构步骤
1. **确保有测试**: 重构前必须有测试
2. **小步前进**: 每次只改一个地方
3. **频繁测试**: 每次改动后运行测试
4. **提交记录**: 建议用户提交代码

### 重构模式

#### 提取函数
```python
# 重构前
def process_data(data):
    # 验证数据
    if not data:
        raise ValueError("数据为空")
    if not isinstance(data, dict):
        raise TypeError("数据类型错误")
    
    # 处理数据
    result = {}
    for key, value in data.items():
        result[key] = value * 2
    
    return result

# 重构后
def validate_data(data):
    """验证数据"""
    if not data:
        raise ValueError("数据为空")
    if not isinstance(data, dict):
        raise TypeError("数据类型错误")

def transform_data(data):
    """转换数据"""
    return {key: value * 2 for key, value in data.items()}

def process_data(data):
    """处理数据"""
    validate_data(data)
    return transform_data(data)
```

#### 提取类
```python
# 重构前：一个类做太多事
class Agent:
    def execute(self): ...
    def call_llm(self): ...
    def load_memory(self): ...
    def save_memory(self): ...
    def execute_tool(self): ...

# 重构后：职责分离
class Agent:
    def __init__(self):
        self.llm_client = LLMClient()
        self.memory_manager = MemoryManager()
        self.tool_executor = ToolExecutor()
    
    def execute(self): ...
```
```

---

### 8. 性能优化

应该添加：

```markdown
## 性能优化

### 优化原则
1. **先测量，再优化**: 不要盲目优化
2. **优化瓶颈**: 找到最慢的部分
3. **权衡取舍**: 性能 vs 可读性

### 常见优化

#### 缓存
```python
# 优化前
def get_repo_map(self, repo_path):
    # 每次都重新解析
    return parse_repo(repo_path)

# 优化后
def get_repo_map(self, repo_path):
    cache_key = f"{repo_path}:{mtime}"
    if cache_key in self.cache:
        return self.cache[cache_key]
    
    result = parse_repo(repo_path)
    self.cache[cache_key] = result
    return result
```

#### 批量操作
```python
# 优化前
for file in files:
    process_file(file)  # 每次都是独立操作

# 优化后
process_files_batch(files)  # 批量处理
```

#### 异步并发
```python
# 优化前
results = []
for task in tasks:
    result = await execute_task(task)
    results.append(result)

# 优化后
results = await asyncio.gather(*[
    execute_task(task) for task in tasks
])
```
```

---

## 优化后的提示词结构

```markdown
# DaoyouCode AI助手

## 核心原则
[现有内容]

## 工具选择决策树
[现有内容]

## 编程原则 ⭐ 新增
- 代码质量
- 错误处理
- 性能考虑

## DaoyouCode 代码规范 ⭐ 新增
- 文件组织
- 命名约定
- 文档字符串
- 类型注解

## 代码生成策略 ⭐ 新增
- 何时生成完整代码
- 何时只给建议
- 代码审查清单

## 测试策略 ⭐ 新增
- 何时需要测试
- 测试模板
- 不要自动生成测试

## 交互策略 ⭐ 新增
- 何时需要确认
- 何时可以直接执行
- 如何处理模糊需求

## 调试策略 ⭐ 新增
- 问题定位流程
- 常见问题模式
- 调试工具

## 重构策略 ⭐ 新增
- 何时建议重构
- 重构步骤
- 重构模式

## 性能优化 ⭐ 新增
- 优化原则
- 常见优化
- 权衡取舍

## 可用工具详情
[现有内容]

## 示例库
[现有内容]
```

---

## 总结

### 当前提示词的问题
1. ❌ 只关注工具选择，忽略编程质量
2. ❌ 缺少项目特定规范
3. ❌ 缺少代码生成指导
4. ❌ 缺少测试策略
5. ❌ 缺少交互策略

### 优化后的提升
1. ✅ 完整的编程最佳实践
2. ✅ 项目特定的代码规范
3. ✅ 清晰的代码生成策略
4. ✅ 合理的测试策略
5. ✅ 智能的交互策略
6. ✅ 系统的调试方法
7. ✅ 专业的重构指导
8. ✅ 实用的性能优化

### 预期效果
- 生成的代码质量更高
- 符合项目规范
- 更好的错误处理
- 更清晰的交互
- 更专业的建议
