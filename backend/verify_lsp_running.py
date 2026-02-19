"""
验证LSP是否真正启动

简单直接的验证方法
"""

import asyncio
import sys
from pathlib import Path

backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))


async def verify_lsp():
    """验证LSP启动"""
    print("=" * 60)
    print("验证LSP是否真正启动")
    print("=" * 60)
    
    from daoyoucode.agents.tools.lsp_tools import get_lsp_manager, BUILTIN_LSP_SERVERS
    
    # 1. 检查pyright是否安装
    print("\n[1] 检查pyright安装状态...")
    manager = get_lsp_manager()
    pyright_config = BUILTIN_LSP_SERVERS.get("pyright")
    
    if not pyright_config:
        print("❌ pyright配置不存在")
        return False
    
    is_installed = manager.is_server_installed(pyright_config)
    print(f"    pyright: {'✅ 已安装' if is_installed else '❌ 未安装'}")
    
    if not is_installed:
        print("\n请先安装: pip install pyright")
        return False
    
    # 2. 启动LSP客户端
    print("\n[2] 启动LSP客户端...")
    try:
        client = await manager.get_client(str(backend_dir), pyright_config)
        print(f"    ✅ LSP客户端已创建")
        
        # 3. 检查进程是否真正运行
        print("\n[3] 检查LSP进程...")
        if client.process:
            print(f"    进程ID: {client.process.pid}")
            print(f"    返回码: {client.process.returncode}")
            print(f"    存活: {client.is_alive()}")
            
            # 4. 尝试调用LSP功能
            print("\n[4] 测试LSP功能...")
            test_file = backend_dir / "daoyoucode" / "agents" / "executor.py"
            
            if test_file.exists():
                print(f"    测试文件: {test_file.name}")
                
                # 获取符号
                symbols = await client.document_symbols(str(test_file))
                
                if symbols:
                    print(f"    ✅ LSP功能正常")
                    print(f"    符号数量: {len(symbols)}")
                    
                    # 显示前3个符号
                    print(f"\n    前3个符号:")
                    for i, sym in enumerate(symbols[:3], 1):
                        name = sym.get('name', 'N/A')
                        kind = sym.get('kind', 0)
                        detail = sym.get('detail', '')
                        print(f"      {i}. {name} (kind: {kind})")
                        if detail:
                            print(f"         {detail}")
                    
                    # 5. 检查管理器状态
                    print(f"\n[5] LSP管理器状态...")
                    print(f"    活跃客户端: {len(manager.clients)}")
                    
                    for key, managed in manager.clients.items():
                        print(f"    - {key}")
                        print(f"      引用计数: {managed['ref_count']}")
                        print(f"      存活: {managed['client'].is_alive()}")
                    
                    print("\n" + "=" * 60)
                    print("✅ LSP已真正启动并正常工作！")
                    print("=" * 60)
                    
                    # 释放客户端
                    manager.release_client(str(backend_dir), pyright_config.id)
                    
                    return True
                else:
                    print(f"    ⚠️  未获取到符号")
                    return False
            else:
                print(f"    ⚠️  测试文件不存在")
                return False
        else:
            print(f"    ❌ LSP进程未创建")
            return False
    
    except Exception as e:
        print(f"    ❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


async def verify_lsp_in_search():
    """验证LSP在搜索中是否工作"""
    print("\n" + "=" * 60)
    print("验证LSP在semantic_code_search中是否工作")
    print("=" * 60)
    
    from daoyoucode.agents.tools.codebase_search_tool import SemanticCodeSearchTool
    
    tool = SemanticCodeSearchTool()
    
    print("\n[1] 执行搜索（enable_lsp=True）...")
    result = await tool.execute(
        query="execute_skill",
        top_k=3,
        repo_path=".",
        enable_lsp=True
    )
    
    if result.success:
        print(f"    ✅ 搜索成功")
        
        # 检查是否有LSP信息
        has_lsp = result.metadata.get('has_lsp_info', False)
        print(f"\n[2] LSP信息状态...")
        print(f"    LSP启用: {result.metadata.get('lsp_enabled', False)}")
        print(f"    有LSP信息: {has_lsp}")
        
        if has_lsp:
            print(f"\n[3] 检查输出内容...")
            content = result.content
            
            # 检查LSP标记
            lsp_markers = {
                "⭐": "质量星级",
                "✅ 有类型注解": "类型注解",
                "🔥 热点代码": "热点代码",
                "📝 符号信息": "符号信息"
            }
            
            found = []
            for marker, name in lsp_markers.items():
                if marker in content:
                    found.append(name)
            
            if found:
                print(f"    ✅ 发现LSP标记: {', '.join(found)}")
                print(f"\n    输出示例:")
                print("    " + "-" * 56)
                lines = content.split('\n')[:15]
                for line in lines:
                    print(f"    {line}")
                print("    " + "-" * 56)
                
                print("\n" + "=" * 60)
                print("✅ LSP在semantic_code_search中正常工作！")
                print("=" * 60)
                return True
            else:
                print(f"    ⚠️  未发现LSP标记")
                return False
        else:
            print(f"    ⚠️  搜索结果中没有LSP信息")
            print(f"\n    可能原因:")
            print(f"    1. LSP服务器未启动")
            print(f"    2. LSP获取信息失败")
            print(f"    3. 文件不在LSP支持范围内")
            return False
    else:
        print(f"    ❌ 搜索失败: {result.error}")
        return False


async def main():
    """主函数"""
    print("\nLSP启动验证工具\n")
    
    # 测试1: 直接验证LSP启动
    result1 = await verify_lsp()
    
    # 测试2: 验证LSP在搜索中工作
    result2 = await verify_lsp_in_search()
    
    # 总结
    print("\n" + "=" * 60)
    print("验证总结")
    print("=" * 60)
    print(f"LSP直接启动: {'通过' if result1 else '失败'}")
    print(f"LSP搜索集成: {'通过' if result2 else '失败'}")
    
    if result1 and result2:
        print("\nLSP已真正启动并完全集成！")
        print("\n现在你可以:")
        print("  1. 使用 semantic_code_search 获取LSP增强的结果")
        print("  2. 看到质量星级、类型注解、热点代码等标记")
        print("  3. Agent会理解并使用这些LSP信息")
    elif result1:
        print("\nLSP已启动，但搜索集成有问题")
    else:
        print("\nLSP未启动")
        print("\n请检查:")
        print("  1. pyright是否已安装: pip install pyright")
        print("  2. 是否有权限启动进程")
        print("  3. 查看错误日志")


if __name__ == "__main__":
    asyncio.run(main())
