"""
调试pylsp返回的符号信息
"""

import asyncio
import sys
import json
from pathlib import Path

backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))


async def debug_pylsp_symbols():
    """调试pylsp返回的符号信息"""
    print("=" * 60)
    print("调试pylsp返回的符号信息")
    print("=" * 60)
    
    from daoyoucode.agents.tools.lsp_tools import with_lsp_client
    
    # 测试文件
    test_file = backend_dir / "daoyoucode" / "agents" / "executor.py"
    
    print(f"\n文件: {test_file}")
    print(f"存在: {test_file.exists()}")
    
    # 获取符号
    symbols = await with_lsp_client(
        str(test_file),
        lambda client: client.document_symbols(str(test_file))
    )
    
    if not symbols:
        print("\n未获取到符号")
        return
    
    print(f"\n符号数: {len(symbols)}")
    
    # 显示前5个符号的完整信息
    print("\n前5个符号的完整信息:")
    for i, sym in enumerate(symbols[:5], 1):
        print(f"\n{i}. {sym.get('name', 'N/A')}")
        print(f"   kind: {sym.get('kind', 'N/A')}")
        print(f"   detail: {sym.get('detail', '(无)')}")
        
        if 'range' in sym:
            start = sym['range']['start']
            end = sym['range']['end']
            print(f"   range: {start['line']}:{start['character']} - {end['line']}:{end['character']}")
        
        # 显示所有字段
        print(f"   所有字段: {list(sym.keys())}")


async def main():
    await debug_pylsp_symbols()


if __name__ == "__main__":
    asyncio.run(main())
