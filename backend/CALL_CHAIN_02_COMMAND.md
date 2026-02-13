# 调用链路分析 - 02 命令层

## 2. 命令层：Chat命令处理

### 入口函数
```
📁 backend/cli/commands/chat.py :: main()
```

### 调用流程

#### 2.1 初始化阶段

**代码**:
```python
def main(files, model, repo):
    from cli.ui.console import console
    import uuid
    
    # 1. 显示欢迎横幅
    show_banner(model, repo, files)
    
    # 2. 生成会话ID
    session_id = str(uuid.uuid4())
    
    # 3. 创建UI上下文
    ui_context = {
        "session_id": session_id,
        "model": model,
        "repo": str(repo),
        "initial_files": [str(f) for f in files] if files else []
    }
```

**职责**:
- 显示欢迎信息
- 生成唯一会话ID（用于Memory系统）
- 准备UI上下文（只存储UI状态，不存储业务逻辑）

---

#### 2.2 主交互循环

**代码**:
```python
try:
    while True:
        # 获取用户输入
        user_input = console.input("\n[bold green]你[/bold green] › ")
        
        if not user_input.strip():
            continue
        
        # 处理命令
        if user_input.startswith("/"):
            if not handle_command(user_input, ui_context):
                break  # /exit命令返回False
            continue
        
        # 处理普通对话
        handle_chat(user_input, ui_context)

except KeyboardInterrupt:
    console.print("\n\n[cyan]👋 再见！[/cyan]\n")
    raise typer.Exit(0)
```

**分支逻辑**:
```
用户输入
├─ 空输入 → continue（忽略）
├─ /命令
│  ├─ /exit, /quit → 退出循环
│  ├─ /help → 显示帮助
│  ├─ /model [name] → 切换模型
│  ├─ /session → 显示会话ID
│  └─ 其他 → 显示"未知命令"
└─ 普通对话 → handle_chat()
```

---

#### 2.3 命令处理

**函数**: `handle_command(cmd: str, ui_context: dict) -> bool`

**代码**:
```python
def handle_command(cmd: str, ui_context: dict) -> bool:
    parts = cmd.split(maxsplit=1)
    command = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""
    
    if command == "/exit" or command == "/quit":
        return False  # 退出主循环
    
    elif command == "/help":
        show_help()
    
    elif command == "/model":
        if not args:
            console.print(f"当前模型: {ui_context['model']}")
        else:
            ui_context['model'] = args
            console.print(f"已切换到模型: {args}")
    
    elif command == "/session":
        console.print(f"会话ID: {ui_context['session_id']}")
    
    else:
        console.print(f"未知命令: {command}")
    
    return True  # 继续主循环
```

**支持的命令**:
- `/exit`, `/quit` - 退出
- `/help` - 帮助
- `/model [name]` - 切换模型
- `/session` - 显示会话ID

---

#### 2.4 对话处理（核心）

**函数**: `handle_chat(user_input: str, ui_context: dict)`

**代码**:
```python
def handle_chat(user_input: str, ui_context: dict):
    from cli.ui.console import console
    import asyncio
    
    # 准备上下文（传递给Skill系统）
    context = {
        "session_id": ui_context["session_id"],
        "repo": ui_context["repo"],
        "model": ui_context["model"],
        "initial_files": ui_context.get("initial_files", [])
    }
    
    # 获取或创建event loop
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        # ========== 关键：初始化Agent系统 ==========
        from daoyoucode.agents.init import initialize_agent_system
        initialize_agent_system()
        
        # ========== 关键：配置LLM客户端 ==========
        from daoyoucode.agents.llm.client_manager import get_client_manager
        from daoyoucode.agents.llm.config_loader import auto_configure
        
        client_manager = get_client_manager()
        auto_configure(client_manager)
        
        # ========== 关键：通过Skill系统执行 ==========
        from daoyoucode.agents.executor import execute_skill
        
        console.print("[bold blue]🤔 AI正在思考...[/bold blue]")
        
        result = loop.run_until_complete(execute_skill(
            skill_name="chat_assistant",
            user_input=user_input,
            session_id=context["session_id"],
            context=context
        ))
        
        # 显示结果
        if result.get('success'):
            ai_response = result.get('content', '')
        else:
            error_msg = result.get('error', '未知错误')
            console.print(f"[yellow]⚠ 执行失败: {error_msg}[/yellow]")
            ai_response = "抱歉，我遇到了一些问题。请重试。"
    
    except Exception as e:
        console.print(f"[yellow]⚠ 调用异常: {str(e)[:100]}[/yellow]")
        ai_response = "抱歉，系统出现异常。请重试。"
    
    # 显示AI响应
    console.print(f"\n[bold blue]AI[/bold blue] › ", end="")
    
    if "```" in ai_response:
        console.print(Markdown(ai_response))
    else:
        console.print(ai_response)
```

**关键步骤**:
1. 准备上下文
2. 初始化Agent系统
3. 配置LLM客户端
4. 调用Skill系统
5. 显示结果

---

### 关键文件清单

| 文件 | 职责 | 关键函数 |
|------|------|---------|
| `cli/commands/chat.py` | Chat命令主逻辑 | `main()`, `handle_chat()`, `handle_command()` |
| `cli/ui/console.py` | Rich Console | `console.input()`, `console.print()` |
| `cli/ui/markdown.py` | Markdown渲染 | `Markdown()` |

---

### 依赖关系

```
chat.py
    ↓
├─ cli/ui/console.py (UI显示)
├─ daoyoucode/agents/init.py (系统初始化)
├─ daoyoucode/agents/llm/client_manager.py (LLM管理)
└─ daoyoucode/agents/executor.py (Skill执行)
```

---

### 下一步

命令层完成后，控制权转移到 **Skill层**

→ 继续阅读 `CALL_CHAIN_03_SKILL.md`
