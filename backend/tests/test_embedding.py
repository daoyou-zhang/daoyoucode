"""
测试Embedding功能

验证：
1. sentence-transformers是否正确安装
2. 模型是否能正确加载
3. 文本编码是否正常
4. 相似度计算是否正确
5. 向量检索是否可用
"""

import asyncio
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_import():
    """测试1：导入依赖"""
    print("=" * 60)
    print("测试1：导入依赖")
    print("=" * 60)
    
    try:
        import sentence_transformers
        print(f"✅ sentence-transformers 版本: {sentence_transformers.__version__}")
    except ImportError as e:
        print(f"❌ sentence-transformers 未安装: {e}")
        print("💡 安装命令: pip install sentence-transformers")
        return False
    
    try:
        import numpy as np
        print(f"✅ numpy 版本: {np.__version__}")
    except ImportError as e:
        print(f"❌ numpy 未安装: {e}")
        return False
    
    try:
        import torch
        print(f"✅ torch 版本: {torch.__version__}")
    except ImportError as e:
        print(f"❌ torch 未安装: {e}")
        return False
    
    return True


async def test_vector_retriever():
    """测试2：VectorRetriever初始化"""
    print("\n" + "=" * 60)
    print("测试2：VectorRetriever初始化")
    print("=" * 60)
    
    try:
        from daoyoucode.agents.memory.vector_retriever import VectorRetriever
        
        print("🔄 创建VectorRetriever实例...")
        retriever = VectorRetriever()
        
        if retriever.enabled:
            print(f"✅ 向量检索已启用")
            print(f"   模型: {retriever.model_name}")
            
            # 获取统计信息
            stats = retriever.get_stats()
            print(f"   维度: {stats.get('embedding_dim', 'unknown')}")
            
            return True
        else:
            print("❌ 向量检索未启用")
            return False
    
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_encode():
    """测试3：文本编码"""
    print("\n" + "=" * 60)
    print("测试3：文本编码")
    print("=" * 60)
    
    try:
        from daoyoucode.agents.memory.vector_retriever import get_vector_retriever
        
        retriever = get_vector_retriever()
        
        if not retriever.enabled:
            print("⚠️ 向量检索未启用，跳过测试")
            return False
        
        # 测试编码
        test_texts = [
            "如何修复Agent执行时的超时错误？",
            "Agent timeout error fix",
            "Python函数定义",
            "class BaseAgent"
        ]
        
        print("\n编码测试:")
        for text in test_texts:
            embedding = retriever.encode(text)
            if embedding is not None:
                print(f"✅ '{text}' → 向量维度: {embedding.shape}")
            else:
                print(f"❌ '{text}' → 编码失败")
                return False
        
        return True
    
    except Exception as e:
        print(f"❌ 编码测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_similarity():
    """测试4：相似度计算"""
    print("\n" + "=" * 60)
    print("测试4：相似度计算")
    print("=" * 60)
    
    try:
        from daoyoucode.agents.memory.vector_retriever import get_vector_retriever
        
        retriever = get_vector_retriever()
        
        if not retriever.enabled:
            print("⚠️ 向量检索未启用，跳过测试")
            return False
        
        # 测试相似度
        test_pairs = [
            ("如何修复超时错误", "timeout error fix"),
            ("Python函数", "Python function"),
            ("猫咪", "小猫"),
            ("苹果", "香蕉"),
            ("编程", "做饭")
        ]
        
        print("\n相似度测试:")
        for text1, text2 in test_pairs:
            emb1 = retriever.encode(text1)
            emb2 = retriever.encode(text2)
            
            if emb1 is not None and emb2 is not None:
                similarity = retriever.cosine_similarity(emb1, emb2)
                print(f"  '{text1}' vs '{text2}': {similarity:.4f}")
            else:
                print(f"❌ 编码失败")
                return False
        
        return True
    
    except Exception as e:
        print(f"❌ 相似度测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_codebase_index():
    """测试5：CodebaseIndex集成"""
    print("\n" + "=" * 60)
    print("测试5：CodebaseIndex集成")
    print("=" * 60)
    
    try:
        from pathlib import Path
        from daoyoucode.agents.memory.codebase_index import CodebaseIndex
        
        print("🔄 创建CodebaseIndex...")
        index = CodebaseIndex(Path("."))
        
        print("🔄 构建索引（强制重建）...")
        chunk_count = index.build_index(force=True)
        
        print(f"✅ 索引构建完成: {chunk_count} chunks")
        
        # 检查是否使用了向量
        if index.embeddings is not None:
            print(f"✅ 向量已生成: {index.embeddings.shape}")
        else:
            print("⚠️ 未生成向量（可能使用关键词回退）")
        
        # 测试检索
        print("\n🔍 测试检索:")
        query = "agent execute timeout"
        results = index.search(query, top_k=3)
        
        print(f"   查询: '{query}'")
        print(f"   结果数: {len(results)}")
        
        for i, result in enumerate(results[:3], 1):
            print(f"\n   {i}. {result.get('path')}")
            print(f"      名称: {result.get('name')}")
            print(f"      类型: {result.get('type')}")
            print(f"      分数: {result.get('score', 0.0):.4f}")
        
        return True
    
    except Exception as e:
        print(f"❌ CodebaseIndex测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主函数"""
    print("测试Embedding功能\n")
    
    results = []
    
    # 测试1：导入依赖
    result = await test_import()
    results.append(("import", result))
    
    if not result:
        print("\n❌ 依赖未安装，请先安装:")
        print("   pip install sentence-transformers numpy torch")
        return False
    
    # 测试2：VectorRetriever初始化
    result = await test_vector_retriever()
    results.append(("vector_retriever", result))
    
    if not result:
        print("\n❌ VectorRetriever初始化失败")
        return False
    
    # 测试3：文本编码
    result = await test_encode()
    results.append(("encode", result))
    
    # 测试4：相似度计算
    result = await test_similarity()
    results.append(("similarity", result))
    
    # 测试5：CodebaseIndex集成
    result = await test_codebase_index()
    results.append(("codebase_index", result))
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {test_name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n🎉 所有测试通过！Embedding功能已正常启用")
        print("\n下一步:")
        print("  1. 重新构建代码索引: index.build_index(force=True)")
        print("  2. 享受更精准的语义检索")
    else:
        print("\n⚠️ 部分测试失败")
        print("\n故障排除:")
        print("  1. 确保已安装依赖: pip install -r requirements.txt")
        print("  2. 检查网络连接（首次使用会下载模型）")
        print("  3. 查看上面的错误信息")
    
    return all_passed


if __name__ == "__main__":
    asyncio.run(main())
