# API Key轮询配置说明

## 功能介绍

为了解决API配额限制和500错误问题，系统支持配置多个API Key进行轮询使用。

### 优势

1. **分散请求压力** - 多个key轮流使用，避免单个key配额耗尽
2. **提高可用性** - 一个key失败可以切换到下一个
3. **灵活配置** - 1个key就用1个，多个就轮询
4. **自动管理** - 系统自动Round-robin轮询，无需手动干预

## 配置方法

### 方式1: 单个API Key（默认）

```yaml
providers:
  qwen:
    api_key: "sk-your-api-key-here"
    base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
    models:
      - qwen-max
      - qwen-plus
    enabled: true
```

### 方式2: 多个API Key（推荐）

```yaml
providers:
  qwen:
    # 注释掉单个key
    # api_key: "sk-your-api-key-here"
    
    # 配置多个key（轮询使用）
    api_keys:
      - "sk-key1-here"
      - "sk-key2-here"
      - "sk-key3-here"
    
    base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
    models:
      - qwen-max
      - qwen-plus
    enabled: true
```

## 工作原理

### Round-robin轮询

系统使用Round-robin（轮询）策略：

```
请求1 → Key1
请求2 → Key2
请求3 → Key3
请求4 → Key1  (循环)
请求5 → Key2
请求6 → Key3
...
```

### 示例

假设配置了3个API Key：

```yaml
api_keys:
  - "sk-aaa"
  - "sk-bbb"
  - "sk-ccc"
```

系统行为：
- 第1次调用LLM → 使用 `sk-aaa`
- 第2次调用LLM → 使用 `sk-bbb`
- 第3次调用LLM → 使用 `sk-ccc`
- 第4次调用LLM → 使用 `sk-aaa` (循环)
- ...

## 配置示例

### 示例1: 2个API Key

```yaml
providers:
  qwen:
    api_keys:
      - "sk-d2971f2015574377bdf97046b1a03b87"
      - "sk-e3a82g3126685488ceg08157c2b14c98"
    base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
    models:
      - qwen-max
      - qwen-plus
      - qwen-coder-plus
    enabled: true
```

### 示例2: 3个API Key

```yaml
providers:
  qwen:
    api_keys:
      - "sk-key1-xxxxxxxxxx"
      - "sk-key2-yyyyyyyyyy"
      - "sk-key3-zzzzzzzzzz"
    base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
    models:
      - qwen-max
      - qwen-plus
    enabled: true
```

### 示例3: 多个提供商，各自配置多个key

```yaml
providers:
  qwen:
    api_keys:
      - "sk-qwen-key1"
      - "sk-qwen-key2"
    base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
    models:
      - qwen-max
    enabled: true
  
  deepseek:
    api_keys:
      - "sk-deepseek-key1"
      - "sk-deepseek-key2"
      - "sk-deepseek-key3"
    base_url: "https://api.deepseek.com/v1"
    models:
      - deepseek-chat
    enabled: true
```

## 验证配置

运行测试验证配置是否正确：

```bash
cd backend
python test_api_key_rotation.py
```

输出示例：
```
✅ 所有测试通过！

📝 使用说明：
1. 在 config/llm_config.yaml 中配置多个API Key
2. 系统会自动轮询使用这些key
3. 1个key就用1个，多个就轮询
4. 可以有效分散API配额压力
```

## 日志查看

系统会在日志中显示使用的API Key信息（部分隐藏）：

```
INFO - 已配置提供商: qwen (3 个API Key)
DEBUG - 提供商 qwen: 使用API Key #1/3 (sk-d2971f2...)
DEBUG - 提供商 qwen: 使用API Key #2/3 (sk-e3a82g3...)
DEBUG - 提供商 qwen: 使用API Key #3/3 (sk-f4b93h4...)
```

## 常见问题

### Q: 如何申请多个API Key？

A: 在阿里云控制台创建多个API Key：
1. 登录阿里云控制台
2. 进入DashScope服务
3. 创建多个API Key
4. 将它们配置到 `llm_config.yaml`

### Q: 多个key会增加成本吗？

A: 不会。总请求数不变，只是分散到多个key上。

### Q: 如果一个key失败了怎么办？

A: 当前版本会继续轮询到下一个key。未来可以添加自动故障切换。

### Q: 可以动态添加/删除key吗？

A: 目前需要修改配置文件并重启。未来可以支持热重载。

### Q: 轮询是线程安全的吗？

A: 是的。使用了计数器和取模运算，保证线程安全。

## 最佳实践

1. **建议配置2-3个API Key** - 平衡成本和可用性
2. **监控各key的使用情况** - 确保负载均衡
3. **定期检查配额** - 避免所有key同时耗尽
4. **保持key的安全** - 不要提交到git仓库

## 技术细节

### 实现位置

- 配置文件: `backend/config/llm_config.yaml`
- 客户端管理器: `backend/daoyoucode/agents/llm/client_manager.py`
- 配置加载器: `backend/daoyoucode/agents/llm/config_loader.py`
- 测试文件: `backend/test_api_key_rotation.py`

### 核心代码

```python
def _get_next_api_key(self, provider: str) -> str:
    """获取下一个API Key（Round-robin轮询）"""
    config = self.provider_configs[provider]
    keys = config['api_keys']
    
    # 如果只有一个key，直接返回
    if len(keys) == 1:
        return keys[0]
    
    # 轮询：获取当前计数器对应的key，然后递增计数器
    current_index = self.key_counters[provider] % len(keys)
    self.key_counters[provider] += 1
    
    return keys[current_index]
```

## 更新记录

- **2025-02-17**: 初始版本，支持Round-robin轮询
- 支持单个或多个API Key配置
- 自动适配key数量
- 完整的测试覆盖

---

**配置完成后，系统会自动使用轮询机制，无需额外操作！**
