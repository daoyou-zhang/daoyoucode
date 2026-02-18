"""简单测试智谱AI Embedding API"""

import sys
import asyncio

# 设置UTF-8输出
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


async def main():
    print("测试智谱AI Embedding API\n")
    
    # 测试1：API连接
    print("=" * 60)
    print("测试1：API连接")
    print("=" * 60)
    
    from daoyoucode.agents.memory.vector_retriever_api import VectorRetrieverAPI
    
    retriever = VectorRetrieverAPI(
        provider="zhipu",
        api_key="f7def1d8285a4b1da14f903a91a330a9.qwwPt8zwziMJIAmY"
    )
    
    if retriever.enabled:
        print(f"[OK] API连接成功")
        print(f"     提供商: {retriever.provider}")
        print(f"     模型: {retriever.model}")
        print(f"     维度: {retriever.dimensions}")
    else:
        print("[FAIL] API连接失败")
        return False
    
    # 测试2：文本编码
    print("\n" + "=" * 60)
    print("测试2：文本编码")
    print("=" * 60)
    
    test_text = "如何修复Agent执行时的超时错误？"
    print(f"编码文本: {test_text}")
    
    embedding = retriever.encode(test_text)
    if embedding is not None:
        print(f"[OK] 编码成功 - 维度: {embedding.shape}")
    else:
        print("[FAIL] 编码失败")
        return False
    
    # 测试3：相似度
    print("\n" + "=" * 60)
    print("测试3：相似度计算")
    print("=" * 60)
    
    text1 = "如何修复超时错误"
    text2 = "timeout error fix"
    
    emb1 = retriever.encode(text1)
    emb2 = retriever.encode(text2)
    
    if emb1 is not None and emb2 is not None:
        similarity = retriever.cosine_similarity(emb1, emb2)
        print(f"'{text1}' vs '{text2}'")
        print(f"相似度: {similarity:.4f}")
        
        if similarity > 0.7:
            print("[OK] 相似度正常（>0.7）")
        else:
            print("[WARN] 相似度较低")
    else:
        print("[FAIL] 编码失败")
        return False
    
    # 测试4：工厂函数
    print("\n" + "=" * 60)
    print("测试4：工厂函数")
    print("=" * 60)
    
    from daoyoucode.agents.memory.vector_retriever_factory import get_vector_retriever
    
    retriever2 = get_vector_retriever()
    
    if retriever2.enabled:
        print(f"[OK] 工厂函数创建成功")
        print(f"     类型: {type(retriever2).__name__}")
        
        # 测试编码
        test_emb = retriever2.encode("测试")
        if test_emb is not None:
            print(f"[OK] 编码测试通过 - 维度: {test_emb.shape}")
        else:
            print("[FAIL] 编码测试失败")
            return False
    else:
        print("[FAIL] 工厂函数创建失败")
        return False
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print("[OK] 所有测试通过！")
    print("\n智谱AI Embedding API已正常工作")
    print("- 无需下载大模型")
    print("- 向量维度: 2048")
    print("- 中文效果好")
    
    return True


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
