# LLM模块测试

## 测试结构

```
tests/llm/
├── __init__.py
├── test_base.py              # 基础接口测试
├── test_exceptions.py        # 异常测试
├── test_client_manager.py    # 客户端管理器测试
└── clients/
    ├── __init__.py
    └── test_unified.py       # 统一客户端测试
```

## 运行测试

### 运行所有LLM测试

```bash
cd backend
pytest tests/llm -v
```

### 运行特定测试文件

```bash
pytest tests/llm/test_base.py -v
pytest tests/llm/test_client_manager.py -v
```

### 运行特定测试函数

```bash
pytest tests/llm/test_base.py::test_llm_request_creation -v
```

### 生成覆盖率报告

```bash
pytest tests/llm --cov=daoyoucode.llm --cov-report=html
```

覆盖率报告会生成在 `htmlcov/index.html`

### 使用测试脚本

```bash
python run_tests.py
```

## 测试覆盖

### test_base.py
- ✅ LLMRequest创建和默认值
- ✅ LLMResponse创建和元数据

### test_exceptions.py
- ✅ 所有异常类型
- ✅ 异常继承关系

### test_unified.py
- ✅ 成功的对话请求
- ✅ 超时处理
- ✅ 连接错误处理
- ✅ 成本计算
- ✅ 流式对话
- ✅ 请求头生成

### test_client_manager.py
- ✅ 单例模式
- ✅ 提供商配置
- ✅ 提供商推断
- ✅ 客户端获取
- ✅ 使用统计
- ✅ HTTP客户端共享

## 依赖

测试需要以下依赖：

```bash
pip install pytest pytest-asyncio pytest-cov
```

## 注意事项

1. 测试使用mock，不会真正调用LLM API
2. 异步测试使用 `@pytest.mark.asyncio` 装饰器
3. 单例测试需要重置 `_instance` 和 `_initialized`
