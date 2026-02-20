"""
测试pyright的references功能
"""

import asyncio
import sys
from pathlib import Path

backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))


async def test_pyright_references():
    """测试pyright的references功能"""
    print("=" * 60)
    print("测试pyright的references功能")
    print("=" * 60)
    
    from daoyoucode.agents.tools.lsp_tools import LSPServerManager, BUILTIN_LSP_SERVERS
    
    # 使用pyright
    pyright_config = BUILTIN_LSP_SERVERS['pyright']
    print(f"\n使用LSP服务器: {pyright_config.id}")
    print(f"命令: {' '.join(pyright_config.command)}")
    
    # 创建管理器
    manager = LSPServerManager()
    
    # 检查是否已安装
    if not manager.is_server_installed(pyright_config):
        print("\n✗ pyright未安装")
        print("安装方式: pip install pyright")
        return
    
    print("✓ pyright已安装")
    
    # 测试文件
    test_file = backend_dir / "daoyoucode" / "agents" / "executor.py"
    print(f"\n测试文件: {test_file}")
    
    # 获取客户端
    client = await manager.get_or_create_client(str(backend_dir.parent), pyright_config)
    
    # 初始化
    print("\n[1] 初始化LSP...")
    await client.initialize()
    
    # 打开文件
    print("\n[2] 打开文件...")
    await client.open_file(str(test_file))
    
    # 等待索引
    print("\n[3] 等待索引（3秒）...")
    await asyncio.sleep(3.0)
    
    # 获取符号
    print("\n[4] 获取符号...")
    symbols = await client.document_symbols(str(test_file))
    
    if not symbols:
        print("✗ 未获取到符号")
        return
    
    print(f"✓ 获取到 {len(symbols)} 个符号")
    
    # 找到execute_skill
    execute_skill = None
    for sym in symbols:
        if sym.get('name') == 'execute_skill':
            execute_skill = sym
            break
    
    if not execute_skill:
        print("✗ 未找到execute_skill")
        return
    
    print(f"✓ 找到execute_skill")
    line = execute_skill['range']['start']['line']
    char = execute_skill['range']['start']['character']
    print(f"  位置: {line}:{char}")
    
    # 获取引用
    print("\n[5] 获取引用...")
    references = await client.references(str(test_file), line, char, include_declaration=False)
    
    if references and len(references) > 0:
        print(f"✓ 找到 {len(references)} 个引用")
        for i, ref in enumerate(references[:10], 1):
            uri = ref.get('uri', '')
            ref_line = ref.get('range', {}).get('start', {}).get('line', 'N/A')
            # 简化URI显示
            if 'file:///' in uri:
                uri = uri.split('file:///')[-1]
            print(f"  {i}. {uri}:{ref_line}")
    else:
        print("✗ 未找到引用")
    
    # 停止客户端
    await client.stop()


async def main():
    await test_pyright_references()


if __name__ == "__main__":
    asyncio.run(main())
