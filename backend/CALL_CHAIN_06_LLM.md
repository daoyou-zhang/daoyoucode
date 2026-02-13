# 调用链路分析 - 06 LLM层

## 6. LLM层：模型调用

### 入口函数
```
📁 backend/daoyoucode/agents/llm/clients/unified.py :: UnifiedLLMClient.chat()
```

### 调用流程

#### 6.1 LLM客户端管理器

**文件**: `backend/daoyoucode/agents/llm/client_manager.py`

**代码**:
```python
class LLMClientManager:
    """LLM客户端管理器"""
    
    def __init__(self):
        self.http_client = httpx.AsyncClient(
            timeout=60.0,
            limits=httpx.Limits(max_connections=10)
        )
        self.provider_configs = {}
        self.clients = {}
    
    def add_provider(self, name: str, config: Dict):
        """添加提供商配置"""
        self.provider_configs[name] = config
    
    def get_client(self, model: str) -> BaseLLMClient:
        """获取客户端（根据模型名称）"""
        # 查找模型所属的提供商
        provider = self._find_provider_for_model(model)
        
        # 获取或创建客户端
        if provider not in self.clients:
            config = self.provider_configs[provider]
            self.clients[provider] = UnifiedLLMClient(
                http_client=self.http_client,
                api_key=config['api_key'],
                base_url=config['base_url'],
                model=model
            )
        
        return self.clients[provider]
```

**职责**:
- 管理多个LLM提供商
- 共享HTTP连接池
- 根据模型名称路由到正确的客户端

---

#### 6.2 配置加载

**文件**: `backend/daoyoucode/agents/llm/config_loader.py`

**代码**:
```python
def auto_configure(client_manager: LLMClientManager):
    """自动配置LLM客户端"""
    # 1. 加载配置文件
    config = load_llm_config()
    
    # 2. 注册提供商
    for provider_name, provider_config in config.get('providers', {}).items():
        if provider_config.get('enabled', True):
            client_manager.add_provider(provider_name, provider_config)
```

**配置文件**: `backend/config/llm_config.yaml`

**内容**:
```yaml
providers:
  qwen:
    enabled: true
    api_key: ${DASHSCOPE_API_KEY}
    base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
    models:
      - qwen-max
      - qwen-plus
      - qwen-turbo
  
  deepseek:
    enabled: false
    api_key: ${DEEPSEEK_API_KEY}
    base_url: "https://api.deepseek.com/v1"
    models:
      - deepseek-chat
      - deepseek-coder
```

---

#### 6.3 统一LLM客户端

**文件**: `backend/daoyoucode/agents/llm/clients/unified.py`

**代码**:
```python
class UnifiedLLMClient(BaseLLMClient):
    """统一LLM客户端（OpenAI兼容格式）"""
    
    async def chat(self, request: LLMRequest) -> LLMResponse:
        """同步对话"""
        start_time = time.time()
        
        # 支持多轮对话
        if hasattr(request, 'messages') and request.messages:
            messages = request.messages
        else:
            messages = [{"role": "user", "content": request.prompt}]
        
        try:
            # 构建请求payload
            payload = {
                "model": request.model,
                "messages": messages,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
            }
            
            # 添加Function Calling支持
            if hasattr(request, 'functions') and request.functions:
                payload["functions"] = request.functions
                if hasattr(request, 'function_call'):
                    payload["function_call"] = request.function_call
            
            # 发送HTTP请求
            response = await self.http_client.post(
                f"{self.base_url}/chat/completions",
                headers=self._get_headers(),
                json=payload,
                timeout=60.0
            )
            response.raise_for_status()
            data = response.json()
            
            latency = time.time() - start_time
            
            # 解析响应
            message = data["choices"][0]["message"]
            function_call = message.get("function_call")
            
            return LLMResponse(
                content=message.get("content", ""),
                model=request.model,
                tokens_used=data["usage"]["total_tokens"],
                cost=self._calculate_cost(data["usage"], request.model),
                latency=latency,
                metadata={
                    "prompt_tokens": data["usage"]["prompt_tokens"],
                    "completion_tokens": data["usage"]["completion_tokens"],
                    "function_call": function_call
                }
            )
        
        except httpx.TimeoutException as e:
            raise LLMTimeoutError(f"请求超时: {e}")
        except httpx.HTTPError as e:
            raise LLMConnectionError(f"连接错误: {e}")
```

**关键特性**:
- OpenAI兼容格式
- 支持多轮对话（messages参数）
- 支持Function Calling
- 自动计算成本
- 错误处理

---

#### 6.4 请求/响应数据结构

**LLMRequest**:
```python
@dataclass
class LLMRequest:
    prompt: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 4000
    messages: Optional[List[Dict]] = None  # 多轮对话
    functions: Optional[List[Dict]] = None  # Function schemas
    function_call: Optional[str] = None  # "auto" | "none"
```

**LLMResponse**:
```python
@dataclass
class LLMResponse:
    content: str
    model: str
    tokens_used: int
    cost: float
    latency: float
    metadata: Dict[str, Any] = field(default_factory=dict)
```

---

#### 6.5 Function Calling格式

**请求格式**:
```json
{
  "model": "qwen-max",
  "messages": [
    {"role": "user", "content": "Agent系统是怎么实现的？"}
  ],
  "functions": [
    {
      "name": "repo_map",
      "description": "生成代码仓库地图",
      "parameters": {
        "type": "object",
        "properties": {
          "repo_path": {
            "type": "string",
            "description": "仓库根目录路径"
          },
          "max_tokens": {
            "type": "integer",
            "description": "最大token数量",
            "default": 2000
          }
        },
        "required": ["repo_path"]
      }
    }
  ],
  "temperature": 0.7
}
```

**响应格式（有function_call）**:
```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": null,
        "function_call": {
          "name": "repo_map",
          "arguments": "{\"repo_path\": \"backend\", \"max_tokens\": 2000}"
        }
      }
    }
  ],
  "usage": {
    "prompt_tokens": 1234,
    "completion_tokens": 56,
    "total_tokens": 1290
  }
}
```

**响应格式（无function_call）**:
```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "Agent系统主要在backend/daoyoucode/agents/目录下实现..."
      }
    }
  ],
  "usage": {
    "prompt_tokens": 1234,
    "completion_tokens": 567,
    "total_tokens": 1801
  }
}
```

---

#### 6.6 成本计算

**代码**:
```python
# 模型定价（每1000 tokens，单位：元）
PRICING = {
    "qwen-max": {"input": 0.02, "output": 0.06},
    "qwen-plus": {"input": 0.004, "output": 0.012},
    "qwen-turbo": {"input": 0.002, "output": 0.006},
    "default": {"input": 0.01, "output": 0.03},
}

def _calculate_cost(self, usage: dict, model: str) -> float:
    """计算成本"""
    input_tokens = usage.get("prompt_tokens", 0)
    output_tokens = usage.get("completion_tokens", 0)
    
    pricing = self.PRICING.get(model, self.PRICING["default"])
    
    cost = (
        input_tokens * pricing["input"] +
        output_tokens * pricing["output"]
    ) / 1000
    
    return cost
```

**示例**:
```
输入: 1000 tokens
输出: 500 tokens
模型: qwen-plus

成本 = (1000 * 0.004 + 500 * 0.012) / 1000
     = (4 + 6) / 1000
     = 0.01 元
```

---

### 关键文件清单

| 文件 | 职责 | 关键类/函数 |
|------|------|------------|
| `llm/client_manager.py` | 客户端管理 | `LLMClientManager` |
| `llm/config_loader.py` | 配置加载 | `auto_configure()` |
| `llm/clients/unified.py` | 统一客户端 | `UnifiedLLMClient` |
| `llm/base.py` | 基础定义 | `LLMRequest`, `LLMResponse` |
| `config/llm_config.yaml` | LLM配置 | YAML配置 |

---

### 依赖关系

```
client_manager.py
    ↓
├─ config_loader.py
│   └─ llm_config.yaml
├─ clients/unified.py
│   ├─ httpx (HTTP客户端)
│   └─ base.py (数据结构)
└─ exceptions.py (异常定义)
```

---

### 下一步

LLM层完成后，返回到 **Agent层**，或继续到 **Memory层**

→ 继续阅读 `CALL_CHAIN_07_MEMORY.md`
