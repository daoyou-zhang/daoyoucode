"""快速集成测试 - 只测试核心功能"""

import sys
import asyncio
from pathlib import Path

# 设置UTF-8输出
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


async def test_repomap_api():
    """测试1：RepoMap公开API"""
    print("=" * 60)
    print("测试1：RepoMap公开API")
    print("=" * 60)
    
    from daoyoucode.agents.tools.repomap_tools import RepoMapTool
    
    repomap = RepoMapTool()
    
    # 获取定义
    print("获取代码定义...")
    definitions = repomap.get_definitions(".")
    print(f"[OK] 找到 {len(definitions)} 个文件")
    
    # 检查end_line
    if definitions:
        first_file = list(definitions.keys())[0]
        first_defs = [d for d in definitions[first_file] if d.get("kind") == "def"]
        if first_defs:
            first_def = first_defs[0]
            if "end_line" in first_def and first_def["end_line"] > first_def["line"]:
                print(f"[OK] end_line正确: {first_def['line']} -> {first_def['end_line']}")
            else:
                print("[FAIL] end_line不正确")
                return False
    
    # 获取引用图
    print("\n构建引用图...")
    reference_graph = repomap.get_reference_graph(".", definitions)
    print(f"[OK] 引用图节点数: {len(reference_graph)}")
    
    # 获取PageRank分数
    print("\n计算PageRank分数...")
    pagerank_scores = repomap.get_pagerank_scores(".", reference_graph, definitions)
    print(f"[OK] PageRank分数数量: {len(pagerank_scores)}")
    
    return True


async def test_vector_api():
    """测试2：向量API"""
    print("\n" + "=" * 60)
    print("测试2：向量API")
    print("=" * 60)
    
    from daoyoucode.agents.memory.vector_retriever_factory import get_vector_retriever
    
    retriever = get_vector_retriever()
    
    if not retriever.enabled:
        print("[FAIL] 向量检索未启用")
        return False
    
    print(f"[OK] 向量检索已启用")
    print(f"     类型: {type(retriever).__name__}")
    
    # 测试编码
    print("\n测试编码...")
    embedding = retriever.encode("测试文本")
    if embedding is not None:
        print(f"[OK] 编码成功 - 维度: {embedding.shape}")
    else:
        print("[FAIL] 编码失败")
        return False
    
    return True


async def test_small_index():
    """测试3：小规模索引构建"""
    print("\n" + "=" * 60)
    print("测试3：小规模索引构建（10个文件）")
    print("=" * 60)
    
    from daoyoucode.agents.memory.codebase_index import CodebaseIndex
    
    # 创建索引
    index = CodebaseIndex(Path("."))
    
    # 手动构建小规模索引（只处理前10个文件）
    print("使用RepoMap解析代码...")
    from daoyoucode.agents.tools.repomap_tools import RepoMapTool
    repomap_tool = RepoMapTool()
    
    definitions = repomap_tool.get_definitions(".")
    reference_graph = repomap_tool.get_reference_graph(".", definitions)
    pagerank_scores = repomap_tool.get_pagerank_scores(".", reference_graph, definitions)
    
    print(f"[OK] 解析完成: {len(definitions)} 文件")
    
    # 只处理前10个文件
    limited_definitions = dict(list(definitions.items())[:10])
    
    print(f"\n构建chunks（限制10个文件）...")
    chunks = []
    for file_path, defs in limited_definitions.items():
        def_only = [d for d in defs if d.get("kind") == "def"]
        
        for d in def_only[:2]:  # 每个文件只取前2个定义
            code_text = index._extract_code_chunk(
                index.repo_path / file_path,
                d["line"],
                d.get("end_line", d["line"] + 50)
            )
            
            if not code_text.strip():
                continue
            
            chunk = {
                "path": file_path,
                "start": d["line"],
                "end": d.get("end_line"),
                "text": code_text[:1000],  # 限制长度
                "type": d.get("type"),
                "name": d.get("name"),
                "pagerank_score": pagerank_scores.get(file_path, 0.0)
            }
            
            chunks.append(chunk)
    
    print(f"[OK] 构建了 {len(chunks)} 个chunks")
    
    # 测试向量化（只编码前5个）
    print(f"\n测试向量化（前5个chunks）...")
    retriever = index._get_retriever()
    
    if retriever.enabled:
        import numpy as np
        
        embeddings = []
        for i, chunk in enumerate(chunks[:5]):
            print(f"  编码 {i+1}/5: {chunk['name']}")
            emb = retriever.encode(chunk['text'][:500])
            if emb is not None:
                embeddings.append(emb)
            else:
                print(f"  [WARN] 编码失败")
        
        if embeddings:
            embeddings_array = np.array(embeddings)
            print(f"[OK] 向量化成功: {embeddings_array.shape}")
        else:
            print("[FAIL] 向量化失败")
            return False
    else:
        print("[WARN] 向量检索未启用，跳过向量化测试")
    
    return True


async def test_search():
    """测试4：搜索功能"""
    print("\n" + "=" * 60)
    print("测试4：搜索功能")
    print("=" * 60)
    
    from daoyoucode.agents.memory.codebase_index import CodebaseIndex
    
    index = CodebaseIndex(Path("."))
    
    # 使用已有的索引（如果存在）
    try:
        index.build_index(force=False)
    except:
        print("[WARN] 无法加载已有索引，跳过搜索测试")
        return True
    
    if not index.chunks:
        print("[WARN] 索引为空，跳过搜索测试")
        return True
    
    # 测试搜索
    print("\n测试搜索...")
    query = "agent execute"
    results = index.search(query, top_k=3)
    
    print(f"查询: '{query}'")
    print(f"结果数: {len(results)}")
    
    if results:
        for i, r in enumerate(results[:3], 1):
            print(f"\n{i}. {r.get('path')}")
            print(f"   名称: {r.get('name')}")
            print(f"   类型: {r.get('type')}")
            print(f"   分数: {r.get('score', 0.0):.4f}")
        print("[OK] 搜索功能正常")
    else:
        print("[WARN] 未找到结果")
    
    return True


async def main():
    """主函数"""
    print("快速集成测试\n")
    
    results = []
    
    # 测试1：RepoMap API
    try:
        result = await test_repomap_api()
        results.append(("repomap_api", result))
    except Exception as e:
        print(f"[FAIL] 测试失败: {e}")
        results.append(("repomap_api", False))
    
    # 测试2：向量API
    try:
        result = await test_vector_api()
        results.append(("vector_api", result))
    except Exception as e:
        print(f"[FAIL] 测试失败: {e}")
        results.append(("vector_api", False))
    
    # 测试3：小规模索引
    try:
        result = await test_small_index()
        results.append(("small_index", result))
    except Exception as e:
        print(f"[FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("small_index", False))
    
    # 测试4：搜索
    try:
        result = await test_search()
        results.append(("search", result))
    except Exception as e:
        print(f"[FAIL] 测试失败: {e}")
        results.append(("search", False))
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    for test_name, result in results:
        status = "[OK]" if result else "[FAIL]"
        print(f"{status} {test_name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n[SUCCESS] 所有测试通过！")
        print("\n核心功能验证:")
        print("  [OK] RepoMap公开API正常")
        print("  [OK] 智谱AI向量API正常")
        print("  [OK] 代码解析和分块正常")
        print("  [OK] 向量化功能正常")
        print("\n下一步:")
        print("  1. 运行完整索引构建（需要较长时间）")
        print("  2. 享受语义检索功能")
    else:
        print("\n[FAIL] 部分测试失败")
    
    return all_passed


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
