# API 配置指南

## 📋 配置方式

DaoyouCode支持两种配置方式：

### 方式1: 配置文件（推荐）

编辑 `backend/config/llm_config.yaml`

### 方式2: 环境变量

设置环境变量（适合CI/CD）

---

## 🔑 获取API密钥

### 通义千问 (推荐)

1. 访问：https://dashscope.aliyun.com/
2. 注册/登录阿里云账号
3. 开通DashScope服务
4. 创建API密钥
5. 复制API Key

**配置示例**:
```yaml
providers:
  qwen:
    api_key: "sk-xxxxxxxxxxxxxxxxxxxxx"  # 你的API密钥
    base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
    models:
      - qwen-max
      - qwen-plus
      - qwen-coder-plus
    enabled: true  # 设置为true启用
```

### DeepSeek

1. 访问：https://platform.deepseek.com/
2. 注册/登录
3. 创建API密钥
4. 复制API Key

**配置示例**:
```yaml
providers:
  deepseek:
    api_key: "sk-xxxxxxxxxxxxxxxxxxxxx"
    base_url: "https://api.deepseek.com/v1"
    models:
      - deepseek-chat
      - deepseek-coder
    enabled: true
```

### OpenAI

1. 访问：https://platform.openai.com/
2. 注册/登录
3. 创建API密钥
4. 复制API Key

**配置示例**:
```yaml
providers:
  openai:
    api_key: "sk-xxxxxxxxxxxxxxxxxxxxx"
    base_url: "https://api.openai.com/v1"
    models:
      - gpt-4
      - gpt-3.5-turbo
    enabled: true
```

---

## 📝 配置步骤

### 步骤1: 编辑配置文件

```bash
# 打开配置文件
notepad backend\config\llm_config.yaml
```

### 步骤2: 填入API密钥

找到对应的提供商，替换 `your-xxx-api-key-here` 为你的真实API密钥：

```yaml
providers:
  qwen:
    api_key: "sk-your-real-api-key-here"  # ← 替换这里
    enabled: true  # ← 设置为true
```

### 步骤3: 启用提供商

将 `enabled: false` 改为 `enabled: true`：

```yaml
providers:
  qwen:
    api_key: "sk-xxxxx"
    enabled: true  # ← 改为true
```

### 步骤4: 保存文件

保存 `llm_config.yaml` 文件

### 步骤5: 测试配置

```bash
cd backend
.\venv\Scripts\activate
python daoyoucode.py doctor
```

如果看到 "✓ API密钥已配置"，说明配置成功！

---

## 🌍 使用环境变量

如果不想在配置文件中存储API密钥，可以使用环境变量：

### Windows (PowerShell)

```powershell
# 临时设置（当前会话）
$env:QWEN_API_KEY = "sk-xxxxxxxxxxxxxxxxxxxxx"

# 永久设置（系统环境变量）
[System.Environment]::SetEnvironmentVariable('QWEN_API_KEY', 'sk-xxxxx', 'User')
```

### Windows (CMD)

```cmd
# 临时设置
set QWEN_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxx

# 永久设置
setx QWEN_API_KEY "sk-xxxxxxxxxxxxxxxxxxxxx"
```

### Linux/Mac

```bash
# 临时设置
export QWEN_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxx"

# 永久设置（添加到 ~/.bashrc 或 ~/.zshrc）
echo 'export QWEN_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxx"' >> ~/.bashrc
source ~/.bashrc
```

### 支持的环境变量

- `QWEN_API_KEY` - 通义千问
- `DEEPSEEK_API_KEY` - DeepSeek
- `OPENAI_API_KEY` - OpenAI
- `ANTHROPIC_API_KEY` - Claude

---

## ✅ 验证配置

### 方法1: 使用doctor命令

```bash
python daoyoucode.py doctor
```

期望输出：
```
API密钥
  ✓ 已配置API密钥
```

### 方法2: 测试chat命令

```bash
python daoyoucode.py chat
```

如果看到 "✓ Agent系统初始化完成"，说明配置成功！

### 方法3: 运行测试脚本

```bash
python test_agent_integration.py
```

期望输出：
```
LLM客户端: ✓ 通过
```

---

## 🔒 安全建议

### 1. 不要提交API密钥到Git

确保 `llm_config.yaml` 在 `.gitignore` 中：

```gitignore
# API配置（包含密钥）
backend/config/llm_config.yaml
```

### 2. 使用环境变量（生产环境）

在生产环境中，建议使用环境变量而不是配置文件。

### 3. 定期轮换密钥

定期更换API密钥以提高安全性。

### 4. 限制密钥权限

在API提供商的控制台中，限制密钥的使用范围和配额。

---

## 🐛 常见问题

### Q1: 配置后仍然提示"未配置API密钥"

**解决方法**:
1. 检查 `enabled: true` 是否设置
2. 检查API密钥是否正确（没有多余空格）
3. 检查YAML格式是否正确（缩进）
4. 重启CLI

### Q2: 提示"未配置提供商: qwen"

**解决方法**:
1. 确保 `enabled: true`
2. 确保API密钥不是 `your-xxx-api-key-here`
3. 检查配置文件路径是否正确

### Q3: API调用失败

**解决方法**:
1. 检查API密钥是否有效
2. 检查网络连接
3. 检查API配额是否用完
4. 查看详细错误信息

### Q4: 想使用多个提供商

**解决方法**:
可以同时启用多个提供商：

```yaml
providers:
  qwen:
    api_key: "sk-xxxxx"
    enabled: true
  
  deepseek:
    api_key: "sk-xxxxx"
    enabled: true
```

然后使用 `--model` 参数选择：

```bash
python daoyoucode.py chat --model deepseek-coder
```

---

## 📞 获取帮助

如果遇到问题：

1. 查看日志：`python daoyoucode.py --verbose chat`
2. 运行诊断：`python daoyoucode.py doctor`
3. 查看文档：`backend/cli/README.md`
4. 提交Issue：GitHub Issues

---

## 🎉 配置完成

配置完成后，你就可以使用真实的AI功能了！

```bash
# 启动交互式对话
python daoyoucode.py chat

# 编辑文件
python daoyoucode.py edit main.py "添加日志功能"
```

享受DaoyouCode带来的AI编程体验！🚀
