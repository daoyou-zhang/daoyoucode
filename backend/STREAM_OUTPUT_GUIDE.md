# 流式输出使用指南

## 概述

流式输出（Streaming Output）是一种实时返回LLM响应的技术，可以逐token显示内容，而不是等待完整响应生成后才返回。这大幅提升了用户体验，特别是在长响应场景下。

---

## 核心特性

### 1. 实时反馈
- 逐token返回，用户立即看到响应
- 首字延迟（TTFT）低，体验流畅
- 长响应时不会感觉"卡住"

### 2. 事件驱动
- `token` 事件：每个文本token
- `metadata` 事件：状态信息（开始/完成）
- `error` 事件：错误信息

### 3. 自动降级
- 带工具调用时自动降级到普通模式
- 保证功能完整性

### 4. 完整记忆管理
- 保持智能加载、摘要生成等功能
- 与普通模式行为一致

---

## 使用方法

### 基础用法

```python
from daoyoucode.agents.core.agent import BaseAgent, AgentConfig

# 创建Agent
config = AgentConfig(
    name="chat_agent",
    description="聊天助手",
    model="qwen-turbo",
    temperature=0.7,
    system_prompt="你是一个友好的AI助手。"
)
agent = BaseAgent(config)

# 流式执行
async for event in agent.execute_stream(
    prompt_source={'use_agent_default': True},
    user_input="介绍一下Python",
    context={'session_id': 'demo', 'user_id': 'user123'}
):
    if event['type'] == 'token':
        # 处理文本token
        print(event['content'], end='', flush=True)
    
    elif event['type'] == 'metadata':
        # 处理元数据
        data = event['data']
        if data.get('status') == 'started':
            print("[开始]")
        elif data.get('done'):
            print("\n[完成]")
    
    elif event['type'] == 'error':
        # 处理错误
        print(f"错误: {event['error']}")
```

### 事件类型

#### 1. Token事件
```python
{
    'type': 'token',
    'content': '文本内容'
}
```

每个文本token都会触发一个token事件。

#### 2. Metadata事件
```python
# 开始事件
{
    'type': 'metadata',
    'data': {'status': 'started'}
}

# 完成事件
{
    'type': 'metadata',
    'data': {'status': 'completed', 'done': True}
}

# 失败事件
{
    'type': 'metadata',
    'data': {'status': 'failed', 'done': True}
}
```

#### 3. Error事件
```python
{
    'type': 'error',
    'error': '错误信息'
}
```

---

## 实际示例

### 示例1：简单聊天

```python
import asyncio

async def simple_chat():
    agent = BaseAgent(config)
    
    print("用户: 介绍一下Python")
    print("AI: ", end='', flush=True)
    
    async for event in agent.execute_stream(
        prompt_source={'use_agent_default': True},
        user_input="介绍一下Python",
        context={'session_id': 'chat1', 'user_id': 'user1'}
    ):
        if event['type'] == 'token':
            print(event['content'], end='', flush=True)
    
    print()  # 换行

asyncio.run(simple_chat())
```

### 示例2：带错误处理

```python
async def chat_with_error_handling():
    agent = BaseAgent(config)
    
    try:
        async for event in agent.execute_stream(
            prompt_source={'use_agent_default': True},
            user_input="你好",
            context={'session_id': 'chat2', 'user_id': 'user2'}
        ):
            if event['type'] == 'token':
                print(event['content'], end='', flush=True)
            
            elif event['type'] == 'error':
                print(f"\n错误: {event['error']}")
                break
            
            elif event['type'] == 'metadata':
                if event['data'].get('status') == 'failed':
                    print("\n执行失败")
                    break
    
    except Exception as e:
        print(f"异常: {e}")
```

### 示例3：收集完整响应

```python
async def collect_full_response():
    agent = BaseAgent(config)
    
    full_response = ""
    
    async for event in agent.execute_stream(
        prompt_source={'use_agent_default': True},
        user_input="解释一下异步编程",
        context={'session_id': 'chat3', 'user_id': 'user3'}
    ):
        if event['type'] == 'token':
            content = event['content']
            full_response += content
            print(content, end='', flush=True)
    
    print(f"\n\n完整响应长度: {len(full_response)} 字符")
    return full_response
```

---

## 与普通模式对比

### 普通模式（execute）

```python
# 等待完整响应
result = await agent.execute(
    prompt_source={'use_agent_default': True},
    user_input="介绍一下Python",
    context={'session_id': 'demo', 'user_id': 'user1'}
)

print(result.content)  # 一次性输出
```

**特点**：
- 等待时间长（2-10秒）
- 一次性返回完整内容
- 支持工具调用
- 用户体验较差（长时间等待）

### 流式模式（execute_stream）

```python
# 实时显示响应
async for event in agent.execute_stream(
    prompt_source={'use_agent_default': True},
    user_input="介绍一下Python",
    context={'session_id': 'demo', 'user_id': 'user1'}
):
    if event['type'] == 'token':
        print(event['content'], end='', flush=True)
```

**特点**：
- 首字延迟低（<100ms）
- 逐token实时显示
- 不支持工具调用（自动降级）
- 用户体验好（实时反馈）

---

## 性能指标

### TTFT（Time To First Token）
首字延迟，从发送请求到收到第一个token的时间。

- 流式模式：通常 < 100ms
- 普通模式：需要等待完整响应（2-10秒）

### 吞吐量
每秒生成的token数。

- 流式模式：~50-100 tokens/s（取决于模型和网络）
- 普通模式：相同，但用户感知延迟高

### 用户体验
- 流式模式：⭐⭐⭐⭐⭐（实时反馈）
- 普通模式：⭐⭐（需要等待）

---

## 限制和注意事项

### 1. 不支持工具调用

流式模式下不支持工具调用。如果提供了 `tools` 参数，会自动降级到普通模式。

```python
# 会自动降级到普通模式
async for event in agent.execute_stream(
    prompt_source={'use_agent_default': True},
    user_input="查询天气",
    context={'session_id': 'demo', 'user_id': 'user1'},
    tools=['weather_tool']  # 提供了工具
):
    # 实际上会调用 execute() 而不是流式输出
    pass
```

### 2. 需要LLM客户端支持

LLM客户端必须实现 `stream_chat()` 方法。当前支持的客户端：
- UnifiedLLMClient（OpenAI兼容格式）

### 3. 错误处理

流式输出过程中可能出现网络错误、超时等问题，需要正确处理 `error` 事件。

### 4. 记忆管理

流式模式下仍然保持完整的记忆管理功能：
- 智能加载对话历史
- 生成摘要
- 更新用户画像
- 保存任务历史

---

## 最佳实践

### 1. 实时显示

```python
# 使用 flush=True 确保实时显示
print(event['content'], end='', flush=True)
```

### 2. 错误恢复

```python
async for event in agent.execute_stream(...):
    if event['type'] == 'error':
        # 记录错误
        logger.error(f"流式输出错误: {event['error']}")
        # 可以选择重试或降级
        break
```

### 3. 进度提示

```python
async for event in agent.execute_stream(...):
    if event['type'] == 'metadata':
        if event['data'].get('status') == 'started':
            print("🤖 AI正在思考...")
        elif event['data'].get('done'):
            print("\n✅ 完成")
```

### 4. 性能监控

```python
import time

start_time = time.time()
first_token_time = None
token_count = 0

async for event in agent.execute_stream(...):
    if event['type'] == 'token':
        if first_token_time is None:
            first_token_time = time.time()
        token_count += 1

end_time = time.time()

ttft = first_token_time - start_time if first_token_time else 0
total_time = end_time - start_time

print(f"TTFT: {ttft*1000:.0f}ms")
print(f"总耗时: {total_time:.1f}s")
print(f"速度: {token_count/total_time:.1f} tokens/s")
```

---

## 前端集成

### Web前端（JavaScript）

```javascript
async function streamChat(userInput) {
    const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            user_input: userInput,
            session_id: 'demo',
            user_id: 'user1'
        })
    });
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    while (true) {
        const {done, value} = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        const events = chunk.split('\n').filter(line => line.trim());
        
        for (const line of events) {
            const event = JSON.parse(line);
            
            if (event.type === 'token') {
                // 实时显示token
                appendToChat(event.content);
            } else if (event.type === 'error') {
                showError(event.error);
            }
        }
    }
}
```

### CLI（Python）

```python
async def cli_chat():
    while True:
        user_input = input("\n你: ")
        if user_input.lower() in ['quit', 'exit']:
            break
        
        print("AI: ", end='', flush=True)
        
        async for event in agent.execute_stream(
            prompt_source={'use_agent_default': True},
            user_input=user_input,
            context={'session_id': 'cli', 'user_id': 'user1'}
        ):
            if event['type'] == 'token':
                print(event['content'], end='', flush=True)
        
        print()  # 换行
```

---

## 测试

### 单元测试

参考 `backend/test_stream_output.py`：
- 基础流式输出测试
- 带工具降级测试
- 错误处理测试
- 性能测试

### 实际演示

参考 `backend/example_stream_chat.py`：
- 流式聊天示例
- 对比流式vs普通模式
- 性能指标展示

---

## 总结

流式输出是提升用户体验的关键功能：

✅ **优势**：
- 实时反馈，首字延迟低
- 长响应时体验好
- 更现代的交互方式

⚠️ **限制**：
- 不支持工具调用（自动降级）
- 需要LLM客户端支持

🎯 **适用场景**：
- 聊天对话
- 内容生成
- 长文本响应
- 需要实时反馈的场景

❌ **不适用场景**：
- 需要工具调用的任务
- 需要完整响应后再处理的场景
