"""
测试工具后处理功能
"""

import sys
from pathlib import Path
import asyncio

sys.path.insert(0, str(Path(__file__).parent))


async def test_postprocessing():
    print("\n" + "="*60)
    print("测试工具后处理功能")
    print("="*60)
    
    from daoyoucode.agents.tools import get_tool_registry
    from daoyoucode.agents.tools.postprocessor import get_tool_postprocessor
    
    # 获取工具注册表和后处理器
    registry = get_tool_registry()
    postprocessor = get_tool_postprocessor()
    
    # 测试1: RepoMap后处理
    print("\n1. 测试RepoMap后处理")
    print("-"*60)
    
    user_query = "Agent系统是怎么实现的？"
    print(f"用户问题: {user_query}")
    
    # 执行工具
    result = await registry.execute_tool(
        "repo_map",
        repo_path=".",
        chat_files=[],
        mentioned_idents=[],
        max_tokens=5000
    )
    
    if result.success:
        print(f"\n原始结果: {len(result.content)} 字符")
        print(f"前200字符:\n{result.content[:200]}")
        
        # 后处理
        processed = await postprocessor.process(
            tool_name="repo_map",
            result=result,
            user_query=user_query,
            context={}
        )
        
        print(f"\n后处理结果: {len(processed.content)} 字符")
        print(f"减少: {len(result.content) - len(processed.content)} 字符 "
              f"({(1 - len(processed.content)/len(result.content))*100:.1f}%)")
        
        if processed.metadata.get('post_processed'):
            print(f"关键词: {processed.metadata.get('keywords')}")
            print(f"原始文件数: {processed.metadata.get('original_files')}")
            print(f"过滤后文件数: {processed.metadata.get('filtered_files')}")
        
        print(f"\n前300字符:\n{processed.content[:300]}")
    
    # 测试2: 不同的用户问题
    print("\n\n2. 测试不同用户问题的后处理")
    print("-"*60)
    
    queries = [
        "Memory系统在哪里？",
        "工具注册是怎么实现的？",
        "LLM客户端的配置",
        "编排器有哪些类型？",
    ]
    
    for query in queries:
        print(f"\n问题: {query}")
        
        result = await registry.execute_tool(
            "repo_map",
            repo_path=".",
            chat_files=[],
            mentioned_idents=[],
            max_tokens=3000
        )
        
        if result.success:
            processed = await postprocessor.process(
                tool_name="repo_map",
                result=result,
                user_query=query,
                context={}
            )
            
            reduction = (1 - len(processed.content)/len(result.content)) * 100
            print(f"  原始: {len(result.content)} 字符")
            print(f"  处理后: {len(processed.content)} 字符 (减少 {reduction:.1f}%)")
            
            if processed.metadata.get('post_processed'):
                print(f"  关键词: {processed.metadata.get('keywords')}")
                print(f"  文件: {processed.metadata.get('original_files')} -> "
                      f"{processed.metadata.get('filtered_files')}")
    
    # 测试3: 搜索结果后处理
    print("\n\n3. 测试搜索结果后处理")
    print("-"*60)
    
    user_query = "Agent的execute方法"
    print(f"用户问题: {user_query}")
    
    result = await registry.execute_tool(
        "text_search",
        query="execute",
        directory="daoyoucode/agents",
        max_results=50
    )
    
    if result.success:
        print(f"\n原始结果: {len(result.content)} 字符")
        
        processed = await postprocessor.process(
            tool_name="text_search",
            result=result,
            user_query=user_query,
            context={}
        )
        
        print(f"后处理结果: {len(processed.content)} 字符")
        print(f"减少: {len(result.content) - len(processed.content)} 字符 "
              f"({(1 - len(processed.content)/len(result.content))*100:.1f}%)")
        
        if processed.metadata.get('post_processed'):
            print(f"关键词: {processed.metadata.get('keywords')}")
            print(f"原始匹配: {processed.metadata.get('original_matches')}")
            print(f"过滤后匹配: {processed.metadata.get('filtered_matches')}")
    
    # 测试4: 关键词提取
    print("\n\n4. 测试关键词提取")
    print("-"*60)
    
    from daoyoucode.agents.tools.postprocessor import BasePostProcessor
    
    processor = BasePostProcessor()
    
    test_queries = [
        "Agent系统是怎么实现的？",
        "如何配置LLM客户端？",
        "Memory模块在哪里定义的？",
        "工具注册表的作用是什么？",
        "ReAct编排器和Simple编排器有什么区别？",
    ]
    
    for query in test_queries:
        keywords = processor.extract_keywords(query)
        print(f"{query}")
        print(f"  → 关键词: {keywords}\n")
    
    print("\n" + "="*60)
    print("测试完成！")
    print("="*60)


if __name__ == '__main__':
    asyncio.run(test_postprocessing())
