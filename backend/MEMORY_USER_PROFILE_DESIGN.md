# 用户画像设计说明

## 🎯 设计原则

用户画像是**长期记忆**的一部分，用于理解用户的整体行为模式，而不是用于每轮对话的上下文。

---

## 📊 数据层次

Memory系统有三个层次的用户数据：

### 1. 对话历史（临时，会话级）

```python
# 存储：内存
# 生命周期：当前会话
# 用途：对话上下文

history = memory.get_conversation_history(session_id)
# [
#   {'user': '问题1', 'ai': '回答1'},
#   {'user': '问题2', 'ai': '回答2'}
# ]
```

### 2. 用户偏好（持久化，轻量级）

```python
# 存储：磁盘（preferences.json）
# 生命周期：永久
# 用途：个性化设置

prefs = memory.get_preferences(user_id)
# {
#   'language': 'python',
#   'style': 'functional',
#   'theme': 'dark'
# }
```

### 3. 用户画像（持久化，重量级）

```python
# 存储：磁盘（profiles.json）
# 生命周期：永久
# 用途：长期分析、报告生成

profile = agent.get_user_profile(user_id)
# {
#   'common_topics': ['python', 'testing', 'refactoring'],
#   'total_conversations': 150,
#   'preferred_style': 'functional',
#   'activity_pattern': 'evening',
#   'skill_level': 'advanced'
# }
```

---

## 🚫 错误用法

### ❌ 每轮对话都加载用户画像

```python
async def execute(self, ...):
    # 错误：每轮都加载
    profile = self.memory.long_term_memory.get_user_profile(user_id)
    
    # 问题：
    # 1. 性能差（每轮都读取磁盘）
    # 2. 用途不明确（对话上下文已经足够）
    # 3. 信息冗余（用户偏好已经包含关键信息）
```

### ❌ 在智能加载中包含用户画像

```python
# 错误：在load_context_smart中加载用户画像
context = await memory.load_context_smart(...)
profile = context.get('profile')  # 不应该这样

# 问题：
# 1. 混淆了对话上下文和用户画像
# 2. 增加了每轮对话的开销
# 3. 用户画像不是对话上下文的一部分
```

---

## ✅ 正确用法

### 1. 按需加载（推荐）

```python
# 场景：生成用户报告
async def generate_user_report(self, user_id: str):
    # 按需加载用户画像
    profile = self.get_user_profile(user_id)
    
    if profile:
        report = f"""
        用户报告
        ========
        常讨论话题: {', '.join(profile['common_topics'])}
        总对话数: {profile['total_conversations']}
        技能水平: {profile['skill_level']}
        """
        return report
```

### 2. 个性化推荐

```python
# 场景：推荐相关工具或功能
async def recommend_tools(self, user_id: str):
    profile = self.get_user_profile(user_id)
    
    if profile:
        topics = profile.get('common_topics', [])
        
        if 'testing' in topics:
            return ['pytest', 'unittest', 'coverage']
        elif 'refactoring' in topics:
            return ['black', 'pylint', 'mypy']
```

### 3. 跨会话理解

```python
# 场景：用户提到"上次的项目"
async def resolve_reference(self, user_id: str, message: str):
    if '上次' in message or '之前' in message:
        # 加载用户画像，查找历史项目
        profile = self.get_user_profile(user_id)
        
        if profile:
            recent_projects = profile.get('recent_projects', [])
            return recent_projects[0] if recent_projects else None
```

### 4. 定期更新

```python
# 场景：每N轮对话后更新用户画像
async def execute(self, ...):
    # ... 正常执行 ...
    
    # 检查是否需要更新画像
    conversation_count = len(memory.get_conversation_history(session_id))
    
    if conversation_count % 10 == 0:  # 每10轮更新一次
        await self._update_user_profile(user_id)
```

---

## 🔧 实现细节

### Agent中的缓存机制

```python
class BaseAgent:
    def __init__(self, config):
        # 用户画像缓存（按需加载）
        self._user_profile_cache: Dict[str, Dict[str, Any]] = {}
    
    def get_user_profile(self, user_id: str, force_reload: bool = False):
        """获取用户画像（带缓存）"""
        if force_reload or user_id not in self._user_profile_cache:
            # 从磁盘加载
            profile = self.memory.long_term_memory.get_user_profile(user_id)
            if profile:
                self._user_profile_cache[user_id] = profile
                self.logger.debug(f"加载用户画像: {user_id}")
        
        return self._user_profile_cache.get(user_id)
```

**优点**：
- ✅ 首次访问时加载（懒加载）
- ✅ 后续访问使用缓存（高性能）
- ✅ 支持强制刷新（force_reload=True）
- ✅ 多用户场景下自动管理缓存

---

## 📈 性能对比

### 方案1：每轮都加载（❌）

```
第1轮: 读取磁盘 (10ms)
第2轮: 读取磁盘 (10ms)
第3轮: 读取磁盘 (10ms)
...
总耗时: 10ms × N轮 = O(n)
```

### 方案2：按需加载+缓存（✅）

```
第1轮: 不需要 (0ms)
第2轮: 不需要 (0ms)
第3轮: 不需要 (0ms)
...
需要时: 读取磁盘 (10ms) → 缓存
后续: 读取缓存 (0.01ms)
总耗时: 10ms + 0.01ms × M次 ≈ 10ms
```

---

## 🎯 使用建议

### 日常对话

```python
async def execute(self, ...):
    # ✅ 使用用户偏好（轻量级）
    prefs = self.memory.get_preferences(user_id)
    
    # ✅ 使用对话历史
    context = await self.memory.load_context_smart(...)
    
    # ❌ 不要加载用户画像
    # profile = self.get_user_profile(user_id)  # 不需要
```

### 特殊场景

```python
# ✅ 生成报告时
if user_input.startswith('/report'):
    profile = self.get_user_profile(user_id)
    return self.generate_report(profile)

# ✅ 个性化推荐时
if user_input.startswith('/recommend'):
    profile = self.get_user_profile(user_id)
    return self.recommend_tools(profile)

# ✅ 跨会话引用时
if '上次' in user_input or '之前' in user_input:
    profile = self.get_user_profile(user_id)
    return self.resolve_reference(profile, user_input)
```

---

## 🔄 更新策略

### 何时更新用户画像？

1. **定期更新**：每N轮对话后
2. **会话结束时**：会话结束时汇总
3. **手动触发**：用户请求时
4. **异步更新**：后台定期分析

### 更新示例

```python
async def _update_user_profile(self, user_id: str):
    """更新用户画像"""
    # 获取所有会话
    all_sessions = self._get_user_sessions(user_id)
    
    # 构建画像
    profile = await self.memory.long_term_memory.build_user_profile(
        user_id, all_sessions
    )
    
    # 清除缓存，强制下次重新加载
    if user_id in self._user_profile_cache:
        del self._user_profile_cache[user_id]
    
    self.logger.info(f"更新了用户画像: {user_id}")
```

---

## 📚 数据流

```
用户输入
  ↓
判断是否需要用户画像
  ↓
  ├─ 否 → 使用用户偏好（轻量级）
  │        ↓
  │      正常对话
  │
  └─ 是 → 加载用户画像（重量级）
           ↓
         检查缓存
           ↓
         ├─ 有缓存 → 使用缓存（快）
         └─ 无缓存 → 读取磁盘 → 缓存（慢）
           ↓
         特殊处理（报告、推荐等）
```

---

## ✅ 检查清单

- [x] 用户画像不在每轮对话中加载
- [x] 用户画像按需加载+缓存
- [x] 用户偏好用于日常个性化
- [x] 对话历史用于上下文
- [x] 用户画像用于长期分析
- [x] 性能优化（缓存机制）
- [x] 清晰的使用场景

---

## 🎉 总结

**用户画像的正确定位**：
- 不是对话上下文的一部分
- 不是每轮对话都需要的
- 是长期行为分析的工具
- 是特殊场景的辅助

**使用原则**：
- 日常对话：用户偏好 + 对话历史
- 特殊场景：用户画像（按需加载）
- 性能优化：缓存机制

**实现方式**：
- 按需加载（懒加载）
- 内存缓存（高性能）
- 支持刷新（force_reload）

这样的设计既保留了用户画像的功能，又避免了性能问题。
