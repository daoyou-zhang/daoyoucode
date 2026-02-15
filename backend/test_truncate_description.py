"""
测试智能截断描述功能
"""

import sys
from pathlib import Path

# 添加backend到路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from daoyoucode.agents.executor import _truncate_description


def test_short_text():
    """测试短文本（不需要截断）"""
    text = "这是一个短文本"
    result = _truncate_description(text, max_length=500)
    assert result == text
    print(f"✓ 短文本测试通过: {result}")


def test_long_text():
    """测试长文本（需要截断）"""
    text = "这是一个很长的文本" * 100  # 1000个字符
    result = _truncate_description(text, max_length=100)
    
    print(f"\n原始文本长度: {len(text)}")
    print(f"截断后长度: {len(result)}")
    print(f"截断后内容: {result}")
    
    assert len(result) <= 100
    assert "..." in result
    assert result.startswith("这是一个很长的文本")
    assert result.endswith("很长的文本")
    print("✓ 长文本测试通过")


def test_exact_length():
    """测试刚好等于最大长度"""
    text = "a" * 100
    result = _truncate_description(text, max_length=100)
    assert result == text
    print(f"✓ 精确长度测试通过: 长度={len(result)}")


def test_slightly_over():
    """测试稍微超过最大长度"""
    text = "a" * 101
    result = _truncate_description(text, max_length=100)
    
    print(f"\n原始长度: {len(text)}")
    print(f"截断后长度: {len(result)}")
    print(f"截断后内容: {result[:20]}...{result[-20:]}")
    
    assert len(result) <= 100
    assert "..." in result
    print("✓ 稍微超长测试通过")


def test_very_long_text():
    """测试非常长的文本"""
    text = "用户问题：" + "这是一个非常详细的问题描述，包含了很多背景信息和上下文。" * 50
    result = _truncate_description(text, max_length=500)
    
    print(f"\n原始长度: {len(text)}")
    print(f"截断后长度: {len(result)}")
    print(f"截断后内容:\n{result}")
    
    assert len(result) <= 500
    assert "..." in result
    assert result.startswith("用户问题：")
    print("✓ 超长文本测试通过")


def test_multiline_text():
    """测试多行文本"""
    text = """用户问题：
    
我想了解这个项目的架构设计。

具体来说，我想知道：
1. 项目的整体结构是什么样的？
2. 各个模块之间是如何交互的？
3. 有哪些核心组件？
4. 使用了哪些设计模式？
5. 如何扩展新功能？

请详细说明。
""" * 10  # 重复10次，制造长文本
    
    result = _truncate_description(text, max_length=500)
    
    print(f"\n原始长度: {len(text)}")
    print(f"截断后长度: {len(result)}")
    print(f"截断后内容:\n{result}")
    
    assert len(result) <= 500
    assert "..." in result
    print("✓ 多行文本测试通过")


def test_chinese_text():
    """测试中文文本"""
    text = "这是一段中文文本，用于测试智能截断功能是否能正确处理中文字符。" * 20
    result = _truncate_description(text, max_length=200)
    
    print(f"\n原始长度: {len(text)}")
    print(f"截断后长度: {len(result)}")
    print(f"截断后内容: {result}")
    
    assert len(result) <= 200
    assert "..." in result
    print("✓ 中文文本测试通过")


def test_mixed_text():
    """测试中英文混合文本"""
    text = "User question: 请帮我分析一下这个项目的代码结构。I want to understand the architecture. " * 20
    result = _truncate_description(text, max_length=300)
    
    print(f"\n原始长度: {len(text)}")
    print(f"截断后长度: {len(result)}")
    print(f"截断后内容: {result}")
    
    assert len(result) <= 300
    assert "..." in result
    print("✓ 中英文混合测试通过")


def test_code_snippet():
    """测试包含代码片段的文本"""
    text = """用户问题：请帮我优化这段代码

```python
def process_data(data):
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
    return result
```

这段代码有什么问题？如何优化？
""" * 5
    
    result = _truncate_description(text, max_length=400)
    
    print(f"\n原始长度: {len(text)}")
    print(f"截断后长度: {len(result)}")
    print(f"截断后内容:\n{result}")
    
    assert len(result) <= 400
    assert "..." in result
    print("✓ 代码片段测试通过")


def test_comparison():
    """对比旧方法和新方法"""
    text = "用户问题：" + "这是一个详细的问题描述。" * 50
    
    # 旧方法：简单截断
    old_result = text[:200]
    
    # 新方法：智能截断
    new_result = _truncate_description(text, max_length=200)
    
    print("\n" + "="*60)
    print("对比旧方法和新方法")
    print("="*60)
    print(f"\n原始文本长度: {len(text)}")
    print(f"\n旧方法（简单截断前200字符）:")
    print(f"长度: {len(old_result)}")
    print(f"内容: {old_result}")
    print(f"\n新方法（智能截断，保留开头和结尾）:")
    print(f"长度: {len(new_result)}")
    print(f"内容: {new_result}")
    print("\n" + "="*60)
    print("✓ 对比测试完成")


if __name__ == "__main__":
    print("="*60)
    print("测试智能截断描述功能")
    print("="*60)
    
    test_short_text()
    test_long_text()
    test_exact_length()
    test_slightly_over()
    test_very_long_text()
    test_multiline_text()
    test_chinese_text()
    test_mixed_text()
    test_code_snippet()
    test_comparison()
    
    print("\n" + "="*60)
    print("✓ 所有测试通过！")
    print("="*60)

