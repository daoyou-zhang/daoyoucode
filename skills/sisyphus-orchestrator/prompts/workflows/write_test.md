# 编写测试工作流

## 工具使用原则

⚠️ **必读**：请先阅读 [工具使用指南](tool_usage_guide.md)，了解工具优先级和最佳实践。

**核心原则：优先使用 repo_map、AST 等高效工具，避免逐个文件搜索！**

## 任务目标

为代码编写测试，确保代码质量和功能正确性。

## 测试原则

1. **测试要清晰**：测试名称要说明测试什么
2. **测试要独立**：每个测试独立运行
3. **测试要快速**：测试应该快速执行
4. **测试要可靠**：测试结果要稳定

## 执行步骤

### 1. 理解被测代码

**⚠️ 重要：优先使用 repo_map 和 AST 工具获取全局视图！**

参考：[工具使用指南](tool_usage_guide.md)

#### 1.1 获取项目代码地图（推荐，第一步）
```
使用工具：repo_map
参数：
  - repo_path: "."
  - max_depth: 3
  - include_tests: true

作用：
- ✅ 了解被测代码在项目中的位置
- ✅ 查看现有的测试结构和组织方式
- ✅ 识别哪些代码已有测试，哪些缺少测试
- ✅ 了解测试覆盖情况
```

#### 1.2 读取被测代码
```
使用工具：read_file
参数：
  - file_path: "被测试的文件"

作用：了解代码功能
```

#### 1.3 分析代码结构（AST 优先）
```
使用工具：get_file_symbols
参数：
  - file_path: "被测试的文件"

作用：
- ✅ 快速获取所有函数、类的列表
- ✅ 了解哪些需要测试
- ✅ 比手动阅读更高效
```

#### 1.4 查找现有测试（repo_map 已包含）
```
如果 repo_map 不够详细，可以使用：
使用工具：text_search
参数：
  - query: "test_具体函数名"（不要搜索 "test_"，太宽泛）
  - file_pattern: "**/test_*.py"（根据语言调整）

作用：查找具体函数的测试

注意：repo_map 已经包含了测试文件信息，通常不需要再搜索
```

### 2. 确定测试范围

**明确要测试什么**：

#### 2.1 识别测试点
- 正常情况（Happy Path）
- 边界条件（Boundary Cases）
- 异常情况（Error Cases）
- 特殊输入（Special Inputs）

#### 2.2 确定测试类型
- **单元测试**：测试单个函数/类
- **集成测试**：测试多个模块协作
- **端到端测试**：测试完整流程


### 3. 设计测试用例

**为每个测试点设计用例**：

#### 3.1 测试用例结构（AAA模式）
```
Arrange（准备）：准备测试数据和环境
Act（执行）：执行被测试的代码
Assert（断言）：验证结果是否正确
```

#### 3.2 测试用例命名
- `test_function_name_when_condition_then_expected`
- 例如：`test_login_when_valid_credentials_then_success`

### 4. 编写测试代码

**遵循项目的测试框架**：

#### 4.1 确定测试框架
常见框架：
- Python: pytest, unittest
- JavaScript: Jest, Mocha
- Java: JUnit
- Go: testing

#### 4.2 编写测试
```
使用工具：write_file
参数：
  - file_path: "测试文件路径"
  - content: "测试代码"

作用：创建测试文件
```

#### 4.3 测试代码结构
```python
# 示例：Python pytest
def test_function_name():
    # Arrange
    input_data = "test"
    expected = "TEST"
    
    # Act
    result = function_to_test(input_data)
    
    # Assert
    assert result == expected
```

### 5. 运行测试

**验证测试是否通过**：

#### 5.1 运行测试
```
使用工具：run_test
参数：
  - test_path: "测试文件路径"

作用：执行测试
```

#### 5.2 分析测试结果
- 所有测试通过？
- 有测试失败？
- 失败原因是什么？

#### 5.3 修复失败的测试
如果测试失败：
1. 检查测试代码是否正确
2. 检查被测代码是否有问题
3. 修复问题
4. 重新运行测试

### 6. 检查测试覆盖率

**确保测试覆盖了关键代码**：

#### 6.1 检查覆盖的场景
- ✅ 正常情况
- ✅ 边界条件
- ✅ 异常情况
- ✅ 特殊输入

#### 6.2 补充缺失的测试
如果发现遗漏：
1. 添加新的测试用例
2. 运行测试验证
3. 确保覆盖完整

### 7. 说明测试

简要说明测试内容和运行方法，根据用户需求灵活调整说明的详细程度。

## 常见测试场景

### 场景1：测试纯函数

**特点**：输入确定，输出确定，无副作用

```python
def test_add():
    # Arrange
    a, b = 1, 2
    expected = 3
    
    # Act
    result = add(a, b)
    
    # Assert
    assert result == expected
```

### 场景2：测试边界条件

**特点**：测试极端情况

```python
def test_divide_by_zero():
    # Arrange
    a, b = 10, 0
    
    # Act & Assert
    with pytest.raises(ZeroDivisionError):
        divide(a, b)
```

### 场景3：测试异常处理

**特点**：测试错误情况

```python
def test_invalid_input():
    # Arrange
    invalid_input = None
    
    # Act & Assert
    with pytest.raises(ValueError):
        process(invalid_input)
```

### 场景4：测试类方法

**特点**：需要创建对象

```python
def test_user_login():
    # Arrange
    user = User("test@example.com", "password")
    
    # Act
    result = user.login()
    
    # Assert
    assert result is True
```

### 场景5：测试异步代码

**特点**：需要异步测试框架

```python
async def test_async_function():
    # Arrange
    data = "test"
    
    # Act
    result = await async_function(data)
    
    # Assert
    assert result == expected
```

### 场景6：测试 Mock

**特点**：隔离外部依赖

```python
def test_with_mock(mocker):
    # Arrange
    mock_api = mocker.patch('module.api_call')
    mock_api.return_value = {"status": "ok"}
    
    # Act
    result = function_that_calls_api()
    
    # Assert
    assert result["status"] == "ok"
    mock_api.assert_called_once()
```

## 测试最佳实践

### 1. 测试命名

✅ **好的命名**：
- `test_login_with_valid_credentials_returns_success`
- `test_divide_by_zero_raises_exception`
- `test_empty_list_returns_zero`

❌ **不好的命名**：
- `test1`
- `test_function`
- `test_case`

### 2. 测试独立性

✅ **好的做法**：
- 每个测试独立运行
- 不依赖其他测试
- 不共享状态

❌ **不好的做法**：
- 测试之间有依赖
- 共享全局变量
- 依赖执行顺序

### 3. 测试数据

✅ **好的做法**：
- 使用有意义的测试数据
- 测试数据清晰明确
- 使用 fixture 或 factory

❌ **不好的做法**：
- 使用随机数据
- 测试数据不清晰
- 硬编码大量数据

### 4. 断言

✅ **好的做法**：
- 一个测试一个断言（或相关的几个）
- 断言要清晰
- 使用合适的断言方法

❌ **不好的做法**：
- 一个测试太多断言
- 断言不清晰
- 只断言不抛异常

## 工具使用原则

### 编写测试前

1. **必须理解代码**：知道要测试什么
2. **必须查看现有测试**：保持风格一致
3. **必须确定测试框架**：使用项目的测试框架

### 编写测试时

1. **遵循 AAA 模式**：Arrange, Act, Assert
2. **测试要清晰**：命名和结构要清晰
3. **测试要完整**：覆盖主要场景

### 编写测试后

1. **必须运行测试**：确保测试通过
2. **必须检查覆盖**：确保覆盖关键代码
3. **必须说明测试**：告诉用户如何运行

## 注意事项

### 测试质量

1. **测试要有价值**：测试真正的功能，不是测试框架
2. **测试要可维护**：代码改动时，测试也要易于更新
3. **测试要快速**：避免慢测试，影响开发效率
4. **测试要稳定**：避免不稳定的测试（Flaky Tests）

### 避免的错误

❌ **不要测试实现细节**
- 测试公共接口，不是私有方法
- 测试行为，不是实现

❌ **不要过度 Mock**
- 只 Mock 外部依赖
- 不要 Mock 被测试的代码

❌ **不要忽略边界条件**
- 空值、空集合
- 最大值、最小值
- 特殊字符

❌ **不要写不稳定的测试**
- 避免依赖时间
- 避免依赖随机数
- 避免依赖网络

## 成功标准

- ✅ 测试覆盖了主要功能
- ✅ 测试覆盖了边界条件
- ✅ 测试覆盖了异常情况
- ✅ 所有测试通过
- ✅ 测试代码清晰易懂
- ✅ 测试运行快速稳定
