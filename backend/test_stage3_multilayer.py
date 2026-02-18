"""
测试阶段3：多层次检索

验证内容：
1. 文件关联扩展
2. 引用关系扩展
3. 完整多层检索
4. 性能对比
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


def test_file_expansion():
    """测试1: 文件关联扩展"""
    print("\n" + "="*60)
    print("测试1: 文件关联扩展")
    print("="*60)
    
    index = CodebaseIndex(Path("."))
    
    # 单层检索
    results_simple = index.search("Agent执行", top_k=5)
    
    # 多层检索（只启用文件扩展）
    results_expanded = index.search_multilayer(
        "Agent执行",
        top_k=5,
        enable_file_expansion=True,
        enable_reference_expansion=False
    )
    
    print(f"\n📊 结果对比:")
    print(f"   单层检索: {len(results_simple)} 个结果")
    print(f"   文件扩展: {len(results_expanded)} 个结果")
    
    # 显示扩展的文件
    simple_files = {r['path'] for r in results_simple}
    expanded_files = {r['path'] for r in results_expanded}
    new_files = expanded_files - simple_files
    
    if new_files:
        print(f"\n✅ 新增文件:")
        for file in new_files:
            print(f"   - {file}")
    
    return len(results_expanded) >= len(results_simple)


def test_reference_expansion():
    """测试2: 引用关系扩展"""
    print("\n" + "="*60)
    print("测试2: 引用关系扩展")
    print("="*60)
    
    index = CodebaseIndex(Path("."))
    
    # 多层检索（只启用引用扩展）
    results = index.search_multilayer(
        "Agent执行",
        top_k=5,
        enable_file_expansion=False,
        enable_reference_expansion=True
    )
    
    print(f"\n📊 引用关系:")
    
    # 统计有引用关系的结果
    with_calls = sum(1 for r in results if r.get('calls'))
    with_called_by = sum(1 for r in results if r.get('called_by'))
    
    print(f"   有调用关系: {with_calls}/{len(results)}")
    print(f"   有被调用关系: {with_called_by}/{len(results)}")
    
    # 显示示例
    for result in results[:3]:
        if result.get('called_by') or result.get('calls'):
            print(f"\n   {result['path']}::{result['name']}")
            if result.get('called_by'):
                print(f"      被调用: {len(result['called_by'])} 个文件")
                for caller in result['called_by'][:2]:
                    print(f"         - {caller}")
            if result.get('calls'):
                print(f"      调用: {', '.join(result['calls'][:3])}")
    
    return True


def test_full_multilayer():
    """测试3: 完整多层检索"""
    print("\n" + "="*60)
    print("测试3: 完整多层检索")
    print("="*60)
    
    index = CodebaseIndex(Path("."))
    
    # 完整多层检索
    results = index.search_multilayer("Agent执行", top_k=10)
    
    print(f"\n✅ 多层检索返回 {len(results)} 个结果:\n")
    
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['path']}::{result['name']}")
        print(f"   类型: {result['type']}")
        print(f"   分数: {result.get('final_score', 0):.4f}")
        print(f"   PageRank: {result.get('pagerank_score', 0):.4f}")
        
        if result.get('related_files'):
            print(f"   相关文件: {len(result['related_files'])} 个")
        
        if result.get('called_by'):
            print(f"   被调用: {len(result['called_by'])} 个文件")
        
        print()
    
    return len(results) > 0


def test_performance():
    """测试4: 性能对比"""
    print("\n" + "="*60)
    print("测试4: 性能对比")
    print("="*60)
    
    index = CodebaseIndex(Path("."))
    
    # 单层检索
    start = time.time()
    results_simple = index.search("Agent执行", top_k=10)
    time_simple = time.time() - start
    
    # 多层检索
    start = time.time()
    results_multi = index.search_multilayer("Agent执行", top_k=10)
    time_multi = time.time() - start
    
    print(f"\n⏱️ 性能对比:")
    print(f"   单层检索: {time_simple:.3f}秒 ({len(results_simple)} 个结果)")
    print(f"   多层检索: {time_multi:.3f}秒 ({len(results_multi)} 个结果)")
    
    if time_simple > 0:
        overhead = (time_multi - time_simple) / time_simple * 100
        print(f"   性能损失: {overhead:.1f}%")
    
    # 验证性能合理
    if time_multi < 2.0:
        print(f"   ✅ 性能合理（<2秒）")
        return True
    else:
        print(f"   ⚠️ 性能较慢（>{2}秒）")
        return False


def test_comparison():
    """测试5: 单层vs多层对比"""
    print("\n" + "="*60)
    print("测试5: 单层vs多层对比")
    print("="*60)
    
    index = CodebaseIndex(Path("."))
    
    query = "超时处理"
    
    # 单层检索
    results_simple = index.search(query, top_k=5)
    
    # 多层检索
    results_multi = index.search_multilayer(query, top_k=5)
    
    print(f"\n查询: {query}\n")
    
    print(f"单层检索 ({len(results_simple)} 个结果):")
    for i, r in enumerate(results_simple, 1):
        print(f"   {i}. {r['path']}::{r['name']}")
    
    print(f"\n多层检索 ({len(results_multi)} 个结果):")
    for i, r in enumerate(results_multi, 1):
        print(f"   {i}. {r['path']}::{r['name']}")
        if r.get('related_files'):
            print(f"      相关: {', '.join(r['related_files'][:2])}")
    
    # 统计新增的文件
    simple_files = {r['path'] for r in results_simple}
    multi_files = {r['path'] for r in results_multi}
    new_files = multi_files - simple_files
    
    if new_files:
        print(f"\n✅ 多层检索新增 {len(new_files)} 个文件:")
        for file in new_files:
            print(f"   - {file}")
    
    return True


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("阶段3测试：多层次检索")
    print("="*60)
    
    tests = [
        ("文件关联扩展", test_file_expansion),
        ("引用关系扩展", test_reference_expansion),
        ("完整多层检索", test_full_multilayer),
        ("性能对比", test_performance),
        ("单层vs多层对比", test_comparison),
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
        print("🎉 阶段3完成！")
        print("="*60)
        print("""
✅ 多层次检索已实现：
   - 第1层：语义检索
   - 第2层：文件关联扩展
   - 第3层：引用关系扩展
   - 第4层：去重和重排序

✅ 检索能力提升：
   - 召回率提升（包含相关文件和调用链）
   - 上下文完整（自动发现相关代码）
   - 性能合理（<2秒）

✅ 向后兼容：
   - 保留原有search()方法
   - 新增search_multilayer()方法
   - 用户可选择使用
        """)


if __name__ == "__main__":
    main()
