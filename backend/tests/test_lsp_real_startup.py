"""
测试LSP真正启动

验证：
1. LSP服务器真正启动
2. LSP客户端连接成功
3. LSP信息真正获取
"""

import asyncio
import sys
from pathlib import Path

# 添加backend到路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))


async def test_lsp_startup():
    """测试LSP启动"""
    print("=" * 60)
    print("测试LSP真正启动")
    print("=" * 60)
    
    from daoyoucode.agents.tools.lsp_tools import get_lsp_manager, BUILTIN_LSP_SERVERS
    
    manager = get_lsp_manager()
    print(f"✓ LSP管理器已创建")
    
    # 检查pyright是否已安装
    pyright_config = BUILTIN_LSP_SERVERS.get("pyright")
    if not pyright_config:
        print("❌ pyright配置不存在")
        return False
    
    is_installed = manager.is_server_installed(pyright_config)
    print(f"pyright安装状态: {'✅ 已安装' if is_installed else '❌ 未安装'}")
    
    if not is_installed:
        print("\n请先安装pyright:")
        print("  pip install pyright")
        return False
    
    # 启动LSP服务器
    print("\n启动LSP服务器...")
    try:
        client = await manager.get_client(str(backend_dir), pyright_config)
        print(f"✅ LSP客户端已启动")
        print(f"  进程ID: {client.process.pid if client.process else 'N/A'}")
        print(f"  存活状态: {client.is_alive()}")
        
        # 测试获取符号
        print("\n测试获取符号...")
        test_file = backend_dir / "daoyoucode" / "agents" / "executor.py"
        
        if test_file.exists():
            symbols = await client.document_symbols(str(test_file))
            print(f"✅ 获取符号成功")
            print(f"  符号数量: {len(symbols) if symbols else 0}")
            
            if symbols:
                print(f"\n前3个符号:")
                for i, sym in enumerate(symbols[:3], 1):
                    name = sym.get('name', 'N/A')
                    kind = sym.get('kind', 0)
                    print(f"  {i}. {name} (kind: {kind})")
        else:
            print(f"⚠️  测试文件不存在: {test_file}")
        
        # 检查管理器状态
        print(f"\n管理器状态:")
        print(f"  活跃客户端数: {len(manager.clients)}")
        for key, managed in manager.clients.items():
            print(f"  - {key}")
            print(f"    引用计数: {managed['ref_count']}")
            print(f"    存活: {managed['client'].is_alive()}")
        
        # 释放客户端
        manager.release_client(str(backend_dir), pyright_config.id)
        print(f"\n✅ 客户端已释放")
        
        return True
    
    except Exception as e:
        print(f"❌ LSP启动失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_lsp_enhanced_search():
    """测试LSP增强的搜索"""
    print("\n" + "=" * 60)
    print("测试LSP增强搜索")
    print("=" * 60)
    
    from daoyoucode.agents.memory.codebase_index_lsp_enhanced import search_codebase_with_lsp
    
    print("执行搜索: 'execute_skill'")
    try:
        results = await search_codebase_with_lsp(
            backend_dir,
            "execute_skill",
            top_k=3,
            enable_lsp=True
        )
        
        print(f"✅ 搜索成功")
        print(f"  结果数量: {len(results)}")
        
        # 检查LSP信息
        has_lsp_count = sum(1 for r in results if r.get('has_lsp_info'))
        print(f"  有LSP信息: {has_lsp_count}/{len(results)}")
        
        if results:
            print(f"\n第1个结果:")
            r = results[0]
            print(f"  文件: {r.get('path', 'N/A')}")
            print(f"  行: {r.get('start', 0)}-{r.get('end', 0)}")
            print(f"  LSP信息: {'✅ 有' if r.get('has_lsp_info') else '❌ 无'}")
            
            if r.get('has_lsp_info'):
                print(f"  符号数量: {r.get('symbol_count', 0)}")
                print(f"  类型注解: {'✅' if r.get('has_type_annotations') else '❌'}")
                print(f"  引用计数: {r.get('reference_count', 0)}")
                
                symbols = r.get('lsp_symbols', [])
                if symbols:
                    print(f"  符号:")
                    for sym in symbols[:3]:
                        name = sym.get('name', 'N/A')
                        detail = sym.get('detail', '')
                        print(f"    - {name}: {detail}")
        
        return has_lsp_count > 0
    
    except Exception as e:
        print(f"❌ 搜索失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("LSP真正启动测试")
    print("=" * 60)
    
    results = []
    
    # 测试1: LSP启动
    try:
        result = await test_lsp_startup()
        results.append(("LSP启动", result))
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        results.append(("LSP启动", False))
    
    # 测试2: LSP增强搜索
    try:
        result = await test_lsp_enhanced_search()
        results.append(("LSP增强搜索", result))
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        results.append(("LSP增强搜索", False))
    
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
        print("\n🎉 所有测试通过！LSP真正启动成功！")
        print("\n现在的结构化信息来自:")
        print("  1. Tree-sitter: 快速语法解析（基础层）")
        print("  2. LSP: 深度语义分析（增强层）")
        print("  3. 两者互补，效果最佳！")
    else:
        print("\n⚠️  部分测试失败")
        if not results[0][1]:
            print("  请先安装LSP服务器: pip install pyright")


if __name__ == "__main__":
    asyncio.run(main())
