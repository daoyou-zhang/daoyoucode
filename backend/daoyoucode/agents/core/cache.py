"""
简单缓存层

提供带TTL的内存缓存，减少文件I/O
"""

import time
import logging
from typing import Any, Optional, Dict, Callable
from dataclasses import dataclass
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """缓存条目"""
    value: Any
    timestamp: float
    ttl: int  # 秒
    
    def is_expired(self) -> bool:
        """是否过期"""
        return time.time() - self.timestamp > self.ttl


class SimpleCache:
    """
    简单的内存缓存（带TTL）
    
    特性：
    1. 支持TTL（过期时间）
    2. 线程安全
    3. 自动清理过期条目
    4. 支持命名空间
    5. 统计信息
    
    使用场景：
    - 用户画像缓存（TTL: 1小时）
    - 对话摘要缓存（TTL: 30分钟）
    - 会话历史缓存（TTL: 5分钟）
    """
    
    def __init__(self, default_ttl: int = 300, max_size: int = 1000):
        """
        初始化缓存
        
        Args:
            default_ttl: 默认TTL（秒），默认5分钟
            max_size: 最大缓存条目数
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = Lock()
        self._default_ttl = default_ttl
        self._max_size = max_size
        
        # 统计信息
        self._stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'evictions': 0,
        }
        
        logger.info(f"缓存已初始化: default_ttl={default_ttl}s, max_size={max_size}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            default: 默认值（如果不存在或过期）
        
        Returns:
            缓存值或默认值
        """
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                
                # 检查是否过期
                if entry.is_expired():
                    # 过期，删除
                    del self._cache[key]
                    self._stats['misses'] += 1
                    logger.debug(f"缓存过期: {key}")
                    return default
                
                # 命中
                self._stats['hits'] += 1
                logger.debug(f"缓存命中: {key}")
                return entry.value
            
            # 未命中
            self._stats['misses'] += 1
            logger.debug(f"缓存未命中: {key}")
            return default
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: TTL（秒），如果为None则使用默认TTL
        """
        with self._lock:
            # 检查是否需要清理
            if len(self._cache) >= self._max_size:
                self._evict_oldest()
            
            # 设置缓存
            self._cache[key] = CacheEntry(
                value=value,
                timestamp=time.time(),
                ttl=ttl if ttl is not None else self._default_ttl
            )
            
            self._stats['sets'] += 1
            logger.debug(f"缓存设置: {key}, ttl={ttl or self._default_ttl}s")
    
    def delete(self, key: str) -> bool:
        """
        删除缓存值
        
        Args:
            key: 缓存键
        
        Returns:
            是否删除成功
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._stats['deletes'] += 1
                logger.debug(f"缓存删除: {key}")
                return True
            return False
    
    def clear(self):
        """清空缓存"""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logger.info(f"缓存已清空: {count} 条目")
    
    def get_or_set(
        self,
        key: str,
        factory: Callable[[], Any],
        ttl: Optional[int] = None
    ) -> Any:
        """
        获取缓存值，如果不存在则调用factory生成并缓存
        
        Args:
            key: 缓存键
            factory: 生成值的函数
            ttl: TTL（秒）
        
        Returns:
            缓存值
        """
        # 先尝试获取
        value = self.get(key)
        if value is not None:
            return value
        
        # 不存在，生成并缓存
        value = factory()
        if value is not None:
            self.set(key, value, ttl)
        
        return value
    
    def _evict_oldest(self):
        """驱逐最老的条目"""
        if not self._cache:
            return
        
        # 找到最老的条目
        oldest_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].timestamp
        )
        
        del self._cache[oldest_key]
        self._stats['evictions'] += 1
        logger.debug(f"缓存驱逐: {oldest_key}")
    
    def cleanup_expired(self) -> int:
        """
        清理所有过期条目
        
        Returns:
            清理的条目数
        """
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                logger.info(f"清理过期缓存: {len(expired_keys)} 条目")
            
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = (
                self._stats['hits'] / total_requests * 100
                if total_requests > 0 else 0
            )
            
            return {
                **self._stats,
                'size': len(self._cache),
                'max_size': self._max_size,
                'hit_rate': f"{hit_rate:.1f}%",
                'total_requests': total_requests,
            }
    
    def __len__(self) -> int:
        """缓存大小"""
        return len(self._cache)
    
    def __contains__(self, key: str) -> bool:
        """是否包含键（不检查过期）"""
        return key in self._cache


class NamespacedCache:
    """
    带命名空间的缓存
    
    用于隔离不同类型的缓存数据
    """
    
    def __init__(self, cache: SimpleCache, namespace: str):
        """
        初始化命名空间缓存
        
        Args:
            cache: 底层缓存实例
            namespace: 命名空间
        """
        self._cache = cache
        self._namespace = namespace
    
    def _make_key(self, key: str) -> str:
        """生成带命名空间的键"""
        return f"{self._namespace}:{key}"
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取缓存值"""
        return self._cache.get(self._make_key(key), default)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """设置缓存值"""
        self._cache.set(self._make_key(key), value, ttl)
    
    def delete(self, key: str) -> bool:
        """删除缓存值"""
        return self._cache.delete(self._make_key(key))
    
    def get_or_set(
        self,
        key: str,
        factory: Callable[[], Any],
        ttl: Optional[int] = None
    ) -> Any:
        """获取或设置缓存值"""
        return self._cache.get_or_set(self._make_key(key), factory, ttl)


# 全局缓存实例
_global_cache: Optional[SimpleCache] = None


def get_cache() -> SimpleCache:
    """
    获取全局缓存实例（单例）
    
    Returns:
        SimpleCache实例
    """
    global _global_cache
    
    if _global_cache is None:
        _global_cache = SimpleCache(
            default_ttl=300,  # 5分钟
            max_size=1000
        )
        logger.info("全局缓存已创建")
    
    return _global_cache


def get_namespaced_cache(namespace: str) -> NamespacedCache:
    """
    获取命名空间缓存
    
    Args:
        namespace: 命名空间名称
    
    Returns:
        NamespacedCache实例
    """
    cache = get_cache()
    return NamespacedCache(cache, namespace)


# 预定义的命名空间缓存
def get_profile_cache() -> NamespacedCache:
    """获取用户画像缓存（TTL: 1小时）"""
    return get_namespaced_cache("profile")


def get_summary_cache() -> NamespacedCache:
    """获取摘要缓存（TTL: 30分钟）"""
    return get_namespaced_cache("summary")


def get_history_cache() -> NamespacedCache:
    """获取历史缓存（TTL: 5分钟）"""
    return get_namespaced_cache("history")


def get_preference_cache() -> NamespacedCache:
    """获取偏好缓存（TTL: 1小时）"""
    return get_namespaced_cache("preference")
