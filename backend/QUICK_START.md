# DaoyouCode 快速开始

## 5分钟上手指南

### 1. 安装依赖

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e .
```

### 2. 配置API密钥

**编辑配置文件**（推荐）:

```bash
vim config/llm_config.yaml
```

填入你的API密钥：

```yaml
providers:
  qwen:
    api_key: 
      - "sk-your-key-1"
      - "sk-your-key-2"  # 可选：多个key自动轮询
    enabled: true
```

**或使用环境变量**（备用）:

```bash
export QWEN_API_KEY=sk-your-key
```

### 3. 启动对话

```bash
daoyoucode chat
```

## 配置说明

### 主要配置：YAML文件

所有API密钥都配置在 `config/llm_config.yaml` 中：

```yaml
providers:
  # 通义千问（主力）
  qwen:
    api_key: ["sk-key1", "sk-key2"]  # 支持多key轮询
    enabled: true
  
  # DeepSeek（备用）
  deepseek:
    api_key: "sk-xxx"
    enabled: false  # 暂时禁用
```

**优势**:
- ✅ 支持多个API Key轮询（负载均衡）
- ✅ 可以启用/禁用特定提供商
- ✅ 配置集中，易于管理

### 备用方案：环境变量

只有当YAML未配置时，才会读取环境变量：

```bash
# .env 文件
QWEN_API_KEY=sk-xxx
DEEPSEEK_API_KEY=sk-xxx
```

**限制**:
- ❌ 不支持多Key轮询
- ❌ 不支持启用/禁用

### 配置优先级

```
YAML配置文件 > 环境变量
```

## 常用命令

```bash
# 启动对话
daoyoucode chat

# 使用特定Skill
daoyoucode chat --skill oracle          # 架构分析
daoyoucode chat --skill sisyphus        # 复杂任务

# 使用特定模型
daoyoucode chat --model deepseek-coder

# 查看帮助
daoyoucode --help
daoyoucode chat --help

# 查看可用Agent
daoyoucode agent

# 查看可用Skill
daoyoucode skills
```

## 开发模式

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest -v

# 格式化代码
black .

# 类型检查
mypy daoyoucode
```

## 调试

```bash
# 开启调试日志
export DEBUG_LLM=1
export LOG_LEVEL=DEBUG

# 保存请求到文件
export DEBUG_LLM_REQUEST=1

# 启动
daoyoucode chat
```

## 下一步

- 详细配置: [CONFIG_GUIDE.md](CONFIG_GUIDE.md)
- 开发环境: [DEV_SETUP.md](DEV_SETUP.md)
- 安装指南: [INSTALL.md](INSTALL.md)
- API文档: [../docs/zh-CN/API.md](../docs/zh-CN/API.md)
