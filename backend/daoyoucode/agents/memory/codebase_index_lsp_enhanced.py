"""
LSP增强的代码库索引（阶段1优化）

在现有的混合检索基础上，集成LSP类型信息，提升检索准确率。
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
import re

from .codebase_index import CodebaseIndex

logger = logging.getLogger(__name__)


class LSPEnhancedCodebaseIndex(CodebaseIndex):
    """LSP增强的代码库索引"""
    
    def __init__(self, repo_path: Path):
        super().__init__(repo_path)
        self._lsp_cache = {}  # 缓存LSP结果
    
    async def search_with_lsp(
        self,
        query: str,
        top_k: int = 10,
        enable_lsp: bool = True
    ) -> List[Dict[str, Any]]:
        """
        LSP增强的语义检索
        
        Args:
            query: 查询字符串
            top_k: 返回结果数量
            enable_lsp: 是否启用LSP增强（默认True）
        
        Returns:
            增强的检索结果
        """
        # 1. 使用现有的混合检索获取候选结果（获取更多候选）
        candidates = self.search_hybrid(
            query,
            top_k=top_k * 2,  # 获取2倍候选，后续用LSP重排序
            enable_multilayer=True,
            enable_adaptive_weights=True
        )
        
        if not candidates:
            return []
        
        logger.info(f"🔍 LSP增强检索: {len(candidates)} 个候选")
        
        # 2. 如果不启用LSP，直接返回
        if not enable_lsp:
            return candidates[:top_k]
        
        # 3. 使用LSP增强每个候选
        enhanced_candidates = await self._enhance_with_lsp(candidates, query)
        
        # 4. 重新排序
        reranked = self._rerank_with_lsp(enhanced_candidates, query)
        
        # 5. 返回top-k
        return reranked[:top_k]
    
    async def _enhance_with_lsp(
        self,
        candidates: List[Dict],
        query: str
    ) -> List[Dict]:
        """
        使用LSP增强候选结果
        
        为每个候选添加：
        - 类型信息
        - 符号信息
        - 引用计数
        """
        from ..tools.lsp_tools import with_lsp_client
        
        enhanced = []
        
        for chunk in candidates:
            file_path = str(self.repo_path / chunk['path'])
            
            # 检查缓存
            cache_key = f"{chunk['path']}:{chunk['start']}"
            if cache_key in self._lsp_cache:
                chunk.update(self._lsp_cache[cache_key])
                enhanced.append(chunk)
                continue
            
            # 获取LSP信息
            lsp_info = await self._get_lsp_info(file_path, chunk)
            
            # 缓存结果
            self._lsp_cache[cache_key] = lsp_info
            
            # 合并到chunk
            chunk.update(lsp_info)
            enhanced.append(chunk)
        
        return enhanced
    
    async def _get_lsp_info(
        self,
        file_path: str,
        chunk: Dict
    ) -> Dict[str, Any]:
        """
        获取LSP信息（按需启动LSP服务器）
        
        Returns:
            {
                'has_lsp_info': bool,
                'symbol_count': int,
                'has_type_annotations': bool,
                'reference_count': int,
                'lsp_symbols': List[Dict]
            }
        """
        from ..tools.lsp_tools import with_lsp_client, get_lsp_manager
        
        try:
            # 🔥 首次使用时检查并启动LSP服务器
            manager = get_lsp_manager()
            
            # 检查文件扩展名
            from pathlib import Path
            ext = Path(file_path).suffix
            
            # 查找对应的LSP服务器
            server_config = manager.find_server_for_extension(ext)
            if not server_config:
                logger.debug(f"没有找到 {ext} 文件的LSP服务器")
                return self._empty_lsp_info()
            
            # 检查LSP服务器是否已安装
            if not manager.is_server_installed(server_config):
                # 只在第一次时打印提示
                if not hasattr(self, '_lsp_warning_shown'):
                    logger.warning(f"⚠️  LSP服务器未安装: {server_config.id}")
                    logger.warning(f"   安装方式: pip install {server_config.id}")
                    logger.warning("   安装后将自动启用LSP增强功能")
                    self._lsp_warning_shown = True
                return self._empty_lsp_info()
            
            # 🔥 使用with_lsp_client会自动启动LSP服务器
            # 获取文档符号
            symbols = await with_lsp_client(
                file_path,
                lambda client: client.document_symbols(file_path)
            )
            
            if not symbols:
                return self._empty_lsp_info()
            
            # 过滤出当前chunk范围内的符号
            chunk_symbols = self._filter_symbols_in_range(
                symbols,
                chunk['start'],
                chunk['end']
            )
            
            # 分析类型注解
            has_type_annotations = self._has_type_annotations(chunk_symbols)
            
            # 估算引用计数（基于符号数量和重要性）
            reference_count = self._estimate_reference_count(chunk_symbols)
            
            return {
                'has_lsp_info': True,
                'symbol_count': len(chunk_symbols),
                'has_type_annotations': has_type_annotations,
                'reference_count': reference_count,
                'lsp_symbols': chunk_symbols
            }
        
        except Exception as e:
            logger.debug(f"获取LSP信息失败 {file_path}: {e}")
            return self._empty_lsp_info()
    
    def _empty_lsp_info(self) -> Dict[str, Any]:
        """返回空的LSP信息"""
        return {
            'has_lsp_info': False,
            'symbol_count': 0,
            'has_type_annotations': False,
            'reference_count': 0,
            'lsp_symbols': []
        }
    
    def _filter_symbols_in_range(
        self,
        symbols: List[Dict],
        start_line: int,
        end_line: int
    ) -> List[Dict]:
        """过滤出指定行范围内的符号"""
        filtered = []
        
        logger.debug(f"过滤符号: 范围 {start_line}-{end_line}, 总符号数 {len(symbols)}")
        
        for symbol in symbols:
            # LSP符号的位置信息
            if 'range' in symbol:
                symbol_start = symbol['range']['start']['line']
                symbol_end = symbol['range']['end']['line']
                
                logger.debug(f"  符号 {symbol.get('name', 'N/A')}: {symbol_start}-{symbol_end}")
                
                # 🔥 修复：LSP行号是0-based，chunk可能是1-based
                # 检查是否有重叠（更宽松的条件）
                if not (symbol_end < start_line or symbol_start > end_line):
                    filtered.append(symbol)
                    logger.debug(f"    ✓ 包含")
                else:
                    logger.debug(f"    ✗ 排除")
        
        logger.debug(f"过滤后符号数: {len(filtered)}")
        return filtered
    
    def _has_type_annotations(self, symbols: List[Dict]) -> bool:
        """检查是否有类型注解"""
        for symbol in symbols:
            # 检查符号的detail字段（通常包含类型信息）
            if 'detail' in symbol and symbol['detail']:
                # Python类型注解通常包含 -> 或 :
                if '->' in symbol['detail'] or ': ' in symbol['detail']:
                    return True
        
        return False
    
    def _estimate_reference_count(self, symbols: List[Dict]) -> int:
        """估算引用计数"""
        # 简单估算：符号数量 * 平均引用数
        # 实际应该调用lsp_find_references，但那样太慢
        # 这里用启发式方法
        
        count = 0
        for symbol in symbols:
            # 函数和类通常有更多引用
            if symbol.get('kind') in [12, 5]:  # Function=12, Class=5
                count += 5
            else:
                count += 1
        
        return count
    
    def _rerank_with_lsp(
        self,
        candidates: List[Dict],
        query: str
    ) -> List[Dict]:
        """
        使用LSP信息重新排序
        
        策略：
        1. 基础分数：hybrid_score
        2. LSP加成：
           - 有类型注解：+20%
           - 符号数量多：+10%
           - 引用计数高：+15%
           - 查询匹配类型：+30%
        """
        for chunk in candidates:
            base_score = chunk.get('hybrid_score', chunk.get('final_score', 0))
            
            # LSP加成
            lsp_boost = 1.0
            
            # 1. 类型注解加成
            if chunk.get('has_type_annotations'):
                lsp_boost *= 1.2  # +20%
                logger.debug(f"   类型注解加成: {chunk['path']}:{chunk['start']}")
            
            # 2. 符号数量加成
            symbol_count = chunk.get('symbol_count', 0)
            if symbol_count > 3:
                lsp_boost *= 1.1  # +10%
                logger.debug(f"   符号数量加成: {chunk['path']}:{chunk['start']} ({symbol_count}个)")
            
            # 3. 引用计数加成
            ref_count = chunk.get('reference_count', 0)
            if ref_count > 10:
                lsp_boost *= 1.15  # +15%
                logger.debug(f"   引用计数加成: {chunk['path']}:{chunk['start']} ({ref_count}次)")
            
            # 4. 查询匹配类型加成
            if self._query_matches_types(query, chunk):
                lsp_boost *= 1.3  # +30%
                logger.debug(f"   类型匹配加成: {chunk['path']}:{chunk['start']}")
            
            # 应用加成
            chunk['lsp_enhanced_score'] = base_score * lsp_boost
            chunk['lsp_boost'] = lsp_boost
        
        # 按增强分数排序
        candidates.sort(
            key=lambda c: c.get('lsp_enhanced_score', 0),
            reverse=True
        )
        
        logger.info(f"   ✅ LSP重排序完成")
        
        return candidates
    
    def _query_matches_types(self, query: str, chunk: Dict) -> bool:
        """
        检查查询是否匹配类型信息
        
        策略：
        1. 提取查询中的类型关键词
        2. 检查chunk的LSP符号是否包含这些类型
        """
        # 常见的类型关键词
        type_keywords = {
            'string', 'str', 'int', 'integer', 'float', 'bool', 'boolean',
            'list', 'dict', 'tuple', 'set', 'array',
            'function', 'method', 'class', 'object',
            'async', 'await', 'promise', 'future',
            'optional', 'union', 'any', 'none'
        }
        
        # 提取查询中的类型关键词
        query_lower = query.lower()
        query_types = [kw for kw in type_keywords if kw in query_lower]
        
        if not query_types:
            return False
        
        # 检查chunk的符号
        symbols = chunk.get('lsp_symbols', [])
        for symbol in symbols:
            detail = symbol.get('detail', '').lower()
            
            # 检查是否匹配
            for qtype in query_types:
                if qtype in detail:
                    return True
        
        return False


# 便捷函数
async def search_codebase_with_lsp(
    repo_path: Path,
    query: str,
    top_k: int = 10,
    enable_lsp: bool = True
) -> List[Dict[str, Any]]:
    """
    LSP增强的代码库检索（便捷函数）
    
    Args:
        repo_path: 仓库根路径
        query: 自然语言查询
        top_k: 返回条数
        enable_lsp: 是否启用LSP增强
    
    Returns:
        检索结果列表
    """
    idx = LSPEnhancedCodebaseIndex.get_index(repo_path)
    return await idx.search_with_lsp(query, top_k=top_k, enable_lsp=enable_lsp)
