# Repo Path 错误修复 ✅

## 问题

AI 使用了占位符路径 `/home/user/project`，导致错误：
```
⚠️  工具返回错误: 仓库路径不存在: D:\home\user\project
```

## 根本原因

AI 可能从训练数据或其他示例中学到了使用占位符路径的习惯。

## 解决方案

在 `chat_assistant.md` 的多个位置添加了明确的规则：

### 1. 当前项目部分

```markdown
**重要 - 路径规则** ⭐⭐⭐: 
- 当前工作目录已经是项目根目录
- 调用工具时，使用 `repo_path="."` 表示当前目录
- **绝对不要使用占位符路径**，如 `/home/user/project`、`/path/to/project` 等
- **绝对不要使用子目录路径**，如 `repo_path="backend/"` 
- **只使用 `repo_path="."`** - 这是唯一正确的值
```

### 2. 工作环境部分

```markdown
**调用工具时请使用** ⭐ 重要:
- `repo_path="."` - 表示当前工作目录
- **绝对不要使用占位符路径**，如 `/home/user/project`、`/path/to/project`
- **绝对不要使用绝对路径**，如 `D:\daoyouspace\daoyoucode`
- **只使用 `repo_path="."`** - 这是唯一正确的值
```

### 3. 重要原则部分

```markdown
12. **repo_path 规则** ⭐⭐⭐ 极其重要:
    - **只使用 `repo_path="."`** - 这是唯一正确的值
    - ❌ 绝对不要使用占位符: `/home/user/project`、`/path/to/project`
    - ❌ 绝对不要使用绝对路径: `D:\daoyouspace\daoyoucode`
    - ❌ 绝对不要使用子目录: `repo_path="backend/"`
    - ✅ 只使用: `repo_path="."`
```

### 4. 示例中添加注释

在示例1中的每个工具调用都添加了注释：
```markdown
**参数**: repo_path="." （注意：只使用"."，不要使用占位符路径）
```

## 修改的文件

- ✅ `skills/chat-assistant/prompts/chat_assistant.md`

## 测试验证

重启 CLI 后测试：
```bash
cd backend
python -m cli chat
```

测试命令：
```
用户: 了解下当前项目
```

预期：AI 应该使用 `repo_path="."`，而不是占位符路径。

## 关键点

### 正确的用法 ✅

```python
# 所有需要 repo_path 的工具都应该使用 "."
discover_project_docs(repo_path=".")
get_repo_structure(repo_path=".", annotate=True, max_depth=3)
repo_map(repo_path=".", max_tokens=6000)
```

### 错误的用法 ❌

```python
# 绝对不要使用这些
discover_project_docs(repo_path="/home/user/project")  # ❌ 占位符
discover_project_docs(repo_path="/path/to/project")    # ❌ 占位符
discover_project_docs(repo_path="D:\\daoyouspace\\daoyoucode")  # ❌ 绝对路径
discover_project_docs(repo_path="backend/")  # ❌ 子目录
```

## 为什么只能用 "."

1. **工作目录已设置**: CLI 启动时已经设置了正确的工作目录
2. **路径解析**: 工具会自动解析相对路径
3. **跨平台**: "." 在所有平台上都有效
4. **简单明确**: 不需要猜测或构造路径

## 总结

通过在 prompt 的多个关键位置添加明确的规则和示例，确保 AI 只使用 `repo_path="."`，避免使用占位符路径或绝对路径。

修复完成！✅
