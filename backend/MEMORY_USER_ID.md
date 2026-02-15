# 用户ID管理说明

## 🎯 设计目标

用户ID用于：
1. 区分不同用户的数据（偏好、任务历史、画像）
2. 跨会话追踪用户行为
3. 提供个性化体验

## 📦 实现方案

### 用户ID生成策略

```python
# 优先级1：使用机器标识（主机名）
machine_id = platform.node()  # 例如：DESKTOP-ABC123
user_id = f"user-{hash(machine_id)[:12]}"  # user-d62ba4d8ee38

# 优先级2：使用UUID（回退方案）
user_id = f"user-{uuid.uuid4().hex[:12]}"
```

**特点**：
- ✅ 同一台机器上的用户ID保持不变
- ✅ 不同机器上的用户ID不同
- ✅ 无需用户手动配置
- ✅ 隐私友好（不收集个人信息）

### 持久化存储

**位置**：`~/.daoyoucode/user.json`

**格式**：
```json
{
  "user_id": "user-d62ba4d8ee38",
  "created_at": "2026-02-15T12:00:00",
  "config": {
    "language": "zh-CN",
    "theme": "default",
    "preferred_language": "python"
  }
}
```

**生命周期**：
- 首次运行时创建
- 程序重启后自动加载
- 用户可以手动删除文件重置

---

## 🔧 使用方法

### 方法1：自动获取（推荐）

```python
from daoyoucode.agents.memory import get_current_user_id

# 获取当前用户ID
user_id = get_current_user_id()
# 'user-d62ba4d8ee38'
```

### 方法2：通过UserManager

```python
from daoyoucode.agents.memory import get_user_manager

user_manager = get_user_manager()

# 获取用户ID
user_id = user_manager.get_user_id()

# 获取用户配置
language = user_manager.get_user_config('preferred_language')

# 设置用户配置
user_manager.set_user_config('theme', 'dark')
```

### 方法3：在Agent中自动获取

```python
# 在Agent.execute()中
async def execute(self, ...):
    # 提取user_id（自动获取）
    user_id = context.get('user_id')
    if not user_id:
        from ..memory import get_current_user_id
        user_id = get_current_user_id()
    
    # 使用user_id
    prefs = self.memory.get_preferences(user_id)
```

---

## 🔄 完整流程

### 首次运行

```
程序启动
  ↓
get_user_manager()
  ↓
检查 ~/.daoyoucode/user.json
  ↓
文件不存在
  ↓
生成user_id（基于机器标识）
  ↓
创建user.json
  ↓
返回user_id
```

### 后续运行

```
程序启动
  ↓
get_user_manager()
  ↓
检查 ~/.daoyoucode/user.json
  ↓
文件存在
  ↓
加载user_id
  ↓
返回user_id（与首次相同）
```

### 在Agent中使用

```
Agent.execute()
  ↓
提取user_id from context
  ↓
如果没有
  ↓
get_current_user_id()
  ↓
使用user_id
  ├─ 加载用户偏好
  ├─ 加载任务历史
  ├─ 保存对话（维护映射）
  └─ 更新用户画像
```

---

## 📊 数据关联

### user_id的作用

```
user_id: user-d62ba4d8ee38
  ↓
关联数据：
  ├─ 用户偏好（preferences.json）
  │   └─ preferred_language: python
  │
  ├─ 任务历史（tasks.json）
  │   └─ [task1, task2, task3, ...]
  │
  ├─ 用户画像（profiles.json）
  │   └─ {common_topics: [...], skill_level: ...}
  │
  └─ 会话映射（user_sessions.json）
      └─ [session-1, session-2, session-3, ...]
```

### session_id vs user_id

| 维度 | session_id | user_id |
|------|-----------|---------|
| 生成时机 | 每次启动CLI | 首次运行 |
| 生命周期 | 单次会话 | 永久 |
| 用途 | 对话历史 | 用户数据 |
| 示例 | uuid-abc-123 | user-d62ba4d8ee38 |

**关系**：
- 一个user_id可以有多个session_id
- 通过user_sessions.json维护映射

---

## 🎯 使用场景

### 场景1：用户偏好

```python
from daoyoucode.agents.memory import get_memory_manager, get_current_user_id

memory = get_memory_manager()
user_id = get_current_user_id()

# 保存偏好
memory.remember_preference(user_id, 'preferred_language', 'python')

# 获取偏好
prefs = memory.get_preferences(user_id)
# {'preferred_language': 'python'}
```

### 场景2：任务历史

```python
# 保存任务
memory.add_task(user_id, {
    'agent': 'MainAgent',
    'input': '重构代码',
    'success': True
})

# 获取历史
tasks = memory.get_task_history(user_id, limit=10)
```

### 场景3：用户画像

```python
# 生成画像
profile = await memory.long_term_memory.build_user_profile(user_id)

# 获取画像
profile = memory.long_term_memory.get_user_profile(user_id)
# {
#   'common_topics': ['python', 'testing'],
#   'skill_level': 'intermediate',
#   ...
# }
```

### 场景4：跨会话追踪

```python
# 获取用户的所有会话
sessions = memory.get_user_sessions(user_id)
# ['session-1', 'session-2', 'session-3']

# 分析用户行为
for session_id in sessions:
    history = memory.get_conversation_history(session_id)
    # 分析对话内容
```

---

## ⚙️ 配置选项

### 用户配置

```python
from daoyoucode.agents.memory import get_user_manager

user_manager = get_user_manager()

# 设置配置
user_manager.set_user_config('language', 'zh-CN')
user_manager.set_user_config('theme', 'dark')
user_manager.set_user_config('preferred_language', 'python')

# 获取配置
language = user_manager.get_user_config('language')
theme = user_manager.get_user_config('theme', default='light')
```

### 重置用户

```python
# 重置用户（生成新的user_id）
user_manager.reset_user()

# 注意：这会清除所有用户数据的关联
```

---

## 🔒 隐私和安全

### 隐私保护

- ✅ 不收集个人信息
- ✅ 不上传到服务器
- ✅ 本地存储
- ✅ 用户可以删除

### 数据位置

```
~/.daoyoucode/
├── user.json              # 用户ID和配置
└── memory/
    ├── preferences.json   # 用户偏好
    ├── tasks.json        # 任务历史
    ├── profiles.json     # 用户画像
    └── user_sessions.json # 会话映射
```

### 删除数据

```bash
# 删除所有用户数据
rm -rf ~/.daoyoucode

# 或只删除用户ID（重新生成）
rm ~/.daoyoucode/user.json
```

---

## 🧪 测试

### 运行测试

```bash
python backend/test_user_manager.py
```

### 测试内容

- ✅ 用户ID生成
- ✅ 持久化存储
- ✅ 程序重启后恢复
- ✅ 用户配置管理
- ✅ Agent自动获取

---

## 📚 相关文档

- `MEMORY_PERSISTENCE.md` - 持久化说明
- `MEMORY_USER_PROFILE_DESIGN.md` - 用户画像设计
- `MEMORY_PROFILE_GENERATION.md` - 画像生成策略

---

## ✅ 总结

**用户ID管理方案**：
- ✅ 自动生成（基于机器标识）
- ✅ 持久化存储（程序重启后保持）
- ✅ 隐私友好（本地存储，不上传）
- ✅ 易于使用（自动获取）
- ✅ 支持配置（用户可自定义）

**使用方式**：
```python
# 最简单的方式
from daoyoucode.agents.memory import get_current_user_id
user_id = get_current_user_id()
```

**存储位置**：`~/.daoyoucode/user.json`

**测试命令**：`python backend/test_user_manager.py`
