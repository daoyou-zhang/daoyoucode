"""
向量检索器工厂

根据配置自动选择使用本地模型或API
"""

from typing import Optional, Union
import logging
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)


def get_vector_retriever(config_path: Optional[str] = None):
    """
    获取向量检索器（自动选择本地或API）
    
    Args:
        config_path: 配置文件路径（可选）
    
    Returns:
        VectorRetriever 或 VectorRetrieverAPI 实例
    """
    # 读取配置
    if config_path is None:
        # 修正路径：从当前文件向上3级到backend，再到config
        config_path = Path(__file__).parent.parent.parent.parent / "config" / "embedding_config.yaml"
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        logger.warning(f"⚠️ 无法读取配置文件: {e}")
        logger.info("   使用默认配置（API模式 - 智谱AI）")
        config = {
            "mode": "api",
            "api": {
                "provider": "zhipu",
                "api_key": "f7def1d8285a4b1da14f903a91a330a9.qwwPt8zwziMJIAmY"  # 使用配置中的密钥
            }
        }
    
    mode = config.get("mode", "api")
    
    if mode == "api":
        # 使用API模式
        from .vector_retriever_api import VectorRetrieverAPI
        
        api_config = config.get("api", {})
        provider = api_config.get("provider", "zhipu")
        api_key = api_config.get("api_key")
        
        # 如果配置中没有api_key，尝试从环境变量读取
        if not api_key:
            import os
            if provider == "zhipu":
                api_key = os.getenv("ZHIPU_API_KEY")
            elif provider == "openai":
                api_key = os.getenv("OPENAI_API_KEY")
            elif provider == "qwen":
                api_key = os.getenv("DASHSCOPE_API_KEY")
        
        logger.info(f"🔄 使用API模式: {provider}")
        
        retriever = VectorRetrieverAPI(
            provider=provider,
            api_key=api_key
        )
        
        if not retriever.enabled:
            logger.warning("⚠️ API模式初始化失败，回退到关键词匹配")
        
        return retriever
    
    else:
        # 使用本地模式
        from .vector_retriever import VectorRetriever
        
        local_config = config.get("local", {})
        model_name = local_config.get("model_name", "paraphrase-multilingual-MiniLM-L12-v2")
        
        logger.info(f"🔄 使用本地模式: {model_name}")
        
        retriever = VectorRetriever(model_name=model_name)
        
        if not retriever.enabled:
            logger.warning("⚠️ 本地模式初始化失败，回退到关键词匹配")
        
        return retriever


# 全局单例
_retriever_instance = None

def get_retriever_singleton(config_path: Optional[str] = None):
    """获取向量检索器单例"""
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = get_vector_retriever(config_path)
    return _retriever_instance
