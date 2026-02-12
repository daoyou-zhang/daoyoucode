# CLI集成后端计划

## 🎯 目标

将CLI命令与后端的18大核心系统集成

## 📋 集成任务

### 1. chat命令集成 ⭐⭐⭐⭐⭐

**文件**: `backend/cli/commands/chat.py`

**需要集成**:
```python
# 导入后端Agent
from daoyoucode.agents.core.agent import BaseAgent, get_agent_registry
from daoyoucode.agents.memory import get_memory_manager

# 在chat.py的main函数中:
def main(files, model, repo):
    # 1. 获取Agent
    registry = get_agent_registry()
    agent = registry.get_agent("MainAgent")
    
    # 2. 加载文件到上下文
    context = {"files": files, "repo": repo}
    
    # 3. 交互循环
    while True:
        user_input = input("你: ")
        
        # 4. 调用Agent
        result = await agent.execute(
            prompt_source={"use_agent_default": True},
            user_input=user_input,
            context=context
        )
        
        # 5. 显示结果
        print(f"AI: {result.content}")
```

**预计时间**: 1天

---

### 2. edit命令集成 ⭐⭐⭐⭐⭐

**文件**: `backend/cli/commands/edit.py`

**需要集成**:
```python
# 导入后端Agent和工具
from daoyoucode.agents.core.agent import get_agent_registry
from daoyoucode.tools import get_tool_registry

# 在edit.py的main函数中:
def main(files, instruction, model, yes, repo):
    # 1. 获取Agent
    agent = get_agent_registry().get_agent("CodeAgent")
    
    # 2. 准备上下文
    context = {
        "files": files,
        "repo": repo,
        "instruction": instruction
    }
    
    # 3. 执行编辑
    result = await agent.execute(
        prompt_source={"use_agent_default": True},
        user_input=instruction,
        context=context,
        tools=["read_file", "write_file", "diff"]
    )
    
    # 4. 显示diff并确认
    if not yes:
        show_diff(result.metadata.get("diff"))
        if not confirm("应用修改？"):
            return
    
    # 5. 应用修改
    apply_changes(result)
```

**预计时间**: 1天

---

### 3. config命令集成 ⭐⭐⭐

**文件**: `backend/cli/commands/config.py`

**需要集成**:
```python
# 读写配置文件
import json
from pathlib import Path

CONFIG_FILE = Path.home() / ".daoyoucode" / "config.json"

def show():
    """显示配置"""
    if CONFIG_FILE.exists():
        config = json.loads(CONFIG_FILE.read_text())
        # 显示配置
    else:
        # 显示默认配置
        
def set(key, value):
    """设置配置"""
    config = load_config()
    config[key] = value
    save_config(config)
```

**预计时间**: 半天

---

### 4. session命令集成 ⭐⭐⭐

**文件**: `backend/cli/commands/session.py`

**需要集成**:
```python
# 导入记忆系统
from daoyoucode.agents.memory import get_memory_manager

def list():
    """列出会话"""
    memory = get_memory_manager()
    sessions = memory.list_sessions()
    # 显示会话列表
    
def show(session_id):
    """显示会话详情"""
    memory = get_memory_manager()
    history = memory.get_conversation_history(session_id)
    # 显示对话历史
```

**预计时间**: 半天

---

### 5. serve命令集成 ⭐⭐

**文件**: `backend/cli/commands/serve.py`

**需要集成**:
```python
# 导入FastAPI应用
from daoyoucode.api.main import app
import uvicorn

def main(host, port):
    """启动服务器"""
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
```

**预计时间**: 半天

---

## 📅 实施计划

### 第1天
- ✅ CLI框架完成
- 🔄 chat命令集成

### 第2天
- 🔄 edit命令集成
- 🔄 config命令集成

### 第3天
- 🔄 session命令集成
- 🔄 serve命令集成
- 🔄 测试和完善

## 🎯 成功标准

- [ ] chat命令能正常对话
- [ ] edit命令能编辑文件
- [ ] config命令能管理配置
- [ ] session命令能查看历史
- [ ] serve命令能启动服务器
- [ ] 所有命令有完整的错误处理
- [ ] 所有命令有美观的输出

## 💡 注意事项

1. **异步处理**: Agent的execute是异步的，需要用asyncio
2. **错误处理**: 要捕获所有异常并友好显示
3. **进度显示**: 长时间操作要显示进度
4. **流式输出**: chat命令要支持流式显示
5. **配置管理**: 要有默认配置和用户配置

## 🚀 下一步

完成集成后，我们就有了一个完整可用的CLI工具！

**精简而强大，基于18大核心系统！**
