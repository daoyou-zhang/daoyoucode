# 工作流 Context 集成总结

## 完成的工作

### 1. 创建 Context 使用指南 ✅

**文件**: `skills/sisyphus-orchestrator/prompts/workflows/context_usage_guide.md`

**内容**:
- Context 变量说明（target_file, target_files, target_dir, last_search_paths, search_history）
- 使用原则和最佳实践
- 4 种工作流模式
- 常见问题解答
- 完整的使用示例

### 2. 更新主要工作流 ✅

已更新的工作流：

1. **refactor_code.md** - 代码重构工作流
   - 添加 Context 使用指南链接
   - 添加 Context 变量说明
   - 添加使用示例

2. **write_code.md** - 编写代码工作流
   - 添加 Context 使用指南链接
   - 添加 Context 变量说明
   - 添加使用示例

3. **search_code.md** - 搜索代码工作流
   - 添加 Context 使用指南链接
   - 说明搜索结果如何自动保存
   - 添加使用示例

4. **analyze_code.md** - 代码分析工作流
   - 添加 Context 使用指南链接
   - 说明如何使用 Context 简化分析
   - 添加使用示例

## Context 变量说明

### 核心变量

| 变量名 | 用途 | 设置时机 | 是否覆盖 |
|--------|------|----------|----------|
| `target_file` | 主目标文件 | 首次搜索 | ❌ 不覆盖 |
| `target_files` | 多文件列表 | 首次搜索(多文件) | ❌ 不覆盖 |
| `target_dir` | 目标目录 | 首次搜索 | ❌ 不覆盖 |
| `target_dirs` | 多目录列表 | 首次搜索(多文件) | ❌ 不覆盖 |
| `last_search_paths` | 最新搜索结果 | 每次搜索 | ✅ 总是更新 |
| `search_history` | 搜索历史 | 每次搜索 | ❌ 只追加 |

### 使用场景

#### 场景1：单文件操作
```
1. text_search("agent.py")
   → target_file = "agent.py"

2. read_file(path="{{target_file}}")
3. write_file(path="{{target_file}}", content="...")
```

#### 场景2：多文件操作
```
1. text_search("test_*.py")
   → target_file = 第一个文件
   → target_files = 所有文件

2. for file in {{target_files}}:
       read_file(path=file)
```

#### 场景3：目标文件 + 参考文件
```
1. text_search("target.py")
   → target_file = "target.py"

2. text_search("reference.py")
   → target_file 保持不变
   → last_search_paths = ["reference.py"]

3. read_file(path="{{target_file}}")  # 读取目标
4. read_file(path="{{last_search_paths[0]}}")  # 读取参考
5. write_file(path="{{target_file}}", content="...")  # 修改目标
```

#### 场景4：回溯历史
```
1. 执行多次搜索
2. history = context.get("search_history")
3. first_file = history[0]["paths"][0]  # 第一次搜索
4. last_file = history[-1]["paths"][0]  # 最后一次搜索
```

## 优势

### 1. 自动路径管理 ✅
- 不需要手动记录路径
- 不需要硬编码路径
- 减少路径错误

### 2. 目标文件保护 ✅
- target_file 只在首次设置
- 后续搜索不会覆盖
- 避免修改错误的文件

### 3. 搜索历史记录 ✅
- 记录所有搜索操作
- 可以回溯查找
- 不会丢失信息

### 4. 多文件支持 ✅
- 自动保存所有文件
- 支持批量操作
- 不会遗漏文件

### 5. 简化工作流 ✅
- 减少重复代码
- 提高可读性
- 降低出错概率

## 工作流模式

### 模式1：搜索 → 读取 → 修改

```markdown
## 步骤1：搜索目标文件
text_search("target_file.py")
→ 自动设置 target_file

## 步骤2：读取文件
read_file(path="{{target_file}}")

## 步骤3：修改文件
write_file(path="{{target_file}}", content="...")
```

### 模式2：搜索 → 读取 → 搜索 → 修改

```markdown
## 步骤1：搜索目标文件
text_search("target.py")
→ target_file = "target.py"

## 步骤2：读取目标文件
read_file(path="{{target_file}}")

## 步骤3：搜索参考文件
text_search("reference.py")
→ target_file 保持不变
→ last_search_paths = ["reference.py"]

## 步骤4：读取参考文件
read_file(path="{{last_search_paths[0]}}")

## 步骤5：修改目标文件
write_file(path="{{target_file}}", content="...")
```

### 模式3：批量操作

```markdown
## 步骤1：搜索多个文件
text_search("test_*.py")
→ target_files = [所有测试文件]

## 步骤2：批量处理
for file in {{target_files}}:
    read_file(path=file)
    # 处理文件
    write_file(path=file, content="...")
```

## 最佳实践

### ✅ 推荐做法

1. **使用 Context 变量代替硬编码**
   ```
   ✅ write_file(path="{{target_file}}", content="...")
   ❌ write_file(path="backend/daoyoucode/agents/core/agent.py", content="...")
   ```

2. **明确区分目标和参考**
   ```
   ✅ target_file 用于要修改的文件
   ✅ last_search_paths 用于参考文件
   ```

3. **利用搜索历史**
   ```
   ✅ 从 search_history 中获取之前的搜索
   ```

4. **手动设置明确目标**
   ```
   ✅ 如果需要明确指定，手动设置 target_file
   ```

### ❌ 避免的错误

1. **不要假设会被覆盖**
   ```
   ❌ 担心 target_file 会被覆盖
   ✅ 系统已经自动保护
   ```

2. **不要重复硬编码**
   ```
   ❌ 在多个步骤中重复写路径
   ✅ 使用 Context 变量
   ```

3. **不要忽略 last_search_paths**
   ```
   ❌ 再次搜索同一个文件
   ✅ 使用 last_search_paths
   ```

## 工作流更新清单

### 已更新 ✅

- [x] context_usage_guide.md - Context 使用指南（新建）
- [x] refactor_code.md - 添加 Context 说明
- [x] write_code.md - 添加 Context 说明
- [x] search_code.md - 添加 Context 说明
- [x] analyze_code.md - 添加 Context 说明

### 可选更新

其他工作流也可以添加 Context 说明，但不是必须的：

- [ ] debug_code.md
- [ ] run_test.md
- [ ] write_test.md
- [ ] understand_project.md
- [ ] find_unused_code.md
- [ ] find_hardcoded_config.md

这些工作流可以根据需要逐步添加 Context 支持。

## 使用示例

### 示例1：重构 agent.py

```
用户："重构 agent.py 中的 execute 方法"

工作流：
1. text_search("agent.py")
   → target_file = "backend/daoyoucode/agents/core/agent.py"

2. read_file(path="{{target_file}}")
   → 读取 agent.py

3. get_file_symbols(path="{{target_file}}")
   → 获取文件结构

4. text_search("context.py")  # 查找参考
   → target_file 保持不变
   → last_search_paths = ["context.py"]

5. read_file(path="{{last_search_paths[0]}}")
   → 读取参考文件

6. write_file(path="{{target_file}}", content="...")
   → 修改 agent.py（正确的文件）
```

### 示例2：批量修改测试文件

```
用户："给所有测试文件添加 docstring"

工作流：
1. text_search("test_*.py")
   → target_files = [所有测试文件]

2. for file in {{target_files}}:
       read_file(path=file)
       # 添加 docstring
       write_file(path=file, content="...")
```

### 示例3：分析多个文件

```
用户："分析 agent.py 和 context.py 的关系"

工作流：
1. text_search("agent.py")
   → target_file = "agent.py"

2. read_file(path="{{target_file}}")
   → 分析 agent.py

3. text_search("context.py")
   → target_file 保持不变
   → last_search_paths = ["context.py"]

4. read_file(path="{{last_search_paths[0]}}")
   → 分析 context.py

5. 总结两个文件的关系
```

## 下一步

### 1. 测试工作流 🔄

在实际场景中测试更新后的工作流：
- 重构代码任务
- 编写代码任务
- 搜索代码任务
- 分析代码任务

### 2. 收集反馈 📝

观察 Context 变量的使用情况：
- 是否正确设置？
- 是否正确使用？
- 是否有遗漏的场景？

### 3. 持续优化 🎯

根据反馈优化：
- 更新工作流说明
- 添加更多示例
- 完善最佳实践

### 4. 扩展到其他工作流 📚

将 Context 支持扩展到其他工作流：
- debug_code.md
- run_test.md
- write_test.md
- 等等

## 总结

Context 集成让工作流更加智能和可靠：

- ✅ 自动管理路径，减少错误
- ✅ 保持目标文件稳定
- ✅ 记录搜索历史
- ✅ 支持多文件操作
- ✅ 简化工作流编写

**核心原则**：让系统自动管理路径，专注于业务逻辑！

---

**完成时间**: 2024-01-01  
**更新文件**: 5 个工作流 + 1 个使用指南  
**状态**: ✅ 完成
