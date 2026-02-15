"""
BM25算法 - 用于话题相似度计算

核心优化：
1. 时间衰减权重（越近的消息权重越高）
2. 动态阈值（根据历史长度调整）
3. 多粒度匹配（词级 + bigram）

依赖：
- rank-bm25（可选，如果安装则使用，否则降级到简单实现）
- jieba（可选，如果安装则使用，否则降级到简单分词）
"""

from typing import List, Dict, Tuple, Optional, Set
from datetime import datetime
import math
import logging

logger = logging.getLogger(__name__)


class BM25Matcher:
    """
    BM25匹配器
    
    用于计算文本相似度，支持：
    1. 时间衰减：越近的消息权重越高
    2. 动态阈值：根据历史长度自适应调整
    3. 多粒度：词级 + bigram匹配
    4. 降级策略：rank-bm25不可用时使用简单实现
    """
    
    def __init__(
        self,
        base_threshold: float = 0.35,  # 提高基础阈值，使话题切换更敏感
        time_decay_halflife: float = 120.0,  # 2分钟半衰期
        use_rank_bm25: bool = True  # 是否尝试使用rank-bm25库
    ):
        self.base_threshold = base_threshold
        self.time_decay_halflife = time_decay_halflife
        self.stopwords = self._load_stopwords()
        
        # 尝试导入rank-bm25
        self.rank_bm25_available = False
        if use_rank_bm25:
            try:
                from rank_bm25 import BM25Okapi
                self.BM25Okapi = BM25Okapi
                self.rank_bm25_available = True
                logger.info("BM25Matcher: 使用rank-bm25库（更准确）")
            except ImportError:
                logger.info("BM25Matcher: rank-bm25未安装，使用简化实现")
        
        # 尝试导入jieba
        self.jieba_available = False
        try:
            import jieba
            import jieba.posseg as pseg
            self.jieba = jieba
            self.pseg = pseg
            self.jieba_available = True
            logger.info("BM25Matcher: 使用jieba分词（更准确）")
        except ImportError:
            logger.info("BM25Matcher: jieba未安装，使用简单分词")
    
    def calculate_similarity(
        self,
        current_text: str,
        history_texts: List[str],
        history_timestamps: Optional[List[datetime]] = None,
        current_time: Optional[datetime] = None
    ) -> Tuple[float, float]:
        """
        计算当前文本与历史文本的相似度
        
        Args:
            current_text: 当前文本
            history_texts: 历史文本列表
            history_timestamps: 历史文本的时间戳（可选）
            current_time: 当前时间（可选）
        
        Returns:
            (平均加权相似度, 最大相似度)
        """
        if not history_texts:
            return 0.0, 0.0
        
        if current_time is None:
            current_time = datetime.now()
        
        # 分词
        current_tokens = self._tokenize(current_text)
        
        if not current_tokens:
            return 0.0, 0.0
        
        # 提取关键实体（如"猫"、"狗"等核心名词）
        current_entities = self._extract_key_entities(current_text)
        
        # 如果使用rank-bm25
        if self.rank_bm25_available:
            avg_sim, max_sim = self._calculate_with_rank_bm25(
                current_tokens,
                history_texts,
                history_timestamps,
                current_time
            )
            
            # 应用实体惩罚：如果关键实体完全不同，降低相似度
            if current_entities:
                entity_penalty = self._calculate_entity_penalty(
                    current_entities,
                    history_texts
                )
                avg_sim *= entity_penalty
                max_sim *= entity_penalty
            
            return avg_sim, max_sim
        else:
            # 降级到简单实现
            return self._calculate_simple(
                current_tokens,
                history_texts,
                history_timestamps,
                current_time
            )
    
    def _calculate_with_rank_bm25(
        self,
        current_tokens: List[str],
        history_texts: List[str],
        history_timestamps: Optional[List[datetime]],
        current_time: datetime
    ) -> Tuple[float, float]:
        """使用rank-bm25库计算相似度"""
        # 分词历史文本
        corpus_tokens = [self._tokenize(text) for text in history_texts]
        
        # 过滤空文档
        valid_indices = [i for i, tokens in enumerate(corpus_tokens) if tokens]
        if not valid_indices:
            return 0.0, 0.0
        
        corpus_tokens = [corpus_tokens[i] for i in valid_indices]
        
        # 计算时间权重
        time_weights = []
        if history_timestamps:
            for i in valid_indices:
                if i < len(history_timestamps):
                    time_diff = (current_time - history_timestamps[i]).total_seconds()
                    weight = self._calculate_time_decay(time_diff)
                else:
                    weight = 1.0
                time_weights.append(weight)
        else:
            time_weights = [1.0] * len(corpus_tokens)
        
        # BM25计算
        bm25 = self.BM25Okapi(corpus_tokens)
        bm25_scores = bm25.get_scores(current_tokens)
        
        # 找到最大和最小分数用于归一化
        min_score = float(bm25_scores.min()) if len(bm25_scores) > 0 else 0
        max_bm25_score = float(bm25_scores.max()) if len(bm25_scores) > 0 else 0
        score_range = max_bm25_score - min_score
        
        # 综合分数：BM25 × 时间权重
        max_score = 0.0
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for i, bm25_score in enumerate(bm25_scores):
            # 归一化BM25分数到[0, 1]
            if score_range > 0:
                normalized_bm25 = (bm25_score - min_score) / score_range
            else:
                normalized_bm25 = 0.5  # 所有分数相同，给个中间值
            
            # 加权
            weighted_score = normalized_bm25 * time_weights[i]
            total_weighted_score += weighted_score
            total_weight += time_weights[i]
            
            if normalized_bm25 > max_score:
                max_score = normalized_bm25
        
        avg_score = total_weighted_score / total_weight if total_weight > 0 else 0
        
        return avg_score, max_score
    
    def _calculate_simple(
        self,
        current_tokens: List[str],
        history_texts: List[str],
        history_timestamps: Optional[List[datetime]],
        current_time: datetime
    ) -> Tuple[float, float]:
        """简单实现（Jaccard相似度 + 时间衰减）"""
        current_set = set(current_tokens)
        
        max_similarity = 0.0
        total_weighted_similarity = 0.0
        total_weight = 0.0
        
        for i, text in enumerate(history_texts):
            tokens = self._tokenize(text)
            if not tokens:
                continue
            
            token_set = set(tokens)
            
            # Jaccard相似度
            overlap = len(current_set & token_set)
            union = len(current_set | token_set)
            similarity = overlap / union if union > 0 else 0
            
            # 时间权重
            if history_timestamps and i < len(history_timestamps):
                time_diff = (current_time - history_timestamps[i]).total_seconds()
                time_weight = self._calculate_time_decay(time_diff)
            else:
                time_weight = 1.0
            
            # 加权相似度
            weighted_similarity = similarity * time_weight
            total_weighted_similarity += weighted_similarity
            total_weight += time_weight
            
            if similarity > max_similarity:
                max_similarity = similarity
        
        avg_similarity = total_weighted_similarity / total_weight if total_weight > 0 else 0
        
        return avg_similarity, max_similarity
    
    def _calculate_time_decay(self, time_diff_seconds: float) -> float:
        """
        计算时间衰减权重（指数衰减）
        
        公式：weight = 0.5 ^ (time_diff / halflife)
        
        示例：
        - 0秒：权重 1.0
        - 2分钟（120秒）：权重 0.5
        - 4分钟：权重 0.25
        - 8分钟：权重 0.125
        """
        return 0.5 ** (time_diff_seconds / self.time_decay_halflife)
    
    def calculate_dynamic_threshold(self, history_length: int) -> float:
        """
        动态阈值（根据历史长度调整）
        
        逻辑：
        - 历史越长，越容易混淆，阈值应该越高
        - 历史很短，阈值可以低一些
        
        公式：threshold = base + log(history_length) * 0.02
        """
        if history_length <= 1:
            return self.base_threshold * 0.8  # 只有1条历史，降低阈值
        
        # 对数增长（避免阈值过高）
        adjustment = math.log(history_length) * 0.02
        dynamic = self.base_threshold + adjustment
        
        # 限制范围：[0.2, 0.4]
        return max(0.2, min(0.4, dynamic))
    
    def _tokenize(self, text: str) -> List[str]:
        """
        分词（多粒度）
        
        优化：
        1. 使用jieba分词（词级）
        2. 提取bigram（短语级）
        3. 过滤停用词
        """
        if self.jieba_available:
            return self._tokenize_with_jieba(text)
        else:
            return self._tokenize_simple(text)
    
    def _tokenize_with_jieba(self, text: str) -> List[str]:
        """使用jieba分词"""
        # 使用jieba分词
        words = self.jieba.lcut(text)
        
        # 过滤停用词
        # 注意：保留单字名词（如"猫"、"狗"），但过滤其他单字
        tokens = []
        for w in words:
            if w in self.stopwords:
                continue
            if len(w) > 1:
                tokens.append(w)
            elif len(w) == 1 and '\u4e00' <= w <= '\u9fa5':
                # 单字中文，可能是重要名词，保留
                tokens.append(w)
        
        # 提取bigram（2-gram）
        if len(tokens) >= 2:
            bigrams = [f"{tokens[i]}_{tokens[i+1]}" for i in range(len(tokens)-1)]
            tokens.extend(bigrams)
        
        return tokens
    
    def _tokenize_simple(self, text: str) -> List[str]:
        """简单分词（滑动窗口）"""
        import re
        # 提取所有中文字符
        chinese_chars = re.findall(r'[\u4e00-\u9fa5]', text)
        
        if not chinese_chars:
            return []
        
        tokens = []
        
        # 提取所有2-3字的连续组合
        for i in range(len(chinese_chars)):
            # 2字词
            if i + 1 < len(chinese_chars):
                word2 = ''.join(chinese_chars[i:i+2])
                if word2 not in self.stopwords:
                    tokens.append(word2)
            
            # 3字词
            if i + 2 < len(chinese_chars):
                word3 = ''.join(chinese_chars[i:i+3])
                if word3 not in self.stopwords:
                    tokens.append(word3)
        
        return tokens
    
    def _load_stopwords(self) -> Set[str]:
        """加载停用词"""
        return {
            # 基础停用词
            '的', '了', '是', '在', '我', '有', '和', '就', '不', '人',
            '都', '一', '个', '上', '也', '很', '到', '说', '要', '去',
            '你', '会', '着', '没有', '看', '好', '自己', '这',
            # 对话停用词
            '吗', '呢', '啊', '哦', '嗯', '哈', '呀', '吧',
            # 时间停用词
            '今天', '明天', '昨天', '现在', '刚才',
            # 其他
            '什么', '怎么', '可以', '需要',
        }
    
    def _extract_key_entities(self, text: str) -> Set[str]:
        """
        提取关键实体（核心名词）
        
        关键实体是指那些能够明确区分话题的核心词，如：
        - 动物名称：猫、狗、鸟、鱼
        - 人物：妈妈、爸爸、老师
        - 地点：学校、医院、公园
        
        策略：
        1. 使用jieba词性标注，提取名词(n)
        2. 优先保留单字名词（如"猫"、"狗"）
        3. 过滤通用词（如"问题"、"情况"）
        """
        entities = set()
        
        if self.jieba_available:
            try:
                # 使用词性标注
                words = self.pseg.cut(text)
                
                # 通用词列表（不作为关键实体）
                generic_nouns = {'问题', '情况', '事情', '东西', '方面', '时候', '地方', '办法', '方法'}
                
                for word, flag in words:
                    # 只保留名词
                    if flag.startswith('n'):
                        # 单字名词（如"猫"、"狗"）优先
                        if len(word) == 1 and '\u4e00' <= word <= '\u9fa5':
                            entities.add(word)
                        # 2-3字名词，排除通用词
                        elif len(word) <= 3 and word not in generic_nouns:
                            entities.add(word)
                
                logger.debug(f"提取关键实体: {entities}")
                return entities
            
            except Exception as e:
                logger.debug(f"实体提取失败: {e}")
        
        # 降级：提取单字中文（可能是关键实体）
        import re
        chinese_chars = re.findall(r'[\u4e00-\u9fa5]', text)
        
        # 常见动物、人物等关键词
        key_entities = {'猫', '狗', '鸟', '鱼', '兔', '鼠', '牛', '羊', '马', '猪'}
        
        for char in chinese_chars:
            if char in key_entities:
                entities.add(char)
        
        return entities
    
    def _calculate_entity_penalty(
        self,
        current_entities: Set[str],
        history_texts: List[str]
    ) -> float:
        """
        计算实体惩罚系数
        
        如果当前消息的关键实体与历史消息完全不同，应该降低相似度。
        
        策略：
        - 如果有任何实体重叠，不惩罚（返回1.0）
        - 如果实体完全不同，惩罚（返回0.3-0.7）
        
        Args:
            current_entities: 当前消息的关键实体
            history_texts: 历史文本列表
        
        Returns:
            惩罚系数（0.3-1.0）
        """
        if not current_entities:
            return 1.0  # 没有关键实体，不惩罚
        
        # 提取历史文本的所有实体
        history_entities = set()
        for text in history_texts:
            history_entities.update(self._extract_key_entities(text))
        
        if not history_entities:
            return 1.0  # 历史没有关键实体，不惩罚
        
        # 计算实体重叠
        overlap = len(current_entities & history_entities)
        
        if overlap > 0:
            # 有实体重叠，不惩罚
            return 1.0
        else:
            # 实体完全不同，应用惩罚
            # 惩罚力度：0.3（强惩罚，相似度降低70%）
            penalty = 0.3
            logger.debug(
                f"实体完全不同，应用惩罚: current={current_entities}, "
                f"history={history_entities}, penalty={penalty}"
            )
            return penalty
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            'base_threshold': self.base_threshold,
            'time_decay_halflife': self.time_decay_halflife,
            'rank_bm25_available': self.rank_bm25_available,
            'jieba_available': self.jieba_available,
        }


# 单例
_bm25_matcher = None


def get_bm25_matcher() -> BM25Matcher:
    """获取BM25匹配器单例"""
    global _bm25_matcher
    
    if _bm25_matcher is None:
        _bm25_matcher = BM25Matcher()
    
    return _bm25_matcher
