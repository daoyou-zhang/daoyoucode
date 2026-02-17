"""
测试API Key轮询功能

验证：
1. 单个API Key正常工作
2. 多个API Key轮询使用
3. 轮询顺序正确
"""

import sys
from pathlib import Path

# 添加backend到路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))


def test_single_key():
    """测试单个API Key"""
    
    print("=" * 60)
    print("测试1: 单个API Key")
    print("=" * 60)
    
    from daoyoucode.agents.llm.client_manager import LLMClientManager
    
    # 创建新实例
    manager = LLMClientManager()
    
    # 配置单个key
    manager.configure_provider(
        provider='test_provider',
        api_key='sk-key1',
        base_url='https://api.test.com/v1',
        models=['test-model']
    )
    
    # 获取多次客户端，应该都使用同一个key
    for i in range(5):
        client = manager.get_client('test-model', 'test_provider')
        print(f"请求 {i+1}: API Key = {client.api_key}")
        assert client.api_key == 'sk-key1', "单个key应该始终返回同一个"
    
    print("✅ 单个API Key测试通过")


def test_multiple_keys_rotation():
    """测试多个API Key轮询"""
    
    print("\n" + "=" * 60)
    print("测试2: 多个API Key轮询")
    print("=" * 60)
    
    from daoyoucode.agents.llm.client_manager import LLMClientManager
    
    # 创建新实例（清除之前的配置）
    LLMClientManager._instance = None
    manager = LLMClientManager()
    
    # 配置多个key
    keys = ['sk-key1', 'sk-key2', 'sk-key3']
    manager.configure_provider(
        provider='test_provider',
        api_keys=keys,
        base_url='https://api.test.com/v1',
        models=['test-model']
    )
    
    # 获取多次客户端，应该轮询使用
    used_keys = []
    for i in range(9):  # 测试3轮完整轮询
        client = manager.get_client('test-model', 'test_provider')
        used_keys.append(client.api_key)
        print(f"请求 {i+1}: API Key = {client.api_key}")
    
    # 验证轮询顺序
    expected = keys * 3  # 3轮完整轮询
    assert used_keys == expected, f"轮询顺序不正确: {used_keys} != {expected}"
    
    print("✅ 多个API Key轮询测试通过")


def test_two_keys_rotation():
    """测试2个API Key轮询"""
    
    print("\n" + "=" * 60)
    print("测试3: 2个API Key轮询")
    print("=" * 60)
    
    from daoyoucode.agents.llm.client_manager import LLMClientManager
    
    # 创建新实例
    LLMClientManager._instance = None
    manager = LLMClientManager()
    
    # 配置2个key
    keys = ['sk-key-a', 'sk-key-b']
    manager.configure_provider(
        provider='test_provider',
        api_keys=keys,
        base_url='https://api.test.com/v1',
        models=['test-model']
    )
    
    # 获取多次客户端
    used_keys = []
    for i in range(6):
        client = manager.get_client('test-model', 'test_provider')
        used_keys.append(client.api_key)
        print(f"请求 {i+1}: API Key = {client.api_key}")
    
    # 验证轮询：应该是 a, b, a, b, a, b
    expected = ['sk-key-a', 'sk-key-b'] * 3
    assert used_keys == expected, f"轮询顺序不正确: {used_keys} != {expected}"
    
    print("✅ 2个API Key轮询测试通过")


def test_config_loading():
    """测试从配置文件加载"""
    
    print("\n" + "=" * 60)
    print("测试4: 从配置文件加载")
    print("=" * 60)
    
    from daoyoucode.agents.llm.config_loader import load_llm_config
    
    config = load_llm_config()
    
    if not config:
        print("⚠️ 配置文件未找到或为空")
        return
    
    print(f"✅ 配置文件加载成功")
    
    providers = config.get('providers', {})
    for provider_name, provider_config in providers.items():
        if not provider_config.get('enabled'):
            continue
        
        api_key = provider_config.get('api_key')
        api_keys = provider_config.get('api_keys')
        
        # 处理api_key可能是列表的情况
        if api_key and isinstance(api_key, list):
            api_keys = api_key
            api_key = None
        
        if api_keys:
            print(f"提供商 {provider_name}: {len(api_keys)} 个API Key")
            for i, key in enumerate(api_keys, 1):
                print(f"  Key {i}: {key[:10]}...{key[-4:]}")
        elif api_key:
            print(f"提供商 {provider_name}: 1 个API Key")
            print(f"  Key: {api_key[:10]}...{api_key[-4:]}")


def main():
    """运行所有测试"""
    
    print("\n" + "🧪 API Key轮询功能测试")
    print("=" * 60)
    
    try:
        test_single_key()
        test_multiple_keys_rotation()
        test_two_keys_rotation()
        test_config_loading()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        
        print("\n📝 使用说明：")
        print("1. 在 config/llm_config.yaml 中配置多个API Key：")
        print("   api_keys:")
        print("     - 'sk-key1'")
        print("     - 'sk-key2'")
        print("     - 'sk-key3'")
        print("")
        print("2. 系统会自动轮询使用这些key")
        print("3. 1个key就用1个，多个就轮询")
        print("4. 可以有效分散API配额压力")
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
