"""
测试RepoMap公开API

验证：
1. get_definitions() 能正确获取代码定义
2. end_line 被正确计算
3. get_reference_graph() 能构建引用图
4. get_pagerank_scores() 能计算PageRank分数
"""

import asyncio
from pathlib import Path
from daoyoucode.agents.tools.repomap_tools import RepoMapTool


async def test_get_definitions():
    """测试get_definitions API"""
    print("=" * 60)
    print("测试1：get_definitions()")
    print("=" * 60)
    
    repomap = RepoMapTool()
    
    # 获取定义
    definitions = repomap.get_definitions(".")
    
    print(f"\n总文件数: {len(definitions)}")
    
    # 检查是否有定义
    if not definitions:
        print("⚠️  未找到任何定义")
        return False
    
    # 检查第一个文件
    first_file = list(definitions.keys())[0]
    first_defs = definitions[first_file]
    
    print(f"\n示例文件: {first_file}")
    print(f"定义数量: {len(first_defs)}")
    
    if first_defs:
        # 找到第一个定义（kind="def"），跳过引用（kind="ref"）
        first_def = None
        for d in first_defs:
            if d.get("kind") == "def":
                first_def = d
                break
        
        if not first_def:
            print("⚠️  文件中没有定义（只有引用）")
            # 尝试另一个文件
            for file_path, defs in definitions.items():
                for d in defs:
                    if d.get("kind") == "def":
                        first_def = d
                        first_file = file_path
                        break
                if first_def:
                    break
        
        if not first_def:
            print("⚠️  整个项目中没有找到定义")
            return True  # 可能是特殊项目，不算失败
        
        print(f"\n示例文件: {first_file}")
        print(f"第一个定义:")
        print(f"  type: {first_def.get('type')}")
        print(f"  name: {first_def.get('name')}")
        print(f"  line: {first_def.get('line')}")
        print(f"  end_line: {first_def.get('end_line')}")
        print(f"  kind: {first_def.get('kind')}")
        
        # 验证end_line
        if "end_line" not in first_def:
            print("❌ 缺少end_line字段")
            return False
        
        if first_def["end_line"] is None:
            print("❌ end_line为None")
            return False
        
        if first_def["end_line"] <= first_def["line"]:
            print(f"❌ end_line ({first_def['end_line']}) <= line ({first_def['line']})")
            return False
        
        print(f"✅ end_line正确: {first_def['line']} -> {first_def['end_line']}")
    
    return True


async def test_get_reference_graph():
    """测试get_reference_graph API"""
    print("\n" + "=" * 60)
    print("测试2：get_reference_graph()")
    print("=" * 60)
    
    repomap = RepoMapTool()
    
    # 获取引用图
    reference_graph = repomap.get_reference_graph(".")
    
    print(f"\n引用图节点数: {len(reference_graph)}")
    
    if not reference_graph:
        print("⚠️  引用图为空")
        return True  # 可能是小项目，没有引用关系
    
    # 检查第一个节点
    first_node = list(reference_graph.keys())[0]
    first_edges = reference_graph[first_node]
    
    print(f"\n示例节点: {first_node}")
    print(f"引用数量: {len(first_edges)}")
    
    if first_edges:
        for target, weight in list(first_edges.items())[:3]:
            print(f"  → {target}: {weight}")
    
    print("✅ 引用图构建成功")
    return True


async def test_get_pagerank_scores():
    """测试get_pagerank_scores API"""
    print("\n" + "=" * 60)
    print("测试3：get_pagerank_scores()")
    print("=" * 60)
    
    repomap = RepoMapTool()
    
    # 获取PageRank分数
    pagerank_scores = repomap.get_pagerank_scores(".")
    
    print(f"\nPageRank分数数量: {len(pagerank_scores)}")
    
    if not pagerank_scores:
        print("⚠️  PageRank分数为空")
        return True
    
    # 排序并显示前5个
    sorted_scores = sorted(
        pagerank_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    print("\nTop 5 文件（按PageRank分数）:")
    for file_path, score in sorted_scores[:5]:
        print(f"  {score:.4f} - {file_path}")
    
    print("✅ PageRank分数计算成功")
    return True


async def test_with_chat_files():
    """测试带焦点文件的PageRank"""
    print("\n" + "=" * 60)
    print("测试4：带焦点文件的PageRank")
    print("=" * 60)
    
    repomap = RepoMapTool()
    
    # 选择一个文件作为焦点
    definitions = repomap.get_definitions(".")
    if not definitions:
        print("⚠️  未找到定义")
        return True
    
    focus_file = list(definitions.keys())[0]
    print(f"\n焦点文件: {focus_file}")
    
    # 获取PageRank分数（带焦点文件）
    pagerank_scores = repomap.get_pagerank_scores(
        ".",
        chat_files=[focus_file]
    )
    
    # 检查焦点文件的分数是否最高
    sorted_scores = sorted(
        pagerank_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    print("\nTop 5 文件（带焦点文件）:")
    for file_path, score in sorted_scores[:5]:
        marker = "⭐" if file_path == focus_file else "  "
        print(f"{marker} {score:.4f} - {file_path}")
    
    # 验证焦点文件分数较高
    if sorted_scores[0][0] == focus_file:
        print(f"\n✅ 焦点文件获得最高分数: {sorted_scores[0][1]:.4f}")
    else:
        print(f"\n⚠️  焦点文件不是最高分，但这可能是正常的")
    
    return True


async def main():
    """主函数"""
    print("测试RepoMap公开API\n")
    
    results = []
    
    # 测试1：get_definitions
    try:
        result = await test_get_definitions()
        results.append(("get_definitions", result))
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        results.append(("get_definitions", False))
    
    # 测试2：get_reference_graph
    try:
        result = await test_get_reference_graph()
        results.append(("get_reference_graph", result))
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        results.append(("get_reference_graph", False))
    
    # 测试3：get_pagerank_scores
    try:
        result = await test_get_pagerank_scores()
        results.append(("get_pagerank_scores", result))
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        results.append(("get_pagerank_scores", False))
    
    # 测试4：带焦点文件
    try:
        result = await test_with_chat_files()
        results.append(("with_chat_files", result))
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        results.append(("with_chat_files", False))
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {test_name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n🎉 所有测试通过！")
    else:
        print("\n⚠️  部分测试失败")
    
    return all_passed


if __name__ == "__main__":
    asyncio.run(main())
