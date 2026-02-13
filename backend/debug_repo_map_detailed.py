"""
详细调试repo_map - 查看定义过滤问题
"""

import sys
from pathlib import Path
import asyncio

sys.path.insert(0, str(Path(__file__).parent))

async def debug():
    from daoyoucode.agents.tools.repomap_tools import RepoMapTool
    
    tool = RepoMapTool()
    
    # 初始化缓存
    repo_path = Path('.').resolve()
    tool._init_cache(repo_path)
    
    # 扫描仓库
    print("扫描仓库...")
    definitions = tool._scan_repository(repo_path)
    
    print(f"\n总文件数: {len(definitions)}")
    
    # 统计定义类型
    total_defs = 0
    total_refs = 0
    files_with_defs = 0
    
    for file_path, defs in definitions.items():
        def_count = len([d for d in defs if d.get('kind') == 'def'])
        ref_count = len([d for d in defs if d.get('kind') == 'ref'])
        
        total_defs += def_count
        total_refs += ref_count
        
        if def_count > 0:
            files_with_defs += 1
    
    print(f"总定义数: {total_defs}")
    print(f"总引用数: {total_refs}")
    print(f"有定义的文件数: {files_with_defs}")
    
    # 显示前10个有定义的文件
    print(f"\n前10个有定义的文件:")
    count = 0
    for file_path, defs in definitions.items():
        file_defs = [d for d in defs if d.get('kind') == 'def']
        if file_defs and count < 10:
            print(f"\n{file_path}:")
            for d in file_defs[:3]:
                print(f"  - {d['type']} {d['name']} (line {d['line']})")
            count += 1
    
    # 构建引用图
    print(f"\n构建引用图...")
    graph = tool._build_reference_graph(definitions, repo_path)
    print(f"图节点数: {len(graph)}")
    print(f"图边数: {sum(len(targets) for targets in graph.values())}")
    
    # PageRank
    print(f"\nPageRank排序...")
    ranked = tool._pagerank(graph, [], [])
    print(f"排序结果数: {len(ranked)}")
    if ranked:
        print(f"前5个文件:")
        for file_path, score in ranked[:5]:
            print(f"  {file_path}: {score:.4f}")
    
    # 生成地图
    print(f"\n生成地图...")
    repo_map = tool._generate_map(ranked, definitions, max_tokens=2000)
    print(f"地图长度: {len(repo_map)}")
    print(f"\n地图内容（前500字符）:")
    print("-"*60)
    print(repo_map[:500])
    print("-"*60)
    
    # 关闭数据库
    if tool.cache_db:
        tool.cache_db.close()

if __name__ == '__main__':
    asyncio.run(debug())
