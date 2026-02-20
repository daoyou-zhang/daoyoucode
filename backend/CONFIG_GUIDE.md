# DaoyouCode 配置指南

## 配置优先级

DaoyouCode 使用以下优先级读取配置：

1. **YAML配置文件**（推荐）: `backend/config/llm_config.yaml`
2. **环境变量**（备用）: `.env` 文件或系统环境变量

## 推荐方式：使用YAML配置

### 1. 编辑配置文件

```bash
cd backend
vim config/llm_config.yaml
```

### 2. 配置示例

```yaml
providers:
  # 通义千问（主力）
  qwen:
    # 支持多个API Key轮询（负载均衡）
    api_key: 
      - "sk-d2971f2015574377bdf97046b1a03b87"
      - "sk-4b232539c58d497ebe6212017060cd2e"
    base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
    models:
      - qwen-max
      - qwen-plus
      - qwen-turbo
      - qwen-coder-plus
    enabled: true  # 启用
  
  # DeepSeek（备用）
  deepseek:
    api_key: "sk-your-deepseek-key"
    base_url: "https://api.deepseek.com/v1"
    models:
      - deepseek-chat
      - deepseek-coder
    enabled: false  # 暂时禁用
  
  # OpenAI（可选）
  openai:
    api_key: "sk-your-openai-key"
    base_url: "https://api.openai.com/v1"
    models:
      - gpt-4
      - gpt-3.5-turbo
    enabled: false

# 默认配置
default:
  model: "qwen-max"
  temperature: 0.7
  max_tokens: 4000
  timeout: 1800
```

### 3. YAML配置的优势

✅ **多Key轮询**: 支持配置多个API Key，自动轮询使用（负载均衡）
✅ **灵活启用**: 可以随时启用/禁用某个提供商
✅ **集中管理**: 所有配置在一个文件中
✅ **版本控制**: 可以提交到Git（注意不要提交真实密钥）
✅ **团队协作**: 团队成员可以共享配置模板

### 4. 多Key轮询示例

```yaml
qwen:
  api_key:  # 列表形式，自动轮询
    - "sk-key1-for-project-a"
    - "sk-key2-for-project-b"
    - "sk-key3-for-backup"
  enabled: true
```

系统会自动在这3个Key之间轮询，避免单个Key的频率限制。

## 备用方式：使用环境变量

### 1. 创建.env文件

```bash
cd backend
cp .env.example .env
vim .env
```

### 2. 配置环境变量

```bash
# 通义千问
QWEN_API_KEY=sk-your-qwen-key

# DeepSeek
DEEPSEEK_API_KEY=sk-your-deepseek-key

# OpenAI
OPENAI_API_KEY=sk-your-openai-key
```

### 3. 环境变量的限制

❌ **不支持多Key**: 只能配置一个API Key
❌ **不支持启用/禁用**: 配置了就会使用
❌ **配置分散**: 需要在多个地方配置

### 4. 何时使用环境变量

- 在Docker容器中运行
- 在CI/CD环境中
- 临时测试不同的Key
- 不想修改配置文件

## 配置加载逻辑

```python
# 伪代码
def auto_configure(client_manager):
    # 1. 尝试从YAML加载
    config = load_yaml("config/llm_config.yaml")
    if config.has_enabled_providers():
        use_yaml_config(config)
        return
    
    # 2. YAML没有配置，尝试环境变量
    if has_env_vars():
        use_env_vars()
        return
    
    # 3. 都没有配置
    raise ConfigError("请配置API密钥")
```

## 向量检索配置

### 使用向量API（推荐）

在 `config/embedding_config.yaml` 中配置：

```yaml
# 向量检索配置
retriever:
  mode: "api"  # 使用API模式
  
  # 智谱AI Embedding API
  api:
    provider: "zhipu"
    api_key: "your-zhipu-api-key"
    model: "embedding-2"
```

### 使用本地向量模型

```yaml
retriever:
  mode: "local"  # 使用本地模型
  
  local:
    model: "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    device: "cpu"  # 或 "cuda"
```

注意：本地模式需要安装额外依赖：
```bash
pip install -e ".[embedding]"
```

## 配置验证

### 检查配置是否生效

```bash
# 启动CLI，查看日志
daoyoucode chat

# 应该看到类似输出：
# ✓ 已配置提供商: qwen (2 个API Key)
# ✓ LLM配置完成，可用提供商: qwen
```

### 测试API连接

```python
# 在Python中测试
from daoyoucode.agents.llm import get_client_manager

manager = get_client_manager()
print(manager.provider_configs.keys())  # 应该显示: dict_keys(['qwen'])
```

### 调试配置问题

```bash
# 开启调试日志
export LOG_LEVEL=DEBUG
daoyoucode chat

# 或在配置文件中设置
# .env:
LOG_LEVEL=DEBUG
```

## 安全建议

### 1. 不要提交真实密钥到Git

```bash
# .gitignore 中应该包含：
backend/config/llm_config.yaml
backend/.env
*.key
```

### 2. 使用配置模板

提交一个模板文件：

```yaml
# llm_config.yaml.example
providers:
  qwen:
    api_key: "your-qwen-api-key-here"  # 占位符
    enabled: true
```

团队成员复制后填入真实密钥：
```bash
cp llm_config.yaml.example llm_config.yaml
vim llm_config.yaml  # 填入真实密钥
```

### 3. 使用密钥管理工具

生产环境建议使用：
- AWS Secrets Manager
- HashiCorp Vault
- Azure Key Vault

## 常见问题

### Q1: 配置了YAML但还是提示未配置？

检查：
1. `enabled: true` 是否设置
2. API Key是否是占位符（`your-xxx-key-here`）
3. YAML格式是否正确（缩进、引号）

```bash
# 验证YAML格式
python -c "import yaml; yaml.safe_load(open('config/llm_config.yaml'))"
```

### Q2: 多个Key如何轮询？

系统会自动轮询，每次请求使用下一个Key：

```yaml
api_key:
  - "key1"  # 第1次请求
  - "key2"  # 第2次请求
  - "key3"  # 第3次请求
  - "key1"  # 第4次请求（循环）
```

### Q3: 如何临时切换到另一个提供商？

方式1：修改YAML
```yaml
qwen:
  enabled: false  # 禁用
deepseek:
  enabled: true   # 启用
```

方式2：使用命令行参数
```bash
daoyoucode chat --model deepseek-chat
```

### Q4: 环境变量和YAML同时配置会怎样？

YAML优先。只有YAML未配置时才会读取环境变量。

### Q5: 如何配置代理？

在YAML中添加：
```yaml
qwen:
  api_key: "sk-xxx"
  base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
  proxy: "http://127.0.0.1:7890"  # 代理地址
```

或使用环境变量：
```bash
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
```

## 配置文件位置

```
backend/
├── config/
│   ├── llm_config.yaml          # LLM API配置（主要）
│   ├── embedding_config.yaml    # 向量检索配置
│   ├── agent_router_config.yaml # Agent路由配置
│   └── memory_load_strategies.yaml  # 记忆加载策略
├── .env                         # 环境变量（备用）
└── .env.example                 # 环境变量模板
```

## 下一步

- 查看 [安装指南](INSTALL.md)
- 了解 [开发配置](DEV_SETUP.md)
- 阅读 [API文档](../docs/zh-CN/API.md)
