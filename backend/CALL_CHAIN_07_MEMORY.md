# 调用链路分析 - 07 Memory层

## 7. Memory层：记忆管理

### 入口函数
```
📁 backend/daoyoucode/agents/memory/__init__.py :: MemoryManager
```

### 调用流程

#### 7.1 Memory管理器（增强版）

**代码**:
```python
class MemoryManager:
    """
    统一的记忆管理器（单例）
    
    职责：
    1. 管理对话历史（LLM层）
    2. 管理用户偏好（Agent层）
    3. 管理任务历史（Agent层）
    4. 判断追问
    5. 智能加载上下文
    6. 生成对话摘要
    7. 构建用户画像
    8. 提供多智能体共享接口
    """
    
    def __init__(self):
        self.storage = MemoryStorage()
        self.detector = FollowupDetector()
        
        # 长期记忆和智能加载
        from .long_term_memory import LongTermMemory
        from .smart_loader import SmartLoader
        
        self.long_term_memory = LongTermMemory(storage=self.storage)
        self.smart_loader = SmartLoader()
```

**存储策略**:
- **内存存储（临时）**：对话历史、共享上下文
- **持久化存储（永久）**：用户偏好、任务历史、摘要、画像、会话映射

**存储位置**:
```
~/.daoyoucode/memory/
├── preferences.json      # 用户偏好
├── tasks.json           # 任务历史
├── summaries.json       # 对话摘要
├── profiles.json        # 用户画像
└── user_sessions.json   # 用户会话映射
```

---

#### 7.2 智能加载（核心功能）

**入口函数**:
```python
async def load_context_smart(
    self,
    session_id: str,
    user_id: str,
    user_input: str,
    is_followup: bool = False,
    confidence: float = 0.0
) -> Dict[str, Any]:
    """
    智能加载上下文
    
    Returns:
        {
            'strategy': 'medium_followup',
            'history': [...],  # 智能筛选的对话
            'summary': '...',  # 对话摘要（如果有）
            'cost': 2,
            'filtered': True
        }
    """
```

**加载策略**:

| 策略 | 触发条件 | 加载内容 | 成本 |
|------|---------|---------|------|
| new_conversation | 首轮对话 | 无 | 0 |
| simple_followup | 简单追问 | 最近2轮 | 1 |
| medium_followup | 中等追问 | 最近3轮 | 2 |
| complex_followup | 复杂追问 | 摘要+2轮 | 3 |
| cross_session | 跨会话 | 向量检索 | 5 |

**智能筛选**:
```python
# 提取关键词
keywords = self._extract_keywords(current_message)
# ['memory', '系统', '功能']

# 筛选相关对话
relevant = []
for conv in history:
    if any(kw in conv['user'].lower() for kw in keywords):
        relevant.append(conv)

# 组合：相关对话 + 最近对话
combined = relevant + recent[-limit:]
```

**性能优化**:
- 节省50-70%的token成本
- 关键词筛选相关对话
- 使用摘要代替早期对话
- 动态调整加载量

---

#### 7.3 对话历史管理

**添加对话**:
```python
def add_conversation(
    self,
    session_id: str,
    user_message: str,
    ai_response: str,
    metadata: Optional[Dict] = None,
    user_id: Optional[str] = None
):
    """
    添加对话到历史
    
    Args:
        session_id: 会话ID
        user_message: 用户消息
        ai_response: AI响应
        metadata: 元数据
        user_id: 用户ID（用于维护映射）
    """
    # 保存到内存（临时）
    self.storage.add_conversation(
        session_id, user_message, ai_response, metadata, user_id
    )
    
    # 维护user_id到session_id的映射（持久化）
    if user_id:
        self.storage._register_session(user_id, session_id)
```

**获取对话历史**:
```python
def get_conversation_history(
    self,
    session_id: str,
    limit: Optional[int] = None
) -> List[Dict]:
    """获取对话历史"""
    return self.storage.get_conversation_history(session_id, limit)
```

**数据格式**:
```python
[
    {
        'user': '这个项目是做什么的？',
        'ai': '这是一个AI代码助手...',
        'timestamp': '2026-02-15T12:00:00',
        'metadata': {'agent': 'MainAgent'}
    }
]
```

---

#### 7.4 用户偏好（Agent层记忆）

**记住偏好**:
```python
def remember_preference(
    self,
    user_id: str,
    key: str,
    value: Any
):
    """记住用户偏好（持久化）"""
    self.storage.add_preference(user_id, key, value)
    # 自动保存到 ~/.daoyoucode/memory/preferences.json
```

**获取偏好**:
```python
def get_preferences(self, user_id: str) -> Dict[str, Any]:
    """获取用户偏好"""
    return self.storage.get_preferences(user_id)
```

**示例偏好**:
```python
# 编程语言偏好
memory.remember_preference(user_id, 'preferred_language', 'python')

# 代码风格偏好
memory.remember_preference(user_id, 'code_style', 'functional')

# 详细程度偏好
memory.remember_preference(user_id, 'verbosity', 'concise')
```

**持久化**:
```json
{
  "user-123": {
    "preferred_language": {
      "value": "python",
      "timestamp": "2026-02-15T12:00:00",
      "count": 5
    }
  }
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
