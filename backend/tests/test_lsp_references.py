"""
测试LSP references功能
"""

import asyncio
import sys
from pathlib import Path

backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))


async def test_lsp_references():
    """测试LSP references功能"""
    print("=" * 60)
    print("测试LSP references功能")
    print("=" * 60)
    
    from daoyoucode.agents.tools.lsp_tools import with_lsp_client
    
    # 测试文件：executor.py中的execute_skill函数
    test_file = backend_dir / "daoyoucode" / "agents" / "executor.py"
    
    print(f"\n文件: {test_file}")
    
    # 1. 先打开文件
    print("\n[1] 打开文件...")
    await with_lsp_client(
        str(test_file),
        lambda client: client.open_file(str(test_file))
    )
    
    # 等待LSP处理
    await asyncio.sleep(1.0)
    
    # 2. 获取符号
    print("\n[2] 获取符号...")
    symbols = await with_lsp_client(
        str(test_file),
        lambda client: client.document_symbols(str(test_file))
    )
    
    if not symbols:
        print("未获取到符号")
        return
    
    print(f"符号数: {len(symbols)}")
    
    # 找到execute_skill函数
    execute_skill_symbol = None
    for sym in symbols:
        if sym.get('name') == 'execute_skill' and sym.get('kind') == 12:
            execute_skill_symbol = sym
            break
    
    if not execute_skill_symbol:
        print("未找到execute_skill函数")
        return
    
    print(f"\n找到函数: execute_skill")
    line = execute_skill_symbol['range']['start']['line']
    char = execute_skill_symbol['range']['start']['character']
    print(f"位置: {line}:{char}")
    
    # 3. 获取引用
    print("\n[3] 获取引用...")
    references = await with_lsp_client(
        str(test_file),
        lambda client: client.references(
            str(test_file), line, char,
            include_declaration=False
        )
    )
    
    if references:
        print(f"✓ 找到 {len(references)} 个引用")
        for i, ref in enumerate(references[:5], 1):
            ref_file = ref.get('uri', 'N/A')
            ref_line = ref.get('range', {}).get('start', {}).get('line', 'N/A')
            print(f"  {i}. {ref_file}:{ref_line}")
    else:
        print("✗ 未找到引用")
        print("可能原因：")
        print("  1. LSP还在索引项目")
        print("  2. 该函数确实没有被引用")
        print("  3. LSP配置问题")


async def main():
    await test_lsp_references()


if __name__ == "__main__":
    asyncio.run(main())
