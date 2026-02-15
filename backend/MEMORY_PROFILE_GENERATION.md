# 用户画像生成策略

## 🎯 生成时机

用户画像采用**智能触发**策略，在以下情况下自动生成/更新：

### 1. 首次生成（10轮对话后）

```python
# 条件：用户对话数 >= 10 且没有画像
if conversation_count >= 10 and not has_profile:
    await build_user_profile(user_id)
```

**原因**：
- 10轮对话足以了解用户的基本特征
- 避免过早生成（数据不足）
- 避免过晚生成（错过个性化机会）

### 2. 定期更新（每20轮）

```python
# 条件：对话数增加了20轮
if current_count - last_count >= 20:
    await build_user_profile(user_id)
```

**原因**：
- 用户习惯会随时间变化
- 定期更新保持画像准确性
- 20轮是平衡频率和性能的最佳值

### 3. 手动触发

```python
# 用户命令
if user_input == '/update-profile':
    await build_user_profile(user_id, force=True)
```

**原因**：
- 用户可以主动更新画像
- 用于测试和调试
- 提供用户控制权

### 4. 会话结束时（可选）

```python
# 会话结束时
async def on_session_end(session_id, user_id):
    await build_user_profile(user_id)
```

**原因**：
- 汇总本次会话的信息
- 不阻塞用户交互
- 后台异步执行

---

## 📊 生成流程

### 完整流程

```
1. 触发条件检查
   ↓
2. 收集用户数据
   ├─ 所有会话历史
   ├─ 对话记录
   ├─ 关键信息
   └─ 用户偏好
   ↓
3. 基础分析（规则）
   ├─ 提取常见话题
   ├─ 分析技能水平
   ├─ 分析偏好风格
   ├─ 分析活动模式
   └─ 提取最近项目
   ↓
4. 深度分析（LLM，可选）
   ├─ 兴趣爱好
   ├─ 学习目标
   ├─ 痛点问题
   └─ 沟通风格
   ↓
5. 保存到磁盘
   ↓
6. 清除缓存
```

### 代码示例

```python
# 在Agent的execute方法中
async def execute(self, ...):
    # ... 正常执行 ...
    
    # 保存对话
    self.memory.add_conversation(session_id, user_input, response)
    
    # 检查是否需要更新画像
    await self._check_and_update_profile(user_id, session_id)
    
    return result

async def _check_and_update_profile(self, user_id, session_id):
    """检查并更新用户画像"""
    # 获取总对话数
    tasks = self.memory.get_task_history(user_id, limit=1000)
    total_conversations = len(tasks)
    
    # 检查是否需要更新
    should_update = self.memory.long_term_memory.should_update_profile(
        user_id, total_conversations
    )
    
    if should_update:
        # 异步更新（不阻塞）
        await self._update_user_profile_async(user_id)
```

---

## 🔍 分析维度

### 1. 常见话题（Common Topics）

**方法**：统计关键词频率

```python
keywords = ['python', 'javascript', 'testing', 'refactoring', ...]

for conversation in all_conversations:
    for keyword in keywords:
        if keyword in conversation['user'].lower():
            topic_counter[keyword] += 1

# 返回前5个
common_topics = topic_counter.most_common(5)
```

**示例输出**：
```json
{
  "common_topics": ["python", "testing", "refactoring", "api", "docker"]
}
```

### 2. 技能水平（Skill Level）

**方法**：启发式规则

```python
complex_indicators = [
    'architecture', 'design pattern', 'optimization',
    'performance', 'scalability', 'concurrency'
]

complex_ratio = count_complex / total_conversations

if complex_ratio > 0.3:
    skill_level = 'advanced'
elif complex_ratio > 0.1:
    skill_level = 'intermediate'
else:
    skill_level = 'beginner'
```

**示例输出**：
```json
{
  "skill_level": "intermediate"
}
```

### 3. 偏好风格（Preferred Style）

**方法**：关键词匹配

```python
style_keywords = {
    'functional': ['functional', 'lambda', 'map', 'filter'],
    'oop': ['class', 'object', 'inheritance'],
    'procedural': ['function', 'procedure', 'step by step']
}

# 统计每种风格的出现次数
# 返回最常见的
```

**示例输出**：
```json
{
  "preferred_style": "functional"
}
```

### 4. 活动模式（Activity Pattern）

**方法**：时间戳分析

```python
# 提取所有对话的时间戳
hours = [datetime.fromisoformat(conv['timestamp']).hour 
         for conv in conversations]

avg_hour = sum(hours) / len(hours)

if 6 <= avg_hour < 12:
    pattern = 'morning'
elif 12 <= avg_hour < 18:
    pattern = 'afternoon'
elif 18 <= avg_hour < 24:
    pattern = 'evening'
else:
    pattern = 'night'
```

**示例输出**：
```json
{
  "activity_pattern": "evening"
}
```

### 5. 最近项目（Recent Projects）

**方法**：关键词提取

```python
project_indicators = ['project', '项目', 'working on', '在做']

# 从最近20轮对话中提取
for conv in conversations[-20:]:
    if any(indicator in conv['user'] for indicator in project_indicators):
        # 提取项目名称
        extract_project_name(conv['user'])
```

**示例输出**：
```json
{
  "recent_projects": ["web-app", "cli-tool", "api-service"]
}
```

### 6. 深度分析（LLM，可选）

**方法**：使用LLM分析对话

```python
prompt = f"""
分析以下用户的对话记录，提取用户画像信息：

{sampled_conversations}

请以JSON格式返回：
{{
    "interests": ["兴趣1", "兴趣2"],
    "learning_goals": ["目标1", "目标2"],
    "pain_points": ["痛点1", "痛点2"],
    "communication_style": "简洁/详细/技术性"
}}
"""

response = await llm_client.chat(prompt)
analysis = json.loads(response.content)
```

**示例输出**：
```json
{
  "interests": ["web开发", "性能优化"],
  "learning_goals": ["掌握微服务架构", "提升代码质量"],
  "pain_points": ["调试困难", "性能瓶颈"],
  "communication_style": "技术性"
}
```

---

## 📈 性能优化

### 1. 异步更新

```python
# ❌ 同步更新（阻塞用户）
profile = await build_user_profile(user_id)  # 可能需要5-10秒

# ✅ 异步更新（不阻塞）
asyncio.create_task(build_user_profile(user_id))  # 后台执行
```

### 2. 采样分析

```python
# ❌ 分析所有对话（慢）
all_conversations = get_all_conversations(user_id)  # 可能有1000+条

# ✅ 采样分析（快）
sampled = conversations[-50:]  # 只分析最近50条
```

### 3. 缓存结果

```python
# ✅ 生成后缓存
profile = await build_user_profile(user_id)
cache[user_id] = profile

# ✅ 后续访问使用缓存
profile = cache.get(user_id) or load_from_disk(user_id)
```

### 4. 增量更新

```python
# ❌ 每次重新分析所有数据
profile = analyze_all_conversations(user_id)

# ✅ 增量更新（只分析新数据）
new_conversations = get_conversations_since(last_update)
profile = update_profile_incrementally(profile, new_conversations)
```

---

## 🎯 使用示例

### 自动生成

```python
# 在Agent中自动触发
async def execute(self, ...):
    # ... 执行任务 ...
    
    # 保存对话
    self.memory.add_conversation(session_id, user_input, response)
    
    # 自动检查并更新画像
    await self._check_and_update_profile(user_id, session_id)
    # 输出：
    # 🔄 触发用户画像更新: user_id=user-123, conversations=20
    # ✅ 用户画像已更新: user_id=user-123
```

### 手动生成

```python
# 用户命令触发
if user_input == '/update-profile':
    profile = await agent.memory.long_term_memory.build_user_profile(
        user_id=user_id,
        llm_client=llm_client
    )
    
    return f"用户画像已更新：\n{format_profile(profile)}"
```

### 定时任务

```python
# 后台定时任务（每天凌晨）
async def daily_profile_update():
    """每天更新所有活跃用户的画像"""
    active_users = get_active_users(days=7)
    
    for user_id in active_users:
        try:
            await build_user_profile(user_id)
            logger.info(f"✅ 更新画像: {user_id}")
        except Exception as e:
            logger.error(f"❌ 更新失败: {user_id}, {e}")
        
        # 避免过载
        await asyncio.sleep(1)
```

---

## 📊 完整画像示例

```json
{
  "user_id": "user-123",
  "total_sessions": 15,
  "total_conversations": 150,
  "last_updated": "2026-02-15T12:00:00",
  
  "common_topics": [
    "python",
    "testing",
    "refactoring",
    "api",
    "docker"
  ],
  
  "skill_level": "intermediate",
  "preferred_style": "functional",
  "activity_pattern": "evening",
  
  "recent_projects": [
    "web-app",
    "cli-tool",
    "api-service"
  ],
  
  "interests": [
    "web开发",
    "性能优化",
    "自动化测试"
  ],
  
  "learning_goals": [
    "掌握微服务架构",
    "提升代码质量",
    "学习容器化部署"
  ],
  
  "pain_points": [
    "调试困难",
    "性能瓶颈",
    "测试覆盖率低"
  ],
  
  "communication_style": "技术性"
}
```

---

## ✅ 检查清单

- [x] 首次生成（10轮后）
- [x] 定期更新（每20轮）
- [x] 手动触发
- [x] 异步执行（不阻塞）
- [x] 基础分析（规则）
- [x] 深度分析（LLM，可选）
- [x] 持久化存储
- [x] 缓存机制
- [x] 性能优化

---

## 🎉 总结

**生成策略**：
- 首次：10轮对话后
- 更新：每20轮对话
- 手动：用户命令触发
- 异步：不阻塞用户交互

**分析维度**：
- 常见话题（关键词统计）
- 技能水平（启发式规则）
- 偏好风格（关键词匹配）
- 活动模式（时间分析）
- 最近项目（关键词提取）
- 深度分析（LLM，可选）

**性能优化**：
- 异步更新
- 采样分析
- 缓存结果
- 增量更新

这样的设计既保证了画像的准确性，又不影响用户体验。
