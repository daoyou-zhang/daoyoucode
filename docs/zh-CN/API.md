# daoyoucode API 参考文档

> **完整的 API 接口文档**

---

## 📋 目录

1. [REST API](#rest-api)
2. [WebSocket API](#websocket-api)
3. [Python SDK](#python-sdk)
4. [TypeScript SDK](#typescript-sdk)
5. [CLI 命令](#cli-命令)

---

## REST API

### 基础信息

- **Base URL**: `http://localhost:8000/api/v1`
- **认证**: Bearer Token（可选）
- **Content-Type**: `application/json`

### 通用响应格式

#### 成功响应

```json
{
  "success": true,
  "data": { ... },
  "message": "操作成功"
}
```

#### 错误响应

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述",
    "details": { ... }
  }
}
```

---

### 任务管理

#### 创建任务

创建一个新的编辑任务。

**请求**

```http
POST /api/v1/tasks
Content-Type: application/json

{
  "instruction": "重构登录模块",
  "files": ["auth.py", "login.py"],
  "options": {
    "model": "qwen-max",
    "temperature": 0.7,
    "auto_commit": true
  }
}
```

**参数说明**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| instruction | string | 是 | 任务指令 |
| files | array | 否 | 文件列表 |
| options | object | 否 | 任务选项 |
| options.model | string | 否 | 使用的模型 |
| options.temperature | number | 否 | 温度参数 (0-1) |
| options.auto_commit | boolean | 否 | 是否自动提交 |

**响应**

```json
{
  "success": true,
  "data": {
    "task_id": "task_123456",
    "status": "pending",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

#### 获取任务状态

获取任务的当前状态和进度。

**请求**

```http
GET /api/v1/tasks/{task_id}
```

**响应**

```json
{
  "success": true,
  "data": {
    "task_id": "task_123456",
    "status": "running",
    "progress": 0.5,
    "current_step": "分析代码结构",
    "agent": "chinese-editor",
    "started_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:01:00Z"
  }
}
```

**状态说明**

| 状态 | 说明 |
|------|------|
| pending | 等待执行 |
| running | 正在执行 |
| completed | 已完成 |
| failed | 执行失败 |
| cancelled | 已取消 |

#### 取消任务

取消正在执行的任务。

**请求**

```http
POST /api/v1/tasks/{task_id}/cancel
```

**响应**

```json
{
  "success": true,
  "message": "任务已取消"
}
```

#### 获取任务结果

获取已完成任务的结果。

**请求**

```http
GET /api/v1/tasks/{task_id}/result
```

**响应**

```json
{
  "success": true,
  "data": {
    "task_id": "task_123456",
    "status": "completed",
    "result": {
      "files_modified": ["auth.py", "login.py"],
      "changes": [
        {
          "file": "auth.py",
          "type": "edit",
          "diff": "..."
        }
      ],
      "commit_hash": "abc123",
      "message": "重构完成"
    },
    "completed_at": "2024-01-01T00:05:00Z"
  }
}
```

#### 列出任务

列出所有任务。

**请求**

```http
GET /api/v1/tasks?status=completed&limit=10&offset=0
```

**查询参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| status | string | 过滤状态 |
| limit | integer | 每页数量 |
| offset | integer | 偏移量 |

**响应**

```json
{
  "success": true,
  "data": {
    "tasks": [
      {
        "task_id": "task_123456",
        "instruction": "重构登录模块",
        "status": "completed",
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "total": 100,
    "limit": 10,
    "offset": 0
  }
}
```

---

### 智能体管理

#### 列出智能体

获取所有可用的智能体。

**请求**

```http
GET /api/v1/agents
```

**响应**

```json
{
  "success": true,
  "data": {
    "agents": [
      {
        "name": "chinese-editor",
        "model": "qwen-coder-plus",
        "description": "中文代码编辑专家",
        "capabilities": ["edit", "refactor", "analyze"]
      },
      {
        "name": "architect",
        "model": "gpt-5.2",
        "description": "架构顾问",
        "capabilities": ["design", "review"]
      }
    ]
  }
}
```

#### 调用智能体

直接调用特定智能体。

**请求**

```http
POST /api/v1/agents/{agent_name}/invoke
Content-Type: application/json

{
  "instruction": "分析这段代码的架构",
  "context": {
    "files": ["main.py"],
    "code": "..."
  }
}
```

**响应**

```json
{
  "success": true,
  "data": {
    "agent": "architect",
    "response": "这段代码采用了 MVC 架构...",
    "suggestions": [
      "建议将业务逻辑分离到 service 层",
      "可以使用依赖注入提高可测试性"
    ]
  }
}
```

---

### 文件操作

#### 读取文件

读取文件内容。

**请求**

```http
GET /api/v1/files?path=main.py
```

**响应**

```json
{
  "success": true,
  "data": {
    "path": "main.py",
    "content": "def main():\n    pass",
    "size": 1024,
    "modified_at": "2024-01-01T00:00:00Z"
  }
}
```

#### 写入文件

写入文件内容。

**请求**

```http
POST /api/v1/files
Content-Type: application/json

{
  "path": "main.py",
  "content": "def main():\n    print('Hello')"
}
```

**响应**

```json
{
  "success": true,
  "message": "文件已保存"
}
```

#### 列出文件

列出目录下的文件。

**请求**

```http
GET /api/v1/files/list?path=src&recursive=true
```

**响应**

```json
{
  "success": true,
  "data": {
    "files": [
      {
        "path": "src/main.py",
        "type": "file",
        "size": 1024
      },
      {
        "path": "src/utils",
        "type": "directory"
      }
    ]
  }
}
```

---

### 配置管理

#### 获取配置

获取当前配置。

**请求**

```http
GET /api/v1/config
```

**响应**

```json
{
  "success": true,
  "data": {
    "llm": {
      "main_model": "qwen-max",
      "temperature": 0.7
    },
    "git": {
      "auto_commit": true
    }
  }
}
```

#### 更新配置

更新配置。

**请求**

```http
PUT /api/v1/config
Content-Type: application/json

{
  "llm": {
    "main_model": "qwen-coder-plus"
  }
}
```

**响应**

```json
{
  "success": true,
  "message": "配置已更新"
}
```

---

## WebSocket API

### 连接

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
```

### 消息格式

#### 客户端 → 服务器

```json
{
  "type": "task.create",
  "data": {
    "instruction": "重构代码",
    "files": ["main.py"]
  }
}
```

#### 服务器 → 客户端

```json
{
  "type": "task.progress",
  "data": {
    "task_id": "task_123456",
    "progress": 0.5,
    "message": "正在分析代码..."
  }
}
```

### 事件类型

#### 任务事件

| 事件类型 | 说明 |
|---------|------|
| task.created | 任务已创建 |
| task.started | 任务开始执行 |
| task.progress | 任务进度更新 |
| task.completed | 任务完成 |
| task.failed | 任务失败 |

#### 智能体事件

| 事件类型 | 说明 |
|---------|------|
| agent.thinking | 智能体思考中 |
| agent.action | 智能体执行动作 |
| agent.response | 智能体响应 |

#### 系统事件

| 事件类型 | 说明 |
|---------|------|
| system.connected | 连接成功 |
| system.error | 系统错误 |
| system.ping | 心跳检测 |

### 示例

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

// 连接成功
ws.onopen = () => {
  console.log('Connected');
  
  // 创建任务
  ws.send(JSON.stringify({
    type: 'task.create',
    data: {
      instruction: '重构代码',
      files: ['main.py']
    }
  }));
};

// 接收消息
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  switch (message.type) {
    case 'task.progress':
      console.log('Progress:', message.data.progress);
      break;
    case 'task.completed':
      console.log('Completed:', message.data.result);
      break;
  }
};

// 错误处理
ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

// 连接关闭
ws.onclose = () => {
  console.log('Disconnected');
};
```

---

## Python SDK

### 安装

```bash
pip install daoyoucode
```

### 基础使用

```python
from daoyoucode import DaoyouCode

# 初始化客户端
client = DaoyouCode(
    api_key="your_api_key",
    base_url="http://localhost:8000"
)

# 创建任务
task = client.tasks.create(
    instruction="重构登录模块",
    files=["auth.py", "login.py"],
    options={
        "model": "qwen-max",
        "auto_commit": True
    }
)

print(f"Task ID: {task.task_id}")

# 等待任务完成
result = client.tasks.wait(task.task_id)
print(f"Status: {result.status}")
print(f"Files modified: {result.files_modified}")
```

### 流式响应

```python
# 流式获取任务进度
for event in client.tasks.stream(task.task_id):
    if event.type == "progress":
        print(f"Progress: {event.progress * 100}%")
    elif event.type == "completed":
        print("Task completed!")
        break
```

### 智能体调用

```python
# 调用特定智能体
response = client.agents.invoke(
    agent="architect",
    instruction="分析代码架构",
    context={"files": ["main.py"]}
)

print(response.response)
for suggestion in response.suggestions:
    print(f"- {suggestion}")
```

### 文件操作

```python
# 读取文件
content = client.files.read("main.py")
print(content)

# 写入文件
client.files.write("main.py", "def main():\n    pass")

# 列出文件
files = client.files.list("src", recursive=True)
for file in files:
    print(file.path)
```

### 异步支持

```python
import asyncio
from daoyoucode import AsyncDaoyouCode

async def main():
    client = AsyncDaoyouCode()
    
    # 异步创建任务
    task = await client.tasks.create(
        instruction="重构代码",
        files=["main.py"]
    )
    
    # 异步等待完成
    result = await client.tasks.wait(task.task_id)
    print(result.status)

asyncio.run(main())
```

---

## TypeScript SDK

### 安装

```bash
npm install @daoyoucode/sdk
# or
pnpm add @daoyoucode/sdk
```

### 基础使用

```typescript
import { DaoyouCode } from '@daoyoucode/sdk';

// 初始化客户端
const client = new DaoyouCode({
  apiKey: 'your_api_key',
  baseUrl: 'http://localhost:8000'
});

// 创建任务
const task = await client.tasks.create({
  instruction: '重构登录模块',
  files: ['auth.py', 'login.py'],
  options: {
    model: 'qwen-max',
    autoCommit: true
  }
});

console.log(`Task ID: ${task.taskId}`);

// 等待任务完成
const result = await client.tasks.wait(task.taskId);
console.log(`Status: ${result.status}`);
```

### 流式响应

```typescript
// 流式获取任务进度
for await (const event of client.tasks.stream(task.taskId)) {
  if (event.type === 'progress') {
    console.log(`Progress: ${event.progress * 100}%`);
  } else if (event.type === 'completed') {
    console.log('Task completed!');
    break;
  }
}
```

### React Hooks

```typescript
import { useDaoyouCode, useTask } from '@daoyoucode/react';

function MyComponent() {
  const client = useDaoyouCode();
  const { task, loading, error } = useTask('task_123456');
  
  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;
  
  return (
    <div>
      <h1>Task Status: {task.status}</h1>
      <p>Progress: {task.progress * 100}%</p>
    </div>
  );
}
```

---

## CLI 命令

### 基础命令

```bash
# 查看版本
daoyoucode --version

# 查看帮助
daoyoucode --help

# 交互式对话
daoyoucode

# 单次编辑
daoyoucode edit <files> <instruction>
```

### 编辑命令

```bash
# 基本用法
daoyoucode edit main.py "添加日志功能"

# 多文件编辑
daoyoucode edit auth.py login.py "重构认证逻辑"

# 指定模型
daoyoucode edit main.py "优化性能" --model qwen-coder-plus

# 指定编辑模式
daoyoucode edit main.py "重构" --format editblock

# 不自动提交
daoyoucode edit main.py "修改" --no-commit

# 自动确认
daoyoucode edit main.py "修改" --yes
```

### 智能体命令

```bash
# 调用特定智能体
daoyoucode agent chinese-editor "重构代码"
daoyoucode agent architect "分析架构"
daoyoucode agent oracle "调试问题"

# 列出所有智能体
daoyoucode agent list
```

### 配置命令

```bash
# 查看配置
daoyoucode config show

# 设置配置
daoyoucode config set llm.main_model qwen-max
daoyoucode config set git.auto_commit true

# 重置配置
daoyoucode config reset
```

### 服务命令

```bash
# 启动服务器
daoyoucode serve --port 8000

# 启动 GUI
daoyoucode gui

# 启动 TUI
daoyoucode tui
```

---

## 错误码

| 错误码 | 说明 |
|--------|------|
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 403 | 禁止访问 |
| 404 | 资源不存在 |
| 429 | 请求过于频繁 |
| 500 | 服务器内部错误 |
| 1001 | 任务创建失败 |
| 1002 | 任务执行失败 |
| 1003 | 智能体不可用 |
| 1004 | 模型不支持 |
| 1005 | 文件操作失败 |

---

## 速率限制

| 端点 | 限制 |
|------|------|
| POST /api/v1/tasks | 10 次/分钟 |
| GET /api/v1/tasks/* | 100 次/分钟 |
| WebSocket 连接 | 5 个/用户 |

---

## 示例代码

完整的示例代码请查看 [examples/](../../examples/) 目录：

- [基础使用](../../examples/basic-usage/)
- [API 集成](../../examples/api-integration/)
- [自定义智能体](../../examples/custom-agent/)
- [自定义插件](../../examples/custom-plugin/)

---

<div align="center">

**完整 API 文档，助力快速集成**

</div>
