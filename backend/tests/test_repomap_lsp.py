"""
测试RepoMap的LSP集成
"""

import asyncio
import sys
import logging
from pathlib import Path

backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# 设置日志级别为DEBUG
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')


async def test_repomap_lsp():
    """测试RepoMap LSP集成"""
    print("=" * 60)
    print("测试RepoMap LSP集成")
    print("=" * 60)
    
    from daoyoucode.agents.tools.repomap_tools import RepoMapTool
    
    tool = RepoMapTool()
    
    # 测试1: 不启用LSP
    print("\n[测试1] 不启用LSP...")
    result1 = await tool.execute(
        repo_path=".",
        max_tokens=1000,
        enable_lsp=False
    )
    
    if result1.success:
        print("  [OK] 成功")
        print(f"  文件数: {result1.metadata.get('file_count', 0)}")
        print(f"  定义数: {result1.metadata.get('definition_count', 0)}")
        print("\n  输出示例（前500字符）:")
        print("  " + "-" * 56)
        lines = result1.content.split('\n')[:15]
        for line in lines:
            print(f"  {line}")
        print("  " + "-" * 56)
    else:
        print(f"  [NO] 失败: {result1.error}")
    
    # 测试2: 启用LSP
    print("\n[测试2] 启用LSP...")
    result2 = await tool.execute(
        repo_path=".",
        max_tokens=1000,
        enable_lsp=True
    )
    
    if result2.success:
        print("  [OK] 成功")
        print(f"  LSP启用: {result2.metadata.get('lsp_enabled', False)}")
        print("\n  输出示例（前500字符）:")
        print("  " + "-" * 56)
        lines = result2.content.split('\n')[:15]
        for line in lines:
            print(f"  {line}")
        print("  " + "-" * 56)
        
        # 检查LSP标记
        print("\n  [检查LSP标记]")
        has_signature = ': async' in result2.content or ': def' in result2.content or '-> ' in result2.content
        has_ref_count = '被引用' in result2.content
        has_lsp_header = 'LSP增强' in result2.content
        
        print(f"    类型签名: {'[OK]' if has_signature else '[NO]'}")
        print(f"    引用计数: {'[OK]' if has_ref_count else '[NO]'}")
        print(f"    LSP头部: {'[OK]' if has_lsp_header else '[NO]'}")
        
        # 保存完整输出
        output_file = backend_dir / "repomap_lsp_output.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result2.content)
        print(f"\n  完整输出已保存到: {output_file.name}")
    else:
        print(f"  [NO] 失败: {result2.error}")
    
    # 对比
    print("\n" + "=" * 60)
    print("对比结果")
    print("=" * 60)
    
    if result1.success and result2.success:
        print("\n[不启用LSP]")
        print(result1.content.split('\n')[2:5])  # 显示几行
        
        print("\n[启用LSP]")
        print(result2.content.split('\n')[2:5])  # 显示几行
        
        print("\n[总结]")
        if has_signature or has_ref_count:
            print("  [OK] RepoMap LSP集成成功！")
            print("  现在代码地图包含:")
            print("    - 类型签名（函数参数和返回值）")
            print("    - 引用计数（被引用次数）")
            print("    - 更丰富的代码理解")
        else:
            print("  [NO] LSP标记未显示")
            print("  可能原因:")
            print("    1. LSP服务器未启动")
            print("    2. 符号匹配失败")
            print("    3. 文件不是Python")


async def main():
    await test_repomap_lsp()


if __name__ == "__main__":
    asyncio.run(main())
