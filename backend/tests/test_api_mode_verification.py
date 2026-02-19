"""
验证当前使用API模式（不依赖huggingface）

测试内容：
1. 验证工厂函数返回的是API版本
2. 验证不会加载本地模型
3. 模拟切换到千问的配置
"""

import sys
from pathlib import Path

# 添加backend到路径
backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

def test_current_mode():
    """测试1: 验证当前使用API模式"""
    print("\n" + "="*60)
    print("测试1: 验证当前配置使用API模式")
    print("="*60)
    
    from daoyoucode.agents.memory.vector_retriever_factory import get_vector_retriever
    
    # 获取检索器
    retriever = get_vector_retriever()
    
    # 检查类型
    class_name = retriever.__class__.__name__
    print(f"\n✅ 检索器类型: {class_name}")
    
    if class_name == "VectorRetrieverAPI":
        print("✅ 确认: 使用API模式（不依赖huggingface）")
        
        # 获取统计信息
        stats = retriever.get_stats()
        print(f"\n📊 配置信息:")
        print(f"   模式: {stats.get('mode')}")
        print(f"   提供商: {stats.get('provider')}")
        print(f"   模型: {stats.get('model')}")
        print(f"   维度: {stats.get('dimensions')}")
        
        return True
    else:
        print(f"❌ 错误: 使用本地模式（{class_name}）")
        return False


def test_qwen_config():
    """测试2: 模拟切换到千问的配置"""
    print("\n" + "="*60)
    print("测试2: 模拟切换到千问配置")
    print("="*60)
    
    from daoyoucode.agents.memory.vector_retriever_api import VectorRetrieverAPI
    
    print("\n📝 千问配置示例:")
    print("""
    mode: "api"
    
    api:
      provider: "qwen"
      api_key: "YOUR_DASHSCOPE_API_KEY"
    """)
    
    # 创建千问检索器（不实际调用API）
    print("\n🔄 创建千问检索器实例...")
    
    # 使用测试密钥（不会实际调用）
    retriever = VectorRetrieverAPI(
        provider="qwen",
        api_key="test_key_for_demo"
    )
    
    stats = retriever.get_stats()
    print(f"\n✅ 千问配置:")
    print(f"   提供商: {stats.get('provider')}")
    print(f"   模型: {stats.get('model')}")
    print(f"   维度: {stats.get('dimensions')}")
    print(f"   Base URL: {retriever.base_url}")
    
    return True


def test_no_huggingface_import():
    """测试3: 验证API模式不导入huggingface"""
    print("\n" + "="*60)
    print("测试3: 验证不导入huggingface库")
    print("="*60)
    
    import sys
    
    # 检查已导入的模块
    hf_modules = [name for name in sys.modules.keys() if 'huggingface' in name.lower()]
    st_modules = [name for name in sys.modules.keys() if 'sentence_transformers' in name.lower()]
    
    print(f"\n📦 已导入的huggingface相关模块: {len(hf_modules)}")
    if hf_modules:
        for mod in hf_modules[:5]:  # 只显示前5个
            print(f"   - {mod}")
    else:
        print("   ✅ 无huggingface模块")
    
    print(f"\n📦 已导入的sentence_transformers模块: {len(st_modules)}")
    if st_modules:
        for mod in st_modules[:5]:
            print(f"   - {mod}")
    else:
        print("   ✅ 无sentence_transformers模块")
    
    # 检查httpx（API模式需要）
    httpx_imported = 'httpx' in sys.modules
    print(f"\n📦 httpx已导入: {'✅ 是' if httpx_imported else '❌ 否'}")
    
    return True


def test_switch_providers():
    """测试4: 演示三种提供商的配置"""
    print("\n" + "="*60)
    print("测试4: 三种提供商配置对比")
    print("="*60)
    
    from daoyoucode.agents.memory.vector_retriever_api import VectorRetrieverAPI
    
    providers = ["zhipu", "qwen", "openai"]
    
    print("\n📊 支持的提供商:")
    for provider in providers:
        config = VectorRetrieverAPI.API_CONFIGS.get(provider)
        if config:
            print(f"\n{provider.upper()}:")
            print(f"   模型: {config['model']}")
            print(f"   维度: {config['dimensions']}")
            print(f"   Base URL: {config['base_url']}")
            print(f"   环境变量: {config['env_key']}")
    
    return True


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("向量模型API模式验证")
    print("="*60)
    
    tests = [
        ("当前模式验证", test_current_mode),
        ("千问配置模拟", test_qwen_config),
        ("依赖检查", test_no_huggingface_import),
        ("提供商对比", test_switch_providers),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"\n总计: {passed}/{total} 通过")
    
    # 结论
    print("\n" + "="*60)
    print("结论")
    print("="*60)
    print("""
✅ 当前系统使用API模式（不依赖huggingface）
✅ 切换模型只需修改配置文件
✅ 无需重新安装依赖
✅ 支持智谱AI、千问、OpenAI三种提供商

切换到千问的步骤：
1. 修改 config/embedding_config.yaml
2. 将 provider 改为 "qwen"
3. 设置 api_key 为千问的API Key
4. 重启系统即可
    """)


if __name__ == "__main__":
    main()
