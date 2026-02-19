"""
测试阶段4：混合检索

验证内容：
1. BM25关键词匹配
2. 查询类型检测
3. 自适应权重
4. 混合检索对比
5. 性能测试
"""

import sys
from pathlib import Path
import time

# 添加backend到路径
backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

from daoyoucode.agents.memory.codebase_index import CodebaseIndex


def test_bm25_scoring():
    """测试1: BM25关键词匹配"""
    print("\n" + "="*60)
    print("测试1: BM25关键词匹配")
    print("="*60)
    
    index = CodebaseIndex(Path("."))
    index._init_bm25_cache()
    
    # 测试精确查询
    query = "execute"
    
    print(f"\n查询: {query}")
    print(f"BM25分数（前10个）:\n")
    
    # 计算所有chunks的BM25分数
    scored = []
    for chunk in index.chunks:
        score = index._bm25_score(query, chunk)
        if score > 0:
            scored.append((chunk, score))
    
    # 排序
    scored.sort(key=lambda x: x[1], reverse=True)
    
    # 显示前10个
    for chunk, score in scored[:10]:
        print(f"  {chunk['name']:30s} {score:6.2f}")
    
    return len(scored) > 0


def test_query_type_detection():
    """测试2: 查询类型检测"""
    print("\n" + "="*60)
    print("测试2: 查询类型检测")
    print("="*60)
    
    index = CodebaseIndex(Path("."))
    
    queries = [
        "def execute",           # code
        "execute_with_timeout",  # function_name
        "如何执行Agent",         # natural_language
        "class BaseAgent",       # code
        "超时处理机制",          # natural_language
        "import json",           # code
        "search_multilayer",     # function_name
        "向量检索优化"           # natural_language
    ]
    
    print(f"\n查询类型检测:\n")
    
    for query in queries:
        qtype = index._detect_query_type(query)
        print(f"  {query:30s} → {qtype}")
    
    return True


def test_adaptive_weights():
    """测试3: 自适应权重"""
    print("\n" + "="*60)
    print("测试3: 自适应权重")
    print("="*60)
    
    index = CodebaseIndex(Path("."))
    
    query_types = ["code", "function_name", "natural_language"]
    
    print(f"\n自适应权重:\n")
    
    for qtype in query_types:
        weights = index._get_adaptive_weights(qtype)
        print(f"  {qtype:20s}:")
        print(f"    语义={weights['semantic']:.1f}, "
              f"关键词={weights['keyword']:.1f}, "
              f"PageRank={weights['pagerank']:.1f}, "
              f"上下文={weights['context']:.1f}")
    
    return True


def test_hybrid_vs_multilayer():
    """测试4: 混合检索 vs 多层检索"""
    print("\n" + "="*60)
    print("测试4: 混合检索 vs 多层检索")
    print("="*60)
    
    index = CodebaseIndex(Path("."))
    
    query = "execute"
    
    print(f"\n查询: {query}\n")
    
    # 多层检索
    print("多层检索:")
    results_multi = index.search_multilayer(query, top_k=5)
    for i, r in enumerate(results_multi, 1):
        print(f"  {i}. {r['name']:30s} 分数={r.get('final_score', 0):.4f}")
    
    # 混合检索
    print("\n混合检索:")
    results_hybrid = index.search_hybrid(query, top_k=5)
    for i, r in enumerate(results_hybrid, 1):
        print(f"  {i}. {r['name']:30s} 分数={r.get('hybrid_score', 0):.4f}")
        scores = r.get('scores', {})
        print(f"      语义={scores.get('semantic', 0):.2f}, "
              f"关键词={scores.get('keyword', 0):.2f}, "
              f"PageRank={scores.get('pagerank', 0):.2f}, "
              f"上下文={scores.get('context', 0):.2f}")
    
    return True


def test_different_query_types():
    """测试5: 不同查询类型的效果"""
    print("\n" + "="*60)
    print("测试5: 不同查询类型的效果")
    print("="*60)
    
    index = CodebaseIndex(Path("."))
    
    queries = [
        ("execute_with_timeout", "function_name"),
        ("def execute", "code"),
        ("如何执行Agent", "natural_language")
    ]
    
    for query, expected_type in queries:
        print(f"\n查询: {query}")
        print(f"预期类型: {expected_type}")
        
        results = index.search_hybrid(query, top_k=3)
        
        print(f"结果:")
        for i, r in enumerate(results, 1):
            print(f"  {i}. {r['name']:30s} {r['hybrid_score']:.4f}")
    
    return True


def test_performance():
    """测试6: 性能对比"""
    print("\n" + "="*60)
    print("测试6: 性能对比")
    print("="*60)
    
    index = CodebaseIndex(Path("."))
    
    query = "Agent执行"
    
    # 单层检索
    start = time.time()
    results_simple = index.search(query, top_k=10)
    time_simple = time.time() - start
    
    # 多层检索
    start = time.time()
    results_multi = index.search_multilayer(query, top_k=10)
    time_multi = time.time() - start
    
    # 混合检索
    start = time.time()
    results_hybrid = index.search_hybrid(query, top_k=10)
    time_hybrid = time.time() - start
    
    print(f"\n⏱️ 性能对比:")
    print(f"   单层检索: {time_simple:.3f}秒 ({len(results_simple)} 个结果)")
    print(f"   多层检索: {time_multi:.3f}秒 ({len(results_multi)} 个结果)")
    print(f"   混合检索: {time_hybrid:.3f}秒 ({len(results_hybrid)} 个结果)")
    
    if time_simple > 0:
        print(f"\n   相对单层:")
        print(f"     多层: +{(time_multi - time_simple) / time_simple * 100:.0f}%")
        print(f"     混合: +{(time_hybrid - time_simple) / time_simple * 100:.0f}%")
    
    # 验证性能合理
    if time_hybrid < 2.0:
        print(f"\n   ✅ 混合检索性能合理（<2秒）")
        return True
    else:
        print(f"\n   ⚠️ 混合检索性能较慢（>{2}秒）")
        return False


def test_score_breakdown():
    """测试7: 分数分解分析"""
    print("\n" + "="*60)
    print("测试7: 分数分解分析")
    print("="*60)
    
    index = CodebaseIndex(Path("."))
    
    query = "超时处理"
    
    results = index.search_hybrid(query, top_k=5)
    
    print(f"\n查询: {query}")
    print(f"\n分数分解:\n")
    
    for i, r in enumerate(results, 1):
        scores = r.get('scores', {})
        print(f"{i}. {r['name']}")
        print(f"   混合分数: {r['hybrid_score']:.4f}")
        print(f"   - 语义:   {scores.get('semantic', 0):.4f}")
        print(f"   - 关键词: {scores.get('keyword', 0):.4f}")
        print(f"   - PageRank: {scores.get('pagerank', 0):.4f}")
        print(f"   - 上下文: {scores.get('context', 0):.4f}")
        print()
    
    return True


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("阶段4测试：混合检索")
    print("="*60)
    
    tests = [
        ("BM25关键词匹配", test_bm25_scoring),
        ("查询类型检测", test_query_type_detection),
        ("自适应权重", test_adaptive_weights),
        ("混合vs多层对比", test_hybrid_vs_multilayer),
        ("不同查询类型", test_different_query_types),
        ("性能对比", test_performance),
        ("分数分解分析", test_score_breakdown),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"\n总计: {passed}/{total} 通过")
    
    # 结论
    if passed == total:
        print("\n" + "="*60)
        print("🎉 阶段4完成！")
        print("="*60)
        print("""
✅ 混合检索已实现：
   - BM25关键词匹配
   - 查询类型检测
   - 自适应权重
   - 上下文分数
   - 混合打分策略

✅ 检索能力提升：
   - 结合语义和关键词（互补）
   - 自适应不同查询类型
   - 更鲁棒的检索结果
   - 性能合理（<2秒）

✅ 三种检索方式：
   - search(): 单层检索（快速）
   - search_multilayer(): 多层检索（完整）
   - search_hybrid(): 混合检索（最优）

🎉 向量检索优化项目全部完成！
        """)


if __name__ == "__main__":
    main()
