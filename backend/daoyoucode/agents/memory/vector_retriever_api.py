"""
向量检索器 - API版本

使用远程API进行embedding，无需下载模型

支持的API：
- OpenAI Embeddings API
- 通义千问 Embeddings API
- 其他兼容OpenAI格式的API

优势：
- 无需下载大模型
- 更快的启动速度
- 更好的embedding质量
- 自动扩展，无需GPU
"""

from typing import List, Dict, Tuple, Optional, Any
import logging
import httpx
import json
import os

logger = logging.getLogger(__name__)


class VectorRetrieverAPI:
    """
    向量检索器（API版本）
    
    功能：
    1. 通过API将文本转换为向量
    2. 计算向量相似度
    3. 检索最相关的内容
    
    支持的API提供商：
    - openai: OpenAI Embeddings API
    - qwen: 通义千问 Embeddings API
    - custom: 自定义兼容OpenAI格式的API
    """
    
    # API配置
    API_CONFIGS = {
        "openai": {
            "base_url": "https://api.openai.com/v1",
            "model": "text-embedding-3-small",
            "dimensions": 1536,
            "env_key": "OPENAI_API_KEY"
        },
        "qwen": {
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "model": "text-embedding-v3",
            "dimensions": 1024,
            "env_key": "DASHSCOPE_API_KEY"
        },
        "zhipu": {
            "base_url": "https://open.bigmodel.cn/api/paas/v4",
            "model": "embedding-3",
            "dimensions": 2048,
            "env_key": "ZHIPU_API_KEY"
        }
    }
    
    def __init__(
        self,
        provider: str = "openai",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        """
        初始化向量检索器（API版本）
        
        Args:
            provider: API提供商 ("openai", "qwen", "custom")
            api_key: API密钥（如果为None，从环境变量读取）
            base_url: API基础URL（可选，覆盖默认值）
            model: 模型名称（可选，覆盖默认值）
        """
        self.provider = provider
        self.enabled = False
        
        # 获取配置
        if provider in self.API_CONFIGS:
            config = self.API_CONFIGS[provider].copy()
            self.base_url = base_url or config["base_url"]
            self.model = model or config["model"]
            self.dimensions = config["dimensions"]
            
            # 获取API密钥
            if api_key:
                self.api_key = api_key
            else:
                env_key = config["env_key"]
                self.api_key = os.getenv(env_key)
                if not self.api_key:
                    logger.warning(
                        f"⚠️ 未找到API密钥: {env_key}\n"
                        f"   请设置环境变量或在配置中提供api_key"
                    )
                    return
        else:
            # 自定义配置
            if not all([base_url, model, api_key]):
                logger.warning(
                    "⚠️ 自定义provider需要提供: base_url, model, api_key"
                )
                return
            
            self.base_url = base_url
            self.model = model
            self.api_key = api_key
            self.dimensions = 1536  # 默认维度
        
        # 创建HTTP客户端
        self.client = httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            timeout=30.0
        )
        
        self.enabled = True
        logger.info(f"✅ 向量检索已启用（API模式）")
        logger.info(f"   提供商: {self.provider}")
        logger.info(f"   模型: {self.model}")
        logger.info(f"   维度: {self.dimensions}")
    
    def encode(self, text: str) -> Optional['numpy.ndarray']:
        """
        将文本转换为向量（通过API）
        
        Args:
            text: 文本
        
        Returns:
            向量（numpy数组），如果失败返回None
        """
        if not self.enabled:
            return None
        
        try:
            import numpy as np
            
            # 调用API
            response = self.client.post(
                "/embeddings",
                json={
                    "model": self.model,
                    "input": text
                }
            )
            
            if response.status_code != 200:
                logger.error(
                    f"❌ API请求失败: {response.status_code}\n"
                    f"   响应: {response.text}"
                )
                return None
            
            # 解析响应
            data = response.json()
            embedding = data["data"][0]["embedding"]
            
            return np.array(embedding, dtype=np.float32)
        
        except Exception as e:
            logger.error(f"❌ 文本编码失败: {e}")
            return None
    
    def encode_batch(self, texts: List[str], batch_size: int = 100) -> Optional[List['numpy.ndarray']]:
        """
        批量编码文本（通过API）
        
        Args:
            texts: 文本列表
            batch_size: 批次大小
        
        Returns:
            向量列表，如果失败返回None
        """
        if not self.enabled:
            return None
        
        try:
            import numpy as np
            
            embeddings = []
            
            # 分批处理
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                # 调用API
                response = self.client.post(
                    "/embeddings",
                    json={
                        "model": self.model,
                        "input": batch
                    }
                )
                
                if response.status_code != 200:
                    logger.error(
                        f"❌ API请求失败: {response.status_code}\n"
                        f"   响应: {response.text}"
                    )
                    return None
                
                # 解析响应
                data = response.json()
                batch_embeddings = [
                    np.array(item["embedding"], dtype=np.float32)
                    for item in data["data"]
                ]
                embeddings.extend(batch_embeddings)
                
                logger.info(f"   已编码: {len(embeddings)}/{len(texts)}")
            
            return embeddings
        
        except Exception as e:
            logger.error(f"❌ 批量编码失败: {e}")
            return None
    
    def cosine_similarity(self, vec1, vec2) -> float:
        """
        计算余弦相似度
        
        Args:
            vec1: 向量1
            vec2: 向量2
        
        Returns:
            相似度分数（0-1）
        """
        try:
            import numpy as np
            
            # 归一化
            vec1_norm = vec1 / np.linalg.norm(vec1)
            vec2_norm = vec2 / np.linalg.norm(vec2)
            
            # 余弦相似度
            similarity = np.dot(vec1_norm, vec2_norm)
            
            return float(similarity)
        except Exception as e:
            logger.error(f"❌ 计算相似度失败: {e}")
            return 0.0
    
    async def find_relevant_history(
        self,
        current_message: str,
        full_history: List[Dict],
        limit: int = 3,
        threshold: float = 0.5
    ) -> List[Tuple[int, float]]:
        """
        使用向量检索查找相关历史
        
        Args:
            current_message: 当前消息
            full_history: 完整历史
            limit: 最多返回多少条
            threshold: 相似度阈值（0-1）
        
        Returns:
            [(索引, 相似度分数), ...]
        """
        if not self.enabled:
            logger.debug("向量检索未启用，返回空结果")
            return []
        
        try:
            # 1. 编码当前消息
            current_embedding = self.encode(current_message)
            if current_embedding is None:
                return []
            
            # 2. 编码所有历史消息并计算相似度
            similarities = []
            
            for idx, item in enumerate(full_history):
                user_msg = item.get('user', '')
                if not user_msg:
                    continue
                
                # 编码历史消息
                msg_embedding = self.encode(user_msg)
                if msg_embedding is None:
                    continue
                
                # 计算相似度
                similarity = self.cosine_similarity(current_embedding, msg_embedding)
                
                # 只保留超过阈值的
                if similarity >= threshold:
                    similarities.append((idx, similarity))
                    logger.debug(
                        f"  🎯 向量匹配第{idx+1}轮: {user_msg[:30]}... "
                        f"(相似度: {similarity:.3f})"
                    )
            
            # 3. 按相似度排序，返回top N
            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities[:limit]
        
        except Exception as e:
            logger.error(f"❌ 向量检索失败: {e}", exc_info=True)
            return []
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            'enabled': self.enabled,
            'provider': self.provider if self.enabled else None,
            'model': self.model if self.enabled else None,
            'dimensions': self.dimensions if self.enabled else None,
            'mode': 'api'
        }
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'client'):
            self.client.close()


# 全局单例
_vector_retriever_api = None

def get_vector_retriever_api(
    provider: str = "openai",
    api_key: Optional[str] = None,
    **kwargs
) -> VectorRetrieverAPI:
    """获取向量检索器单例（API版本）"""
    global _vector_retriever_api
    if _vector_retriever_api is None:
        _vector_retriever_api = VectorRetrieverAPI(
            provider=provider,
            api_key=api_key,
            **kwargs
        )
    return _vector_retriever_api
