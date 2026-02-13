# 调用链路分析 - 07 Memory层

## 7. Memory层：记忆管理

### 入口函数
```
📁 backend/daoyoucode/agents/memory/__init__.py :: MemoryManager
```

### 调用流程

#### 7.1 Memory管理器

**代码**:
```python
class MemoryManager:
    """记忆管理器（单例）"""
    
    def __init__(self):
        # 初始化存储后端（SQLite）
        self.db_path = Path(".daoyoucode/memory/memory.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self._init_tables()
    
    def _init_tables(self):
        """初始化数据库表"""
        # 对话历史表
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_message TEXT NOT NULL,
                ai_response TEXT NOT NULL,
                timestamp REAL NOT NULL,
                metadata TEXT
            )
        """)
        
        # 用户偏好表
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS preferences (
                user_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                PRIMARY KEY (user_id, key)
            )
        """)
        
        # 任务历史表
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                task_data TEXT NOT NULL,
                timestamp REAL NOT NULL
            )
        """)
        
        self.conn.commit()
```

**职责**:
- 管理所有记忆数据
- 提供统一的存储接口
- 支持多种记忆类型

---

#### 7.2 对话历史（LLM层记忆）

**添加对话**:
```python
def add_conversation(
    self,
    session_id: str,
    user_message: str,
    ai_response: str,
    metadata: Optional[Dict] = None
):
    """添加对话到历史"""
    import time
    import json
    
    self.conn.execute(
        """
        INSERT INTO conversations 
        (session_id, user_message, ai_response, timestamp, metadata)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            session_id,
            user_message,
            ai_response,
            time.time(),
            json.dumps(metadata or {})
        )
    )
    self.conn.commit()
```

**获取对话历史**:
```python
def get_conversation_history(
    self,
    session_id: str,
    limit: int = 10
) -> List[Dict]:
    """获取对话历史"""
    cursor = self.conn.execute(
        """
        SELECT user_message, ai_response, timestamp, metadata
        FROM conversations
        WHERE session_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
        """,
        (session_id, limit)
    )
    
    rows = cursor.fetchall()
    
    # 反转顺序（最旧的在前）
    history = []
    for row in reversed(rows):
        history.append({
            'user': row[0],
            'ai': row[1],
            'timestamp': row[2],
            'metadata': json.loads(row[3])
        })
    
    return history
```

**使用场景**:
- Agent执行前：加载最近3轮对话
- Agent执行后：保存当前对话
- 用于构建LLM的messages参数

---

#### 7.3 用户偏好（Agent层记忆）

**记住偏好**:
```python
def remember_preference(
    self,
    user_id: str,
    key: str,
    value: str
):
    """记住用户偏好"""
    self.conn.execute(
        """
        INSERT OR REPLACE INTO preferences (user_id, key, value)
        VALUES (?, ?, ?)
        """,
        (user_id, key, value)
    )
    self.conn.commit()
```

**获取偏好**:
```python
def get_preferences(self, user_id: str) -> Dict[str, str]:
    """获取用户偏好"""
    cursor = self.conn.execute(
        "SELECT key, value FROM preferences WHERE user_id = ?",
        (user_id,)
    )
    
    return {row[0]: row[1] for row in cursor.fetchall()}
```

**示例偏好**:
```python
# 编程语言偏好
memory.remember_preference(user_id, 'preferred_language', 'python')

# 代码风格偏好
memory.remember_preference(user_id, 'code_style', 'pep8')

# 详细程度偏好
memory.remember_preference(user_id, 'verbosity', 'concise')
```

---

#### 7.4 任务历史（Agent层记忆）

**添加任务**:
```python
def add_task(self, user_id: str, task_data: Dict):
    """添加任务到历史"""
    import time
    import json
    
    self.conn.execute(
        """
        INSERT INTO tasks (user_id, task_data, timestamp)
        VALUES (?, ?, ?)
        """,
        (user_id, json.dumps(task_data), time.time())
    )
    self.conn.commit()
```

**获取任务历史**:
```python
def get_task_history(
    self,
    user_id: str,
    limit: int = 10
) -> List[Dict]:
    """获取任务历史"""
    cursor = self.conn.execute(
        """
        SELECT task_data, timestamp
        FROM tasks
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
        """,
        (user_id, limit)
    )
    
    return [
        {**json.loads(row[0]), 'timestamp': row[1]}
        for row in cursor.fetchall()
    ]
```

**任务数据示例**:
```python
{
    'agent': 'MainAgent',
    'input': '如何实现Agent系统？',
    'result': 'Agent系统主要包括...',
    'success': True,
    'tools_used': ['repo_map', 'read_file']
}
```

---

#### 7.5 记忆在Agent中的使用

**Agent执行前（加载记忆）**:
```python
# 在Agent.execute()中
session_id = context.get('session_id', 'default')
user_id = context.get('user_id', session_id)

# 1. 对话历史
history = self.memory.get_conversation_history(session_id, limit=3)
if history:
    context['conversation_history'] = history

# 2. 用户偏好
prefs = self.memory.get_preferences(user_id)
if prefs:
    context['user_preferences'] = prefs

# 3. 任务历史
task_history = self.memory.get_task_history(user_id, limit=5)
if task_history:
    context['recent_tasks'] = task_history
```

**Agent执行后（保存记忆）**:
```python
# 1. 保存对话
self.memory.add_conversation(
    session_id,
    user_input,
    response,
    metadata={'agent': self.name}
)

# 2. 保存任务
self.memory.add_task(user_id, {
    'agent': self.name,
    'input': user_input[:200],
    'result': response[:200],
    'success': True,
    'tools_used': tools_used
})

# 3. 学习偏好
if 'python' in user_input.lower():
    self.memory.remember_preference(user_id, 'preferred_language', 'python')
```

---

#### 7.6 记忆类型对比

| 记忆类型 | 存储位置 | 生命周期 | 用途 | 示例 |
|---------|---------|---------|------|------|
| 对话历史 | conversations表 | 会话级别 | LLM上下文 | 最近3轮对话 |
| 用户偏好 | preferences表 | 用户级别 | 个性化 | 编程语言偏好 |
| 任务历史 | tasks表 | 用户级别 | 学习改进 | 最近5个任务 |

---

#### 7.7 数据库结构

**conversations表**:
```sql
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,           -- 会话ID
    user_message TEXT NOT NULL,         -- 用户消息
    ai_response TEXT NOT NULL,          -- AI响应
    timestamp REAL NOT NULL,            -- 时间戳
    metadata TEXT                       -- 元数据（JSON）
);

CREATE INDEX idx_session ON conversations(session_id);
```

**preferences表**:
```sql
CREATE TABLE preferences (
    user_id TEXT NOT NULL,              -- 用户ID
    key TEXT NOT NULL,                  -- 偏好键
    value TEXT NOT NULL,                -- 偏好值
    PRIMARY KEY (user_id, key)
);
```

**tasks表**:
```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,              -- 用户ID
    task_data TEXT NOT NULL,            -- 任务数据（JSON）
    timestamp REAL NOT NULL             -- 时间戳
);

CREATE INDEX idx_user ON tasks(user_id);
```

---

### 关键文件清单

| 文件 | 职责 | 关键类/函数 |
|------|------|------------|
| `memory/__init__.py` | Memory管理器 | `MemoryManager` |
| `memory/conversation.py` | 对话历史 | `add_conversation()`, `get_conversation_history()` |
| `memory/preference.py` | 用户偏好 | `remember_preference()`, `get_preferences()` |
| `memory/task.py` | 任务历史 | `add_task()`, `get_task_history()` |

---

### 依赖关系

```
MemoryManager
    ↓
├─ SQLite (存储后端)
│   ├─ conversations表
│   ├─ preferences表
│   └─ tasks表
└─ Agent (使用方)
    ├─ 执行前：加载记忆
    └─ 执行后：保存记忆
```

---

### 下一步

Memory层完成后，整个调用链路分析完成

→ 继续阅读 `CALL_CHAIN_FLOWCHART.md` 查看完整流程图
