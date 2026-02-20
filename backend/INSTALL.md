# DaoyouCode Backend 安装指南

## 快速开始

### 1. 基础安装（推荐 - 使用向量API）

```bash
cd backend
pip install -e .
```

这将安装所有核心依赖，**不包含**本地向量模型（节省~2GB空间）：
- Web框架 (FastAPI, Uvicorn)
- CLI工具 (Typer, Rich)
- 代码分析 (GitPython, Tree-sitter, grep-ast)
- LSP支持 (Pyright)
- 文本处理 (rank-bm25, jieba)

### 2. 本地向量检索（如果不使用API）

```bash
pip install -e ".[embedding]"
```

额外安装：
- Sentence-transformers (~500MB)
- PyTorch (~2GB)

### 3. 开发环境安装

```bash
pip install -e ".[dev]"
```

额外包含：
- 测试工具 (pytest, pytest-asyncio)
- 代码格式化 (black, ruff)
- 类型检查 (mypy)

### 4. 完整功能安装

```bash
pip install -e ".[full,dev]"
```

包含所有依赖（本地向量 + 开发工具）

## 依赖说明

### 核心依赖

| 依赖 | 版本 | 用途 |
|------|------|------|
| fastapi | >=0.104.0 | Web API框架 |
| uvicorn | >=0.24.0 | ASGI服务器 |
| pydantic | >=2.5.0 | 数据验证 |
| typer | >=0.9.0 | CLI框架 |
| rich | >=13.7.0 | 终端UI |
| gitpython | >=3.1.40 | Git操作 |
| tree-sitter | >=0.20.0 | 代码解析 |
| tree-sitter-languages | >=1.10.0 | 多语言支持 |
| grep-ast | >=0.3.0 | AST搜索 |
| pygments | >=2.15.0 | 语法高亮 |
| pyright | >=1.1.350 | Python LSP服务器 |
| httpx | >=0.24.0 | HTTP客户端 |
| numpy | >=1.24.0 | 数组计算 |
| rank-bm25 | >=0.2.2 | BM25搜索 |
| jieba | >=0.42.1 | 中文分词 |

### 可选依赖（本地向量检索）

| 依赖 | 版本 | 用途 | 大小 | 安装方式 |
|------|------|------|------|----------|
| sentence-transformers | >=2.2.0 | 向量编码 | ~500MB | `pip install -e ".[embedding]"` |
| torch | >=2.0.0 | 深度学习框架 | ~2GB | `pip install -e ".[embedding]"` |

**注意**: 如果使用向量API（如OpenAI Embeddings、智谱AI等），不需要安装这两个包。

### LSP服务器（其他语言）

如果需要支持其他编程语言，请手动安装对应的LSP服务器：

```bash
# TypeScript/JavaScript
npm install -g typescript-language-server typescript

# Rust
rustup component add rust-analyzer

# Go
go install golang.org/x/tools/gopls@latest
```

## 验证安装

### 1. 检查Python依赖

```bash
pip list | grep -E "fastapi|typer|tree-sitter|pyright"
```

### 2. 检查LSP服务器

```bash
# Python LSP
pyright --version

# TypeScript LSP (如果安装了)
typescript-language-server --version

# Rust LSP (如果安装了)
rust-analyzer --version

# Go LSP (如果安装了)
gopls version
```

### 3. 运行测试

```bash
# 基础测试
pytest tests/test_import.py

# LSP测试
pytest tests/test_lsp_tools.py

# 完整测试
pytest
```

### 4. 启动CLI

```bash
# 查看帮助
daoyoucode --help

# 或使用简写
dyc --help

# 启动对话
daoyoucode chat
```

## 常见问题

### Q1: 我应该使用本地向量还是API？

**使用向量API（推荐）**:
- ✅ 安装快（节省~2.5GB）
- ✅ 内存占用小
- ✅ 无需GPU
- ❌ 需要网络
- ❌ 有API调用成本

**使用本地向量**:
- ✅ 无网络依赖
- ✅ 无API成本
- ❌ 安装慢（~2.5GB）
- ❌ 内存占用大（~2GB）
- ❌ CPU推理较慢

**建议**: 开发阶段使用API，生产环境根据需求选择。

### Q2: torch安装失败或太慢

如果需要本地向量，Torch包很大（~2GB），可以：

1. 使用CPU版本（更小）：
```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

2. 或者使用国内镜像：
```bash
pip install torch -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q3: pyright安装后找不到命令

确保pip安装目录在PATH中：

```bash
# 查看安装位置
pip show pyright

# 添加到PATH（Linux/Mac）
export PATH="$HOME/.local/bin:$PATH"

# 添加到PATH（Windows）
# 将 %APPDATA%\Python\Scripts 添加到系统PATH
```

### Q4: tree-sitter-languages安装失败

这个包需要编译，确保安装了编译工具：

```bash
# Ubuntu/Debian
sudo apt-get install build-essential

# macOS
xcode-select --install

# Windows
# 安装 Visual Studio Build Tools
```

### Q5: 如何卸载

```bash
cd backend
pip uninstall daoyoucode
```

## 开发模式

使用 `-e` 参数安装后，代码修改会立即生效，无需重新安装：

```bash
pip install -e .
```

## 生产部署

生产环境建议固定版本：

```bash
# 生成requirements.txt
pip freeze > requirements-lock.txt

# 在生产环境安装
pip install -r requirements-lock.txt
```

## 系统要求

- Python >= 3.10
- pip >= 21.0
- 磁盘空间 >= 1GB (基础安装) 或 >= 5GB (含本地向量)
- 内存 >= 2GB (基础) 或 >= 4GB (本地向量)

## 下一步

安装完成后，查看：
- [开发文档](../docs/zh-CN/DEVELOPMENT.md)
- [API文档](../docs/zh-CN/API.md)
- [CLI使用指南](./01_CLI命令参考.md)
