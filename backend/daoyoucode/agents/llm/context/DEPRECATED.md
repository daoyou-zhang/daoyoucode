# ⚠️ 此目录已废弃

> 此目录下的记忆管理功能已迁移到 `agents/memory` 模块

---

## 迁移说明

### 旧模块 → 新模块

| 旧模块 | 新模块 | 说明 |
|--------|--------|------|
| `llm/context/memory_manager.py` | `memory/storage.py` | 对话历史存储 |
| `llm/context/followup_detector.py` | `memory/detector.py` | 追问判断器 |
| `llm/context/manager.py` | `memory/manager.py` | 统一记忆管理器 |

### 为什么迁移？

1. **职责分离** - 记忆管理是Agent层的职责，不应该在LLM层
2. **功能增强** - 新模块支持更多功能：
   - 用户偏好记忆
   - 任务历史记忆
   - 多智能体共享记忆
3. **架构清晰** - LLM层专注于模型调用，记忆管理独立出来

### 新模块的优势

```python
# 旧方式（llm/context）
from daoyoucode.agents.llm.context import get_context_manager
context_manager = get_context_manager()
context_manager.add_conversation(session_id, user_msg, ai_msg)

# 新方式（memory）
from daoyoucode.agents.memory import get_memory_manager
memory = get_memory_manager()

# 1. 对话历史（LLM层）
memory.add_conversation(session_id, user_msg, ai_msg)

# 2. 用户偏好（Agent层）
memory.remember_preference(user_id, 'language', 'python')

# 3. 任务历史（Agent层）
memory.add_task(user_id, task_data)

# 4. 多智能体共享
shared_memory = memory.create_shared_memory(session_id, agent_names)
```

### 迁移步骤

如果你的代码还在使用旧模块：

1. 替换导入：
   ```python
   # 旧
   from daoyoucode.agents.llm.context import get_context_manager
   
   # 新
   from daoyoucode.agents.memory import get_memory_manager
   ```

2. 更新API调用：
   ```python
   # 旧
   context_manager.add_message(session_id, user, ai, metadata)
   
   # 新
   memory.add_conversation(session_id, user, ai, metadata)
   ```

3. 利用新功能：
   ```python
   # 用户偏好
   memory.remember_preference(user_id, key, value)
   prefs = memory.get_preferences(user_id)
   
   # 任务历史
   memory.add_task(user_id, task)
   tasks = memory.get_task_history(user_id)
   ```

### 何时删除此目录？

此目录将在下一个大版本中删除。目前保留是为了：
1. 向后兼容
2. 给用户时间迁移

---

**请使用新的 `agents/memory` 模块！**

