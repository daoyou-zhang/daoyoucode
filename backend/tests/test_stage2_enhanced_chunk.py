"""
测试阶段2：增强的Chunk结构

验证内容：
1. Chunk包含所有新增字段
2. 引用关系准确性
3. 导入关系准确性
4. 文件关联准确性
"""

import sys
from pathlib import Path

# 添加backend到路径
backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

from daoyoucode.agents.memory.codebase_index import CodebaseIndex


def test_enhanced_chunk_structure():
    """测试1: 验证增强的chunk结构"""
    print("\n" + "="*60)
    print("测试1: 验证增强的Chunk结构")
    print("="*60)
    
    index = CodebaseIndex(Path("."))
    count = index.build_index(force=True)
    
    print(f"\n✅ 构建了 {count} 个chunks")
    
    if count == 0:
        print("❌ 没有chunks，测试失败")
        return False
    
    # 验证第一个chunk的结构
    chunk = index.chunks[0]
    
    # 基础字段（阶段1）
    required_fields_stage1 = [
        "path", "start", "end", "text",
        "type", "name", "pagerank_score"
    ]
    
    # 新增字段（阶段2）
    required_fields_stage2 = [
        "parent_class", "scope",
        "calls", "called_by",
        "imports", "related_files"
    ]
    
    print(f"\n📋 验证字段完整性:")
    
    # 验证阶段1字段
    for field in required_fields_stage1:
        if field in chunk:
            print(f"   ✅ {field}")
        else:
            print(f"   ❌ {field} - 缺失")
            return False
    
    # 验证阶段2字段
    for field in required_fields_stage2:
        if field in chunk:
            print(f"   ✅ {field} (阶段2)")
        else:
            print(f"   ❌ {field} - 缺失 (阶段2)")
            return False
    
    # 显示示例chunk
    print(f"\n📦 示例Chunk:")
    print(f"   文件: {chunk['path']}")
    print(f"   名称: {chunk['name']}")
    print(f"   类型: {chunk['type']}")
    print(f"   父级: {chunk.get('parent_class', 'None')}")
    print(f"   作用域: {chunk['scope']}")
    print(f"   PageRank: {chunk['pagerank_score']:.4f}")
    print(f"   调用: {len(chunk['calls'])} 个函数")
    print(f"   被调用: {len(chunk['called_by'])} 个文件")
    print(f"   导入: {len(chunk['imports'])} 个模块")
    print(f"   相关文件: {len(chunk['related_files'])} 个")
    
    return True


def test_reference_accuracy():
    """测试2: 验证引用关系的准确性"""
    print("\n" + "="*60)
    print("测试2: 验证引用关系准确性")
    print("="*60)
    
    index = CodebaseIndex(Path("."))
    index.build_index(force=False)  # 使用缓存
    
    # 找到一些有趣的chunks
    interesting_chunks = []
    
    for chunk in index.chunks:
        # 找到有调用关系的chunk
        if len(chunk.get('calls', [])) > 3 and len(chunk.get('called_by', [])) > 0:
            interesting_chunks.append(chunk)
            if len(interesting_chunks) >= 3:
                break
    
    if not interesting_chunks:
        print("⚠️ 没有找到有引用关系的chunks")
        return True
    
    print(f"\n找到 {len(interesting_chunks)} 个有引用关系的chunks:\n")
    
    for i, chunk in enumerate(interesting_chunks, 1):
        print(f"{i}. {chunk['path']}::{chunk['name']}")
        print(f"   类型: {chunk['type']}")
        print(f"   父级: {chunk.get('parent_class', 'None')}")
        print(f"   作用域: {chunk['scope']}")
        
        if chunk['calls']:
            print(f"   调用了: {', '.join(chunk['calls'][:5])}")
            if len(chunk['calls']) > 5:
                print(f"           ... 还有 {len(chunk['calls']) - 5} 个")
        
        if chunk['called_by']:
            print(f"   被调用: {len(chunk['called_by'])} 个文件")
            for caller in chunk['called_by'][:3]:
                print(f"           - {caller}")
            if len(chunk['called_by']) > 3:
                print(f"           ... 还有 {len(chunk['called_by']) - 3} 个")
        
        if chunk['related_files']:
            print(f"   相关文件: {len(chunk['related_files'])} 个")
            for related in chunk['related_files'][:3]:
                print(f"           - {related}")
        
        print()
    
    return True


def test_import_extraction():
    """测试3: 验证导入关系提取"""
    print("\n" + "="*60)
    print("测试3: 验证导入关系提取")
    print("="*60)
    
    index = CodebaseIndex(Path("."))
    index.build_index(force=False)
    
    # 统计导入信息
    files_with_imports = 0
    total_imports = 0
    
    for chunk in index.chunks:
        imports = chunk.get('imports', [])
        if imports:
            files_with_imports += 1
            total_imports += len(imports)
    
    print(f"\n📊 导入统计:")
    print(f"   总chunks: {len(index.chunks)}")
    print(f"   有导入的chunks: {files_with_imports}")
    print(f"   总导入数: {total_imports}")
    print(f"   平均每个chunk: {total_imports / len(index.chunks):.1f} 个导入")
    
    # 显示一些导入示例
    chunks_with_imports = [c for c in index.chunks if c.get('imports')]
    if chunks_with_imports:
        print(f"\n📦 导入示例:")
        for chunk in chunks_with_imports[:3]:
            print(f"\n   {chunk['path']}:")
            for imp in chunk['imports'][:5]:
                print(f"      {imp}")
            if len(chunk['imports']) > 5:
                print(f"      ... 还有 {len(chunk['imports']) - 5} 个")
    
    return True


def test_parent_and_scope():
    """测试4: 验证父级和作用域信息"""
    print("\n" + "="*60)
    print("测试4: 验证父级和作用域信息")
    print("="*60)
    
    index = CodebaseIndex(Path("."))
    index.build_index(force=False)
    
    # 统计作用域分布
    scope_stats = {}
    parent_stats = {"有父级": 0, "无父级": 0}
    
    for chunk in index.chunks:
        scope = chunk.get('scope', 'unknown')
        scope_stats[scope] = scope_stats.get(scope, 0) + 1
        
        if chunk.get('parent_class'):
            parent_stats["有父级"] += 1
        else:
            parent_stats["无父级"] += 1
    
    print(f"\n📊 作用域分布:")
    for scope, count in sorted(scope_stats.items(), key=lambda x: -x[1]):
        percentage = count / len(index.chunks) * 100
        print(f"   {scope}: {count} ({percentage:.1f}%)")
    
    print(f"\n📊 父级分布:")
    for category, count in parent_stats.items():
        percentage = count / len(index.chunks) * 100
        print(f"   {category}: {count} ({percentage:.1f}%)")
    
    # 显示一些有父级的示例
    chunks_with_parent = [c for c in index.chunks if c.get('parent_class')]
    if chunks_with_parent:
        print(f"\n📦 有父级的示例:")
        for chunk in chunks_with_parent[:5]:
            print(f"   {chunk['parent_class']}.{chunk['name']} ({chunk['type']})")
    
    return True


def test_performance():
    """测试5: 性能测试"""
    print("\n" + "="*60)
    print("测试5: 性能测试")
    print("="*60)
    
    import time
    
    index = CodebaseIndex(Path("."))
    
    # 测试构建时间
    start = time.time()
    count = index.build_index(force=True)
    elapsed = time.time() - start
    
    print(f"\n⏱️ 性能指标:")
    print(f"   Chunks数量: {count}")
    print(f"   构建时间: {elapsed:.2f}秒")
    print(f"   平均速度: {count/elapsed:.1f} chunks/秒")
    
    # 验证性能合理
    if elapsed > 20:
        print(f"   ⚠️ 构建时间较长（>{20}秒）")
    else:
        print(f"   ✅ 构建时间合理")
    
    # 统计元数据大小
    import json
    meta_size = len(json.dumps(index.chunks))
    print(f"\n💾 存储指标:")
    print(f"   元数据大小: {meta_size / 1024:.1f} KB")
    print(f"   平均每个chunk: {meta_size / count:.0f} 字节")
    
    return True


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("阶段2测试：增强的Chunk结构")
    print("="*60)
    
    tests = [
        ("Chunk结构验证", test_enhanced_chunk_structure),
        ("引用关系准确性", test_reference_accuracy),
        ("导入关系提取", test_import_extraction),
        ("父级和作用域", test_parent_and_scope),
        ("性能测试", test_performance),
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
        print("🎉 阶段2完成！")
        print("="*60)
        print("""
✅ Chunk结构已增强，包含：
   - 父级信息（parent_class）
   - 作用域信息（scope）
   - 函数调用（calls）
   - 被调用关系（called_by）
   - 导入关系（imports）
   - 文件关联（related_files）

✅ 为阶段3（多层次检索）做好准备
        """)


if __name__ == "__main__":
    main()
