# 共享缓存快速测试指南

## 🚀 快速开始

### 1. 确认配置

检查 `backend/.env` 文件：
```bash
DEBUG_LLM=1
DEBUG_LLM_REQUEST=1
LOG_LEVEL=DEBUG
```

### 2. 运行测试命令

```bash
cd backend
python -m daoyoucode.cli chat "请分析 chat_assistant_v2.md 文档的结构"
```

### 3. 观察输出

**期望看到的关键信息**：

#### ✅ 第一个Agent执行工具
```
🔧 执行工具: text_search (programmer)
query         chat_assistant_v2.md
file_pattern  **/*.md
✓ 执行完成 (2.16秒)
```

#### ✅ 第二个Agent命中缓存
```
🔧 执行工具: text_search (code_analyzer)
query         chat_assistant_v2.md
file_pattern  **/*.md
✓ 执行完成 (0.00秒) (缓存)  👈 关键：显示 "(缓存)" 标记
```

#### ✅ 缓存统计
```
📊 共享缓存统计: 共缓存了2个工具调用结果
```

## 🔍 验证清单

### UI输出验证
- [ ] 第二次相同工具调用显示 `(缓存)` 标记
- [ ] 缓存命中的执行时间接近 `0.00秒`
- [ ] 最后显示缓存统计信息

### 日志验证

查看日志：
```bash
cd backend
tail -n 200 logs/daoyoucode_*.log | grep -E "(共享缓存|缓存命中|保存到共享缓存)"
```

期望看到：
```
[INFO] 💾 保存到共享缓存: text_search
[INFO] 🔄 共享缓存命中: text_search (code_analyzer) - 另一个Agent已执行过，直接使用结果
[INFO] 📊 共享缓存统计: 共缓存了2个工具调用结果
```

## 🐛 常见问题

### 问题1：没有显示 "(缓存)" 标记

**可能原因**：
1. 只有一个辅助Agent被选中（没有重复调用）
2. 工具参数不同（不会命中缓存）
3. 使用了 chat-assistant 而不是 sisyphus-orchestrator

**解决方法**：
```bash
# 检查当前使用的编排器
cd backend
grep -r "orchestrator" .daoyoucode.conf.yml

# 应该看到：
# orchestrator: sisyphus-orchestrator
```

### 问题2：缓存统计显示0

**可能原因**：
- 没有辅助Agent被执行
- 意图识别判断为简单寒暄

**解决方法**：
使用更明确的编程相关问题，例如：
```bash
python -m daoyoucode.cli chat "请帮我重构 hello_world.py 文件"
```

### 问题3：日志中没有缓存相关信息

**可能原因**：
- LOG_LEVEL 不是 DEBUG
- 日志文件路径错误

**解决方法**：
```bash
# 检查日志配置
cd backend
cat .env | grep LOG_LEVEL

# 查找最新的日志文件
ls -lt logs/ | head -5
```

## 📊 性能对比测试

### 测试步骤

1. **测试有缓存的情况**：
```bash
cd backend
time python -m daoyoucode.cli chat "请分析 chat_assistant_v2.md 文档"
```
记录时间：`T1 = X.XX秒`

2. **临时禁用缓存**（可选）：
编辑 `backend/daoyoucode/agents/core/agent.py`，注释掉缓存检查：
```python
# 在第1000行左右
# elif cache_key in shared_tool_cache:
#     # 缓存逻辑...
#     continue
```

3. **测试无缓存的情况**：
```bash
time python -m daoyoucode.cli chat "请分析 chat_assistant_v2.md 文档"
```
记录时间：`T2 = X.XX秒`

4. **计算性能提升**：
```
性能提升 = (T2 - T1) / T2 * 100%
```

### 预期结果

| 场景 | 无缓存 | 有缓存 | 提升 |
|------|--------|--------|------|
| 2个辅助Agent | 4.5秒 | 2.5秒 | ~44% |
| 3个辅助Agent | 6.5秒 | 3.0秒 | ~54% |
| 4个辅助Agent | 8.5秒 | 3.5秒 | ~59% |

## ✅ 测试成功标准

### 必须满足
- [x] UI显示 "(缓存)" 标记
- [x] 缓存命中执行时间 < 0.1秒
- [x] 日志包含 "🔄 共享缓存命中" 消息
- [x] 显示缓存统计信息

### 性能要求
- [x] 2个辅助Agent：性能提升 ≥ 30%
- [x] 3个辅助Agent：性能提升 ≥ 40%
- [x] 4个辅助Agent：性能提升 ≥ 50%

## 📝 测试报告示例

```markdown
## 测试报告

**测试时间**：2024-03-07 14:30

**测试命令**：
```bash
python -m daoyoucode.cli chat "请分析 chat_assistant_v2.md 文档的结构"
```

**UI输出**：
```
🔧 执行工具: text_search (programmer)
✓ 执行完成 (2.16秒)

🔧 执行工具: text_search (code_analyzer)
✓ 执行完成 (0.00秒) (缓存)  ✅

🔧 执行工具: read_file (programmer)
✓ 执行完成 (0.01秒)

🔧 执行工具: read_file (code_analyzer)
✓ 执行完成 (0.00秒) (缓存)  ✅

📊 共享缓存统计: 共缓存了2个工具调用结果  ✅
```

**性能数据**：
- 无缓存：4.33秒
- 有缓存：2.17秒
- 性能提升：49.9%  ✅

**验证结果**：
- ✅ 缓存命中显示正确
- ✅ 执行时间符合预期
- ✅ 日志信息完整
- ✅ 性能提升达标

**结论**：✅ 测试通过
```

## 🎯 下一步

测试通过后，可以：
1. 关闭调试日志（生产环境）
2. 监控实际使用中的缓存效果
3. 根据使用情况优化缓存策略

测试失败时，参考 `TEST_SHARED_CACHE.md` 中的详细排查步骤。
