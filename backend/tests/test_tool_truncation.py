"""
测试工具输出截断功能
"""

import sys
from pathlib import Path
import asyncio

sys.path.insert(0, str(Path(__file__).parent))


async def test_truncation():
    print("\n" + "="*60)
    print("测试工具输出截断功能")
    print("="*60)
    
    from daoyoucode.agents.tools import get_tool_registry
    
    # 获取工具注册表
    registry = get_tool_registry()
    
    # 测试1: 读取一个长文件
    print("\n1. 测试ReadFileTool截断")
    print("-"*60)
    
    # 创建一个测试文件（很长）
    test_file = Path("test_long_file.txt")
    long_content = "\n".join([f"Line {i}: " + "x" * 100 for i in range(500)])
    test_file.write_text(long_content, encoding="utf-8")
    
    print(f"原始文件: {len(long_content)} 字符, {long_content.count(chr(10)) + 1} 行")
    
    result = await registry.execute_tool("read_file", file_path=str(test_file))
    
    if result.success:
        print(f"截断后: {len(result.content)} 字符")
        print(f"截断标记: {result.metadata.get('truncated', False)}")
        if result.metadata.get('truncated'):
            print(f"原始长度: {result.metadata.get('original_length')}")
            print(f"截断长度: {result.metadata.get('truncated_length')}")
        
        # 显示前100和后100字符
        print(f"\n前100字符:\n{result.content[:100]}")
        print(f"\n后100字符:\n{result.content[-100:]}")
    else:
        print(f"失败: {result.error}")
    
    # 清理测试文件
    test_file.unlink()
    
    # 测试2: 测试repo_map
    print("\n\n2. 测试RepoMapTool截断")
    print("-"*60)
    
    result = await registry.execute_tool(
        "repo_map",
        repo_path=".",  # 当前目录（backend）
        chat_files=[],
        mentioned_idents=[],
        max_tokens=5000  # 设置一个较大的值，看看是否会被截断
    )
    
    if result.success:
        print(f"结果长度: {len(result.content)} 字符")
        print(f"截断标记: {result.metadata.get('truncated', False)}")
        if result.metadata.get('truncated'):
            print(f"原始长度: {result.metadata.get('original_length')}")
            print(f"截断长度: {result.metadata.get('truncated_length')}")
        
        # 显示前200字符
        print(f"\n前200字符:\n{result.content[:200]}")
    else:
        print(f"失败: {result.error}")
    
    # 测试3: 测试get_repo_structure
    print("\n\n3. 测试GetRepoStructureTool截断")
    print("-"*60)
    
    result = await registry.execute_tool(
        "get_repo_structure",
        repo_path=".",  # 当前目录（backend）
        max_depth=5,  # 深度很大，可能产生很长的输出
        show_files=True
    )
    
    if result.success:
        lines = result.content.splitlines()
        print(f"结果: {len(result.content)} 字符, {len(lines)} 行")
        print(f"截断标记: {result.metadata.get('truncated', False)}")
        if result.metadata.get('truncated'):
            print(f"原始长度: {result.metadata.get('original_length')}")
            print(f"截断长度: {result.metadata.get('truncated_length')}")
        
        # 显示前10行和后10行
        print(f"\n前10行:")
        for line in lines[:10]:
            print(line)
        
        if len(lines) > 20:
            print(f"\n后10行:")
            for line in lines[-10:]:
                print(line)
    else:
        print(f"失败: {result.error}")
    
    # 测试4: 测试截断策略
    print("\n\n4. 测试不同的截断策略")
    print("-"*60)
    
    from daoyoucode.agents.tools.base import BaseTool, ToolResult
    
    class TestTool(BaseTool):
        """测试工具"""
        MAX_OUTPUT_CHARS = 100
        
        def __init__(self, strategy="head_tail"):
            super().__init__("test_tool", "测试工具")
            self.TRUNCATION_STRATEGY = strategy
        
        async def execute(self, **kwargs):
            return ToolResult(success=True, content="x" * 200)
    
    # head_tail策略
    tool1 = TestTool("head_tail")
    content = "0123456789" * 20  # 200字符
    truncated = tool1.truncate_output(content)
    print(f"head_tail策略: {len(content)} -> {len(truncated)} 字符")
    print(f"内容: {truncated[:50]}...{truncated[-50:]}")
    
    # head_only策略
    tool2 = TestTool("head_only")
    truncated = tool2.truncate_output(content)
    print(f"\nhead_only策略: {len(content)} -> {len(truncated)} 字符")
    print(f"内容: {truncated}")
    
    # none策略
    tool3 = TestTool("none")
    truncated = tool3.truncate_output(content)
    print(f"\nnone策略: {len(content)} -> {len(truncated)} 字符")
    print(f"未截断: {len(truncated) == len(content)}")
    
    print("\n" + "="*60)
    print("测试完成！")
    print("="*60)


if __name__ == '__main__':
    asyncio.run(test_truncation())
