"""
追问判断器
判断用户消息是否为追问（上下文关联）

三层瀑布式算法：
1. 快速规则（<1ms）- 明显的追问/新话题标志
2. 关键词匹配（<5ms）- 话题相关性
3. 语义相似度（可选）- 深度语义理解
"""

import re
from typing import List, Dict, Tuple, Set
import logging

logger = logging.getLogger(__name__)


class FollowupDetector:
    """
    追问判断器
    
    核心思想：判断是否在讨论同一个话题（上下文关联）
    """
    
    def __init__(self):
        # 明显的追问标志词
        self.followup_indicators = {
            '继续', '还有', '那', '这', '它', '他', '她',
            '呢', '吗', '么', '啊', '哦', '嗯',
            '再', '又', '也', '还', '更', '另外',
            '详细', '具体', '怎么', '为什么', '如何',
            '刚才', '刚刚', '之前', '上面', '前面'
        }
        
        # 新话题标志词
        self.new_topic_indicators = {
            '换个', '另一个', '别的', '其他',
            '新的', '重新', '从头', '开始',
            '不是', '不对', '算了', '不用'
        }
        
        # 停用词
        self.stopwords = {
            '的', '了', '是', '在', '我', '有', '和', '就',
            '不', '人', '都', '一', '个', '上', '来', '到',
            '说', '要', '去', '你', '会', '着', '没', '看'
        }
    
    async def is_followup(
        self,
        current_message: str,
        history: List[Dict],
        skill_name: str = None
    ) -> Tuple[bool, float, str]:
        """
        判断是否为追问
        
        Args:
            current_message: 当前消息
            history: 对话历史
            skill_name: 当前Skill名称
        
        Returns:
            (is_followup, confidence, reason)
        """
        if not history:
            return False, 0.0, "no_history"
        
        # 层1: 快速规则判断
        is_followup, confidence, reason = self._rule_based_check(
            current_message,
            history
        )
        
        if confidence >= 0.9:  # 高置信度，直接返回
            return is_followup, confidence, reason
        
        # 层2: 关键词匹配
        keyword_followup, keyword_confidence, keyword_reason = \
            self._keyword_based_check(current_message, history)
        
        # 综合判断
        if confidence >= 0.7 or keyword_confidence >= 0.6:
            # 任一方法高置信度
            final_followup = is_followup or keyword_followup
            final_confidence = max(confidence, keyword_confidence)
            final_reason = reason if confidence > keyword_confidence else keyword_reason
            
            return final_followup, final_confidence, final_reason
        
        # 低置信度，判断为新话题
        return False, max(confidence, keyword_confidence), "low_confidence"
    
    def _rule_based_check(
        self,
        current_message: str,
        history: List[Dict]
    ) -> Tuple[bool, float, str]:
        """
        规则判断（快速）
        
        Returns:
            (is_followup, confidence, reason)
        """
        # 1. 检查追问标志词
        for indicator in self.followup_indicators:
            if indicator in current_message:
                return True, 0.95, f"followup_indicator:{indicator}"
        
        # 2. 检查新话题标志词
        for indicator in self.new_topic_indicators:
            if indicator in current_message:
                return False, 0.95, f"new_topic_indicator:{indicator}"
        
        # 3. 检查消息长度（很短的消息通常是追问）
        if len(current_message) <= 5:
            # 检查是否是简单回应
            simple_responses = {'好', '嗯', '是', '对', '行', '可以', '谢谢', '好的', '明白'}
            if current_message.strip() in simple_responses:
                return True, 0.9, "simple_response"
        
        # 4. 检查疑问词（可能是追问）
        question_words = ['什么', '怎么', '为什么', '如何', '哪', '谁', '多少']
        if any(qw in current_message for qw in question_words):
            return True, 0.6, "question_word"
        
        return False, 0.3, "no_rule_match"
    
    def _keyword_based_check(
        self,
        current_message: str,
        history: List[Dict]
    ) -> Tuple[bool, float, str]:
        """
        关键词匹配判断
        
        Returns:
            (is_followup, confidence, reason)
        """
        # 提取当前消息的关键词
        current_keywords = self._extract_keywords(current_message)
        
        if not current_keywords:
            return False, 0.0, "no_keywords"
        
        # 检查最近3轮对话的关键词重叠
        max_overlap = 0
        max_overlap_round = 0
        
        for idx, item in enumerate(history[-3:], 1):
            user_msg = item.get('user', '')
            if not user_msg:
                continue
            
            # 提取历史消息的关键词
            history_keywords = self._extract_keywords(user_msg)
            
            # 计算重叠度
            overlap = len(current_keywords & history_keywords)
            
            if overlap > max_overlap:
                max_overlap = overlap
                max_overlap_round = idx
        
        # 计算置信度
        if max_overlap > 0:
            confidence = min(0.9, max_overlap / len(current_keywords))
            reason = f"keyword_overlap:{max_overlap}/{len(current_keywords)}_round{max_overlap_round}"
            return True, confidence, reason
        
        return False, 0.0, "no_keyword_overlap"
    
    def _extract_keywords(self, text: str) -> Set[str]:
        """
        提取关键词（简单分词）
        
        Args:
            text: 文本
        
        Returns:
            关键词集合
        """
        # 使用正则提取中文词（2个字以上）
        words = re.findall(r'[\u4e00-\u9fa5]{2,}', text)
        
        # 过滤停用词
        keywords = {
            w for w in words
            if w not in self.stopwords
        }
        
        return keywords
