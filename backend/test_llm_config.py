"""
测试LLM配置加载
"""

import sys
from pathlib import Path

# 添加backend到路径
sys.path.insert(0, str(Path(__file__).parent))

from daoyoucode.agents.llm.client_manager import get_client_manager
from daoyoucode.agents.llm.config_loader import auto_configure

def test_config():
    print("="*60)
    print("测试LLM配置加载")
    print("="*60)
    
    # 获取客户端管理器
    client_manager = get_client_manager()
    
    # 自动配置
    print("\n1. 自动配置...")
    auto_configure(client_manager)
    
    # 检查配置
    print("\n2. 检查配置...")
    if not client_manager.provider_configs:
        print("❌ 未找到任何提供商配置")
        return False
    
    print(f"✓ 找到 {len(client_manager.provider_configs)} 个提供商:")
    for provider, config in client_manager.provider_configs.items():
        print(f"  • {provider}")
        if isinstance(config, dict):
            print(f"    - API Key: {config.get('api_key', '')[:10]}..." if config.get('api_key') else "    - API Key: 未配置")
            print(f"    - Base URL: {config.get('base_url', 'N/A')}")
            print(f"    - 模型数量: {len(config.get('models', []))}")
        else:
            print(f"    - API Key: {config.api_key[:10]}..." if config.api_key else "    - API Key: 未配置")
            print(f"    - Base URL: {config.base_url}")
            print(f"    - 模型数量: {len(config.models)}")
    
    # 测试获取客户端
    print("\n3. 测试获取客户端...")
    try:
        client = client_manager.get_client(model="qwen-max")
        print(f"✓ 成功获取qwen-max客户端")
        print(f"  • 提供商: {client_manager._get_provider_for_model('qwen-max')}")
        return True
    except Exception as e:
        print(f"❌ 获取客户端失败: {e}")
        return False

if __name__ == "__main__":
    success = test_config()
    print("\n" + "="*60)
    if success:
        print("✅ 配置测试通过")
    else:
        print("❌ 配置测试失败")
    print("="*60)
