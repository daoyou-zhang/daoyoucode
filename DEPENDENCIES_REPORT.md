# 依赖文件检查报告（已更新）

## ✅ 最终方案：使用 pyproject.toml

已将所有依赖整合到 `backend/pyproject.toml`，这是现代Python项目的标准做法。

## 📦 完整依赖清单

### 核心依赖（必装 - 使用向量API）

```toml
[project]
dependencies = [
    # Web框架
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "pydantic>=2.5.0",
    
    # CLI框架
    "click>=8.1.0",
    "typer[all]>=0.9.0",
    "rich>=13.7.0",
    "python-dotenv>=1.0.0",
    
    # 代码分析工具
    "gitpython>=3.1.40",
    "tree-sitter>=0.20.0",
    "tree-sitter-languages>=1.10.0",
    "watchdog>=3.0.0",
    "grep-ast>=0.3.0",
    "pygments>=2.15.0",
    
    # LSP服务器（代码智能）
    "pyright>=1.1.350",
    
    # LLM客户端依赖
    "httpx>=0.24.0",
    "pyyaml>=6.0",
    "jinja2>=3.0.0",
    
    # 基础数据处理
    "numpy>=1.24.0",
    
    # 文本处理
    "rank-bm25>=0.2.2",
    "jieba>=0.42.1",
]
```

### 可选依赖（本地向量检索）

```toml
[project.optional-dependencies]
# 本地向量检索（~2.5GB）
embedding = [
    "sentence-transformers>=2.2.0",
    "torch>=2.0.0",
]

# 开发工具
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
    "black>=23.11.0",
    "ruff>=0.1.6",
    "mypy>=1.7.0",
]
```

## 🎯 安装命令

### 基础安装（推荐 - 使用向量API）
```bash
cd backend
pip install -e .
```
**大小**: ~500MB，**不包含**本地向量模型

### 本地向量检索
```bash
pip install -e ".[embedding]"
```
**额外大小**: ~2.5GB (sentence-transformers + torch)

### 开发环境
```bash
pip install -e ".[dev]"
```

### 完整功能
```bash
pip install -e ".[full,dev]"
```

## 📝 新增的关键依赖

### 1. pyright (>=1.1.350)
- **用途**: Python LSP服务器，提供代码智能功能
- **功能**: 
  - 代码诊断（错误检查）
  - 代码补全
  - 跳转定义
  - 查找引用
  - 符号搜索
- **使用位置**: `backend/daoyoucode/agents/tools/lsp_tools.py`

### 2. grep-ast (>=0.3.0)
- **用途**: AST级别的代码搜索
- **功能**: 基于语法树的精确代码匹配
- **使用位置**: `backend/daoyoucode/agents/tools/repomap_tools.py`

### 3. pygments (>=2.15.0)
- **用途**: 语法高亮和词法分析
- **功能**: 代码着色、语言检测
- **使用位置**: `backend/daoyoucode/agents/tools/repomap_tools.py`

### 4. rank-bm25 (>=0.2.2)
- **用途**: BM25算法实现，用于文本相似度计算
- **功能**: 提升话题相似度匹配准确性
- **使用位置**: `backend/daoyoucode/agents/memory/bm25_matcher.py`
- **必需**: 是（已包含在核心依赖）

### 5. jieba (>=0.42.1)
- **用途**: 中文分词
- **功能**: 提升中文文本处理能力
- **使用位置**: `backend/daoyoucode/agents/memory/bm25_matcher.py`
- **必需**: 是（已包含在核心依赖）

### 6. sentence-transformers (>=2.2.0) - 可选
- **用途**: 本地向量编码模型
- **功能**: 将文本转换为向量（用于语义搜索）
- **使用位置**: `backend/daoyoucode/agents/memory/vector_retriever.py`
- **必需**: 否（使用向量API时不需要）
- **大小**: ~500MB
- **安装**: `pip install -e ".[embedding]"`

### 7. torch (>=2.0.0) - 可选
- **用途**: 深度学习框架（sentence-transformers的依赖）
- **功能**: 运行向量编码模型
- **必需**: 否（使用向量API时不需要）
- **大小**: ~2GB
- **安装**: `pip install -e ".[embedding]"`

## 🔍 依赖验证

### 检查已安装的包
```bash
pip list | grep -E "pyright|grep-ast|pygments|rank-bm25|jieba"
```

### 验证LSP服务器
```bash
pyright --version
```

### 运行测试
```bash
cd backend
pytest tests/test_lsp_tools.py -v
```

## 📂 文件清理建议

### 可以删除的文件
```bash
# CLI子目录的requirements.txt已废弃
rm backend/cli/requirements.txt

# 根目录的requirements.txt可以删除（已整合到pyproject.toml）
rm backend/requirements.txt
```

### 保留的文件
- ✅ `backend/pyproject.toml` - 主依赖配置
- ✅ `backend/INSTALL.md` - 安装指南（新建）
- ✅ `package.json` - 前端依赖
- ✅ `frontend/package.json` - 前端monorepo配置

## ⚠️ 前端依赖问题（待处理）

前端仍需添加ESLint配置：

```bash
cd frontend
pnpm add -D -w eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin eslint-plugin-react
```

创建 `frontend/.eslintrc.json`:
```json
{
  "parser": "@typescript-eslint/parser",
  "extends": [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:react/recommended"
  ],
  "rules": {
    "react/react-in-jsx-scope": "off"
  },
  "settings": {
    "react": {
      "version": "detect"
    }
  }
}
```

## 🎉 总结

现在 `backend/pyproject.toml` 已优化为：

### 核心依赖（~500MB）
- ✅ Web框架 (FastAPI, Uvicorn)
- ✅ CLI工具 (Typer, Rich)
- ✅ 代码分析 (Tree-sitter, grep-ast, pygments)
- ✅ LSP支持 (Pyright)
- ✅ 文本处理 (rank-bm25, jieba)
- ✅ 基础数据 (numpy)

### 可选依赖（~2.5GB）
- ⭕ 本地向量 (sentence-transformers, torch) - 使用API时不需要

## 🚀 快速开始

```bash
# 1. 创建虚拟环境
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 安装依赖（使用向量API）
pip install -e .

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env，填入你的API密钥

# 4. 验证安装
daoyoucode --version
pyright --version

# 5. 启动对话
daoyoucode chat
```

**安装时间**: ~5分钟（使用API模式）  
**磁盘占用**: ~500MB（使用API模式）

