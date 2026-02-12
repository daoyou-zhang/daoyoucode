# 🔑 API配置快速指南

## 方式1: 使用配置向导（最简单）

```bash
cd backend
config_api.bat
```

选择 `[1] 编辑配置文件`，然后按照提示操作。

---

## 方式2: 手动配置

### 步骤1: 打开配置文件

```bash
notepad backend\config\llm_config.yaml
```

### 步骤2: 填入API密钥

找到 `qwen` 部分，修改：

```yaml
providers:
  qwen:
    api_key: "sk-your-real-api-key-here"  # ← 替换为你的API密钥
    enabled: true  # ← 改为true
```

### 步骤3: 保存并测试

```bash
cd backend
.\venv\Scripts\activate
python daoyoucode.py doctor
```

---

## 获取API密钥

### 通义千问（推荐，免费额度）

1. 访问：https://dashscope.aliyun.com/
2. 注册/登录阿里云账号
3. 开通DashScope服务
4. 创建API密钥
5. 复制密钥到配置文件

---

## 验证配置

```bash
# 方法1: 诊断命令
python daoyoucode.py doctor

# 方法2: 测试脚本
python test_agent_integration.py

# 方法3: 直接使用
python daoyoucode.py chat
```

---

## 配置文件位置

```
backend/
  └── config/
      ├── llm_config.yaml          ← API配置文件
      └── API_CONFIG_GUIDE.md      ← 详细配置指南
```

---

## 需要帮助？

查看详细指南：`backend/config/API_CONFIG_GUIDE.md`
