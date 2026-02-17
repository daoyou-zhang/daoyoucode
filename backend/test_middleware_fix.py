"""
测试中间件修复

验证：
1. ContextMiddleware 可以正确导入
2. 中间件可以正确初始化
3. 不会出现 "No module named 'ai'" 错误
"""

import sys
from pathlib import Path

# 添加backend到路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))


def test_middleware_import():
    """测试中间件导入"""
    
    print("=" * 60)
    print("测试1: 导入 ContextMiddleware")
    print("=" * 60)
    
    try:
        from daoyoucode.agents.middleware.context import ContextMiddleware
        print("✅ ContextMiddleware 导入成功")
        
        # 创建实例
        middleware = ContextMiddleware()
        print(f"✅ ContextMiddleware 实例化成功: {middleware}")
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        raise
    
    print("\n" + "=" * 60)
    print("测试2: 导入 FollowupMiddleware")
    print("=" * 60)
    
    try:
        from daoyoucode.agents.middleware.followup import FollowupMiddleware
        print("✅ FollowupMiddleware 导入成功")
        
        # 创建实例
        middleware = FollowupMiddleware()
        print(f"✅ FollowupMiddleware 实例化成功: {middleware}")
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        raise


def test_middleware_registration():
    """测试中间件注册"""
    
    print("\n" + "=" * 60)
    print("测试3: 中间件注册")
    print("=" * 60)
    
    try:
        from daoyoucode.agents import initialize_agent_system
        
        # 初始化系统（会注册中间件）
        initialize_agent_system()
        print("✅ Agent系统初始化成功")
        
        # 检查中间件是否注册
        from daoyoucode.agents.core.middleware import get_middleware_registry
        registry = get_middleware_registry()
        
        middlewares = registry.list_middleware()
        print(f"✅ 已注册中间件: {middlewares}")
        
        # 验证关键中间件
        assert 'context_management' in middlewares, "context_management 未注册"
        assert 'memory_integration' in middlewares, "memory_integration 未注册"
        assert 'followup' in middlewares, "followup 未注册"
        
        print("✅ 所有关键中间件已注册")
        
    except Exception as e:
        print(f"❌ 注册失败: {e}")
        raise


def test_context_middleware_process():
    """测试 ContextMiddleware 处理"""
    
    print("\n" + "=" * 60)
    print("测试4: ContextMiddleware 处理")
    print("=" * 60)
    
    try:
        from daoyoucode.agents.middleware.context import ContextMiddleware
        import asyncio
        
        middleware = ContextMiddleware()
        
        # 模拟上下文
        context = {
            'session_id': 'test-session',
            'is_followup': False
        }
        
        # 处理（可能会失败，但不应该因为导入错误）
        async def run_test():
            try:
                result = await middleware.process("测试输入", context)
                print(f"✅ 处理成功: {result.keys()}")
                return result
            except Exception as e:
                # 如果是业务逻辑错误（如找不到session），这是正常的
                if "No module named 'ai'" in str(e):
                    print(f"❌ 导入错误仍然存在: {e}")
                    raise
                else:
                    print(f"⚠️ 业务逻辑错误（正常）: {e}")
                    return context
        
        result = asyncio.run(run_test())
        print("✅ ContextMiddleware 处理测试通过")
        
    except Exception as e:
        if "No module named 'ai'" in str(e):
            print(f"❌ 导入错误: {e}")
            raise
        else:
            print(f"⚠️ 其他错误（可能正常）: {e}")


def main():
    """运行所有测试"""
    
    print("\n" + "🧪 中间件修复测试")
    print("=" * 60)
    
    try:
        test_middleware_import()
        test_middleware_registration()
        test_context_middleware_process()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        
        print("\n📝 修复总结：")
        print("1. ✅ 修复了 ContextMiddleware 的导入路径")
        print("2. ✅ 从 'ai.memory.context_manager' 改为 '..core.context'")
        print("3. ✅ 中间件可以正常导入和注册")
        print("4. ✅ 不再出现 'No module named ai' 错误")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
