"""
测试实际的API Key轮询
"""

import sys
from pathlib import Path

backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from daoyoucode.agents.llm import get_client_manager
from daoyoucode.agents.llm.config_loader import auto_configure

# 配置客户端管理器
cm = get_client_manager()
auto_configure(cm)

print("=" * 60)
print("实际API Key轮询测试")
print("=" * 60)

# 检查配置
qwen_config = cm.provider_configs.get('qwen', {})
api_keys = qwen_config.get('api_keys', [])

print(f"\n配置的API Key数量: {len(api_keys)}")
for i, key in enumerate(api_keys, 1):
    print(f"  Key {i}: {key[:15]}...{key[-4:]}")

print(f"\n开始轮询测试（6次请求）:")
print("-" * 60)

for i in range(6):
    client = cm.get_client('qwen-plus')
    print(f"请求 {i+1}: 使用 {client.api_key[:15]}...{client.api_key[-4:]}")

print("-" * 60)
print("\n✅ 轮询测试完成！")
print(f"预期行为: {len(api_keys)}个key轮流使用")
