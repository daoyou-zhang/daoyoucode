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
from cli.commands import chat, edit, doctor, ...

app = typer.Typer(name="daoyoucode", help="DaoyouCode CLI")

# 注册命令
app.command(name="chat")(chat.main)
app.command(name="edit")(edit.main)
app.command(name="doctor")(doctor.main)
...
```

**职责**:
- 创建Typer应用实例
- 注册所有CLI命令
- 解析命令行参数
- 路由到对应的命令处理函数

**分支逻辑**:
```
用户输入命令
├─ chat    → chat.main()
├─ edit    → edit.main()
├─ doctor  → doctor.main()
├─ config  → config.main()
├─ models  → models.main()
├─ agent   → agent.main()
├─ session → session.main()
├─ serve   → serve.main()
└─ version → 显示版本信息
```

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
