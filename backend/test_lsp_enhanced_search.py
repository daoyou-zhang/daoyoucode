"""
测试LSP增强的语义检索

对比普通检索和LSP增强检索的效果
"""

import asyncio
import sys
from pathlib import Path

# 添加backend到路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from daoyoucode.agents.memory.codebase_index import search_codebase
from daoyoucode.agents.memory.codebase_index_lsp_enhanced import search_codebase_with_lsp


async def test_search_comparison():
    """对比普通检索和LSP增强检索"""
    
    repo_path = backend_dir.parent
    
    # 测试查询
    test_queries = [
        "函数返回类型是什么",
        "有类型注解的函数",
        "异步函数的实现",
        "LLM客户端的配置",
        "工具注册表的实现"
    ]
    
    print("=" * 80)
    print("LSP增强语义检索测试")
    print("=" * 80)
    
    for query in test_queries:
        print(f"\n\n查询: {query}")
        print("-" * 80)
        
        # 1. 普通检索
        print("\n【普通检索】")
        normal_results = search_codebase(repo_path, query, top_k=3, strategy="hybrid")
        
        for i, result in enumerate(normal_results, 1):
            score = result.get('hybrid_score', result.get('score', 0))
            print(f"\n{i}. {result['path']} (L{result['start']}-{result['end']})")
            print(f"   分数: {score:.3f}")
            print(f"   类型: {result.get('type', 'unknown')}")
            print(f"   名称: {result.get('name', 'N/A')}")
        
        # 2. LSP增强检索
        print("\n【LSP增强检索】")
        lsp_results = await search_codebase_with_lsp(
            repo_path,
            query,
            top_k=3,
            enable_lsp=True
        )
        
        for i, result in enumerate(lsp_results, 1):
            base_score = result.get('hybrid_score', result.get('score', 0))
            lsp_score = result.get('lsp_enhanced_score', base_score)
            lsp_boost = result.get('lsp_boost', 1.0)
            
            print(f"\n{i}. {result['path']} (L{result['start']}-{result['end']})")
            print(f"   基础分数: {base_score:.3f}")
            print(f"   LSP增强分数: {lsp_score:.3f} (加成: {(lsp_boost-1)*100:.0f}%)")
            print(f"   类型: {result.get('type', 'unknown')}")
            print(f"   名称: {result.get('name', 'N/A')}")
            
            # LSP信息
            if result.get('has_lsp_info'):
                print(f"   LSP信息:")
                print(f"     - 符号数量: {result.get('symbol_count', 0)}")
                print(f"     - 类型注解: {'是' if result.get('has_type_annotations') else '否'}")
                print(f"     - 引用计数: {result.get('reference_count', 0)}")
        
        # 3. 对比分析
        print("\n【对比分析】")
        
        # 检查排序是否改变
        normal_top1 = f"{normal_results[0]['path']}:{normal_results[0]['start']}" if normal_results else None
        lsp_top1 = f"{lsp_results[0]['path']}:{lsp_results[0]['start']}" if lsp_results else None
        
        if normal_top1 != lsp_top1:
            print(f"   ✅ 排序改变: LSP增强改变了第一名")
            print(f"      普通: {normal_top1}")
            print(f"      LSP:  {lsp_top1}")
        else:
            print(f"   ⚪ 排序不变: 第一名相同")
        
        # 统计LSP加成
        avg_boost = sum(r.get('lsp_boost', 1.0) for r in lsp_results) / len(lsp_results) if lsp_results else 1.0
        print(f"   平均LSP加成: {(avg_boost-1)*100:.1f}%")


async def test_type_query():
    """测试类型相关的查询"""
    
    repo_path = backend_dir.parent
    
    print("\n\n" + "=" * 80)
    print("类型查询测试")
    print("=" * 80)
    
    # 类型相关的查询
    type_queries = [
        "返回字符串的函数",
        "接受字典参数的方法",
        "异步函数",
        "有类型注解的代码"
    ]
    
    for query in type_queries:
        print(f"\n\n查询: {query}")
        print("-" * 80)
        
        results = await search_codebase_with_lsp(
            repo_path,
            query,
            top_k=5,
            enable_lsp=True
        )
        
        for i, result in enumerate(results, 1):
            lsp_score = result.get('lsp_enhanced_score', 0)
            lsp_boost = result.get('lsp_boost', 1.0)
            
            print(f"\n{i}. {result['path']} (L{result['start']}-{result['end']})")
            print(f"   分数: {lsp_score:.3f} (加成: {(lsp_boost-1)*100:.0f}%)")
            print(f"   类型注解: {'是' if result.get('has_type_annotations') else '否'}")
            
            # 显示部分代码
            code_preview = result['text'][:200].replace('\n', ' ')
            print(f"   代码: {code_preview}...")


async def main():
    """主函数"""
    try:
        # 测试1：对比普通检索和LSP增强检索
        await test_search_comparison()
        
        # 测试2：类型查询
        await test_type_query()
        
        print("\n\n" + "=" * 80)
        print("✅ 测试完成")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
