# 🎯 如何让AI理解项目代码

## 方法1: 使用 /add 命令（推荐）

在chat中添加文件到上下文：

```
你 › /add backend/daoyoucode/agents/core/agent.py
✓ 已添加文件: backend/daoyoucode/agents/core/agent.py
  250 行, 8500 字符

你 › /add backend/cli/commands/chat.py
✓ 已添加文件: backend/cli/commands/chat.py
  450 行, 15000 字符

你 › /files
┏━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ # ┃ 文件路径                                 ┃
┡━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 1 │ backend/daoyoucode/agents/core/agent.py  │
│ 2 │ backend/cli/commands/chat.py             │
└───┴──────────────────────────────────────────┘

你 › 请分析一下agent.py的架构设计
```

AI现在可以看到文件内容并进行分析了！

---

## 方法2: 启动时加载文件

```bash
python daoyoucode.py chat backend/daoyoucode/agents/core/agent.py backend/cli/commands/chat.py
```

---

## 💡 使用示例

### 示例1: 理解项目架构

```
你 › /add backend/daoyoucode/agents/core/agent.py
你 › /add backend/daoyoucode/agents/core/task.py
你 › 请解释一下Agent系统的设计思路
```

### 示例2: 代码审查

```
你 › /add backend/cli/commands/chat.py
你 › 请帮我审查这个文件，看看有没有可以优化的地方
```

### 示例3: 添加功能

```
你 › /add backend/cli/commands/edit.py
你 › 我想在edit命令中添加一个进度条，应该怎么做？
```

### 示例4: 调试问题

```
你 › /add backend/daoyoucode/agents/llm/client_manager.py
你 › 为什么会出现"Event loop is closed"错误？
```

---

## 📁 常用文件路径

### 核心Agent系统
```
backend/daoyoucode/agents/core/agent.py
backend/daoyoucode/agents/core/task.py
backend/daoyoucode/agents/core/memory.py
```

### CLI命令
```
backend/cli/commands/chat.py
backend/cli/commands/edit.py
backend/cli/app.py
```

### LLM客户端
```
backend/daoyoucode/agents/llm/client_manager.py
backend/daoyoucode/agents/llm/config_loader.py
```

### 配置文件
```
backend/config/llm_config.yaml
backend/config/agent_router_config.yaml
```

---

## 🎯 完整工作流

### 1. 启动chat
```bash
cd backend
python daoyoucode.py chat
```

### 2. 添加相关文件
```
你 › /add backend/daoyoucode/agents/core/agent.py
你 › /add backend/cli/commands/chat.py
```

### 3. 查看已加载的文件
```
你 › /files
```

### 4. 开始提问
```
你 › 请分析一下当前的Agent架构
你 › 如何添加一个新的Agent？
你 › 这个项目的核心设计思想是什么？
```

### 5. 移除不需要的文件
```
你 › /drop backend/cli/commands/chat.py
```

---

## 💡 提示

1. **一次添加多个文件**
   ```
   /add file1.py
   /add file2.py
   /add file3.py
   ```

2. **使用相对路径**
   ```
   /add backend/cli/commands/chat.py
   ```

3. **查看文件列表**
   ```
   /files
   ```

4. **清理上下文**
   ```
   /drop file1.py
   /clear  # 清空对话历史
   ```

5. **文件大小限制**
   - 建议单个文件不超过1000行
   - 一次不要加载太多文件（建议3-5个）
   - 如果文件太大，可以只询问特定部分

---

## 🚀 现在试试

```bash
cd backend
python daoyoucode.py chat
```

然后：
```
你 › /add backend/daoyoucode/agents/core/agent.py
你 › 请帮我理解这个Agent系统的设计
```

AI现在可以看到代码并进行深入分析了！🎉
