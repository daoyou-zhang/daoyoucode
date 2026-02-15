# Memory系统持久化说明

## 📦 持久化策略

Memory系统采用混合存储策略：

### 内存存储（临时）

以下数据存储在内存中，程序重启后会丢失：

- **对话历史**：当前会话的对话记录
  - 原因：对话历史通常是临时的，每次会话独立
  - 保留策略：最近10轮（可配置）
  
- **共享上下文**：多智能体之间的临时共享数据
  - 原因：会话级别的临时数据，不需要持久化

### 持久化存储（永久）

以下数据持久化到磁盘，程序重启后自动加载：

- **用户偏好**：用户的个性化设置
  - 文件：`~/.daoyoucode/memory/preferences.json`
  - 示例：编程语言偏好、代码风格等
  
- **任务历史**：用户执行过的任务记录
  - 文件：`~/.daoyoucode/memory/tasks.json`
  - 保留策略：最近100个任务（可配置）
  
- **对话摘要**：长对话的摘要信息
  - 文件：`~/.daoyoucode/memory/summaries.json`
  - 用途：快速回顾历史对话
  
- **关键信息**：从对话中提取的重要信息
  - 文件：`~/.daoyoucode/memory/key_info.json`
  - 用途：保存项目相关的关键信息
  
- **用户画像**：用户的行为分析和偏好画像
  - 文件：`~/.daoyoucode/memory/profiles.json`
  - 用途：个性化推荐和智能辅助

---

## 📁 存储位置

### 默认位置

```
Windows: C:\Users\<用户名>\.daoyoucode\memory\
Linux/Mac: ~/.daoyoucode/memory/
```

### 文件结构

```
~/.daoyoucode/memory/
├── preferences.json    # 用户偏好
├── tasks.json          # 任务历史
├── summaries.json      # 对话摘要
├── key_info.json       # 关键信息
└── profiles.json       # 用户画像
```

### 自定义位置

可以在初始化时指定存储目录：

```python
from daoyoucode.agents.memory.storage import MemoryStorage

storage = MemoryStorage(storage_dir='/path/to/custom/dir')
```

---

## 🔄 自动加载

程序启动时会自动加载持久化数据：

```python
from daoyoucode.agents.memory import get_memory_manager

# 创建管理器（自动加载持久化数据）
memory = get_memory_manager()

# 数据已经加载，可以直接使用
prefs = memory.get_preferences('user-123')
tasks = memory.get_task_history('user-123')
```

日志输出示例：

```
INFO - 加载了 2 个用户的偏好
INFO - 加载了 5 个任务
INFO - 加载了 1 个摘要
INFO - 加载了 1 个用户画像
INFO - 记忆存储已初始化（持久化目录: ~/.daoyoucode/memory）
```

---

## 💾 自动保存

数据修改时会自动保存到磁盘：

```python
memory = get_memory_manager()

# 添加用户偏好（自动保存）
memory.remember_preference('user-123', 'language', 'python')

# 添加任务（自动保存）
memory.add_task('user-123', {
    'agent': 'MainAgent',
    'input': '重构代码',
    'result': '完成',
    'success': True
})

# 保存摘要（自动保存）
memory.long_term_memory.storage.save_summary(
    'session-456',
    '用户询问了项目结构和核心功能...'
)

# 保存用户画像（自动保存）
memory.long_term_memory.storage.save_user_profile(
    'user-123',
    {
        'common_topics': ['python', 'refactoring'],
        'total_conversations': 50
    }
)
```

---

## 📊 数据格式

### preferences.json

```json
{
  "user-123": {
    "language": {
      "value": "python",
      "timestamp": "2026-02-15T12:00:00",
      "count": 5
    },
    "style": {
      "value": "functional",
      "timestamp": "2026-02-15T12:05:00",
      "count": 3
    }
  }
}
```

### tasks.json

```json
{
  "user-123": [
    {
      "agent": "MainAgent",
      "input": "重构代码",
      "result": "完成",
      "success": true,
      "timestamp": "2026-02-15T12:00:00"
    }
  ]
}
```

### summaries.json

```json
{
  "session-456": "用户询问了项目结构和核心功能，讨论了Agent系统的设计..."
}
```

### profiles.json

```json
{
  "user-123": {
    "common_topics": ["python", "refactoring", "testing"],
    "total_conversations": 50,
    "preferred_style": "functional",
    "last_updated": "2026-02-15T12:00:00"
  }
}
```

---

## 🧪 测试持久化

### 运行测试

```bash
python backend/test_persistence.py
```

### 测试流程

1. 写入数据（用户偏好、任务、摘要、画像）
2. 检查文件是否创建
3. 模拟程序重启（清除内存单例）
4. 重新加载数据
5. 验证数据是否正确

### 预期输出

```
✅ 添加了用户偏好
✅ 添加了2个任务
✅ 保存了摘要
✅ 保存了用户画像

检查文件:
  ✅ preferences.json (549 bytes)
  ✅ tasks.json (932 bytes)
  ✅ summaries.json (83 bytes)
  ✅ profiles.json (179 bytes)

✅ 用户偏好加载成功
✅ 任务历史加载成功
✅ 摘要加载成功
✅ 用户画像加载成功

🎉 所有持久化测试通过！
```

---

## 🔧 配置选项

### 存储限制

```python
storage = MemoryStorage(
    max_conversations=10,   # 内存中保留的最大对话轮数
    max_tasks=100,          # 持久化的最大任务数
    max_sessions=1000       # 最大会话数
)
```

### 自定义存储目录

```python
storage = MemoryStorage(
    storage_dir='/path/to/custom/dir'
)
```

---

## 🛡️ 数据安全

### 错误处理

持久化操作包含完整的错误处理：

```python
def _save_preferences(self):
    """保存用户偏好"""
    try:
        with open(self._preferences_file, 'w', encoding='utf-8') as f:
            json.dump(self._preferences, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"保存用户偏好失败: {e}")
        # 不会中断程序运行
```

### 数据备份

建议定期备份存储目录：

```bash
# Linux/Mac
cp -r ~/.daoyoucode/memory ~/.daoyoucode/memory.backup

# Windows
xcopy /E /I %USERPROFILE%\.daoyoucode\memory %USERPROFILE%\.daoyoucode\memory.backup
```

---

## 🔍 调试持久化

### 查看存储文件

```bash
# Linux/Mac
ls -lh ~/.daoyoucode/memory/
cat ~/.daoyoucode/memory/preferences.json

# Windows
dir %USERPROFILE%\.daoyoucode\memory
type %USERPROFILE%\.daoyoucode\memory\preferences.json
```

### 启用详细日志

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 会看到详细的加载和保存日志
# INFO - 加载了 2 个用户的偏好
# INFO - 保存用户偏好成功
```

### 手动清除数据

```bash
# 清除所有持久化数据
rm -rf ~/.daoyoucode/memory/

# 或只清除特定文件
rm ~/.daoyoucode/memory/preferences.json
```

---

## 📈 性能考虑

### 写入性能

- 每次修改都会立即写入磁盘
- 使用JSON格式，写入速度快
- 文件大小通常很小（KB级别）

### 读取性能

- 程序启动时一次性加载所有数据
- 后续操作都在内存中进行
- 不会影响运行时性能

### 优化建议

如果数据量很大（>10MB），可以考虑：

1. 增加批量写入（减少IO次数）
2. 使用数据库（SQLite）
3. 实现延迟写入（定期保存）

---

## 🎯 使用建议

### 对话历史

- **不持久化**：每次会话独立，避免历史混乱
- **使用摘要**：长对话生成摘要并持久化
- **跨会话检索**：使用向量检索查找相关历史

### 用户偏好

- **持久化**：用户设置应该永久保存
- **自动学习**：从用户行为中学习偏好
- **手动设置**：提供配置界面让用户修改

### 任务历史

- **持久化**：记录用户的所有操作
- **限制数量**：只保留最近N个任务
- **用于分析**：分析用户习惯和常用功能

### 摘要和画像

- **持久化**：长期记忆的核心
- **定期更新**：随着对话增加而更新
- **用于个性化**：提供更好的用户体验

---

## ✅ 检查清单

- [x] 用户偏好持久化
- [x] 任务历史持久化
- [x] 对话摘要持久化
- [x] 关键信息持久化
- [x] 用户画像持久化
- [x] 自动加载
- [x] 自动保存
- [x] 错误处理
- [x] 测试验证

---

## 🎉 总结

Memory系统现在支持完整的持久化功能：

- ✅ 用户偏好、任务历史等重要数据会永久保存
- ✅ 程序重启后自动加载
- ✅ 修改时自动保存
- ✅ 完整的错误处理
- ✅ 简单的JSON格式，易于查看和备份

对话历史保持临时存储，避免历史混乱，但可以通过摘要功能保留重要信息。

**存储位置**: `~/.daoyoucode/memory/`

**测试命令**: `python backend/test_persistence.py`
