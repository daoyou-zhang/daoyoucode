# Memory系统的数据层级

## 🎯 核心设计

Memory系统采用**两级数据模型**：

1. **User级别** - 跨会话的长期数据
2. **Session级别** - 单次会话的临时数据

---

## 📊 数据层级对比

### User级别（长期，持久化）

**定义**：一个用户的所有数据，跨越多个会话

**标识**：`user_id`（例如：`user-d62ba4d8ee38`）

**生命周期**：永久（除非用户删除）

**数据类型**：
- ✅ 用户偏好（preferences）
- ✅ 任务历史（tasks）
- ✅ 用户画像（profile）
- ✅ 会话映射（user_sessions）

**存储位置**：
```
~/.daoyoucode/memory/
├── preferences.json      # 用户偏好
├── tasks.json           # 任务历史
├── profiles.json        # 用户画像
└── user_sessions.json   # 会话映射
```

**示例**：
```python
user_id = "user-d62ba4d8ee38"

# 用户偏好
preferences = {
    'preferred_language': 'python',
    'code_style': 'functional',
    'theme': 'dark'
}

# 任务历史
tasks = [
    {'input': '重构代码', 'success': True, 'timestamp': '...'},
    {'input': '写测试', 'success': True, 'timestamp': '...'},
    # ... 最近100个任务
]

# 用户画像
profile = {
    'common_topics': ['python', 'testing', 'refactoring'],
    'skill_level': 'intermediate',
    'total_conversations': 150,
    'total_sessions': 15
}

# 会话映射
user_sessions = ['session-1', 'session-2', 'session-3', ...]
```

---

### Session级别（临时，内存）

**定义**：一次对话会话的数据

**标识**：`session_id`（例如：`uuid-abc-123`）

**生命周期**：单次会话（程序重启后清空）

**数据类型**：
- ✅ 对话历史（conversations）
- ✅ 对话摘要（summary）
- ✅ 共享上下文（shared_context）

**存储位置**：内存（不持久化）

**示例**：
```python
session_id = "uuid-abc-123"

# 对话历史
conversations = [
    {
        'user': '这个项目是做什么的？',
        'ai': '这是一个AI代码助手...',
        'timestamp': '2026-02-15T12:00:00'
    },
    {
        'user': '有哪些核心功能？',
        'ai': '核心功能包括...',
        'timestamp': '2026-02-15T12:01:00'
    },
    # ... 最近10轮对话
]

# 对话摘要（每5轮生成）
summary = "用户询问了项目的基本信息和核心功能..."

# 共享上下文（多智能体）
shared_context = {
    'shared': {'project_name': 'DaoyouCode'},
    'Agent1': {'status': 'analyzing'},
    'Agent2': {'status': 'waiting'}
}
```

---

## 🔗 关系映射

### User → Sessions（一对多）

```
user_id: user-d62ba4d8ee38
  ↓
sessions:
  ├─ session-1 (2026-02-10)
  ├─ session-2 (2026-02-12)
  ├─ session-3 (2026-02-15)
  └─ ...
```

**维护方式**：
```python
# 在add_conversation时自动维护
memory.add_conversation(
    session_id="session-3",
    user_message="...",
    ai_response="...",
    user_id="user-d62ba4d8ee38"  # 关键：传递user_id
)

# 内部会调用
storage._register_session(user_id, session_id)
```

**查询方式**：
```python
# 获取用户的所有会话
sessions = memory.get_user_sessions(user_id)
# ['session-1', 'session-2', 'session-3']

# 反向查询：获取会话对应的用户
user_id = memory.get_session_user(session_id)
# 'user-d62ba4d8ee38'
```

---

## 📋 完整对比表

| 维度 | User级别 | Session级别 |
|------|---------|------------|
| **标识** | user_id | session_id |
| **生成时机** | 首次运行 | 每次启动CLI |
| **生命周期** | 永久 | 单次会话 |
| **存储方式** | 持久化（JSON） | 内存 |
| **数据类型** | 偏好、任务、画像 | 对话历史、摘要 |
| **数量关系** | 1个用户 | 多个会话 |
| **用途** | 长期学习、个性化 | 对话上下文 |
| **示例** | user-d62ba4d8ee38 | uuid-abc-123 |

---

## 🎯 使用场景

### 场景1：日常对话

```python
# CLI启动
session_id = str(uuid.uuid4())  # 生成新的session_id
user_id = get_current_user_id()  # 获取持久的user_id

# 对话1
memory.add_conversation(
    session_id=session_id,
    user_message="你好",
    ai_response="你好！",
    user_id=user_id
)

# 对话2
memory.add_conversation(
    session_id=session_id,
    user_message="这个项目是做什么的？",
    ai_response="这是一个AI助手...",
    user_id=user_id
)

# 获取当前会话的历史（Session级别）
history = memory.get_conversation_history(session_id)
# [对话1, 对话2]

# 获取用户的所有会话（User级别）
all_sessions = memory.get_user_sessions(user_id)
# [session-1, session-2, session-3, ...]
```

### 场景2：用户画像生成

```python
# 收集用户的所有会话
all_sessions = memory.get_user_sessions(user_id)
# ['session-1', 'session-2', 'session-3']

# 遍历所有会话，收集对话历史
all_conversations = []
for session_id in all_sessions:
    history = memory.get_conversation_history(session_id)
    all_conversations.extend(history)

# 分析生成用户画像（User级别）
profile = await memory.long_term_memory.build_user_profile(
    user_id=user_id,
    all_sessions=all_sessions
)

# 画像包含跨会话的统计
# {
#   'total_sessions': 3,
#   'total_conversations': 50,
#   'common_topics': ['python', 'testing'],
#   ...
# }
```

### 场景3：智能加载

```python
# 智能加载（Session级别）
context = await memory.load_context_smart(
    session_id=session_id,  # 当前会话
    user_id=user_id,        # 当前用户
    user_input="能详细说说吗？",
    is_followup=True
)

# 返回：
# {
#   'history': [...],      # 当前会话的历史（Session级别）
#   'summary': '...',      # 当前会话的摘要（Session级别）
#   'strategy': 'medium_followup',
#   'cost': 2
# }

# 同时加载用户偏好（User级别）
prefs = memory.get_preferences(user_id)
# {'preferred_language': 'python'}
```

---

## 🔄 数据流转

### 从Session到User

```
对话发生（Session级别）
  ↓
保存到对话历史
  session_id → conversations
  ↓
维护映射
  user_id → [session_ids]
  ↓
累积到一定数量（10轮、20轮）
  ↓
生成/更新用户画像（User级别）
  user_id → profile
  ↓
用于个性化（User级别）
  user_id → preferences
```

### 从User到Session

```
新会话开始（Session级别）
  ↓
获取用户ID（User级别）
  user_id = get_current_user_id()
  ↓
加载用户数据（User级别）
  ├─ preferences
  ├─ tasks
  └─ profile
  ↓
应用到当前会话（Session级别）
  ├─ 个性化prompt
  ├─ 推荐工具
  └─ 调整策略
```

---

## 💡 设计优势

### 1. 清晰的职责分离

- **Session级别**：专注于对话上下文
- **User级别**：专注于长期学习

### 2. 灵活的生命周期

- **Session**：临时数据，不占用磁盘
- **User**：持久数据，跨会话保留

### 3. 高效的数据管理

- **Session**：内存存储，快速访问
- **User**：持久化存储，可靠保存

### 4. 隐私友好

- **Session**：程序关闭后自动清除
- **User**：用户可以手动删除

---

## 📊 数据量级

### Session级别

```
单个会话：
  对话历史：10轮（最近）
  摘要：1个
  共享上下文：少量

内存占用：~10KB
```

### User级别

```
单个用户：
  偏好：~10项
  任务历史：100个（最近）
  画像：1个
  会话映射：~50个session

磁盘占用：~100KB
```

---

## ✅ 总结

**两级数据模型**：

```
User级别（长期）
  ├─ user_id: user-d62ba4d8ee38
  ├─ 生命周期：永久
  ├─ 存储：持久化（JSON）
  └─ 数据：偏好、任务、画像、会话映射
      ↓
      关联
      ↓
Session级别（临时）
  ├─ session_id: uuid-abc-123
  ├─ 生命周期：单次会话
  ├─ 存储：内存
  └─ 数据：对话历史、摘要、共享上下文
```

**关键关系**：
- 1个User → 多个Sessions
- Session通过user_id关联到User
- User画像基于所有Sessions生成

**设计原则**：
- ✅ 职责分离（对话 vs 学习）
- ✅ 生命周期分离（临时 vs 永久）
- ✅ 存储分离（内存 vs 磁盘）
- ✅ 隐私友好（可清除 vs 可保留）

这个设计既保证了对话的流畅性（Session级别），又实现了长期的个性化（User级别）！🎉
