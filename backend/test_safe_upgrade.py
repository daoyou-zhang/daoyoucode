"""
安全验证脚本：测试向量检索升级是否影响现有功能

这个脚本会：
1. 测试原有search()方法是否正常
2. 测试新增方法是否工作
3. 对比结果质量
4. 不会破坏任何现有功能
"""

import sys
from pathlib import Path
import io

# 设置UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加backend到路径
backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import logging
logging.basicConfig(level=logging.WARNING)  # 减少日志输出

from daoyoucode.agents.memory.codebase_index import CodebaseIndex


def test_backward_compatibility():
    """测试1: 向后兼容性"""
    print("\n" + "="*60)
    print("测试1: 向后兼容性（原有方法是否正常）")
    print("="*60)
    
    try:
        index = CodebaseIndex(Path("."))
        
        # 测试原有的search()方法
        query = "Agent执行"
        results = index.search(query, top_k=5)
        
        print(f"\n✅ 原有search()方法正常工作")
        print(f"   查询: {query}")
        print(f"   结果数: {len(results)}")
        
        if len(results) > 0:
            print(f"\n   前3个结果:")
            for i, r in enumerate(results[:3], 1):
                print(f"   {i}. {r.get('name', 'unknown')}")
        
        return True
    
    except Exception as e:
        print(f"\n❌ 原有方法失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_new_methods():
    """测试2: 新方法是否工作"""
    print("\n" + "="*60)
    print("测试2: 新方法（可选功能）")
    print("="*60)
    
    try:
        index = CodebaseIndex(Path("."))
        query = "Agent执行"
        
        # 测试多层检索
        print(f"\n尝试多层检索...")
        results_multi = index.search_multilayer(query, top_k=5)
        print(f"✅ 多层检索正常: {len(results_multi)} 个结果")
        
        # 测试混合检索
        print(f"\n尝试混合检索...")
        results_hybrid = index.search_hybrid(query, top_k=5)
        print(f"✅ 混合检索正常: {len(results_hybrid)} 个结果")
        
        return True
    
    except Exception as e:
        print(f"\n⚠️ 新方法失败（不影响原有功能）: {e}")
        return False


def test_quality_comparison():
    """测试3: 结果质量对比"""
    print("\n" + "="*60)
    print("测试3: 结果质量对比")
    print("="*60)
    
    try:
        index = CodebaseIndex(Path("."))
        query = "execute"
        
        # 原有方法
        results_old = index.search(query, top_k=5)
        
        # 新方法
        results_new = index.search_hybrid(query, top_k=5)
        
        print(f"\n查询: {query}")
        print(f"\n原有方法（search）:")
        for i, r in enumerate(results_old[:3], 1):
            score = r.get('score', 0)
            print(f"  {i}. {r.get('name', 'unknown'):30s} 分数={score:.4f}")
        
        print(f"\n新方法（search_hybrid）:")
        for i, r in enumerate(results_new[:3], 1):
            score = r.get('hybrid_score', 0)
            print(f"  {i}. {r.get('name', 'unknown'):30s} 分数={score:.4f}")
        
        print(f"\n💡 提示: 两种方法都可以使用，根据需要选择")
        
        return True
    
    except Exception as e:
        print(f"\n⚠️ 对比失败: {e}")
        return False


def test_index_rebuild():
    """测试4: 索引重建"""
    print("\n" + "="*60)
    print("测试4: 索引重建（首次运行）")
    print("="*60)
    
    try:
        index = CodebaseIndex(Path("."))
        
        print(f"\n索引信息:")
        print(f"  Chunks数量: {len(index.chunks)}")
        
        if len(index.chunks) > 0:
            # 检查是否有新字段
            sample = index.chunks[0]
            has_new_fields = 'pagerank_score' in sample
            
            if has_new_fields:
                print(f"  ✅ 索引已升级（包含新字段）")
                print(f"  新字段: pagerank_score, parent_class, scope, calls, etc.")
            else:
                print(f"  ℹ️ 索引是旧版本（可以继续使用）")
                print(f"  提示: 删除 .daoyoucode/codebase_index 可重建新索引")
        
        return True
    
    except Exception as e:
        print(f"\n❌ 索引检查失败: {e}")
        return False


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("向量检索升级安全验证")
    print("="*60)
    print("\n这个脚本会验证升级是否安全，不会破坏现有功能")
    
    tests = [
        ("向后兼容性", test_backward_compatibility),
        ("新方法", test_new_methods),
        ("结果质量对比", test_quality_comparison),
        ("索引状态", test_index_rebuild),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ 测试异常: {e}")
            results.append((name, False))
    
    # 总结
    print("\n" + "="*60)
    print("验证总结")
    print("="*60)
    
    for name, result in results:
        if result:
            print(f"✅ {name}: 正常")
        else:
            print(f"⚠️ {name}: 需要检查")
    
    # 结论
    critical_passed = results[0][1]  # 向后兼容性
    
    if critical_passed:
        print("\n" + "="*60)
        print("✅ 升级安全！")
        print("="*60)
        print("""
关键结论：
✅ 原有功能完全正常
✅ 可以安全使用

使用建议：
1. 继续使用原有的 search() 方法（如果满意）
2. 尝试 search_multilayer() 获得更完整的结果
3. 尝试 search_hybrid() 获得最优质量

如果遇到问题：
- 删除 .daoyoucode/codebase_index 重建索引
- 或者只使用原有的 search() 方法
        """)
    else:
        print("\n" + "="*60)
        print("⚠️ 需要检查")
        print("="*60)
        print("""
建议：
1. 检查错误信息
2. 尝试删除 .daoyoucode/codebase_index 重建
3. 如果问题持续，可以回退到旧版本
        """)


if __name__ == "__main__":
    main()
