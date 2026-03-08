# Context 集成代码修改

## 已完成的修改 ✅

### 1. 添加导入
```python
from .context import Context, ContextManager, get_context_manager
from datetime import datetime
```

### 2. 初始化 ContextManager
```python
# 在 __init__ 中添加
self.context_manager = get_context_manager()
self.logger.debug("上下文管理器已就绪")
```

## 需要继续的修改

由于 agent.py 文件非常大（约 1500 行），我建议采用**渐进式集成**策略：

### 阶段1：最小化集成（立即可用）⭐⭐⭐⭐⭐

**目标**：让 Context 工作起来，但不破坏现有功能

**修改策略**：
1. 在 execute() 开头创建 Context 对象
2. 将 context_dict 的内容复制到 Context
3. 在关键位置保存工具结果
4. 保持向后兼容

**具体修改**：

#### 修改 A：execute() 方法开头

```python
async def execute(
    self,
    prompt_source: Dict[str, Any],
    user_input: str,
    context_dict: Optional[Dict[str, Any]] = None,  # 重命名参数
    llm_config: Optional[Dict[str, Any]] = None,
    tools: Optional[List[str]] = None,
    max_tool_iterations: int = 15,
    enable_streaming: bool = False
):
    """
    执行任务
    
    Args:
        context_dict: 上下文字典（向后兼容）
        ...
    """
    if context_dict is None:
        context_dict = {}
    
    # 🆕 获取或创建 Context 对象
    session_id = context_dict.get('session_id', 'default')
    ctx = self.context_manager.get_or_create_context(session_id)
    
    # 🆕 将字典内容同步到 Context（不追踪变更，避免性能开销）
    ctx.update(context_dict, track_change=False)
    
    # 🆕 保存 Context 对象到字典（供后续使用）
    context_dict['_context_obj'] = ctx
    
    # 后续代码继续使用 context_dict（保持兼容）
    # 但在关键位置使用 ctx 对象
    
    # 提取session_id和user_id
    session_id = context_dict.get('session_id', 'default')
    user_id = context_dict.get('user_id')
    ...
```

#### 修改 B：在工具调用后保存结果

找到工具调用的位置（大约在第 800-1000 行），添加保存逻辑：

```python
# 执行工具
result = await tool.execute(**tool_kwargs)

# 🆕 保存结果到 Context
ctx = context_dict.get('_context_obj')
if ctx:
    self._save_tool_result_to_context(ctx, tool_name, result)
```

#### 修改 C：添加辅助方法（在类的末尾）

```python
def _save_tool_result_to_context(
    self,
    context: Context,
    tool_name: str,
    result: Any
):
    """保存工具结果到 Context"""
    try:
        # 保存最近的工具结果
        context.set("last_tool_result", {
            "tool": tool_name,
            "result": str(result)[:1000],  # 限制长度
            "timestamp": datetime.now().isoformat()
        }, track_change=False)
        
        # 保存特定工具的结果
        context.set(f"last_{tool_name}_result", result, track_change=False)
        
        # 自动提取路径
        if tool_name in ["text_search", "repo_map"]:
            paths = self._extract_paths_from_result(tool_name, result)
            if paths:
                context.set("last_search_paths", paths, track_change=False)
                if len(paths) == 1:
                    context.set("target_file", paths[0], track_change=False)
                    # 提取目录
                    import os
                    target_dir = os.path.dirname(paths[0])
                    if target_dir:
                        context.set("target_dir", target_dir, track_change=False)
                    self.logger.info(f"✅ 自动提取路径: {paths[0]}")
        
        self.logger.debug(f"已保存工具结果到 Context: {tool_name}")
    except Exception as e:
        self.logger.warning(f"保存工具结果失败: {e}")

def _extract_paths_from_result(
    self,
    tool_name: str,
    result: Any
) -> List[str]:
    """从工具结果中提取文件路径"""
    import re
    
    paths = []
    result_str = str(result)
    
    try:
        if tool_name == "text_search":
            # 匹配格式：path/to/file.py:line_number
            pattern = r'([^\s:]+\.(?:py|js|ts|java|cpp|c|h|go|rs|rb|php|md|txt|json|yaml|yml)):\d+'
            matches = re.findall(pattern, result_str)
            paths = list(set(matches))
        
        elif tool_name == "repo_map":
            # repo_map 结果中的路径格式
            pattern = r'([^\s:]+\.(?:py|js|ts|java|cpp|c|h|go|rs|rb|php|md|txt|json|yaml|yml))'
            matches = re.findall(pattern, result_str)
            paths = list(set(matches))
        
        if paths:
            self.logger.info(f"从 {tool_name} 结果中提取了 {len(paths)} 个路径")
    except Exception as e:
        self.logger.warning(f"提取路径失败: {e}")
    
    return paths

def _format_context_info(self, context: Context) -> str:
    """格式化 Context 信息用于 Prompt"""
    try:
        lines = ["## 🔧 当前上下文变量", ""]
        
        # 重要变量
        important_keys = [
            "target_file",
            "target_dir",
            "config_file",
            "last_search_paths"
        ]
        
        has_important = False
        for key in important_keys:
            if context.has(key):
                value = context.get(key)
                if isinstance(value, list):
                    lines.append(f"- **{key}**: {len(value)} 个路径")
                    for i, path in enumerate(value[:3], 1):
                        lines.append(f"  {i}. `{path}`")
                    if len(value) > 3:
                        lines.append(f"  ... 还有 {len(value) - 3} 个")
                else:
                    lines.append(f"- **{key}**: `{value}`")
                has_important = True
        
        if not has_important:
            return ""  # 没有重要变量，不显示
        
        lines.append("")
        lines.append("⚠️ **提示**：上述变量已自动提取并保存，可以直接使用")
        lines.append("")
        
        return "\n".join(lines)
    except Exception as e:
        self.logger.warning(f"格式化 Context 信息失败: {e}")
        return ""
```

### 阶段2：Prompt 增强（可选）⭐⭐⭐

**目标**：在 Prompt 中显示 Context 信息

**修改位置**：`_render_prompt()` 方法

```python
def _render_prompt(
    self,
    prompt: str,
    user_input: str,
    context: Dict[str, Any]  # 保持参数类型不变
) -> str:
    """渲染Prompt"""
    
    # 🆕 获取 Context 对象
    ctx = context.get('_context_obj')
    context_info = ""
    
    if ctx:
        context_info = self._format_context_info(ctx)
    
    # 构建完整 Prompt
    if context_info:
        full_prompt = f"""{context_info}

{prompt}

## 用户输入
{user_input}
"""
    else:
        full_prompt = f"""{prompt}

## 用户输入
{user_input}
"""
    
    return full_prompt
```

## 实施建议

### 建议1：分步实施 ⭐⭐⭐⭐⭐

1. **第一步**：只添加修改 A（创建 Context 对象）
   - 测试是否正常工作
   - 不影响现有功能

2. **第二步**：添加修改 B 和 C（保存工具结果）
   - 测试路径是否被正确提取
   - 检查日志

3. **第三步**：添加阶段2（Prompt 增强）
   - 测试 Prompt 中是否显示 Context
   - 验证效果

### 建议2：保持向后兼容 ⭐⭐⭐⭐⭐

- 参数名从 `context` 改为 `context_dict`
- 内部使用 Context 对象
- 外部调用不需要修改
- 如果 Context 操作失败，不影响主流程

### 建议3：添加日志 ⭐⭐⭐⭐

在关键位置添加日志：
```python
self.logger.info(f"✅ 自动提取路径: {paths[0]}")
self.logger.debug(f"已保存工具结果到 Context: {tool_name}")
```

### 建议4：异常处理 ⭐⭐⭐⭐⭐

所有 Context 操作都要有异常处理：
```python
try:
    context.set("key", "value")
except Exception as e:
    self.logger.warning(f"Context 操作失败: {e}")
    # 不影响主流程
```

## 测试方法

### 测试1：基础功能

```bash
cd backend
python -c "
from daoyoucode.agents.core.agent import BaseAgent, AgentConfig
import asyncio

async def test():
    config = AgentConfig(
        name='test',
        description='test',
        model='gpt-4o-mini'
    )
    agent = BaseAgent(config)
    
    # 检查 context_manager 是否初始化
    assert agent.context_manager is not None
    print('✅ ContextManager 已初始化')
    
    # 创建 Context
    ctx = agent.context_manager.get_or_create_context('test_session')
    assert ctx is not None
    print('✅ Context 创建成功')
    
    # 测试基本操作
    ctx.set('test_key', 'test_value')
    assert ctx.get('test_key') == 'test_value'
    print('✅ Context 基本操作正常')

asyncio.run(test())
"
```

### 测试2：路径提取

```bash
cd backend
python -c "
from daoyoucode.agents.core.agent import BaseAgent, AgentConfig
import asyncio

async def test():
    config = AgentConfig(
        name='test',
        description='test',
        model='gpt-4o-mini'
    )
    agent = BaseAgent(config)
    
    # 测试路径提取
    result = 'backend/daoyoucode/agents/core/agent.py:100: class BaseAgent'
    paths = agent._extract_paths_from_result('text_search', result)
    
    assert len(paths) > 0
    assert 'backend/daoyoucode/agents/core/agent.py' in paths
    print(f'✅ 路径提取成功: {paths}')

asyncio.run(test())
"
```

## 预期效果

### 效果1：工具结果自动保存

```
执行 text_search → 
  Context.set("last_tool_result", {...})
  Context.set("last_text_search_result", result)
  Context.set("last_search_paths", [paths])
  Context.set("target_file", "path/to/file.py")
  Context.set("target_dir", "path/to")
```

### 效果2：日志输出

```
[INFO] ✅ 自动提取路径: backend/daoyoucode/agents/core/agent.py
[DEBUG] 已保存工具结果到 Context: text_search
[INFO] 从 text_search 结果中提取了 1 个路径
```

### 效果3：Prompt 中显示

```
## 🔧 当前上下文变量

- **target_file**: `backend/daoyoucode/agents/core/agent.py`
- **target_dir**: `backend/daoyoucode/agents/core`

⚠️ **提示**：上述变量已自动提取并保存，可以直接使用
```

## 下一步

1. 我先实施修改 A（创建 Context 对象）
2. 然后实施修改 B 和 C（保存工具结果）
3. 测试基础功能
4. 如果一切正常，再实施阶段2（Prompt 增强）

你觉得这个方案如何？要我现在开始实施吗？
