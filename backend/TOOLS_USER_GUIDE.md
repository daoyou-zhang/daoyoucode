# Agent工具使用指南

> **写给开发者的通俗指南**  
> 不懂技术细节？没关系！这份指南用大白话告诉你每个工具是干什么的，什么时候用。

---

## 🎯 快速导航

- [文件操作工具](#文件操作工具) - 读写文件、创建目录
- [搜索工具](#搜索工具) - 在代码中找东西
- [Git工具](#git工具) - 版本控制
- [命令工具](#命令工具) - 运行命令和测试
- [Diff工具](#diff工具) - 精确修改代码
- [RepoMap工具](#repomap工具) - 理解代码结构
- [LSP工具](#lsp工具) - IDE级别的代码智能
- [AST工具](#ast工具) - 结构化代码搜索

---

## 📁 文件操作工具

### 这是干什么的？
就像你在电脑上操作文件一样：打开、保存、删除、创建文件夹。

### 包含哪些工具？

#### 1. read_file - 读取文件
**用途**: 查看文件内容

**例子**:
```python
# 读取配置文件
result = await tool.execute(file_path="config.json")
# 返回: {"port": 3000, "host": "localhost"}
```

**什么时候用**: 
- 需要查看代码内容
- 读取配置文件
- 检查日志文件

---

#### 2. write_file - 写入文件
**用途**: 创建或修改文件

**例子**:
```python
# 创建新文件
result = await tool.execute(
    file_path="src/utils.py",
    content="def hello():\n    print('Hello')"
)
```

**什么时候用**:
- 创建新文件
- 完全重写文件内容
- 保存生成的代码

---

#### 3. list_files - 列出文件
**用途**: 查看目录下有哪些文件

**例子**:
```python
# 列出src目录下的所有Python文件
result = await tool.execute(
    directory="src",
    pattern="*.py",
    recursive=True
)
# 返回: ["src/main.py", "src/utils.py", "src/config.py"]
```

**什么时候用**:
- 了解项目结构
- 查找特定类型的文件
- 统计文件数量

---

#### 4. get_file_info - 获取文件信息
**用途**: 查看文件的详细信息（大小、修改时间等）

**例子**:
```python
result = await tool.execute(file_path="README.md")
# 返回: {"size": 1024, "modified": "2025-02-12", "type": "file"}
```

---

#### 5. create_directory - 创建目录
**用途**: 创建新文件夹

**例子**:
```python
result = await tool.execute(directory="src/components")
```

---

#### 6. delete_file - 删除文件
**用途**: 删除文件或文件夹

**例子**:
```python
result = await tool.execute(file_path="temp.txt")
```

---

## 🔍 搜索工具

### 这是干什么的？
在代码中找东西，就像用Ctrl+F搜索，但更强大。

### 包含哪些工具？

#### 1. text_search - 文本搜索
**用途**: 在文件中搜索文本（简单搜索）

**例子**:
```python
# 搜索所有包含"TODO"的地方
result = await tool.execute(
    query="TODO",
    directory="src"
)
# 返回: 
# src/main.py:10: # TODO: 实现这个功能
# src/utils.py:25: # TODO: 优化性能
```

**什么时候用**:
- 查找TODO注释
- 搜索函数名
- 查找错误信息

---

#### 2. regex_search - 正则搜索
**用途**: 用正则表达式搜索（高级搜索）

**例子**:
```python
# 搜索所有的函数定义
result = await tool.execute(
    pattern=r"def \w+\(",
    directory="src"
)
# 返回:
# src/main.py:5: def main():
# src/utils.py:10: def calculate():
```

**什么时候用**:
- 搜索特定模式的代码
- 查找所有函数/类定义
- 复杂的搜索需求

---

## 🌿 Git工具

### 这是干什么的？
版本控制，查看代码改动、提交代码等。

### 包含哪些工具？

#### 1. git_status - 查看状态
**用途**: 查看哪些文件被修改了

**例子**:
```python
result = await tool.execute(repo_path=".")
# 返回:
# Modified: src/main.py
# Added: src/new_feature.py
# Deleted: src/old_code.py
```

---

#### 2. git_diff - 查看改动
**用途**: 查看文件具体改了什么

**例子**:
```python
result = await tool.execute(
    repo_path=".",
    file_path="src/main.py"
)
# 返回:
# - old_function()
# + new_function()
```

---

#### 3. git_commit - 提交代码
**用途**: 保存代码改动

**例子**:
```python
result = await tool.execute(
    repo_path=".",
    message="修复了登录bug"
)
```

---

#### 4. git_log - 查看历史
**用途**: 查看提交历史

**例子**:
```python
result = await tool.execute(repo_path=".", max_count=5)
# 返回最近5次提交
```

---

## ⚙️ 命令工具

### 这是干什么的？
在终端运行命令，就像你在命令行里输入命令一样。

### 包含哪些工具？

#### 1. run_command - 运行命令
**用途**: 执行任意shell命令

**例子**:
```python
# 安装依赖
result = await tool.execute(command="pip install requests")

# 查看Python版本
result = await tool.execute(command="python --version")
```

**什么时候用**:
- 安装包
- 运行脚本
- 执行系统命令

---

#### 2. run_test - 运行测试
**用途**: 运行测试用例

**例子**:
```python
# 运行pytest测试
result = await tool.execute(
    test_path="tests/",
    framework="pytest"
)
# 返回: 10 passed, 2 failed
```

**什么时候用**:
- 验证代码是否正确
- 运行单元测试
- 检查测试覆盖率

---

## ✏️ Diff工具

### 这是干什么的？
**精确修改代码**，不是整个文件重写，而是只改需要改的部分。

### 为什么需要它？
假设你有一个1000行的文件，只想改其中3行。如果用write_file，需要重写整个文件（容易出错）。用Diff工具，只需要指定要改的部分。

### 工具：search_replace

**用途**: 搜索并替换代码片段

**例子**:
```python
# 把所有的console.log改成logger.info
result = await tool.execute(
    file_path="src/app.js",
    search='console.log("Starting")',
    replace='logger.info("Starting")'
)
```

**什么时候用**:
- 重构代码（改函数名、变量名）
- 修复bug（改错误的代码）
- 更新API调用

**为什么强大**:
- 9种匹配策略（模糊匹配、精确匹配等）
- 自动处理缩进和空格
- 智能找到最相似的代码

---

## 🗺️ RepoMap工具

### 这是干什么的？
**理解代码结构**，告诉你项目里有哪些重要的函数、类，它们之间的关系。

### 为什么需要它？
想象你接手一个陌生项目，有100个文件，你不知道从哪看起。RepoMap会告诉你："这个项目最重要的是这5个文件，它们之间是这样调用的"。

### 包含哪些工具？

#### 1. repo_map - 代码地图
**用途**: 生成项目的代码地图

**例子**:
```python
result = await tool.execute(
    repo_path=".",
    mentioned_idents=["login", "authenticate"]
)
# 返回:
# src/auth.py:
#   class AuthManager:
#     def login(user, password)  # 被main.py调用
#     def authenticate(token)    # 被api.py调用
# 
# src/main.py:
#   def main():
#     auth = AuthManager()
#     auth.login(...)
```

**什么时候用**:
- 理解陌生项目
- 查找函数在哪里被调用
- 了解代码依赖关系

**为什么智能**:
- 使用PageRank算法排序（像Google搜索一样）
- 只显示最重要的代码
- 自动识别函数调用关系

---

#### 2. get_repo_structure - 目录结构
**用途**: 查看项目的文件夹结构

**例子**:
```python
result = await tool.execute(repo_path=".")
# 返回:
# src/
#   ├── main.py
#   ├── utils.py
#   └── components/
#       ├── button.py
#       └── input.py
```

**什么时候用**:
- 了解项目组织方式
- 查找文件位置
- 规划新功能放在哪里

---

## 🧠 LSP工具

### 这是干什么的？
**IDE级别的代码智能**，就像VSCode、PyCharm那样的智能提示、跳转定义、查找引用。

### 为什么需要它？
你在IDE里可以：
- 点击函数名跳转到定义
- 查看哪里调用了这个函数
- 看到代码错误的红色波浪线

LSP工具让Agent也能做这些事！

### 包含哪些工具？

#### 1. lsp_diagnostics - 诊断错误
**用途**: 查找代码中的错误和警告

**例子**:
```python
result = await tool.execute(file_path="src/main.py")
# 返回:
# Error (line 10): Undefined variable 'x'
# Warning (line 25): Unused import 'os'
```

**什么时候用**:
- 检查代码错误
- 查看警告信息
- 代码质量检查

**就像**: VSCode里的红色波浪线

---

#### 2. lsp_goto_definition - 跳转定义
**用途**: 查找函数/类的定义位置

**例子**:
```python
# 在main.py第10行，有个calculate()函数调用
# 想知道这个函数在哪里定义的
result = await tool.execute(
    file_path="src/main.py",
    line=10,
    character=5
)
# 返回: src/utils.py:25 (定义在utils.py的第25行)
```

**什么时候用**:
- 查找函数定义
- 了解类的实现
- 追踪代码流程

**就像**: 在IDE里按F12跳转

---

#### 3. lsp_find_references - 查找引用
**用途**: 查找函数/变量在哪里被使用

**例子**:
```python
# 想知道calculate()函数在哪些地方被调用
result = await tool.execute(
    file_path="src/utils.py",
    line=25,
    character=5
)
# 返回:
# src/main.py:10
# src/api.py:45
# tests/test_utils.py:15
```

**什么时候用**:
- 重构前检查影响范围
- 查找函数的所有调用点
- 了解代码使用情况

**就像**: 在IDE里右键"查找所有引用"

---

#### 4. lsp_symbols - 符号搜索
**用途**: 搜索文件中的所有函数、类、变量

**例子**:
```python
result = await tool.execute(file_path="src/main.py")
# 返回:
# Functions: main, calculate, format_output
# Classes: Application, Config
# Variables: VERSION, DEBUG
```

**什么时候用**:
- 快速了解文件内容
- 查找特定函数
- 生成代码大纲

**就像**: IDE的"文件结构"视图

---

#### 5. lsp_rename - 重命名
**用途**: 安全地重命名函数/变量（自动更新所有引用）

**例子**:
```python
# 把calculate改名为compute
result = await tool.execute(
    file_path="src/utils.py",
    line=25,
    character=5,
    new_name="compute"
)
# 自动更新:
# - src/utils.py: def compute(...)
# - src/main.py: result = compute(...)
# - src/api.py: value = compute(...)
```

**什么时候用**:
- 重构代码
- 改进命名
- 统一代码风格

**为什么安全**: 自动更新所有使用的地方，不会漏掉

---

#### 6. lsp_code_actions - 代码操作
**用途**: 获取代码修复建议

**例子**:
```python
result = await tool.execute(
    file_path="src/main.py",
    line=10,
    character=5
)
# 返回建议:
# - Add import 'os'
# - Remove unused variable
# - Convert to f-string
```

**什么时候用**:
- 修复代码错误
- 优化代码
- 应用最佳实践

**就像**: IDE的"快速修复"（💡灯泡图标）

---

## 🌳 AST工具

### 这是干什么的？
**结构化代码搜索**，不是简单的文本搜索，而是理解代码结构的搜索。

### 为什么需要它？

**问题**: 用文本搜索"console.log"，会找到：
- 实际的代码: `console.log("hello")`
- 注释里的: `// 使用console.log打印`
- 字符串里的: `"请使用console.log"`
- 变量名: `const console_log = ...`

**AST搜索**: 只找实际的代码，忽略注释、字符串、变量名。

### 什么是AST？
AST = Abstract Syntax Tree（抽象语法树）

简单理解：代码的结构化表示。

```python
# 代码
def hello():
    print("Hi")

# AST理解为
FunctionDef(
    name="hello",
    body=[
        Call(func="print", args=["Hi"])
    ]
)
```

### 包含哪些工具？

#### 1. ast_grep_search - AST搜索
**用途**: 用代码结构搜索代码

**例子1: 搜索所有函数定义**
```python
result = await tool.execute(
    pattern="def $FUNC($$):",
    lang="python",
    paths=["src"]
)
# 只找函数定义，不找注释里的"def"
```

**例子2: 搜索所有console.log**
```python
result = await tool.execute(
    pattern="console.log($MSG)",
    lang="javascript",
    paths=["src"]
)
# 只找实际调用，不找注释和字符串
```

**元变量**:
- `$VAR`: 匹配任意单个东西（变量、表达式等）
- `$$`: 匹配任意多个东西（参数列表等）

**什么时候用**:
- 查找特定模式的代码
- 代码审查（找不安全的代码）
- 统计代码指标

**支持语言**: 25种（Python、JavaScript、TypeScript、Java、Go等）

---

#### 2. ast_grep_replace - AST替换
**用途**: 用代码结构替换代码

**例子: 把所有console.log改成logger.info**
```python
# 预览（不实际修改）
result = await tool.execute(
    pattern="console.log($MSG)",
    rewrite="logger.info($MSG)",
    lang="javascript",
    dry_run=True
)
# 显示会改哪些地方

# 实际应用
result = await tool.execute(
    pattern="console.log($MSG)",
    rewrite="logger.info($MSG)",
    lang="javascript",
    dry_run=False
)
# 真的修改文件
```

**什么时候用**:
- 大规模重构
- 升级API（旧API改成新API）
- 统一代码风格

**为什么强大**:
- 保留原有的参数（用$MSG）
- 只改匹配的代码，不改注释
- 支持预览（dry-run）

---

## 🎯 工具选择指南

### 我想读写文件 → 文件操作工具
- 查看内容: `read_file`
- 创建/修改: `write_file`
- 列出文件: `list_files`

### 我想搜索代码 → 看情况
- 简单搜索文本: `text_search`
- 复杂模式搜索: `regex_search`
- 结构化搜索: `ast_grep_search` ⭐

### 我想修改代码 → 看情况
- 整个文件重写: `write_file`
- 精确修改几行: `search_replace` ⭐
- 大规模重构: `ast_grep_replace` ⭐

### 我想理解项目 → RepoMap工具
- 代码地图: `repo_map` ⭐
- 目录结构: `get_repo_structure`

### 我想IDE功能 → LSP工具
- 查错误: `lsp_diagnostics`
- 跳转定义: `lsp_goto_definition`
- 查引用: `lsp_find_references`
- 重命名: `lsp_rename` ⭐

### 我想版本控制 → Git工具
- 查状态: `git_status`
- 查改动: `git_diff`
- 提交: `git_commit`

### 我想运行命令 → 命令工具
- 任意命令: `run_command`
- 运行测试: `run_test`

---

## 💡 实战场景

### 场景1: 修复一个Bug

1. **查找bug位置**
   ```python
   # 搜索错误信息
   await text_search.execute(query="NullPointerException")
   ```

2. **查看代码**
   ```python
   await read_file.execute(file_path="src/main.py")
   ```

3. **检查错误**
   ```python
   await lsp_diagnostics.execute(file_path="src/main.py")
   ```

4. **修复代码**
   ```python
   await search_replace.execute(
       file_path="src/main.py",
       search="user.name",
       replace="user.name if user else None"
   )
   ```

5. **运行测试**
   ```python
   await run_test.execute(test_path="tests/")
   ```

---

### 场景2: 重构代码

1. **查找所有调用**
   ```python
   await lsp_find_references.execute(
       file_path="src/utils.py",
       line=10,
       character=5
   )
   ```

2. **安全重命名**
   ```python
   await lsp_rename.execute(
       file_path="src/utils.py",
       line=10,
       character=5,
       new_name="calculate_total"
   )
   ```

3. **检查改动**
   ```python
   await git_diff.execute(repo_path=".")
   ```

4. **提交代码**
   ```python
   await git_commit.execute(
       repo_path=".",
       message="重构: 重命名calculate为calculate_total"
   )
   ```

---

### 场景3: 理解新项目

1. **查看目录结构**
   ```python
   await get_repo_structure.execute(repo_path=".")
   ```

2. **生成代码地图**
   ```python
   await repo_map.execute(
       repo_path=".",
       mentioned_idents=["main", "start"]
   )
   ```

3. **查看主要文件**
   ```python
   await read_file.execute(file_path="src/main.py")
   ```

4. **查看文件结构**
   ```python
   await lsp_symbols.execute(file_path="src/main.py")
   ```

---

## 🚀 进阶技巧

### 技巧1: 组合使用工具

```python
# 1. 先搜索
matches = await text_search.execute(query="TODO")

# 2. 对每个匹配，查看详细信息
for match in matches:
    content = await read_file.execute(file_path=match.file)
    
# 3. 修改代码
await search_replace.execute(...)

# 4. 运行测试验证
await run_test.execute(test_path="tests/")
```

### 技巧2: 使用RepoMap理解代码

```python
# 先看整体结构
structure = await get_repo_structure.execute(repo_path=".")

# 再看代码地图（关注登录功能）
repo_map = await repo_map.execute(
    repo_path=".",
    mentioned_idents=["login", "authenticate", "session"]
)

# 最后查看具体文件
code = await read_file.execute(file_path="src/auth.py")
```

### 技巧3: 使用AST工具重构

```python
# 1. 先搜索看影响范围
matches = await ast_grep_search.execute(
    pattern="console.log($MSG)",
    lang="javascript"
)

# 2. 预览替换
preview = await ast_grep_replace.execute(
    pattern="console.log($MSG)",
    rewrite="logger.info($MSG)",
    lang="javascript",
    dry_run=True
)

# 3. 确认后应用
result = await ast_grep_replace.execute(
    pattern="console.log($MSG)",
    rewrite="logger.info($MSG)",
    lang="javascript",
    dry_run=False
)
```

---

## 📚 总结

### 核心工具（最常用）⭐

1. **read_file** - 查看代码
2. **search_replace** - 精确修改代码
3. **repo_map** - 理解项目结构
4. **lsp_diagnostics** - 检查错误
5. **ast_grep_search** - 结构化搜索

### 高级工具（强大但复杂）

1. **lsp_rename** - 安全重命名
2. **ast_grep_replace** - 大规模重构
3. **lsp_find_references** - 查找引用

### 辅助工具（简单实用）

1. **text_search** - 简单搜索
2. **git_status** - 查看改动
3. **run_test** - 运行测试

---

<div align="center">

**🎉 现在你知道每个工具是干什么的了！**

记住：工具只是手段，目标是写出更好的代码。

有问题？查看详细文档：
- [工具系统完整文档](TOOLS_SYSTEM_COMPLETE.md)
- [LSP工具详解](LSP_TOOLS_COMPLETE.md)
- [AST工具详解](AST_TOOLS_COMPLETE.md)

</div>
