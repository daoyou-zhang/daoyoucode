"""
测试LLM连接

诊断500错误的可能原因
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加backend到路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))


async def test_simple_request():
    """测试简单请求"""
    
    print("=" * 60)
    print("测试1: 简单LLM请求")
    print("=" * 60)
    
    try:
        from daoyoucode.agents.llm import get_client_manager
        from daoyoucode.agents.llm.base import LLMRequest
        
        client_manager = get_client_manager()
        
        # 测试qwen-plus
        print("\n测试模型: qwen-plus")
        client = client_manager.get_client(model="qwen-plus")
        
        request = LLMRequest(
            prompt="你好，请回复'测试成功'",
            model="qwen-plus",
            temperature=0.7,
            max_tokens=100
        )
        
        print("发送请求...")
        response = await client.chat(request)
        
        print(f"✅ 响应成功")
        print(f"内容: {response.content}")
        print(f"Token使用: {response.tokens_used}")
        print(f"延迟: {response.latency:.2f}秒")
        
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


async def test_function_calling():
    """测试Function Calling"""
    
    print("\n" + "=" * 60)
    print("测试2: Function Calling")
    print("=" * 60)
    
    try:
        from daoyoucode.agents.llm import get_client_manager
        from daoyoucode.agents.llm.base import LLMRequest
        
        client_manager = get_client_manager()
        client = client_manager.get_client(model="qwen-plus")
        
        # 构建带function的请求
        request = LLMRequest(
            prompt="",
            model="qwen-plus",
            temperature=0.7,
            max_tokens=500
        )
        
        # 添加消息
        request.messages = [
            {"role": "user", "content": "请读取当前目录的README.md文件"}
        ]
        
        # 添加简单的function
        request.functions = [
            {
                "name": "read_file",
                "description": "读取文件内容",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "文件路径"
                        }
                    },
                    "required": ["file_path"]
                }
            }
        ]
        
        print("发送Function Calling请求...")
        response = await client.chat(request)
        
        print(f"✅ 响应成功")
        print(f"内容: {response.content}")
        
        if response.metadata.get('function_call'):
            print(f"Function Call: {response.metadata['function_call']}")
        
        print(f"Token使用: {response.tokens_used}")
        
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


async def test_api_key():
    """测试API Key配置"""
    
    print("\n" + "=" * 60)
    print("测试3: API Key配置")
    print("=" * 60)
    
    api_key = os.getenv('DASHSCOPE_API_KEY')
    
    if not api_key:
        print("❌ 未设置 DASHSCOPE_API_KEY 环境变量")
        return False
    
    print(f"✅ API Key已设置: {api_key[:10]}...{api_key[-4:]}")
    
    # 检查配置文件
    config_file = backend_dir / 'config' / 'llm_config.yaml'
    if config_file.exists():
        print(f"✅ 配置文件存在: {config_file}")
        
        import yaml
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if 'providers' in config and 'qwen' in config['providers']:
            print(f"✅ qwen提供商已配置")
            print(f"   模型: {config['providers']['qwen'].get('models', [])}")
        else:
            print("⚠️ qwen提供商未配置")
    else:
        print(f"⚠️ 配置文件不存在: {config_file}")
    
    return True


async def diagnose_500_error():
    """诊断500错误"""
    
    print("\n" + "=" * 60)
    print("诊断500错误")
    print("=" * 60)
    
    print("\n可能的原因：")
    print("1. API配额不足（检查阿里云账户余额）")
    print("2. 请求格式错误（特别是Function Calling格式）")
    print("3. 模型不支持Function Calling（某些模型不支持）")
    print("4. 请求过大（messages或functions太多）")
    print("5. 服务端临时故障（重试可能解决）")
    
    print("\n建议的解决方案：")
    print("1. 检查阿里云账户余额和配额")
    print("2. 尝试不使用Function Calling的简单请求")
    print("3. 减少messages历史长度")
    print("4. 添加重试机制")
    print("5. 检查模型是否支持Function Calling")


async def main():
    """运行所有测试"""
    
    print("\n" + "🧪 LLM连接诊断")
    print("=" * 60)
    
    # 测试API Key
    api_key_ok = await test_api_key()
    
    if not api_key_ok:
        print("\n❌ API Key配置有问题，请先设置环境变量")
        return
    
    # 测试简单请求
    simple_ok = await test_simple_request()
    
    if not simple_ok:
        print("\n❌ 简单请求失败")
        await diagnose_500_error()
        return
    
    # 测试Function Calling
    function_ok = await test_function_calling()
    
    if not function_ok:
        print("\n❌ Function Calling失败")
        await diagnose_500_error()
        return
    
    print("\n" + "=" * 60)
    print("✅ 所有测试通过！")
    print("=" * 60)


if __name__ == '__main__':
    asyncio.run(main())
