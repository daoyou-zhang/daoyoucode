# 工具名称修正总结

## 问题发现

用户在使用CLI时遇到错误：
```
⚠️  工具返回错误: File not found: chat_assistant.md
⚠️  工具返回错误: Directory not found: skills/chat-assistant/prompts
```

## 根本原因

提示词文件中使用的工具名称与实际注册的工具名称不匹配：

### 错误的工具名称（提示词中）
- `grep_search` ❌
- `list_directory` ❌

### 正确的工具名称（实际注册）
- `text_search` ✅
- `list_files` ✅

## 工具名称对照表

| 提示词中的错误名称 | 实际注册的正确名称 | 工具类 | 文件位置 |
|------------------|------------------|--------|---------|
| grep_search | text_search | TextSearchTool | search_tools.py |
| list_directory | list_files | ListFilesTool | file_tools.py |

## 已修复的文件

### 1. skills/chat-assistant/prompts/chat_assistant.md
修改内容：
- `grep_search` → `text_search`
- 更新所有示例中的工具调用

### 2. skills/chat-assistant/prompts/chat_assistant_optimized.md
修改内容：
- `grep_search` → `text_search`
- 更新所有示例和工具说明
- 更新决策树中的工具名称

### 3. backend/daoyoucode/agents/memory/long_term_memory.py
修复了LLM调用bug：
```python
# 修复前
response = await llm_client.chat(
    messages=[{"role": "user", "content": summary_prompt}],
    temperature=0.3,
    max_tokens=300
)

# 修复后
from ..llm.base import LLMRequest
request = LLMRequest(
    prompt=summary_prompt,
    model=llm_client.model,
    temperature=0.3,
    max_tokens=300
)
response = await llm_client.chat(request)
```

## 工具注册详情

### 文件操作工具（6个）
- `read_file` - ReadFileTool
- `write_file` - WriteFileTool
- `list_files` - ListFilesTool ⭐ 注意不是 list_directory
- `get_file_info` - GetFileInfoTool
- `create_directory` - CreateDirectoryTool
- `delete_file` - DeleteFileTool

### 搜索工具（2个）
- `text_search` - TextSearchTool ⭐ 注意不是 grep_search
- `regex_search` - RegexSearchTool

### RepoMap工具（3个）
- `repo_map` - RepoMapTool
- `get_repo_structure` - GetRepoStructureTool
- `discover_project_docs` - DiscoverProjectDocsTool

### Git工具（4个）
- `git_status` - GitStatusTool
- `git_diff` - GitDiffTool
- `git_commit` - GitCommitTool
- `git_log` - GitLogTool

### 命令执行工具（2个）
- `run_command` - RunCommandTool
- `run_test` - RunTestTool

### Diff工具（1个）
- `search_replace` - SearchReplaceTool

### LSP工具（6个）
- `lsp_diagnostics` - LSPDiagnosticsTool
- `lsp_goto_definition` - LSPGotoDefinitionTool
- `lsp_find_references` - LSPFindReferencesTool
- `lsp_symbols` - LSPSymbolsTool
- `lsp_rename` - LSPRenameTool
- `lsp_code_actions` - LSPCodeActionsTool

### AST工具（2个）
- `ast_grep_search` - AstGrepSearchTool
- `ast_grep_replace` - AstGrepReplaceTool

## 工具参数对照

### text_search (原 grep_search)
```python
# 正确用法
text_search(
    query="class BaseAgent",
    directory=".",
    file_pattern="**/*.py",  # 注意：不是 include_pattern
    case_sensitive=False,
    max_results=100
)
```

### list_files (原 list_directory)
```python
# 正确用法
list_files(
    directory="skills/chat-assistant/prompts",
    pattern="*.md",
    recursive=True,
    max_depth=3
)
```

## skill.yaml 配置

### 当前配置（正确）
```yaml
tools:
  - repo_map
  - get_repo_structure
  - read_file
  - text_search          # ✅ 正确
  - regex_search
  - write_file
  - list_files           # ✅ 正确
```

### 如果使用错误名称（会失败）
```yaml
tools:
  - grep_search          # ❌ 工具不存在
  - list_directory       # ❌ 工具不存在
```

## 验证方法

### 1. 查看注册的工具
```python
from daoyoucode.agents.tools.registry import get_tool_registry

registry = get_tool_registry()
print(registry.list_tools())
```

### 2. 测试工具调用
```python
import asyncio
from daoyoucode.agents.tools.registry import get_tool_registry

async def test_tools():
    registry = get_tool_registry()
    
    # 测试 text_search
    result = await registry.execute_tool(
        "text_search",
        query="class BaseAgent",
        file_pattern="**/*.py"
    )
    print(result)
    
    # 测试 list_files
    result = await registry.execute_tool(
        "list_files",
        directory=".",
        pattern="*.md"
    )
    print(result)

asyncio.run(test_tools())
```

## 总结

### 修复的问题
1. ✅ 提示词中的工具名称已全部修正
2. ✅ LongTermMemory的LLM调用bug已修复
3. ✅ 创建了优化版提示词（chat_assistant_optimized.md）

### 注意事项
1. 使用 `text_search` 而不是 `grep_search`
2. 使用 `list_files` 而不是 `list_directory`
3. `text_search` 的参数是 `file_pattern`，不是 `include_pattern`
4. 所有工具名称以 snake_case 命名

### 下一步
建议使用优化版提示词 `chat_assistant_optimized.md`，它包含：
- 正确的工具名称
- 7种问题类型决策树
- 编程最佳实践
- DaoyouCode代码规范
- 6个完整示例
