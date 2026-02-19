"""
简单测试hover功能
"""

import asyncio
import sys
from pathlib import Path

backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))


async def test_hover():
    """测试hover功能"""
    print("=" * 60)
    print("测试hover功能")
    print("=" * 60)
    
    from daoyoucode.agents.tools.lsp_tools import with_lsp_client
    
    # 测试文件
    test_file = backend_dir / "daoyoucode" / "agents" / "core" / "context.py"
    
    print(f"\n文件: {test_file}")
    
    # 获取符号
    symbols = await with_lsp_client(
        str(test_file),
        lambda client: client.document_symbols(str(test_file))
    )
    
    if not symbols:
        print("未获取到符号")
        return
    
    print(f"符号数: {len(symbols)}")
    
    # 找到Context类
    context_class = None
    for sym in symbols:
        if sym.get('name') == 'Context':
            context_class = sym
            break
    
    if not context_class:
        print("未找到Context类")
        return
    
    print(f"\n找到Context类")
    line = context_class['range']['start']['line']
    char = context_class['range']['start']['character']
    print(f"位置: {line}:{char}")
    
    # 测试hover
    print("\n测试hover...")
    hover_info = await with_lsp_client(
        str(test_file),
        lambda client: client.hover(str(test_file), line, char)
    )
    
    print(f"\nhover结果: {hover_info}")
    
    if hover_info and 'contents' in hover_info:
        contents = hover_info['contents']
        print(f"\ncontents类型: {type(contents)}")
        print(f"contents: {contents}")


async def main():
    await test_hover()


if __name__ == "__main__":
    asyncio.run(main())
