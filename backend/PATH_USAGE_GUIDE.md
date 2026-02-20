# 路径使用指南

## 问题说明

AI 在使用工具时遇到路径错误：
```
⚠️  工具返回错误: Directory not found: config (resolved to D:\daoyouspace\daoyoucode\config)
```

## 原因分析

### 项目结构

```
daoyoucode/                    # 项目根目录
├── backend/                   # 后端代码
│   ├── config/               # ← 配置文件在这里
│   │   ├── llm_config.yaml
│   │   └── ...
│   ├── daoyoucode/
│   └── ...
├── frontend/
├── skills/
└── ...
```

### 工作目录

当你在项目根目录运行时：
```bash
cd D:\daoyouspace\daoyoucode\
daoyoucode chat
```

- **工作目录**: `D:\daoyouspace\daoyoucode\`
- **AI 使用路径**: `config` 
- **解析后路径**: `D:\daoyouspace\daoyoucode\config` ❌
- **正确路径**: `D:\daoyouspace\daoyoucode\backend\config` ✅

## 解决方案

### 方案 1: 使用完整相对路径（推荐）

AI 应该使用从项目根目录开始的完整路径：

```python
# ❌ 错误
list_files(directory="config")

# ✅ 正确
list_files(directory="backend/config")
```

### 方案 2: 在 backend 目录运行

```bash
cd D:\daoyouspace\daoyoucode\backend\
daoyoucode chat
```

这样 `config` 就能正确解析了。

### 方案 3: 使用 --repo 参数

```bash
cd D:\daoyouspace\daoyoucode\
daoyoucode chat --repo backend
```

这会将 `backend` 设置为工作目录。

## 路径规则

### 1. 相对路径

相对路径总是相对于 `repo_path`（工作目录）：

```python
# 如果 repo_path = D:\daoyouspace\daoyoucode\
"backend/config/llm_config.yaml"  # → D:\daoyouspace\daoyoucode\backend\config\llm_config.yaml
"README.md"                        # → D:\daoyouspace\daoyoucode\README.md
```

### 2. 绝对路径

绝对路径直接使用：

```python
"D:/daoyouspace/daoyoucode/backend/config/llm_config.yaml"  # 直接使用
```

### 3. 当前目录

`.` 表示 `repo_path`：

```python
"."  # → D:\daoyouspace\daoyoucode\
```

## 常见场景

### 场景 1: 在项目根目录工作

```bash
# 当前目录
D:\daoyouspace\daoyoucode\

# 正确的路径
backend/config/llm_config.yaml
backend/daoyoucode/agents/core/agent.py
skills/programming/skill.yaml
README.md
```

### 场景 2: 在 backend 目录工作

```bash
# 当前目录
D:\daoyouspace\daoyoucode\backend\

# 正确的路径
config/llm_config.yaml
daoyoucode/agents/core/agent.py
../skills/programming/skill.yaml  # 需要 ../ 返回上级
../README.md
```

### 场景 3: 使用 --repo 参数

```bash
# 在任何目录运行
daoyoucode chat --repo D:\daoyouspace\daoyoucode\backend

# 路径相对于 backend
config/llm_config.yaml
daoyoucode/agents/core/agent.py
```

## AI 使用建议

### 1. 明确工作目录

在开始对话时，AI 应该确认工作目录：

```
当前工作目录: D:\daoyouspace\daoyoucode\
```

### 2. 使用完整路径

总是使用从工作目录开始的完整相对路径：

```python
# ✅ 好
read_file("backend/config/llm_config.yaml")
list_files("backend/config")

# ❌ 不好（假设在项目根目录）
read_file("config/llm_config.yaml")
list_files("config")
```

### 3. 处理路径错误

当遇到 "Directory not found" 错误时：

1. 检查错误信息中的 "resolved to" 路径
2. 确认实际文件位置
3. 调整路径

```
错误: Directory not found: config (resolved to D:\daoyouspace\daoyoucode\config)
分析: 实际路径应该是 D:\daoyouspace\daoyoucode\backend\config
修正: 使用 "backend/config" 而不是 "config"
```

## 工具路径处理

### resolve_path() 的行为

```python
# 假设 repo_path = D:\daoyouspace\daoyoucode\

resolve_path("backend/config")
# → D:\daoyouspace\daoyoucode\backend\config

resolve_path("config")
# → D:\daoyouspace\daoyoucode\config

resolve_path("D:/absolute/path")
# → D:/absolute/path
```

### 路径验证

所有工具都会验证路径是否存在：

```python
if not path.exists():
    return ToolResult(
        success=False,
        error=f"Directory not found: {directory} (resolved to {path})"
    )
```

## 最佳实践

### 1. 项目根目录运行（推荐）

```bash
cd D:\daoyouspace\daoyoucode\
daoyoucode chat
```

**优点**:
- 可以访问所有文件
- 路径清晰明确
- 符合项目结构

**路径示例**:
```
backend/config/llm_config.yaml
backend/daoyoucode/agents/core/agent.py
skills/programming/skill.yaml
README.md
```

### 2. backend 目录运行

```bash
cd D:\daoyouspace\daoyoucode\backend\
daoyoucode chat
```

**优点**:
- 路径更短
- 专注于后端代码

**缺点**:
- 访问 skills 需要 `../skills/`
- 访问根目录文件需要 `../`

**路径示例**:
```
config/llm_config.yaml
daoyoucode/agents/core/agent.py
../skills/programming/skill.yaml
../README.md
```

### 3. 使用 --repo 参数

```bash
daoyoucode chat --repo backend
```

**优点**:
- 灵活指定工作目录
- 不需要 cd

**路径示例**:
```
config/llm_config.yaml
daoyoucode/agents/core/agent.py
```

## 调试技巧

### 1. 查看解析后的路径

错误信息会显示解析后的路径：

```
Directory not found: config (resolved to D:\daoyouspace\daoyoucode\config)
                     ^^^^^^                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                     原始路径                    解析后的路径
```

### 2. 列出当前目录

```python
list_files(directory=".")
```

### 3. 检查文件是否存在

```python
read_file("backend/config/llm_config.yaml")
```

如果文件不存在，会显示解析后的路径。

## 常见错误

### 错误 1: 路径不完整

```python
# ❌ 错误（在项目根目录）
list_files("config")

# ✅ 正确
list_files("backend/config")
```

### 错误 2: 使用绝对路径

```python
# ⚠️ 不推荐（不可移植）
read_file("D:/daoyouspace/daoyoucode/backend/config/llm_config.yaml")

# ✅ 推荐（可移植）
read_file("backend/config/llm_config.yaml")
```

### 错误 3: 混淆工作目录

```python
# 在项目根目录运行
cd D:\daoyouspace\daoyoucode\

# ❌ 错误（假设在 backend 目录）
read_file("config/llm_config.yaml")

# ✅ 正确
read_file("backend/config/llm_config.yaml")
```

## 总结

### 关键点

1. **路径相对于工作目录** - 通常是项目根目录
2. **使用完整相对路径** - 从工作目录开始
3. **检查错误信息** - 查看 "resolved to" 路径
4. **保持一致性** - 统一使用相对路径

### 推荐做法

```bash
# 1. 在项目根目录运行
cd D:\daoyouspace\daoyoucode\
daoyoucode chat

# 2. 使用完整相对路径
backend/config/llm_config.yaml
backend/daoyoucode/agents/core/agent.py
skills/programming/skill.yaml
```

### 快速参考

| 场景 | 工作目录 | 路径示例 |
|------|---------|---------|
| 项目根目录 | `daoyoucode/` | `backend/config/llm_config.yaml` |
| backend 目录 | `daoyoucode/backend/` | `config/llm_config.yaml` |
| 使用 --repo | 指定目录 | 相对于指定目录 |

## 相关文档

- `TOOL_PATH_ISSUE_ANALYSIS.md` - 工具路径问题分析
- `TOOL_PATH_FIX_SUMMARY.md` - 路径修复总结
- `USAGE_GUIDE.md` - 使用指南
