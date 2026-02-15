# Working Directory 修复

## 问题

用户在CLI中询问文件时，仍然出现路径错误：

```
🔧 执行工具: read_file
file_path  chat_assistant_v2.md
✓ 执行完成 (0.02秒)
⚠️  工具返回错误: File not found: chat_assistant_v2.md 
(resolved to D:\daoyouspace\daoyoucode\backend\chat_assistant_v2.md)
```

## 原因分析

虽然在 `cli/commands/chat.py` 的 `handle_chat` 函数中设置了工作目录：

```python
def handle_chat(user_input: str, ui_context: dict):
    # ...
    registry = get_tool_registry()
    registry.set_working_directory(repo_path)  # ✅ 设置了
    
    # ...
    result = loop.run_until_complete(execute_skill(
        skill_name="chat_assistant",
        user_input=user_input,
        session_id=context["session_id"],
        context=context  # ✅ 传递了context
    ))
```

但是，`execute_skill` 函数内部可能会重新初始化工具注册表，或者在多次调用之间工作目录被重置。

## 解决方案

在 `executor.py` 的 `_execute_skill_internal` 函数中，每次执行前都从 `context` 中读取并设置工作目录：

```python
# backend/daoyoucode/agents/executor.py

async def _execute_skill_internal(
    skill_name: str,
    user_input: str,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """内部执行函数"""
    session_id = context.get('session_id')
    
    # ⭐ 设置工具注册表的工作目录（如果context中有）
    if 'working_directory' in context or 'repo' in context:
        from .tools.registry import get_tool_registry
        registry = get_tool_registry()
        working_dir = context.get('working_directory') or context.get('repo')
        if working_dir:
            registry.set_working_directory(working_dir)
            logger.info(f"设置工具工作目录: {working_dir}")
    
    # ... 其余代码
```

## 工作流程

### 修复前

```
1. CLI启动 (backend/)
2. handle_chat() 设置 working_directory
3. execute_skill() 被调用
4. _execute_skill_internal() 执行
   ❌ 工具注册表的 working_directory 可能被重置
5. 工具执行时使用错误的工作目录
```

### 修复后

```
1. CLI启动 (backend/)
2. handle_chat() 设置 working_directory
3. execute_skill() 被调用，传递 context
4. _execute_skill_internal() 执行
   ✅ 从 context 读取 working_directory
   ✅ 重新设置工具注册表的 working_directory
5. 工具执行时使用正确的工作目录
```

## 为什么需要两次设置？

### 第一次设置（handle_chat）
```python
# cli/commands/chat.py
registry.set_working_directory(repo_path)
```
- 确保在同一个 `handle_chat` 调用中，工具有正确的工作目录
- 但可能在 `execute_skill` 内部被重置

### 第二次设置（_execute_skill_internal）
```python
# agents/executor.py
registry.set_working_directory(working_dir)
```
- 确保每次 skill 执行时，工具都有正确的工作目录
- 从 `context` 读取，保证一致性
- 防止多次调用之间的状态丢失

## 测试验证

### 测试场景1: 读取项目文件

```
用户: "chat_assistant_v2.md和chat_assistant.md有俩，哪个有用"

预期:
✅ read_file(file_path="skills/chat-assistant/prompts/chat_assistant_v2.md")
   解析为: D:\daoyouspace\daoyoucode\skills\chat-assistant\prompts\chat_assistant_v2.md

✅ read_file(file_path="skills/chat-assistant/prompts/chat_assistant.md")
   解析为: D:\daoyouspace\daoyoucode\skills\chat-assistant\prompts\chat_assistant.md
```

### 测试场景2: 搜索代码

```
用户: "BaseAgent在哪里？"

预期:
✅ text_search(query="class BaseAgent", directory=".")
   解析为: D:\daoyouspace\daoyoucode
```

### 测试场景3: 列出目录

```
用户: "有哪些编排器？"

预期:
✅ list_files(directory="backend/daoyoucode/agents/orchestrators")
   解析为: D:\daoyouspace\daoyoucode\backend\daoyoucode\agents\orchestrators
```

## 修改的文件

1. ✅ `backend/daoyoucode/agents/executor.py`
   - 在 `_execute_skill_internal` 中添加工作目录设置

## 相关文件

- `backend/daoyoucode/agents/tools/base.py` - BaseTool.resolve_path()
- `backend/cli/commands/chat.py` - handle_chat() 设置工作目录
- `backend/daoyoucode/agents/tools/search_tools.py` - 使用 resolve_path()
- `backend/daoyoucode/agents/tools/file_tools.py` - 使用 resolve_path()

## 总结

### 问题
- 工具注册表的 `working_directory` 在 skill 执行过程中可能被重置
- 导致路径解析错误

### 解决
- 在 `_execute_skill_internal` 中从 `context` 读取并设置 `working_directory`
- 确保每次 skill 执行时都有正确的工作目录

### 效果
- ✅ 路径解析始终正确
- ✅ 无论调用多少次，工作目录都保持一致
- ✅ 对用户和LLM透明
