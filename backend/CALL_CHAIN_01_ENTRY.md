# 调用链路分析 - 01 入口层

## 1. 入口层：CLI启动

### 用户操作
```bash
cd backend
python -m cli chat
```

### 调用流程

#### 1.1 Python模块入口
```
📁 backend/cli/__main__.py
```

**代码**:
```python
if __name__ == "__main__":
    from cli.app import app
    app()
```

**职责**:
- Python的`-m`参数会执行`__main__.py`
- 导入并启动Typer应用

---

#### 1.2 Typer应用初始化
```
📁 backend/cli/app.py
```

**代码**:
```python
import typer

app = typer.Typer(name="daoyoucode", help="DaoyouCode CLI")

# 使用装饰器注册命令（推荐方式）
@app.command()
def chat(
    files: Optional[list[Path]] = typer.Argument(None, help="要加载的文件"),
    model: str = typer.Option("qwen-max", "--model", "-m", help="使用的模型"),
    repo: Path = typer.Option(".", "--repo", "-r", help="仓库路径"),
):
    """启动交互式对话"""
    from cli.commands import chat as chat_cmd  # 延迟导入
    chat_cmd.main(files, model, repo)

@app.command()
def edit(...):
    """单次编辑文件"""
    from cli.commands import edit as edit_cmd
    edit_cmd.main(...)

# ... 其他命令
```

**职责**:
- 创建Typer应用实例
- 使用装饰器注册所有CLI命令
- 定义命令参数（Argument和Option）
- 延迟导入命令模块（提升启动速度）
- 解析命令行参数
- 路由到对应的命令处理函数

**注册方式说明**:
- 使用`@app.command()`装饰器注册
- 参数定义在app.py中（清晰可见）
- 实际实现在commands/目录中（分离关注点）
- 延迟导入（只在执行时加载模块）

**分支逻辑**:
```
用户输入命令
├─ chat    → @app.command() → chat_cmd.main()
├─ edit    → @app.command() → edit_cmd.main()
├─ doctor  → @app.command() → doctor_cmd.main()
├─ config  → @app.command() → config_cmd.main()
├─ models  → @app.command() → models_cmd.main()
├─ agent   → @app.command() → agent_cmd.main()
├─ session → @app.command() → session_cmd.main()
├─ serve   → @app.command() → serve_cmd.main()
└─ version → @app.command() → 直接显示版本信息
```

**详细说明**: 参见 `TYPER_REGISTRATION_EXPLAINED.md`

---

#### 1.3 命令参数解析
```
📁 backend/cli/commands/chat.py
```

**函数签名**:
```python
def main(
    files: Optional[List[Path]] = typer.Argument(None, help="要加载的文件"),
    model: str = typer.Option("qwen-plus", "--model", "-m", help="使用的模型"),
    repo: Path = typer.Option(".", "--repo", "-r", help="仓库路径"),
):
```

**Typer自动处理**:
- 解析命令行参数
- 类型转换（str → Path）
- 默认值填充
- 帮助信息生成

**示例**:
```bash
# 基础调用
python -m cli chat
# → files=None, model="qwen-plus", repo="."

# 带参数调用
python -m cli chat main.py utils.py --model deepseek-coder --repo ./backend
# → files=[Path("main.py"), Path("utils.py")], model="deepseek-coder", repo=Path("./backend")
```

---

### 关键文件清单

| 文件 | 职责 | 关键函数/类 |
|------|------|------------|
| `cli/__main__.py` | 模块入口 | `if __name__ == "__main__"` |
| `cli/app.py` | Typer应用 | `app = typer.Typer()` |
| `cli/commands/__init__.py` | 命令导入 | 导入所有命令模块 |
| `cli/commands/chat.py` | Chat命令 | `main()` |

---

### 依赖关系

```
__main__.py
    ↓ import
app.py
    ↓ import
commands/__init__.py
    ↓ import
commands/chat.py
    ↓ import
cli/ui/console.py (Rich Console)
```

---

### 下一步

入口层完成后，控制权转移到 **命令层**

→ 继续阅读 `CALL_CHAIN_02_COMMAND.md`
