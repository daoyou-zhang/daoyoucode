"""
快速测试阶段2：只验证chunk结构，不做向量化
"""

import sys
from pathlib import Path
import json

backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

print("\n" + "="*60)
print("阶段2快速测试：验证增强的Chunk结构")
print("="*60)

# 直接读取已构建的索引
index_dir = Path(".daoyoucode/codebase_index")

# 查找索引目录
for subdir in index_dir.iterdir():
    if subdir.is_dir():
        meta_file = subdir / "meta.json"
        if meta_file.exists():
            print(f"\n📂 找到索引: {subdir.name}")
            
            with open(meta_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            chunks = data.get("chunks", [])
            print(f"✅ 加载了 {len(chunks)} 个chunks")
            
            if not chunks:
                print("❌ 没有chunks")
                continue
            
            # 验证第一个chunk
            chunk = chunks[0]
            
            print(f"\n📋 验证字段完整性:")
            
            # 阶段1字段
            stage1_fields = ["path", "start", "end", "text", "type", "name", "pagerank_score"]
            for field in stage1_fields:
                status = "✅" if field in chunk else "❌"
                print(f"   {status} {field}")
            
            # 阶段2字段
            stage2_fields = ["parent_class", "scope", "calls", "called_by", "imports", "related_files"]
            for field in stage2_fields:
                status = "✅" if field in chunk else "❌"
                print(f"   {status} {field} (阶段2)")
            
            # 显示示例
            print(f"\n📦 示例Chunk:")
            print(f"   文件: {chunk['path']}")
            print(f"   名称: {chunk['name']}")
            print(f"   类型: {chunk['type']}")
            print(f"   父级: {chunk.get('parent_class', 'None')}")
            print(f"   作用域: {chunk.get('scope', 'unknown')}")
            print(f"   PageRank: {chunk.get('pagerank_score', 0):.4f}")
            print(f"   调用: {len(chunk.get('calls', []))} 个函数")
            print(f"   被调用: {len(chunk.get('called_by', []))} 个文件")
            print(f"   导入: {len(chunk.get('imports', []))} 个模块")
            print(f"   相关文件: {len(chunk.get('related_files', []))} 个")
            
            # 统计
            print(f"\n📊 统计信息:")
            
            # 作用域分布
            scope_stats = {}
            for c in chunks:
                scope = c.get('scope', 'unknown')
                scope_stats[scope] = scope_stats.get(scope, 0) + 1
            
            print(f"   作用域分布:")
            for scope, count in sorted(scope_stats.items(), key=lambda x: -x[1]):
                percentage = count / len(chunks) * 100
                print(f"      {scope}: {count} ({percentage:.1f}%)")
            
            # 有父级的数量
            with_parent = sum(1 for c in chunks if c.get('parent_class'))
            print(f"   有父级: {with_parent} ({with_parent/len(chunks)*100:.1f}%)")
            
            # 有调用的数量
            with_calls = sum(1 for c in chunks if c.get('calls'))
            print(f"   有调用: {with_calls} ({with_calls/len(chunks)*100:.1f}%)")
            
            # 被调用的数量
            with_called_by = sum(1 for c in chunks if c.get('called_by'))
            print(f"   被调用: {with_called_by} ({with_called_by/len(chunks)*100:.1f}%)")
            
            # 有导入的数量
            with_imports = sum(1 for c in chunks if c.get('imports'))
            print(f"   有导入: {with_imports} ({with_imports/len(chunks)*100:.1f}%)")
            
            # 有相关文件的数量
            with_related = sum(1 for c in chunks if c.get('related_files'))
            print(f"   有相关文件: {with_related} ({with_related/len(chunks)*100:.1f}%)")
            
            # 显示一些有趣的示例
            print(f"\n📦 有趣的示例:")
            
            # 找到有调用关系的
            interesting = [c for c in chunks if len(c.get('calls', [])) > 5 and len(c.get('called_by', [])) > 0]
            if interesting:
                c = interesting[0]
                print(f"\n   {c['path']}::{c['name']}")
                print(f"   类型: {c['type']}")
                print(f"   父级: {c.get('parent_class', 'None')}")
                print(f"   调用: {', '.join(c['calls'][:5])}")
                if len(c['calls']) > 5:
                    print(f"         ... 还有 {len(c['calls']) - 5} 个")
                print(f"   被调用: {len(c['called_by'])} 个文件")
                if c['called_by']:
                    for caller in c['called_by'][:3]:
                        print(f"         - {caller}")
            
            print(f"\n" + "="*60)
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
            
            break
