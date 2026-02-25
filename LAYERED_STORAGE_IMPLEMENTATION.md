# 分层存储实施文档

## 实施完成

✅ 已创建分层存储系统，实现用户级和项目级的分离存储。

---

## 新增文件

### 1. 配置文件
- `backend/config/memory_storage.yaml` - 存储配置

### 2. 实现文件
- `backend/daoyoucode/agents/memory/layered_storage.py` - 分层存储实现

---

## 架构设计

### 三层存储架构

```
┌─────────────────────────────────────────────────────────────┐
│ 用户级存储（C 盘）- 跨项目                                     │
│ 路径：C:\Users\[用户名]\.daoyoucode\                         │
│                                                              │
│ ├── user_profile.json        # 用户画像（编码风格、偏好）     │
│ ├── preferences.json         # 全局偏好设置                  │
│ └── user_sessions.json       # 用户会话映射                  │
│                                                              │
│ 大小：< 10 MB（轻量级）                                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 项目级存储（项目目录）- 项目独立                               │
│ 路径：[项目根目录]\.daoyoucode\                               │
│                                                              │
│ ├── project_context.json     # 项目上下文（架构、约定）       │
│ ├── chat.history.md          # 对话历史（Markdown）          │
│ ├── input.history            # 输入历史（命令行）             │
│ ├── summaries.json           # 会话摘要                      │
│ ├── key_info.json            # 关键信息                      │
│ └── archive/                 # 归档目录                      │
│     └── chat.history.*.md    # 归档的对话历史                │
│                                                              │
│ 大小：10-100 MB（重量级）                                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 会话级存储（内存）- 临时                                       │
│                                                              │
│ ├── conversation_history     # 当前对话历史                  │
│ ├── current_task             # 当前任务                      │
│ └── context_files            # 上下文文件                    │
│                                                              │
│ 生命周期：会话结束后清除                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 核心功能

### 1. 用户级存储（跨项目）

**目的**：存储用户的"人格画像"和全局偏好

**存储内容**：
```json
{
  "user_profile": {
    "coding_style": {
      "indentation": "4 spaces",
      "naming_convention": "snake_case",
      "prefers_type_hints": true
    },
    "communication_style": {
      "verbosity": "detailed",
      "prefers_examples": true
    },
    "language_preferences": {
      "primary": ["Python", "TypeScript"],
      "frameworks": ["FastAPI", "React"]
    }
  }
}
```

**API**：
```python
from daoyoucode.agents.memory.layered_storage import LayeredStorage

storage = LayeredStorage()

# 保存用户画像
storage.save_user_profile(profile)

# 加载用户画像
profile = storage.load_user_profile()

# 保存全局偏好
storage.save_global_preferences(prefs)

# 加载全局偏好
prefs = storage.load_global_preferences()
```

---

### 2. 项目级存储（项目独立）

**目的**：存储项目相关的上下文和对话历史

**存储内容**：
```json
{
  "project_context": {
    "architecture": {
      "type": "microservices",
      "patterns": ["DDD", "CQRS"]
    },
    "team_conventions": {
      "code_review_checklist": [...]
    }
  }
}
```

**API**：
```python
from pathlib import Path
from daoyoucode.agents.memory.layered_storage import LayeredStorage

# 指定项目路径
project_path = Path("/path/to/project")
storage = LayeredStorage(project_path=project_path)

# 保存项目上下文
storage.save_project_context(context)

# 加载项目上下文
context = storage.load_project_context()

# 追加对话历史（Markdown格式）
storage.append_chat_history(
    user_message="如何优化这个函数？",
    ai_response="可以使用缓存来优化...",
    metadata={"skill": "programming"}
)

# 保存会话摘要
storage.save_session_summaries(summaries)

# 加载会话摘要
summaries = storage.load_session_summaries()
```

---

### 3. 会话级存储（内存）

**目的**：存储当前会话的临时数据

**API**：
```python
# 设置会话数据
storage.set_session_data(session_id, "current_task", "优化RepoMap")

# 获取会话数据
task = storage.get_session_data(session_id, "current_task")

# 清除会话数据
storage.clear_session_data(session_id)
```

---

## 自动迁移

### 从旧版本迁移

系统会自动检测旧数据目录（`~/.daoyoucode/memory/`）并迁移：

**迁移规则**：
1. `profiles.json` → `user_profile.json`（用户级）
2. `preferences.json` → `preferences.json`（用户级）
3. `user_sessions.json` → `user_sessions.json`（用户级）
4. `summaries.json` → `summaries.json`（项目级，需要按项目分离）
5. `key_info.json` → `key_info.json`（项目级，需要按项目分离）
6. `tasks.json` → 归档（不再使用）

**迁移后**：
- 旧数据目录会被移动到 `~/.daoyoucode/archive/memory_backup_[时间戳]/`
- 可以安全删除归档目录

---

## 自动清理

### 对话历史清理

**触发条件**：
- 文件大小超过 10 MB
- 或者包含超过 30 天的旧数据

**清理策略**：
1. 保留最近 30 天的对话
2. 将旧对话归档到 `.daoyoucode/archive/chat.history.[日期].md`
3. 压缩归档文件（可选）

**手动清理**：
```python
# 获取存储统计
stats = storage.get_storage_stats()
print(stats)

# 输出：
# {
#   'user_level': {
#     'total_size_mb': 2.5,
#     'file_count': 3
#   },
#   'project_level': {
#     'total_size_mb': 45.2,
#     'file_count': 15
#   }
# }
```

---

## 配置选项

### 存储位置配置

```yaml
# backend/config/memory_storage.yaml

storage:
  user_level:
    location: "user_home"  # user_home | custom
    custom_path: null      # 自定义路径
  
  project_level:
    location: "project"    # project | user_home | custom
    custom_path: null
```

### 大小限制配置

```yaml
storage:
  user_level:
    limits:
      max_size_mb: 10
      auto_cleanup: true
  
  project_level:
    limits:
      max_size_mb: 100
      chat_history_max_mb: 10
      chat_history_max_days: 30
```

---

## 集成到现有系统

### 方案 1：渐进式集成（推荐）

保留现有的 `MemoryStorage`，逐步迁移到 `LayeredStorage`：

```python
# backend/daoyoucode/agents/memory/manager.py

class MemoryManager:
    def __init__(self, enable_tree: bool = True, project_path: Optional[Path] = None):
        # 旧存储（向后兼容）
        self.storage = MemoryStorage()
        
        # 新存储（分层）
        self.layered_storage = LayeredStorage(project_path=project_path)
        
        # 其他初始化...
    
    def save_user_profile(self, profile: Dict):
        """保存用户画像（使用新存储）"""
        self.layered_storage.save_user_profile(profile)
    
    def add_conversation(self, session_id: str, user_message: str, ai_response: str, ...):
        """添加对话（同时使用新旧存储）"""
        # 旧存储（内存）
        self.storage.add_conversation(session_id, user_message, ai_response, ...)
        
        # 新存储（持久化到项目目录）
        self.layered_storage.append_chat_history(user_message, ai_response, metadata)
```

### 方案 2：完全替换

直接使用 `LayeredStorage` 替换 `MemoryStorage`：

```python
# backend/daoyoucode/agents/memory/manager.py

class MemoryManager:
    def __init__(self, enable_tree: bool = True, project_path: Optional[Path] = None):
        # 只使用新存储
        self.storage = LayeredStorage(project_path=project_path)
        
        # 其他初始化...
```

---

## 使用示例

### 示例 1：在 chat 命令中使用

```python
# backend/cli/commands/chat.py

def main(...):
    from daoyoucode.agents.memory.layered_storage import LayeredStorage
    
    # 初始化分层存储
    storage = LayeredStorage(project_path=repo_path)
    
    # 加载用户画像
    user_profile = storage.load_user_profile()
    if user_profile:
        logger.info(f"加载用户画像: {user_profile.get('coding_style')}")
    
    # 加载项目上下文
    project_context = storage.load_project_context()
    if project_context:
        logger.info(f"加载项目上下文: {project_context.get('architecture')}")
    
    # 对话循环
    while True:
        user_input = console.input("你 > ")
        ai_response = handle_chat(user_input, ...)
        
        # 保存对话历史
        storage.append_chat_history(user_input, ai_response)
```

### 示例 2：学习用户偏好

```python
def learn_user_preferences(storage: LayeredStorage, interaction: Dict):
    """从交互中学习用户偏好"""
    
    # 加载现有画像
    profile = storage.load_user_profile() or {}
    
    # 分析编码风格
    if "type hints" in interaction['user_message']:
        if 'coding_style' not in profile:
            profile['coding_style'] = {}
        profile['coding_style']['prefers_type_hints'] = True
    
    # 分析沟通风格
    if len(interaction['user_message']) > 500:
        if 'communication_style' not in profile:
            profile['communication_style'] = {}
        profile['communication_style']['verbosity'] = 'detailed'
    
    # 保存更新后的画像
    storage.save_user_profile(profile)
```

### 示例 3：学习项目上下文

```python
def learn_project_context(storage: LayeredStorage, code_analysis: Dict):
    """从代码分析中学习项目上下文"""
    
    # 加载现有上下文
    context = storage.load_project_context() or {}
    
    # 分析架构
    if 'architecture' not in context:
        context['architecture'] = {}
    
    context['architecture']['type'] = detect_architecture_type(code_analysis)
    context['architecture']['patterns'] = detect_patterns(code_analysis)
    context['architecture']['key_modules'] = identify_key_modules(code_analysis)
    
    # 保存更新后的上下文
    storage.save_project_context(context)
```

---

## 测试

### 单元测试

```python
# backend/tests/test_layered_storage.py

import pytest
from pathlib import Path
from daoyoucode.agents.memory.layered_storage import LayeredStorage

def test_user_profile():
    storage = LayeredStorage()
    
    # 保存用户画像
    profile = {
        'coding_style': {'indentation': '4 spaces'},
        'communication_style': {'verbosity': 'detailed'}
    }
    storage.save_user_profile(profile)
    
    # 加载用户画像
    loaded = storage.load_user_profile()
    assert loaded == profile

def test_project_context():
    project_path = Path("/tmp/test_project")
    storage = LayeredStorage(project_path=project_path)
    
    # 保存项目上下文
    context = {
        'architecture': {'type': 'microservices'}
    }
    storage.save_project_context(context)
    
    # 加载项目上下文
    loaded = storage.load_project_context()
    assert loaded == context

def test_chat_history():
    project_path = Path("/tmp/test_project")
    storage = LayeredStorage(project_path=project_path)
    
    # 追加对话
    storage.append_chat_history("Hello", "Hi there!")
    
    # 检查文件是否存在
    history_file = project_path / ".daoyoucode" / "chat.history.md"
    assert history_file.exists()
    
    # 检查内容
    content = history_file.read_text()
    assert "Hello" in content
    assert "Hi there!" in content
```

---

## 性能优化

### 1. 缓存

- 用户画像和项目上下文会自动缓存在内存中
- 避免重复读取文件

### 2. 延迟写入

- 对话历史使用追加模式（`append`），避免重写整个文件
- 批量写入（可选）

### 3. 自动清理

- 对话历史超过限制时自动归档
- 避免文件过大影响性能

---

## 监控和调试

### 获取存储统计

```python
stats = storage.get_storage_stats()
print(json.dumps(stats, indent=2))

# 输出：
# {
#   "user_level": {
#     "exists": true,
#     "path": "C:\\Users\\Administrator\\.daoyoucode",
#     "total_size_mb": 2.5,
#     "file_count": 3
#   },
#   "project_level": {
#     "exists": true,
#     "path": "D:\\projects\\myproject\\.daoyoucode",
#     "total_size_mb": 45.2,
#     "file_count": 15
#   },
#   "session_level": {
#     "active_sessions": 2,
#     "total_keys": 8
#   }
# }
```

### 日志

```python
import logging

# 启用调试日志
logging.getLogger('daoyoucode.agents.memory.layered_storage').setLevel(logging.DEBUG)
```

---

## 下一步

### Phase 1：基础集成（1-2 天）
- [ ] 在 `MemoryManager` 中集成 `LayeredStorage`
- [ ] 在 `chat.py` 中使用对话历史功能
- [ ] 测试自动迁移

### Phase 2：用户画像学习（3-5 天）
- [ ] 实现从交互中学习用户偏好
- [ ] 实现个性化 prompt 生成
- [ ] 测试跨项目记忆

### Phase 3：项目上下文学习（3-5 天）
- [ ] 实现从代码分析中学习项目上下文
- [ ] 实现项目相关的 prompt 生成
- [ ] 测试项目独立性

### Phase 4：高级功能（1-2 周）
- [ ] 实现输入历史（命令行历史）
- [ ] 实现记忆可视化
- [ ] 实现记忆管理 CLI 命令

---

## 总结

✅ **已完成**：
- 分层存储架构设计
- 配置文件（`memory_storage.yaml`）
- 实现文件（`layered_storage.py`）
- 自动迁移功能
- 自动清理功能

🎯 **核心优势**：
- 用户画像（C 盘）：轻量级（< 10 MB），跨项目共享
- 项目上下文（项目目录）：重量级（10-100 MB），项目独立
- 对话历史（项目目录）：便于管理，不占 C 盘
- 向后兼容：不破坏现有系统
- 自动迁移：无缝升级

🚀 **下一步**：集成到 `MemoryManager` 和 `chat.py`，开始使用！
