"""
最终验证LSP搜索集成
"""

import asyncio
import sys
from pathlib import Path

backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))


async def final_verify():
    """最终验证"""
    print("=" * 60)
    print("最终验证LSP搜索集成")
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
    
    print(f"    成功: {result.success}")
    print(f"    LSP启用: {result.metadata.get('lsp_enabled', False)}")
    print(f"    有LSP信息: {result.metadata.get('has_lsp_info', False)}")
    
    if result.content:
        # 检查LSP标记（避免打印emoji）
        markers = {
            "\u2b50": "质量星级",  # ⭐
            "有类型注解": "类型注解",
            "热点代码": "热点代码",
            "符号信息": "符号信息"
        }
        
        found = []
        for marker, name in markers.items():
            if marker in result.content:
                found.append(name)
        
        print(f"\n[2] LSP标记检测:")
        if found:
            print(f"    [OK] 发现: {', '.join(found)}")
        else:
            print(f"    [NO] 未发现任何LSP标记")
        
        # 检查内容结构
        print(f"\n[3] 内容结构检测:")
        checks = {
            "[1]": "结果编号",
            "分数:": "分数显示",
            "```": "代码块",
            "质量:": "质量标记"
        }
        
        for marker, name in checks.items():
            found = marker in result.content
            status = "[OK]" if found else "[NO]"
            print(f"    {status} {name}: {found}")
        
        # 保存到文件（避免编码问题）
        output_file = backend_dir / "lsp_search_output.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.content)
        print(f"\n[4] 完整输出已保存到: {output_file.name}")
        print(f"    可以用文本编辑器查看完整的LSP标记")
    
    # 总结
    print("\n" + "=" * 60)
    print("验证结果")
    print("=" * 60)
    
    if result.success and result.metadata.get('has_lsp_info'):
        print("[OK] LSP搜索集成成功！")
        print("\n现在semantic_code_search会返回:")
        print("  1. 质量星级（基于符号数量）")
        print("  2. 类型注解标记")
        print("  3. 热点代码标记（引用计数>10）")
        print("  4. 符号信息（函数签名等）")
        print("\n查看 lsp_search_output.txt 可以看到完整的LSP标记")
    else:
        print("[NO] LSP搜索集成失败")
        print(f"  成功: {result.success}")
        print(f"  有LSP信息: {result.metadata.get('has_lsp_info', False)}")


async def main():
    await final_verify()


if __name__ == "__main__":
    asyncio.run(main())
