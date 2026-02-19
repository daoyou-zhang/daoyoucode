"""
调试RepoMap LSP符号匹配
"""

import asyncio
import sys
from pathlib import Path

backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))


async def debug_symbol_match():
    """调试符号匹配"""
    print("=" * 60)
    print("调试RepoMap LSP符号匹配")
    print("=" * 60)
    
    from daoyoucode.agents.tools.lsp_tools import with_lsp_client
    from daoyoucode.agents.tools.repomap_tools import RepoMapTool
    
    # 1. 获取Tree-sitter的定义
    print("\n[1] 获取Tree-sitter定义...")
    tool = RepoMapTool()
    tool._init_cache(backend_dir)
    definitions = tool._scan_repository(backend_dir)
    
    # 找到executor.py
    executor_file = None
    for file_path in definitions.keys():
        if 'executor.py' in file_path:
            executor_file = file_path
            break
    
    if not executor_file:
        print("  未找到executor.py")
        return
    
    print(f"  找到: {executor_file}")
    
    executor_defs = [d for d in definitions[executor_file] if d.get('kind') == 'def']
    print(f"  定义数: {len(executor_defs)}")
    
    # 显示前5个
    print("\n  前5个定义:")
    for i, d in enumerate(executor_defs[:5], 1):
        print(f"    {i}. {d.get('type')} {d['name']} (line {d['line']})")
    
    # 2. 获取LSP符号
    print("\n[2] 获取LSP符号...")
    abs_file = backend_dir / executor_file
    
    symbols = await with_lsp_client(
        str(abs_file),
        lambda client: client.document_symbols(str(abs_file))
    )
    
    if not symbols:
        print("  未获取到LSP符号")
        return
    
    print(f"  符号数: {len(symbols)}")
    
    # 显示前5个
    print("\n  前5个符号:")
    for i, sym in enumerate(symbols[:5], 1):
        name = sym.get('name', 'N/A')
        kind = sym.get('kind', 0)
        detail = sym.get('detail', '')
        if 'range' in sym:
            line = sym['range']['start']['line']
            print(f"    {i}. {name} (kind: {kind}, line: {line})")
            if detail:
                print(f"       detail: {detail}")
    
    # 3. 尝试匹配
    print("\n[3] 尝试匹配...")
    
    for defn in executor_defs[:5]:
        target_line = defn['line'] - 1  # LSP是0-based
        target_name = defn['name']
        
        print(f"\n  Tree-sitter: {target_name} at line {defn['line']}")
        print(f"  查找LSP符号 (line {target_line}, ±2)...")
        
        found = False
        for sym in symbols:
            if 'range' in sym:
                sym_line = sym['range']['start']['line']
                sym_name = sym.get('name', '')
                
                if abs(sym_line - target_line) <= 2:
                    if sym_name == target_name:
                        print(f"    ✓ 匹配: {sym_name} at line {sym_line}")
                        detail = sym.get('detail', '')
                        if detail:
                            print(f"      detail: {detail}")
                        else:
                            print(f"      (无detail)")
                        found = True
                        break
        
        if not found:
            print(f"    ✗ 未找到匹配")
            # 显示附近的符号
            print(f"    附近的LSP符号:")
            for sym in symbols:
                if 'range' in sym:
                    sym_line = sym['range']['start']['line']
                    if abs(sym_line - target_line) <= 5:
                        print(f"      - {sym.get('name')} at line {sym_line}")


async def main():
    await debug_symbol_match()


if __name__ == "__main__":
    asyncio.run(main())
