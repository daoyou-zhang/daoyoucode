"""
调试LSP搜索集成问题
"""

import asyncio
import sys
from pathlib import Path

backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))


async def debug_search():
    """调试搜索"""
    print("=" * 60)
    print("调试LSP搜索集成")
    print("=" * 60)
    
    from daoyoucode.agents.memory.codebase_index_lsp_enhanced import search_codebase_with_lsp
    
    print("\n[1] 执行LSP增强搜索...")
    results = await search_codebase_with_lsp(
        backend_dir,
        "execute_skill",
        top_k=3,
        enable_lsp=True
    )
    
    print(f"    结果数量: {len(results)}")
    
    # 详细检查每个结果
    for i, r in enumerate(results, 1):
        print(f"\n[结果{i}]")
        print(f"  文件: {r.get('path', 'N/A')}")
        print(f"  行: {r.get('start', 0)}-{r.get('end', 0)}")
        print(f"  has_lsp_info: {r.get('has_lsp_info', False)}")
        
        if r.get('has_lsp_info'):
            print(f"  [OK] 有LSP信息:")
            print(f"    - symbol_count: {r.get('symbol_count', 0)}")
            print(f"    - has_type_annotations: {r.get('has_type_annotations', False)}")
            print(f"    - reference_count: {r.get('reference_count', 0)}")
            
            symbols = r.get('lsp_symbols', [])
            print(f"    - lsp_symbols数量: {len(symbols)}")
            if symbols:
                print(f"    - 符号:")
                for sym in symbols[:3]:
                    print(f"      * {sym.get('name', 'N/A')}: {sym.get('detail', '')}")
        else:
            print(f"  [NO] 无LSP信息")
            print(f"    所有键: {list(r.keys())}")
    
    # 测试工具
    print("\n" + "=" * 60)
    print("测试SemanticCodeSearchTool")
    print("=" * 60)
    
    from daoyoucode.agents.tools.codebase_search_tool import SemanticCodeSearchTool
    
    tool = SemanticCodeSearchTool()
    result = await tool.execute(
        query="execute_skill",
        top_k=3,
        repo_path=".",
        enable_lsp=True
    )
    
    print(f"\n[2] 工具执行结果:")
    print(f"    成功: {result.success}")
    print(f"    metadata: {result.metadata}")
    
    if result.content:
        print(f"\n[3] 输出内容（前500字符）:")
        print("-" * 60)
        print(result.content[:500])
        print("-" * 60)
        
        # 检查标记
        markers = {
            "⭐": "质量星级",
            "✅ 有类型注解": "类型注解",
            "🔥 热点代码": "热点代码",
            "📝 符号信息": "符号信息"
        }
        
        found = []
        for marker, name in markers.items():
            if marker in result.content:
                found.append(name)
        
        if found:
            print(f"\n[OK] 发现LSP标记: {', '.join(found)}")
        else:
            print(f"\n[NO] 未发现任何LSP标记")
            print(f"\n检查内容是否包含关键字:")
            for marker, name in markers.items():
                # 避免打印emoji
                print(f"  '{name}' in content: {marker in result.content}")


async def main():
    await debug_search()


if __name__ == "__main__":
    asyncio.run(main())
