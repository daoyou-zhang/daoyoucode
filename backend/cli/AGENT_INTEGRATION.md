# Agent集成计划

## 🎯 目标

将CLI的chat和edit命令与后端的Agent系统集成，实现真正的AI对话和代码编辑功能。

## 📋 集成步骤

### 第1步：准备工作（30分钟）

#### 1.1 检查后端Agent系统

```bash
# 检查Agent相关文件
ls backend/daoyoucode/agents/core/

# 应该有：
# - agent.py (BaseAgent, AgentRegistry)
# - task.py (Task, TaskManager)
# - memory.py (MemoryManager)
```

#### 1.2 测试Agent系统

```python
# 创建测试脚本
from daoyoucode.agents.core.agent import get_agent_registry, AgentConfig, BaseAgent

# 测试Agent注册
registry = get_agent_registry()
print(f"已注册的Agent: {registry.list_agents()}")
```

---

### 第2步：集成chat命令（2小时）

#### 2.1 修改chat.py

```python
# backend/cli/commands/chat.py

def handle_chat(user_input: str, context: dict):
    """处理对话"""
    from cli.ui.console import console
    from cli.ui.stream import stream_text
    
    # 1. 导入Agent系统
    from daoyoucode.agents.core.agent import get_agent_registry
    from daoyoucode.agents.memory import get_memory_manager
    
    # 2. 获取Agent
    registry = get_agent_registry()
    agent = registry.get_agent("MainAgent")
    
    if not agent:
        console.print("[red]Agent未初始化，使用模拟模式[/red]")
        return generate_mock_response(user_input, context)
    
    # 3. 准备上下文
    session_id = context.get("session_id", "default")
    agent_context = {
        "session_id": session_id,
        "files": context.get("files", []),
        "repo": context.get("repo", "."),
    }
    
    # 4. 调用Agent（异步）
    import asyncio
    
    try:
        with console.status("[bold blue]AI正在思考...[/bold blue]"):
            result = asyncio.run(agent.execute(
                prompt_source={"use_agent_default": True},
                user_input=user_input,
                context=agent_context
            ))
        
        # 5. 流式显示响应
        console.print(f"\n[bold blue]AI[/bold blue] › ", end="")
        
        if result.success:
            # 使用流式输出
            stream_text(result.content, delay=0.01)
        else:
            console.print(f"[red]{result.error}[/red]")
        
        # 6. 保存到历史
        context["history"].append((user_input, result.content))
        
    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")
        # 降级到模拟模式
        ai_response = generate_mock_response(user_input, context)
        console.print(ai_response)
```

#### 2.2 初始化Agent

```python
# backend/cli/commands/chat.py

def main(...):
    # 在main函数开始时初始化Agent
    initialize_agents()
    
    # 然后开始对话循环
    ...

def initialize_agents():
    """初始化Agent系统"""
    from cli.ui.console import console
    
    try:
        # 1. 导入Agent系统
        from daoyoucode.agents.core.agent import (
            get_agent_registry,
            register_agent,
            BaseAgent,
            AgentConfig
        )
        
        # 2. 检查是否已有Agent
        registry = get_agent_registry()
        if registry.list_agents():
            console.print("[dim]Agent系统已初始化[/dim]")
            return
        
        # 3. 创建并注册MainAgent
        config = AgentConfig(
            name="MainAgent",
            description="主对话Agent",
            model="qwen-max",
            temperature=0.7,
            system_prompt="你是DaoyouCode AI助手..."
        )
        
        agent = BaseAgent(config)
        register_agent(agent)
        
        console.print("[dim]Agent系统初始化完成[/dim]")
        
    except Exception as e:
        console.print(f"[yellow]警告: Agent初始化失败，将使用模拟模式[/yellow]")
        console.print(f"[dim]错误: {e}[/dim]")
```

---

### 第3步：集成edit命令（2小时）

#### 3.1 修改edit.py

```python
# backend/cli/commands/edit.py

def main(files, instruction, model, yes, repo):
    """单次编辑文件"""
    from cli.ui.console import console
    from daoyoucode.agents.core.agent import get_agent_registry
    from daoyoucode.tools import get_tool_registry
    
    # 1. 获取CodeAgent
    registry = get_agent_registry()
    agent = registry.get_agent("CodeAgent")
    
    if not agent:
        console.print("[red]CodeAgent未初始化[/red]")
        return
    
    # 2. 准备上下文
    context = {
        "files": [str(f) for f in files],
        "repo": str(repo),
        "instruction": instruction
    }
    
    # 3. 执行编辑
    import asyncio
    
    with Progress(...) as progress:
        task = progress.add_task("分析文件...", total=None)
        
        result = asyncio.run(agent.execute(
            prompt_source={"use_agent_default": True},
            user_input=instruction,
            context=context,
            tools=["read_file", "write_file", "diff"]
        ))
        
        progress.update(task, description="完成")
    
    # 4. 显示结果
    if result.success:
        show_diff_preview(result.metadata.get("diff"))
        if yes or typer.confirm("应用修改？"):
            apply_changes(result)
            show_success(files)
    else:
        console.print(f"[red]错误: {result.error}[/red]")
```

---

### 第4步：测试集成（1小时）

#### 4.1 测试chat命令

```bash
# 启动chat
python daoyoucode.py chat

# 测试对话
> 你好
> 你能做什么
> 写个Python函数
> /exit
```

#### 4.2 测试edit命令

```bash
# 创建测试文件
echo "# TODO" > test.py

# 测试编辑
python daoyoucode.py edit test.py "添加hello world函数"

# 检查结果
cat test.py
```

---

## 🔧 技术细节

### 异步处理

Agent的execute方法是异步的，需要用asyncio：

```python
import asyncio

# 在同步函数中调用异步Agent
result = asyncio.run(agent.execute(...))
```

### 错误处理

```python
try:
    result = asyncio.run(agent.execute(...))
    if result.success:
        # 处理成功
    else:
        # 处理失败
        console.print(f"[red]{result.error}[/red]")
except Exception as e:
    # 降级到模拟模式
    console.print(f"[yellow]使用模拟模式[/yellow]")
```

### 流式输出

```python
from cli.ui.stream import stream_text

# 逐字显示
stream_text(result.content, delay=0.01)
```

---

## 📊 集成检查清单

### chat命令
- [ ] 导入Agent系统
- [ ] 初始化MainAgent
- [ ] 调用agent.execute
- [ ] 处理异步
- [ ] 流式输出
- [ ] 错误处理
- [ ] 降级到模拟模式

### edit命令
- [ ] 导入Agent系统
- [ ] 初始化CodeAgent
- [ ] 调用agent.execute
- [ ] 传递工具列表
- [ ] 显示真实diff
- [ ] 应用修改
- [ ] 错误处理

---

## 🎯 预期效果

### chat命令集成后

```
你 › 你好

[AI正在思考...]

AI › 你好！我是DaoyouCode AI助手，基于18大核心系统。
    我可以帮你编写代码、重构项目、解答问题。
    有什么我可以帮助你的吗？

你 › 写个Python函数计算斐波那契数列

[AI正在思考...]

AI › 好的，我来为你编写一个计算斐波那契数列的函数：

```python
def fibonacci(n):
    """计算斐波那契数列的第n项"""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
```

这是一个递归实现。如果需要更高效的版本，我可以提供动态规划的实现。
```

### edit命令集成后

```bash
$ python daoyoucode.py edit test.py "添加hello world函数"

╭─ 📝 单次编辑 ─────────────────────────────╮
│ • 文件: test.py                           │
│ • 指令: 添加hello world函数              │
│ • 模型: qwen-max                          │
╰───────────────────────────────────────────╯

✓ 文件分析完成
✓ 修改生成完成
✓ 修改验证通过

修改预览

test.py
╭───────────────────────────────────────────╮
│ + def hello_world():                      │
│ +     """打印Hello World"""               │
│ +     print("Hello, World!")              │
│ +     return "Success"                    │
╰───────────────────────────────────────────╯

应用这些修改？ [y/N]: y

✓ 修改已应用

✅ 编辑完成！

┏━━━━━━━━━┳━━━━━━━━┓
┃ 文件    ┃ 状态   ┃
┡━━━━━━━━━╇━━━━━━━━┩
│ test.py │ ✓ 已修改│
└─────────┴────────┘
```

---

## 🚀 开始集成

**准备好了吗？让我们开始集成Agent系统！**

预计时间：
- 准备工作：30分钟
- chat集成：2小时
- edit集成：2小时
- 测试：1小时

**总计：5.5小时完成完整集成**

要开始吗？
