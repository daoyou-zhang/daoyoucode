# daoyoucode API Reference

> **Complete API interface documentation**

---

## 📋 Table of Contents

1. [REST API](#rest-api)
2. [WebSocket API](#websocket-api)
3. [Python SDK](#python-sdk)
4. [TypeScript SDK](#typescript-sdk)
5. [CLI Commands](#cli-commands)

---

## REST API

### Base Information

- **Base URL**: `http://localhost:8000/api/v1`
- **Authentication**: Bearer Token (optional)
- **Content-Type**: `application/json`

### Common Response Format

#### Success Response

```json
{
  "success": true,
  "data": { ... },
  "message": "Operation successful"
}
```

#### Error Response

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Error description",
    "details": { ... }
  }
}
```

---

### Task Management

#### Create Task

Create a new editing task.

**Request**

```http
POST /api/v1/tasks
Content-Type: application/json

{
  "instruction": "Refactor login module",
  "files": ["auth.py", "login.py"],
  "options": {
    "model": "qwen-max",
    "temperature": 0.7,
    "auto_commit": true
  }
}
```

**Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| instruction | string | Yes | Task instruction |
| files | array | No | File list |
| options | object | No | Task options |
| options.model | string | No | Model to use |
| options.temperature | number | No | Temperature (0-1) |
| options.auto_commit | boolean | No | Auto commit |

**Response**

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

#### Get Task Status

Get current task status and progress.

**Request**

```http
GET /api/v1/tasks/{task_id}
```

**Response**

```json
{
  "success": true,
  "data": {
    "task_id": "task_123456",
    "status": "running",
    "progress": 0.5,
    "current_step": "Analyzing code structure",
    "agent": "chinese-editor",
    "started_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:01:00Z"
  }
}
```

**Status Values**

| Status | Description |
|--------|-------------|
| pending | Waiting to execute |
| running | Currently executing |
| completed | Completed |
| failed | Failed |
| cancelled | Cancelled |

---

## WebSocket API

### Connection

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
```

### Message Format

#### Client → Server

```json
{
  "type": "task.create",
  "data": {
    "instruction": "Refactor code",
    "files": ["main.py"]
  }
}
```

#### Server → Client

```json
{
  "type": "task.progress",
  "data": {
    "task_id": "task_123456",
    "progress": 0.5,
    "message": "Analyzing code..."
  }
}
```

---

## Python SDK

### Installation

```bash
pip install daoyoucode
```

### Basic Usage

```python
from daoyoucode import DaoyouCode

# Initialize client
client = DaoyouCode(
    api_key="your_api_key",
    base_url="http://localhost:8000"
)

# Create task
task = client.tasks.create(
    instruction="Refactor login module",
    files=["auth.py", "login.py"],
    options={
        "model": "qwen-max",
        "auto_commit": True
    }
)

print(f"Task ID: {task.task_id}")

# Wait for completion
result = client.tasks.wait(task.task_id)
print(f"Status: {result.status}")
```

---

## TypeScript SDK

### Installation

```bash
npm install @daoyoucode/sdk
# or
pnpm add @daoyoucode/sdk
```

### Basic Usage

```typescript
import { DaoyouCode } from '@daoyoucode/sdk';

// Initialize client
const client = new DaoyouCode({
  apiKey: 'your_api_key',
  baseUrl: 'http://localhost:8000'
});

// Create task
const task = await client.tasks.create({
  instruction: 'Refactor login module',
  files: ['auth.py', 'login.py'],
  options: {
    model: 'qwen-max',
    autoCommit: true
  }
});

console.log(`Task ID: ${task.taskId}`);
```

---

## CLI Commands

### Basic Commands

```bash
# Check version
daoyoucode --version

# Show help
daoyoucode --help

# Interactive chat
daoyoucode

# Single edit
daoyoucode edit <files> <instruction>
```

### Edit Commands

```bash
# Basic usage
daoyoucode edit main.py "Add logging"

# Multiple files
daoyoucode edit auth.py login.py "Refactor authentication"

# Specify model
daoyoucode edit main.py "Optimize performance" --model qwen-coder-plus

# Specify edit mode
daoyoucode edit main.py "Refactor" --format editblock

# No auto commit
daoyoucode edit main.py "Modify" --no-commit

# Auto confirm
daoyoucode edit main.py "Modify" --yes
```

---

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not found |
| 429 | Too many requests |
| 500 | Internal server error |
| 1001 | Task creation failed |
| 1002 | Task execution failed |
| 1003 | Agent unavailable |
| 1004 | Model not supported |
| 1005 | File operation failed |

---

<div align="center">

**Complete API documentation for rapid integration**

</div>
