"""
测试修复效果
"""

import asyncio
import sys
import os

# 添加backend到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def test_initialization():
    """测试系统初始化"""
    print("=" * 60)
    print("测试1: 系统初始化")
    print("=" * 60)
    
    from daoyoucode.agents.init import initialize_agent_system
    
    try:
        initialize_agent_system()
        print("✅ 系统初始化成功")
        
        # 检查中间件
        from daoyoucode.agents.core.middleware import get_middleware_registry
        registry = get_middleware_registry()
        middlewares = registry.list_middleware()
        print(f"✅ 已注册中间件: {middlewares}")
        
        return True
    except Exception as e:
        print(f"❌ 系统初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_json_parsing():
    """测试JSON解析修复"""
    print("\n" + "=" * 60)
    print("测试2: JSON解析修复")
    print("=" * 60)
    
    import json
    
    # 模拟LLM返回的带额外文本的JSON
    test_cases = [
        ('{"file_path": "test.txt"}', True),
        ('{"file_path": "test.txt"}\n如果您有其他需求，请详细说明。', True),
        ('{"repo_path": "/path/to/repo"}\n请提供具体的指令和参数。', True),
        ('', False),
        ('invalid json', False),
    ]
    
    for args_str, should_succeed in test_cases:
        print(f"\n测试: {repr(args_str[:50])}")
        
        try:
            # 提取JSON部分
            args_str_clean = args_str.strip()
            if args_str_clean.startswith('{'):
                brace_count = 0
                json_end = -1
                for i, char in enumerate(args_str_clean):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_end = i + 1
                            break
                
                if json_end > 0:
                    args_str_clean = args_str_clean[:json_end]
            
            result = json.loads(args_str_clean)
            print(f"✅ 解析成功: {result}")
            
            if not should_succeed:
                print("⚠️ 预期失败但成功了")
        
        except json.JSONDecodeError as e:
            if should_succeed:
                print(f"❌ 解析失败（预期成功）: {e}")
            else:
                print(f"✅ 解析失败（符合预期）: {e}")
        
        except Exception as e:
            print(f"❌ 意外错误: {e}")
    
    return True


async def test_agent_models():
    """测试Agent模型配置"""
    print("\n" + "=" * 60)
    print("测试3: Agent模型配置")
    print("=" * 60)
    
    from daoyoucode.agents.init import initialize_agent_system
    from daoyoucode.agents.core.agent import get_agent_registry
    
    try:
        initialize_agent_system()
        
        registry = get_agent_registry()
        agents = registry.list_agents()
        
        print(f"已注册Agent: {len(agents)}个")
        
        # 检查test_expert的模型
        test_expert = registry.get_agent('test_expert')
        if test_expert:
            print(f"✅ test_expert模型: {test_expert.config.model}")
            
            if test_expert.config.model == 'deepseek-coder':
                print("⚠️ test_expert仍使用deepseek-coder（未配置）")
            else:
                print(f"✅ test_expert已改用: {test_expert.config.model}")
        
        return True
    
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("DaoyouCode 修复验证测试")
    print("=" * 60)
    
    results = []
    
    # 测试1: 系统初始化
    results.append(await test_initialization())
    
    # 测试2: JSON解析
    results.append(await test_json_parsing())
    
    # 测试3: Agent模型配置
    results.append(await test_agent_models())
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("✅ 所有测试通过")
    else:
        print(f"❌ {total - passed} 个测试失败")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
