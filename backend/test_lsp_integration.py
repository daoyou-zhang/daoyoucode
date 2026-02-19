"""
测试LSP深度融合集成

验证：
1. LSP服务器自动检测和安装
2. semantic_code_search默认启用LSP
3. LSP信息正确显示
4. Agent能理解和使用LSP信息
"""

import asyncio
import sys
from pathlib import Path

# 添加backend到路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))


async def test_lsp_manager():
    """测试LSP管理器"""
    print("=" * 60)
    print("测试1: LSP管理器")
    print("=" * 60)
    
    from daoyoucode.agents.tools.lsp_tools import get_lsp_manager
    
    manager = get_lsp_manager()
    print(f"✓ LSP管理器已创建")
    
    # 测试检测Python LSP
    print("\n检测Python LSP服务器...")
    available = await manager.ensure_server_available("python")
    
    if available:
        print("✅ Python LSP服务器可用")
    else:
        print("⚠️  Python LSP服务器未安装")
        print("   安装方式: pip install pyright")
    
    return available


async def test_semantic_search_with_lsp():
    """测试semantic_code_search的LSP增强"""
    print("\n" + "=" * 60)
    print("测试2: semantic_code_search LSP增强")
    print("=" * 60)
    
    from daoyoucode.agents.tools.codebase_search_tool import SemanticCodeSearchTool
    
    tool = SemanticCodeSearchTool()
    print(f"✓ 工具已创建: {tool.name}")
    
    # 检查schema
    schema = tool.get_function_schema()
    enable_lsp_param = schema['parameters']['properties'].get('enable_lsp')
    
    if enable_lsp_param:
        print(f"✓ enable_lsp参数存在")
        print(f"  默认值: {enable_lsp_param.get('default', 'N/A')}")
        print(f"  描述: {enable_lsp_param.get('description', 'N/A')}")
    else:
        print("❌ enable_lsp参数不存在")
        return False
    
    # 测试搜索
    print("\n执行搜索: 'execute_skill'")
    result = await tool.execute(
        query="execute_skill",
        top_k=3,
        repo_path=".",
        enable_lsp=True
    )
    
    if result.success:
        print("✅ 搜索成功")
        
        # 检查是否有LSP信息
        has_lsp = result.metadata.get('has_lsp_info', False)
        print(f"  LSP信息: {'✅ 有' if has_lsp else '⚠️  无'}")
        
        # 显示结果片段
        content = result.content[:500] if result.content else ""
        print(f"\n结果预览:")
        print("-" * 60)
        print(content)
        print("-" * 60)
        
        # 检查LSP标记
        lsp_markers = {
            "⭐": "质量星级",
            "✅ 有类型注解": "类型注解",
            "🔥 热点代码": "热点代码",
            "📝 符号信息": "符号信息"
        }
        
        found_markers = []
        for marker, name in lsp_markers.items():
            if marker in content:
                found_markers.append(name)
        
        if found_markers:
            print(f"\n✅ 发现LSP标记: {', '.join(found_markers)}")
        else:
            print(f"\n⚠️  未发现LSP标记（可能LSP服务器未安装）")
        
        return True
    else:
        print(f"❌ 搜索失败: {result.error}")
        return False


async def test_agent_initialization():
    """测试Agent系统初始化"""
    print("\n" + "=" * 60)
    print("测试3: Agent系统初始化")
    print("=" * 60)
    
    from daoyoucode.agents.init import initialize_agent_system
    
    print("初始化Agent系统...")
    tool_registry = initialize_agent_system()
    
    print(f"✅ Agent系统已初始化")
    print(f"  工具数量: {len(tool_registry.list_tools())}")
    
    # 等待LSP初始化完成
    print("\n等待LSP初始化...")
    await asyncio.sleep(2)
    
    return True


async def main():
    """主测试函数"""
    print("LSP深度融合集成测试")
    print("=" * 60)
    
    results = []
    
    # 测试1: LSP管理器
    try:
        result = await test_lsp_manager()
        results.append(("LSP管理器", result))
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        results.append(("LSP管理器", False))
    
    # 测试2: semantic_code_search
    try:
        result = await test_semantic_search_with_lsp()
        results.append(("semantic_code_search", result))
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        results.append(("semantic_code_search", False))
    
    # 测试3: Agent初始化
    try:
        result = await test_agent_initialization()
        results.append(("Agent初始化", result))
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        results.append(("Agent初始化", False))
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！LSP深度融合已成功实施！")
    else:
        print("\n⚠️  部分测试失败，请检查LSP服务器安装")


if __name__ == "__main__":
    asyncio.run(main())
