# 道友code代码还原机制说明

## 道友code的三种还原机制

道友code（daoyoucode）作为AI编程助手，提供了多层次的代码还原机制：

### 1. 工作流回滚机制 ✅ （已实现）

**位置**: `backend/daoyoucode/agents/orchestrators/workflow.py`

**功能**: 
- 自动记录每个执行步骤
- 失败时自动逆序回滚
- 支持配置回滚Agent

**使用方式**:

```yaml
# skills/xxx/skill.yaml
workflow:
  - name: step1
    agent: code_agent
    rollback: cleanup_agent  # 配置回滚Agent
  
  - name: step2
    agent: test_agent
    rollback: restore_agent
```

**工作原理**:

```python
# 1. 执行步骤时记录
executed_steps.append((step, step_result))

# 2. 失败时自动回滚
if not step_result.get('success'):
    await self._rollback_steps(executed_steps, context)

# 3. 逆序执行回滚Agent
for step, result in reversed(executed_steps):
    rollback_agent = step.get('rollback')
    await agent.execute(rollback_input)
```

**优点**:
- ✅ 自动化
- ✅ 支持多步骤回滚
- ✅ 可配置回滚策略

**限制**:
- ⚠️ 需要预先配置回滚Agent
- ⚠️ 只在工作流模式下可用

---

### 2. Git集成机制 ✅ （已配置）

**位置**: `.daoyou.conf.yml`

**配置**:

```yaml
git:
  auto_commit: false        # 编辑完成后自动commit
  attribute_author: true    # 使用当前用户名
  push_after_commit: false  # 自动push
```

**使用方式**:

```bash
# 方式1: 启用自动commit
# 修改 .daoyou.conf.yml:
git:
  auto_commit: true

# 方式2: 手动Git操作
git log                    # 查看历史
git diff                   # 查看修改
git reset --hard HEAD      # 还原到上次commit
git reset --hard <commit>  # 还原到指定commit
```

**优点**:
- ✅ 完整的版本控制
- ✅ 可以还原到任意历史版本
- ✅ 支持分支实验

**推荐配置**:

```yaml
git:
  auto_commit: true         # 开启自动commit
  attribute_author: true
  push_after_commit: false  # 不自动push（本地实验）
```

---

### 3. 历史记录机制 ✅ （已配置）

**位置**: `.daoyou.chat.history.md`

**配置**:

```yaml
history:
  enabled: true
  file: ".daoyou.chat.history.md"
  restore: false  # 启动时是否自动载入
```

**功能**:
- 记录所有对话历史
- 记录代码修改内容
- 支持历史回放

**使用方式**:

```bash
# 查看历史
cat .daoyou.chat.history.md

# 基于历史还原
# 在对话中说：
"帮我还原到上一个版本"
"撤销刚才的修改"
"恢复到修改前的状态"
```

**优点**:
- ✅ 完整的对话上下文
- ✅ 可以精确描述要还原什么
- ✅ 支持部分还原

---

### 4. 备份目录机制 ⚠️ （目录存在但未使用）

**位置**: `.daoyou.backups/history/`

**状态**: 目录已创建但为空

**潜在用途**:
- 可以用于存储文件备份
- 可以用于存储快照

**建议**: 可以扩展这个机制

---

## 推荐的还原策略

### 策略1: Git + 对话结合（最推荐）⭐⭐⭐⭐⭐

```yaml
# 1. 配置自动commit
git:
  auto_commit: true
  push_after_commit: false

# 2. 配置历史记录
history:
  enabled: true
  restore: true  # 启动时载入历史
```

**工作流程**:

```bash
# 1. 道友code修改代码（自动commit）
daoyou "帮我添加XXX功能"
# → 自动commit: "添加XXX功能"

# 2. 测试
pytest

# 3a. 如果成功，继续
daoyou "继续优化"

# 3b. 如果失败，还原
# 方式1: 对话还原
daoyou "刚才的修改有问题，帮我还原"

# 方式2: Git还原
git reset --hard HEAD^

# 方式3: 查看历史后精确还原
git log --oneline
git reset --hard <commit-hash>
```

---

### 策略2: 工作流回滚（适合复杂任务）⭐⭐⭐⭐

**适用场景**: 多步骤的复杂任务

**配置**:

```yaml
# skills/complex-task/skill.yaml
name: complex-task
workflow:
  - name: analyze
    agent: analyzer
    rollback: null  # 分析步骤不需要回滚
  
  - name: modify_code
    agent: coder
    rollback: restore_code  # 配置回滚Agent
  
  - name: run_tests
    agent: tester
    rollback: cleanup_tests
  
  - name: commit
    agent: git_agent
    rollback: git_reset
```

**优点**:
- 自动化回滚
- 多步骤协调
- 失败自动恢复

---

### 策略3: 手动备份（最安全但繁琐）⭐⭐⭐

```bash
# 1. 修改前备份
cp -r backend backend.backup

# 2. 让道友code修改
daoyou "帮我重构XXX"

# 3. 测试
pytest

# 4a. 成功，删除备份
rm -rf backend.backup

# 4b. 失败，还原备份
rm -rf backend
mv backend.backup backend
```

---

## 实际使用建议

### 日常开发

```yaml
# .daoyou.conf.yml
git:
  auto_commit: true         # ✅ 开启
  push_after_commit: false  # ❌ 关闭（本地实验）

history:
  enabled: true             # ✅ 开启
  restore: true             # ✅ 开启
```

**工作流程**:

```bash
# 1. 修改代码
daoyou "添加XXX功能"
# → 自动commit

# 2. 测试
pytest

# 3. 如果失败
daoyou "还原刚才的修改"
# 或
git reset --hard HEAD^
```

---

### 实验性修改

```bash
# 1. 创建实验分支
git checkout -b experiment

# 2. 修改代码
daoyou "尝试XXX方案"

# 3. 测试
pytest

# 4a. 成功，合并
git checkout main
git merge experiment

# 4b. 失败，放弃
git checkout main
git branch -D experiment
```

---

### 生产环境

```yaml
# .daoyou.conf.yml
git:
  auto_commit: true
  push_after_commit: true   # ✅ 自动push

testing:
  auto_test: true           # ✅ 自动测试
  test_cmd: "pytest"
```

**工作流程**:

```bash
# 1. 修改代码
daoyou "修复XXX bug"
# → 自动commit
# → 自动测试
# → 测试通过后自动push

# 2. 如果测试失败
# → 不会push
# → 可以安全还原
git reset --hard HEAD^
```

---

## 对比：道友code vs Cursor/Kiro

| 特性 | 道友code | Cursor/Kiro |
|------|---------|-------------|
| 工作流回滚 | ✅ 支持 | ❌ 不支持 |
| Git集成 | ✅ 自动commit | ⚠️ 手动 |
| 对话历史 | ✅ 完整记录 | ✅ 完整记录 |
| 上下文还原 | ✅ 支持 | ✅ 支持 |
| 自动测试 | ✅ 支持 | ⚠️ 部分支持 |
| 备份机制 | ⚠️ 目录存在 | ❌ 无 |

---

## 总结

### 道友code的还原机制很完善！

✅ **工作流回滚** - 自动化、多步骤  
✅ **Git集成** - 完整版本控制  
✅ **历史记录** - 对话上下文  
✅ **配置灵活** - 可以根据场景调整  

### 推荐配置

```yaml
# .daoyou.conf.yml
git:
  auto_commit: true         # 每次修改自动commit
  push_after_commit: false  # 本地实验，不自动push

history:
  enabled: true
  restore: true             # 启动时载入历史

testing:
  auto_test: true           # 修改后自动测试
  test_cmd: "pytest"
```

### 使用方式

```bash
# 1. 修改代码
daoyou "添加XXX功能"

# 2. 如果有问题
daoyou "还原刚才的修改"
# 或
git reset --hard HEAD^

# 3. 查看历史
git log --oneline
cat .daoyou.chat.history.md
```

---

**结论**: 道友code的还原机制比Cursor/Kiro更完善，特别是工作流回滚和Git自动集成功能！

