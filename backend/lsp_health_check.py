"""
LSP 服务健康检查和修复工具

用于诊断和修复 LSP 服务不稳定的问题
"""

import asyncio
import sys
from pathlib import Path

# 设置 UTF-8 编码
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))


async def check_lsp_health():
    """检查 LSP 服务健康状态"""
    print("=" * 60)
    print("LSP 服务健康检查")
    print("=" * 60)
    
    from daoyoucode.agents.tools.lsp_tools import get_lsp_manager, BUILTIN_LSP_SERVERS
    
    manager = get_lsp_manager()
    
    # 1. 检查 LSP 服务器安装状态
    print("\n[1] 检查 LSP 服务器安装状态...")
    for server_id, config in BUILTIN_LSP_SERVERS.items():
        # 创建临时客户端来检测
        from daoyoucode.agents.tools.lsp_tools import LSPClient
        temp_client = LSPClient(str(backend_dir), config)
        is_installed = temp_client.is_server_installed()
        status = "✅ 已安装" if is_installed else "❌ 未安装"
        print(f"  {server_id}: {status}")
        if is_installed:
            import sys
            from pathlib import Path
            # 尝试找到实际路径
            venv_scripts = Path(sys.prefix) / "Scripts"
            if venv_scripts.exists():
                for ext in ['.exe', '.cmd', '.bat', '']:
                    venv_cmd = venv_scripts / f"{config.command[0]}{ext}"
                    if venv_cmd.exists():
                        print(f"    路径: {venv_cmd}")
                        break
    
    # 2. 测试 pyright 启动
    print("\n[2] 测试 pyright 启动...")
    pyright_config = BUILTIN_LSP_SERVERS.get("pyright")
    
    if not pyright_config:
        print("❌ pyright 配置不存在")
        return False
    
    # 检查安装状态
    from daoyoucode.agents.tools.lsp_tools import LSPClient
    temp_client = LSPClient(str(backend_dir), pyright_config)
    if not temp_client.is_server_installed():
        print("❌ pyright 未安装")
        print("\n请安装: pip install pyright")
        return False
    
    try:
        # 启动客户端
        client = await manager.get_client(str(backend_dir), pyright_config)
        print(f"✅ LSP 客户端已启动")
        print(f"  进程ID: {client.process.pid if client.process else 'N/A'}")
        print(f"  存活状态: {client.is_alive()}")
        
        # 3. 测试基本功能
        print("\n[3] 测试基本功能...")
        
        # 测试文件
        test_file = backend_dir / "daoyoucode" / "agents" / "core" / "agent.py"
        
        if not test_file.exists():
            print(f"❌ 测试文件不存在: {test_file}")
            manager.release_client(str(backend_dir), pyright_config.id)
            return False
        
        # 测试打开文件
        print(f"  测试文件: {test_file.name}")
        await client.open_file(str(test_file))
        print(f"  ✅ 文件已打开")
        
        # 测试诊断
        print(f"  测试诊断功能...")
        diagnostics = await client.diagnostics(str(test_file), wait_time=3.0)
        diag_count = len(diagnostics.get('items', []))
        print(f"  ✅ 诊断完成，发现 {diag_count} 个问题")
        
        # 测试符号
        print(f"  测试符号功能...")
        symbols = await client.document_symbols(str(test_file))
        symbol_count = len(symbols) if symbols else 0
        print(f"  ✅ 符号查询完成，发现 {symbol_count} 个符号")
        
        # 4. 检查客户端状态
        print("\n[4] 检查客户端状态...")
        print(f"  进程存活: {client.is_alive()}")
        print(f"  已打开文件数: {len(client.opened_files)}")
        print(f"  待处理请求数: {len(client.pending_requests)}")
        print(f"  诊断缓存数: {len(client.diagnostics_store)}")
        
        # 5. 压力测试
        print("\n[5] 压力测试（连续请求）...")
        for i in range(5):
            try:
                await client.diagnostics(str(test_file), wait_time=1.0)
                print(f"  请求 {i+1}/5: ✅")
            except Exception as e:
                print(f"  请求 {i+1}/5: ❌ {e}")
                break
        
        # 释放客户端
        manager.release_client(str(backend_dir), pyright_config.id)
        
        print("\n" + "=" * 60)
        print("✅ LSP 服务健康检查通过")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ LSP 服务检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def fix_lsp_issues():
    """修复常见的 LSP 问题"""
    print("\n" + "=" * 60)
    print("LSP 问题修复")
    print("=" * 60)
    
    from daoyoucode.agents.tools.lsp_tools import get_lsp_manager
    
    manager = get_lsp_manager()
    
    # 1. 停止所有客户端
    print("\n[1] 停止所有 LSP 客户端...")
    await manager.stop_all()
    print("  ✅ 所有客户端已停止")
    
    # 2. 清理缓存
    print("\n[2] 清理缓存...")
    manager.clients.clear()
    print("  ✅ 缓存已清理")
    
    # 3. 重新检查
    print("\n[3] 重新检查...")
    result = await check_lsp_health()
    
    return result


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="LSP 服务健康检查和修复工具")
    parser.add_argument("--fix", action="store_true", help="修复 LSP 问题")
    args = parser.parse_args()
    
    if args.fix:
        success = await fix_lsp_issues()
    else:
        success = await check_lsp_health()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
