"""
测试智谱AI Embedding API

验证：
1. API连接是否正常
2. 文本编码是否成功
3. 相似度计算是否正确
4. 与CodebaseIndex集成是否正常
"""

import asyncio
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_api_connection():
    """测试1：API连接"""
    print("=" * 60)
    print("测试1：智谱AI API连接")
    print("=" * 60)
    
    try:
        from daoyoucode.agents.memory.vector_retriever_api import VectorRetrieverAPI
        
        print("🔄 创建VectorRetrieverAPI实例（智谱AI）...")
        retriever = VectorRetrieverAPI(
            provider="zhipu",
            api_key="f7def1d8285a4b1da14f903a91a330a9.qwwPt8zwziMJIAmY"
        )
        
        if retriever.enabled:
            print(f"✅ API连接成功")
            print(f"   提供商: {retriever.provider}")
            print(f"   模型: {retriever.model}")
            print(f"   维度: {retriever.dimensions}")
            return True
        else:
            print("❌ API连接失败")
            return False
    
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_encode():
    """测试2：文本编码"""
    print("\n" + "=" * 60)
    print("测试2：文本编码")
    print("=" * 60)
    
    try:
        from daoyoucode.agents.memory.vector_retriever_api import VectorRetrieverAPI
        
        retriever = VectorRetrieverAPI(
            provider="zhipu",
            api_key="f7def1d8285a4b1da14f903a91a330a9.qwwPt8zwziMJIAmY"
        )
        
        if not retriever.enabled:
            print("⚠️ API未启用，跳过测试")
            return False
        
        # 测试编码
        test_texts = [
            "如何修复Agent执行时的超时错误？",
            "Python函数定义",
            "class BaseAgent"
        ]
        
        print("\n编码测试:")
        for text in test_texts:
            print(f"  编码: '{text}'")
            embedding = retriever.encode(text)
            if embedding is not None:
                print(f"  ✅ 成功 - 向量维度: {embedding.shape}")
            else:
                print(f"  ❌ 失败")
                return False
        
        return True
    
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_similarity():
    """测试3：相似度计算"""
    print("\n" + "=" * 60)
    print("测试3：相似度计算")
    print("=" * 60)
    
    try:
        from daoyoucode.agents.memory.vector_retriever_api import VectorRetrieverAPI
        
        retriever = VectorRetrieverAPI(
            provider="zhipu",
            api_key="f7def1d8285a4b1da14f903a91a330a9.qwwPt8zwziMJIAmY"
        )
        
        if not retriever.enabled:
            print("⚠️ API未启用，跳过测试")
            return False
        
        # 测试相似度
        test_pairs = [
            ("如何修复超时错误", "timeout error fix"),
            ("Python函数", "Python function"),
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
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_factory():
    """测试4：工厂函数"""
    print("\n" + "=" * 60)
    print("测试4：工厂函数")
    print("=" * 60)
    
    try:
        from daoyoucode.agents.memory.vector_retriever_factory import get_vector_retriever
        
        print("🔄 使用工厂函数创建retriever...")
        retriever = get_vector_retriever()
        
        print(f"\n类型: {type(retriever).__name__}")
        print(f"启用: {retriever.enabled}")
        
        if retriever.enabled:
            stats = retriever.get_stats()
            print(f"统计信息:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
            
            # 测试编码
            print("\n测试编码:")
            embedding = retriever.encode("测试文本")
            if embedding is not None:
                print(f"✅ 编码成功 - 维度: {embedding.shape}")
                return True
            else:
                print("❌ 编码失败")
                return False
        else:
            print("❌ Retriever未启用")
            return False
    
    except Exception as e:
        print(f"❌ 测试失败: {e}")
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
        
        print("🔄 构建索引（使用智谱AI embedding）...")
        chunk_count = index.build_index(force=True)
        
        print(f"✅ 索引构建完成: {chunk_count} chunks")
        
        # 检查是否使用了向量
        if index.embeddings is not None:
            print(f"✅ 向量已生成: {index.embeddings.shape}")
        else:
            print("⚠️ 未生成向量（可能使用关键词回退）")
            return False
        
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
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主函数"""
    print("测试智谱AI Embedding API\n")
    
    results = []
    
    # 测试1：API连接
    result = await test_api_connection()
    results.append(("api_connection", result))
    
    if not result:
        print("\n❌ API连接失败，请检查:")
        print("   1. API密钥是否正确")
        print("   2. 网络连接是否正常")
        print("   3. API服务是否可用")
        return False
    
    # 测试2：文本编码
    result = await test_encode()
    results.append(("encode", result))
    
    # 测试3：相似度计算
    result = await test_similarity()
    results.append(("similarity", result))
    
    # 测试4：工厂函数
    result = await test_factory()
    results.append(("factory", result))
    
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
        print("\n🎉 所有测试通过！智谱AI Embedding API已正常工作")
        print("\n优势:")
        print("  ✅ 无需下载大模型")
        print("  ✅ 启动速度快")
        print("  ✅ 向量维度高（2048维）")
        print("  ✅ 中文效果好")
        print("\n下一步:")
        print("  1. 使用 index.build_index(force=True) 重建索引")
        print("  2. 享受更精准的语义检索")
    else:
        print("\n⚠️ 部分测试失败")
    
    return all_passed


if __name__ == "__main__":
    asyncio.run(main())
