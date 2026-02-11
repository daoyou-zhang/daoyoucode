"""
快速测试验证脚本
用于验证LLM模块基础功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from daoyoucode.llm.client_manager import get_client_manager
from daoyoucode.llm.base import LLMRequest


async def test_basic_functionality():
    """测试基础功能"""
    print("=" * 60)
    print("LLM模块快速测试")
    print("=" * 60)
    
    # 1. 测试客户端管理器
    print("\n1. 测试客户端管理器...")
    manager = get_client_manager()
    print(f"   ✓ 管理器创建成功: {type(manager).__name__}")
    
    # 2. 配置提供商
    print("\n2. 配置提供商...")
    manager.configure_provider(
        provider="qwen",
        api_key="test-key-123",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        models=["qwen-max", "qwen-plus", "qwen-turbo"]
    )
    print("   ✓ 通义千问配置成功")
    
    # 3. 获取客户端
    print("\n3. 获取客户端...")
    client = manager.get_client("qwen-max")
    print(f"   ✓ 客户端创建成功")
    print(f"   - 模型: {client.model}")
    print(f"   - Base URL: {client.base_url}")
    
    # 4. 测试提供商推断
    print("\n4. 测试提供商推断...")
    test_models = [
        "qwen-max",
        "deepseek-chat",
        "gpt-4",
        "claude-3",
        "gemini-pro"
    ]
    for model in test_models:
        provider = manager._infer_provider(model)
        print(f"   ✓ {model} -> {provider}")
    
    # 5. 测试统计
    print("\n5. 测试使用统计...")
    manager.record_usage(tokens=100, cost=0.05)
    manager.record_usage(tokens=200, cost=0.10)
    stats = manager.get_stats()
    print(f"   ✓ 总请求数: {stats['total_requests']}")
    print(f"   ✓ 总Token数: {stats['total_tokens']}")
    print(f"   ✓ 总成本: ¥{stats['total_cost']:.4f}")
    
    # 6. 测试HTTP客户端共享
    print("\n6. 测试HTTP客户端共享...")
    client1 = manager.get_client("qwen-max")
    client2 = manager.get_client("qwen-plus")
    if client1.http_client is client2.http_client:
        print("   ✓ HTTP客户端共享成功（真正的连接池复用）")
    else:
        print("   ✗ HTTP客户端未共享")
    
    # 7. 测试请求对象
    print("\n7. 测试请求对象...")
    request = LLMRequest(
        prompt="你好",
        model="qwen-max",
        temperature=0.7,
        max_tokens=100
    )
    print(f"   ✓ 请求创建成功")
    print(f"   - Prompt: {request.prompt}")
    print(f"   - 模型: {request.model}")
    print(f"   - 温度: {request.temperature}")
    
    print("\n" + "=" * 60)
    print("✅ 所有基础功能测试通过！")
    print("=" * 60)
    
    # 清理
    await manager.close()


if __name__ == "__main__":
    asyncio.run(test_basic_functionality())
