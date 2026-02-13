# LLM Function Calling 无限循环问题

## 问题描述

LLM在调用工具后，无法理解应该停止调用并给出最终答案，导致：
1. 重复调用同一个工具（参数相同或略有不同）
2. 达到最大迭代次数（5次）后强制停止
3. 没有返回有意义的最终答案

## 问题表现

```
🔧 执行工具: repo_map
   参数: {'repo_path': 'backend', ...}
   ✓ 执行完成
   
🔧 执行工具: repo_map
   参数: {'repo_path': 'backend/', ...}  # 参数略有不同
   ✓ 执行完成
   
🔧 执行工具: repo_map
   参数: {'repo_path': 'backend/', ...}  # 又调用一次
   ✓ 执行完成
   
... (重复5次)

达到最大工具调用迭代次数: 5
```

## 已尝试的修复

### 1. 修复工具结果格式 ✓
- **问题**: `str(tool_result)` 返回整个对象的字符串表示
- **修复**: 改为 `str(tool_result.content)`
- **结果**: 问题依然存在

### 2. 检查工具注册 ✓
- 工具正确注册（25个工具）
- 工具能被正确调用
- 工具返回正确的结果

## 根本原因分析

问题可能在于：

### 1. LLM的Function Calling实现
当前使用的是通义千问（qwen-plus），可能的问题：
- LLM不理解何时停止调用工具
- 工具返回结果的格式不符合LLM的预期
- 消息历史的构建方式有问题

### 2. 消息历史格式
当前的消息格式：
```python
messages = [
    {"role": "user", "content": prompt},
    {"role": "assistant", "content": None, "function_call": {...}},
    {"role": "function", "name": tool_name, "content": tool_result_str},
    ...
]
```

可能需要的格式（OpenAI标准）：
```python
messages = [
    {"role": "user", "content": prompt},
    {"role": "assistant", "content": "", "tool_calls": [...]},  # 注意：tool_calls而不是function_call
    {"role": "tool", "tool_call_id": "...", "content": result},
    ...
]
```

### 3. LLM客户端实现
需要检查 `backend/daoyoucode/agents/llm/` 中的客户端实现：
- 是否正确处理function calling
- 是否正确构建请求
- 是否正确解析响应

## 可能的解决方案

### 方案1: 检查LLM客户端实现
查看 `backend/daoyoucode/agents/llm/clients/` 中通义千问的实现，确认：
1. Function calling的请求格式是否正确
2. 响应解析是否正确
3. 是否支持多轮function calling

### 方案2: 简化测试
创建一个最简单的function calling测试：
1. 只有一个简单工具（如get_time）
2. 只调用一次
3. 检查LLM是否能正确停止

### 方案3: 参考daoyouCodePilot
查看daoyouCodePilot中function calling的实现方式

### 方案4: 添加停止条件
在工具调用循环中添加额外的停止条件：
1. 检查工具返回结果是否足够回答问题
2. 检查是否重复调用同一工具
3. 添加更智能的停止逻辑

### 方案5: 使用不同的LLM
测试其他LLM（如GPT-4）是否有同样的问题

## 下一步行动

1. **优先级1**: 检查LLM客户端的function calling实现
2. **优先级2**: 创建简单的function calling测试
3. **优先级3**: 参考daoyouCodePilot的实现
4. **优先级4**: 考虑添加智能停止逻辑

## 相关文件

- `backend/daoyoucode/agents/core/agent.py` - Agent基类，工具调用循环
- `backend/daoyoucode/agents/llm/clients/` - LLM客户端实现
- `backend/daoyoucode/agents/llm/base.py` - LLM基类
- `skills/chat-assistant/skill.yaml` - Skill配置
- `skills/chat-assistant/prompts/chat_assistant.md` - Prompt配置

## 临时解决方案

在修复之前，可以：
1. 增加最大迭代次数（但治标不治本）
2. 在达到最大迭代次数后，强制LLM基于已有信息给出答案
3. 禁用function calling，使用简单的对话模式
