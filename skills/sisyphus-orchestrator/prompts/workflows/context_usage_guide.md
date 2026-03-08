# Context 变量使用指南

## 什么是 Context 变量？

Context 变量是系统自动维护的上下文信息，用于在多步骤工作流中保持状态。

## 核心 Context 变量

### 1. target_file（主目标文件）

**用途**：当前要操作的主文件

**设置时机**：首次搜索时自动设置

**特点**：
- ✅ 只在首次搜索时设置
- ✅ 后续搜索不会覆盖
- ✅ 可以手动设置

**使用场景**：
```
# 场景：搜索 → 读取 → 修改
1. text_search("agent.py")
   → 自动设置 target_file = "backend/daoyoucode/agents/core/agent.py"

2. read_file(path="{{target_file}}")
   → 读取 agent.py

3. text_search("config.yaml")  # 搜索其他文件
   → target_file 保持不变（仍然是 agent.py）

4. write_file(path="{{target_file}}", content="...")
   → 修改 agent.py（正确的文件）
```

**访问方式**：
- 在工具参数中：`{{target_file}}`
- 在 Python 中：`context.get("target_file")`

### 2. target_files（多文件列表）

**用途**：首次搜索返回多个文件时保存所有文件

**设置时机**：首次搜索返回 > 1 个文件时

**特点**：
- ✅ 保存所有文件路径
- ✅ 不会被后续搜索覆盖

**使用场景**：
```
# 场景：批量操作多个文件
1. text_search("test_*.py")
   → target_file = "tests/test_agent.py"（第一个）
   → target_files = ["tests/test_agent.py", "tests/test_tools.py", ...]

2. 批量读取所有测试文件
   for file in {{target_files}}:
       read_file(path=file)
```

### 3. target_dir / target_dirs（目录）

**用途**：目标文件所在的目录

**设置时机**：与 target_file 同时设置

**特点**：
- ✅ 自动从文件路径提取
- ✅ 不会被后续搜索覆盖

**使用场景**：
```
# 场景：在同一目录下创建新文件
1. text_search("agent.py")
   → target_file = "backend/daoyoucode/agents/core/agent.py"
   → target_dir = "backend/daoyoucode/agents/core"

2. 在同一目录创建新文件
   write_file(path="{{target_dir}}/new_agent.py", content="...")
```

### 4. last_search_paths（最新搜索结果）

**用途**：最近一次搜索的结果

**设置时机**：每次搜索都更新

**特点**：
- ✅ 总是更新为最新搜索
- ✅ 可以访问最新搜索结果

**使用场景**：
```
# 场景：使用最新搜索的文件
1. text_search("agent.py")
   → last_search_paths = ["backend/daoyoucode/agents/core/agent.py"]

2. text_search("config.yaml")
   → last_search_paths = ["backend/daoyoucode/config.yaml"]（更新）

3. 读取最新搜索的文件
   read_file(path="{{last_search_paths[0]}}")
   → 读取 config.yaml
```

### 5. search_history（搜索历史）

**用途**：所有搜索操作的历史记录

**设置时机**：每次搜索都追加

**特点**：
- ✅ 记录所有搜索
- ✅ 只追加，不覆盖
- ✅ 可以回溯查找

**使用场景**：
```
# 场景：回溯查找之前的搜索
1. text_search("agent.py")
2. text_search("config.yaml")
3. text_search("base.py")

# 访问搜索历史
search_history = context.get("search_history")
# [
#   {"tool": "text_search", "paths": ["agent.py"], "timestamp": "..."},
#   {"tool": "text_search", "paths": ["config.yaml"], "timestamp": "..."},
#   {"tool": "text_search", "paths": ["base.py"], "timestamp": "..."}
# ]

# 获取第一次搜索的文件
first_file = search_history[0]["paths"][0]
```

## 使用原则

### 1. 优先使用 target_file

在多步骤工作流中，优先使用 `target_file` 而不是重复搜索：

❌ **不推荐**：
```
1. text_search("agent.py")
2. read_file(path="backend/daoyoucode/agents/core/agent.py")  # 硬编码路径
3. write_file(path="backend/daoyoucode/agents/core/agent.py", content="...")  # 重复路径
```

✅ **推荐**：
```
1. text_search("agent.py")
   → 自动设置 target_file
2. read_file(path="{{target_file}}")
3. write_file(path="{{target_file}}", content="...")
```

### 2. 明确区分目标文件和参考文件

如果需要操作多个文件，明确哪个是目标文件：

✅ **推荐**：
```
# 场景：修改 agent.py，参考 config.yaml

1. text_search("agent.py")
   → target_file = "agent.py"（要修改的文件）

2. read_file(path="{{target_file}}")
   → 读取 agent.py

3. text_search("config.yaml")
   → target_file 保持不变
   → last_search_paths = ["config.yaml"]

4. read_file(path="{{last_search_paths[0]}}")
   → 读取 config.yaml（参考文件）

5. write_file(path="{{target_file}}", content="...")
   → 修改 agent.py（正确的文件）
```

### 3. 手动设置 target_file

如果需要明确指定目标文件，可以手动设置：

```python
# 在工作流中明确指定
context.set("target_file", "backend/daoyoucode/agents/core/agent.py")

# 后续搜索不会覆盖
text_search("other_file.py")
# target_file 仍然是 agent.py
```

### 4. 使用搜索历史回溯

如果需要访问之前的搜索结果：

```python
# 获取搜索历史
history = context.get("search_history")

# 获取第一次搜索的文件
first_file = history[0]["paths"][0]

# 获取最后一次搜索的文件
last_file = history[-1]["paths"][0]

# 获取所有搜索的文件
all_files = [entry["paths"][0] for entry in history]
```

## 工作流模式

### 模式1：单文件操作

```
目标：搜索 → 读取 → 修改

步骤：
1. text_search("target_file.py")
   → 自动设置 target_file

2. read_file(path="{{target_file}}")
   → 读取目标文件

3. write_file(path="{{target_file}}", content="...")
   → 修改目标文件

优势：
- 路径自动管理
- 不会修改错误的文件
```

### 模式2：多文件操作

```
目标：搜索多个文件 → 批量处理

步骤：
1. text_search("test_*.py")
   → target_file = 第一个文件
   → target_files = 所有文件

2. 批量读取
   for file in {{target_files}}:
       read_file(path=file)

3. 批量修改
   for file in {{target_files}}:
       write_file(path=file, content="...")

优势：
- 一次搜索，多次使用
- 不会遗漏文件
```

### 模式3：目标文件 + 参考文件

```
目标：修改目标文件，参考其他文件

步骤：
1. text_search("target.py")
   → target_file = "target.py"

2. read_file(path="{{target_file}}")
   → 读取目标文件

3. text_search("reference.py")
   → target_file 保持不变
   → last_search_paths = ["reference.py"]

4. read_file(path="{{last_search_paths[0]}}")
   → 读取参考文件

5. write_file(path="{{target_file}}", content="...")
   → 修改目标文件（正确）

优势：
- 目标文件不会被覆盖
- 可以参考多个文件
```

### 模式4：回溯历史

```
目标：访问之前搜索的文件

步骤：
1. text_search("file1.py")
2. text_search("file2.py")
3. text_search("file3.py")

4. 访问第一次搜索的文件
   history = context.get("search_history")
   first_file = history[0]["paths"][0]
   read_file(path=first_file)

优势：
- 可以回溯任何搜索
- 不会丢失信息
```

## 常见问题

### Q1: target_file 什么时候设置？

A: 首次执行搜索工具（text_search、regex_search、repo_map）时自动设置。

### Q2: 如何避免 target_file 被覆盖？

A: 系统已经自动处理，后续搜索不会覆盖 target_file。如果需要明确指定，可以手动设置。

### Q3: 如何访问最新搜索的文件？

A: 使用 `last_search_paths` 变量，它总是更新为最新搜索结果。

### Q4: 如何访问之前搜索的文件？

A: 使用 `search_history` 变量，它记录了所有搜索历史。

### Q5: 多文件搜索时，target_file 是哪个？

A: target_file 是第一个文件，所有文件保存在 target_files 中。

## 最佳实践

### ✅ 推荐做法

1. **使用 Context 变量代替硬编码路径**
   ```
   ✅ write_file(path="{{target_file}}", content="...")
   ❌ write_file(path="backend/daoyoucode/agents/core/agent.py", content="...")
   ```

2. **明确区分目标文件和参考文件**
   ```
   ✅ target_file 用于要修改的文件
   ✅ last_search_paths 用于参考文件
   ```

3. **利用搜索历史回溯**
   ```
   ✅ 从 search_history 中获取之前的搜索结果
   ```

4. **手动设置明确目标**
   ```
   ✅ 如果需要明确指定目标文件，手动设置 target_file
   ```

### ❌ 避免的错误

1. **不要假设 target_file 会被覆盖**
   ```
   ❌ 担心后续搜索会覆盖 target_file
   ✅ 系统已经自动保护，不会覆盖
   ```

2. **不要重复硬编码路径**
   ```
   ❌ 在多个步骤中重复写同一个路径
   ✅ 使用 target_file 变量
   ```

3. **不要忽略 last_search_paths**
   ```
   ❌ 再次搜索同一个文件
   ✅ 使用 last_search_paths 访问最新搜索
   ```

## 总结

Context 变量让工作流更加智能和可靠：

- ✅ 自动管理路径，减少错误
- ✅ 保持目标文件稳定，不会被覆盖
- ✅ 记录搜索历史，可以回溯
- ✅ 支持多文件操作
- ✅ 简化工作流编写

**核心原则**：让系统自动管理路径，专注于业务逻辑！
