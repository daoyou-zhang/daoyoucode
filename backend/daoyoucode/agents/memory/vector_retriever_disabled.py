"""
禁用的向量检索器（空对象模式）

当向量检索被禁用时，返回这个空对象而不是 None，
避免到处检查 None 的防御性代码。
"""

import logging
from typing import Optional, List
import numpy as np

logger = logging.getLogger(__name__)


class DisabledVectorRetriever:
    """
    禁用的向量检索器（空对象模式）
    
    提供与 VectorRetriever 相同的接口，但所有操作都是空操作。
    这样调用方不需要检查 None，代码更简洁。
    """
    
    def __init__(self):
        self.enabled = False
        self.model = None
    
    def encode(self, text: str) -> Optional[np.ndarray]:
        """
        编码文本（空操作）
        
        Returns:
            None - 表示没有向量
        """
        return None
    
    def encode_batch(self, texts: List[str]) -> Optional[np.ndarray]:
        """
        批量编码（空操作）
        
        Returns:
            None - 表示没有向量
        """
        return None
    
    def __repr__(self):
        return "DisabledVectorRetriever(enabled=False)"
