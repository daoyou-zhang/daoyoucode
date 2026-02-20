"""
测试LSP hover功能
"""

import asyncio
import sys
from pathlib import Path

backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))


async def test_hover():
    """测试LSP hover功能"""
    print("=" * 60)
    print("测试LSP hover功能")
    print("=" * 60)
    
    from daoyoucode.agents.tools.lsp_tools import with_lsp_client
    
    # 测试文件
    test_file = backend_dir / "daoyoucode" / "agents" / "executor.py"
    
    print(f"\n文件: {test_file}")
    
    # 获取符号
    symbols = await with_lsp_client(
        str(test_file),
        lambda client: client.document_symbols(str(test_file))
    )
    
    if not symbols:
        print("未获取到符号")
        return
    
    # 测试第一个函数的hover
    for sym in symbols:
        if sym.get('kind') == 12:  # Function
            name = sym.get('name')
            line = sym['range']['start']['line']
            char = sym['range']['start']['character']
            
            print(f"\n测试函数: {name} at {line}:{char}")
            
            hover_info = await with_lsp_client(
                str(test_file),
                lambda client: client.hover(str(test_file), line, char)
            )
            
            print(f"Hover结果: {hover_info}")
            
            if hover_info and 'contents' in hover_info:
                contents = hover_info['contents']
                print(f"Contents类型: {type(contents)}")
                print(f"Contents: {contents}")
            
            # 只测试第一个
            break


async def main():
    await test_hover()


if __name__ == "__main__":
    asyncio.run(main())
