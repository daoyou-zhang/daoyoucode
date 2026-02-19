"""
测试pyright的hover功能
"""

import asyncio
import sys
from pathlib import Path

backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))


async def test_pyright_hover():
    """测试pyright的hover功能"""
    print("=" * 60)
    print("测试pyright的hover功能")
    print("=" * 60)
    
    from daoyoucode.agents.tools.lsp_tools import LSPClient, BUILTIN_LSP_SERVERS
    
    # 使用pyright配置
    pyright_config = BUILTIN_LSP_SERVERS['pyright']
    print(f"\nLSP服务器: {pyright_config.id}")
    print(f"命令: {' '.join(pyright_config.command)}")
    
    # 创建客户端
    client = LSPClient(str(backend_dir.parent), pyright_config)
    
    # 启动
    print("\n[1] 启动LSP服务器...")
    await client.start()
    print("✓ 启动成功")
    
    # 初始化
    print("\n[2] 初始化...")
    await client.initialize()
    print("✓ 初始化成功")
    
    # 测试文件
    test_file = backend_dir / "daoyoucode" / "agents" / "core" / "context.py"
    print(f"\n[3] 测试文件: {test_file}")
    
    # 打开文件
    print("\n[4] 打开文件...")
    await client.open_file(str(test_file))
    print("✓ 文件已打开")
    
    # 等待索引
    print("\n[5] 等待索引（2秒）...")
    await asyncio.sleep(2.0)
    
    # 获取符号
    print("\n[6] 获取符号...")
    symbols = await client.document_symbols(str(test_file))
    print(f"✓ 获取到 {len(symbols)} 个符号")
    
    # 找到Context类
    context_class = None
    for sym in symbols:
        if sym.get('name') == 'Context':
            context_class = sym
            break
    
    if not context_class:
        print("✗ 未找到Context类")
        await client.stop()
        return
    
    print(f"✓ 找到Context类")
    line = context_class['range']['start']['line']
    char = context_class['range']['start']['character']
    print(f"  LSP位置（0-based）: {line}:{char}")
    
    # 转换为1-based，并移动到类名位置（class后面）
    line_1based = line + 1
    char_on_name = 6  # "class " 后面
    print(f"  转换为1-based: {line_1based}:{char_on_name}")
    
    # 测试hover
    print("\n[7] 测试hover...")
    print(f"  调用: hover(file, line={line_1based}, char={char_on_name})")
    hover_info = await client.hover(str(test_file), line_1based, char_on_name)
    
    if hover_info:
        print("✓ hover成功")
        print(f"\nhover结果:")
        print(f"  类型: {type(hover_info)}")
        
        if 'contents' in hover_info:
            contents = hover_info['contents']
            print(f"  contents类型: {type(contents)}")
            
            if isinstance(contents, dict) and 'value' in contents:
                print(f"\n内容:\n{contents['value']}")
            elif isinstance(contents, str):
                print(f"\n内容:\n{contents}")
            elif isinstance(contents, list):
                print(f"\n内容（列表）:")
                for i, item in enumerate(contents):
                    print(f"  [{i}]: {item}")
            else:
                print(f"\n内容: {contents}")
    else:
        print("✗ hover返回None")
    
    # 测试references
    print("\n[8] 测试references...")
    references = await client.references(str(test_file), line_1based, char_on_name, include_declaration=False)
    
    if references:
        print(f"✓ 找到 {len(references)} 个引用")
        for i, ref in enumerate(references[:5], 1):
            uri = ref.get('uri', '')
            ref_line = ref.get('range', {}).get('start', {}).get('line', 'N/A')
            if 'file:///' in uri:
                uri = uri.split('file:///')[-1]
            print(f"  {i}. {uri}:{ref_line}")
    else:
        print("✗ 未找到引用")
    
    # 停止
    print("\n[9] 停止LSP服务器...")
    await client.stop()
    print("✓ 已停止")


async def main():
    await test_pyright_hover()


if __name__ == "__main__":
    asyncio.run(main())
