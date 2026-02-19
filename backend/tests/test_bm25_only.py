"""
单独测试BM25功能
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
logging.basicConfig(level=logging.INFO, format='%(message)s')

from daoyoucode.agents.memory.codebase_index import CodebaseIndex


def test_bm25():
    """测试BM25关键词匹配"""
    print("\n" + "="*60)
    print("测试BM25关键词匹配")
    print("="*60)
    
    # 创建索引
    index = CodebaseIndex(Path("."))
    
    # 确保索引已构建
    if len(index.chunks) == 0:
        print(f"\n索引为空，正在构建...")
        index.build_index()
    
    print(f"\n索引信息:")
    print(f"  Chunks数量: {len(index.chunks)}")
    
    # 初始化BM25缓存
    print(f"\n初始化BM25缓存...")
    try:
        index._init_bm25_cache()
        print(f"  ✅ BM25缓存初始化成功")
        print(f"  平均文档长度: {index._avg_doc_len:.1f}")
        print(f"  文档频率词数: {len(index._doc_freq)}")
    except Exception as e:
        print(f"  ❌ BM25缓存初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 测试BM25打分
    query = "execute"
    print(f"\n查询: {query}")
    
    try:
        # 计算前10个chunks的BM25分数
        scored = []
        for i, chunk in enumerate(index.chunks[:10]):
            score = index._bm25_score(query, chunk)
            scored.append((chunk, score))
            print(f"  Chunk {i}: {chunk['name']:30s} BM25={score:.4f}")
        
        # 找到所有非零分数
        all_scored = []
        for chunk in index.chunks:
            score = index._bm25_score(query, chunk)
            if score > 0:
                all_scored.append((chunk, score))
        
        print(f"\n找到 {len(all_scored)} 个匹配的chunks")
        
        if len(all_scored) > 0:
            # 排序并显示top-5
            all_scored.sort(key=lambda x: x[1], reverse=True)
            print(f"\nTop-5 BM25分数:")
            for chunk, score in all_scored[:5]:
                print(f"  {chunk['name']:30s} {score:.4f}")
            return True
        else:
            print(f"\n⚠️ 没有找到匹配的chunks")
            return False
    
    except Exception as e:
        print(f"\n❌ BM25打分失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_bm25()
    if success:
        print("\n✅ BM25测试通过")
    else:
        print("\n❌ BM25测试失败")
    
    sys.exit(0 if success else 1)
