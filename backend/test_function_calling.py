"""测试LLM是否支持function calling"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from daoyoucode.agents.llm.client_manager import get_client_manager
from daoyoucode.agents.llm.config_loader import auto_configure

async def test_function_calling():
    print("="*60)
    print("测试LLM Function Calling支持")
    print("="*60)
    
    # 1. 配置LLM
    print("\n1. 配置LLM...")
    client_manager = get_client_manager()
    auto_configure(client_manager)
    
    if not client_manager.provider_configs:
        print("❌ 未配置LLM提供商")
        return False
    
    print(f"✓ 已配置提供商: {list(client_manager.provider_configs.keys())}")
    
    # 2. 获取客户端
    print("\n2. 获取qwen-max客户端...")
    try:
        client = client_manager.get_client(model="qwen-max")
        print(f"✓ 客户端获取成功")
    except Exception as e:
        print(f"❌ 获取客户端失败: {e}")
        return False
    
    # 3. 测试简单调用（不带工具）
    print("\n3. 测试简单调用（不带工具）...")
    try:
        response = await client.chat(
            messages=[{"role": "user", "content": "你好"}],
            model="qwen-max"
        )
        print(f"✓ 简单调用成功")
        print(f"  响应: {response.get('content', '')[:50]}...")
    except Exception as e:
        print(f"❌ 简单调用失败: {e}")
        return False
    
    # 4. 测试function calling
    print("\n4. 测试function calling...")
    
    # 定义一个简单的工具
    tools = [{
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取天气信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称"
                    }
                },
                "required": ["city"]
            }
        }
    }]
    
    try:
        response = await client.chat(
            messages=[{"role": "user", "content": "北京的天气怎么样？"}],
            model="qwen-max",
            tools=tools
        )
        
        print(f"✓ Function calling调用成功")
        
        # 检查是否有tool_calls
        if 'tool_calls' in response or 'function_call' in response:
            print(f"✓ LLM支持function calling")
            print(f"  响应类型: {type(response)}")
            print(f"  响应键: {list(response.keys())}")
            if 'tool_calls' in response:
                print(f"  tool_calls: {response['tool_calls']}")
            if 'function_call' in response:
                print(f"  function_call: {response['function_call']}")
            return True
        else:
            print(f"⚠ LLM可能不支持function calling")
            print(f"  响应: {response}")
            return False
            
    except Exception as e:
        print(f"❌ Function calling调用失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_function_calling())
    print("\n" + "="*60)
    if success:
        print("✅ LLM支持function calling")
    else:
        print("❌ LLM可能不支持function calling或配置有问题")
    print("="*60)
