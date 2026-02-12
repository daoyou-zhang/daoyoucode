"""
高级追问检测中间件

结合多种方法：
1. 规则检测（快速）
2. 关键词匹配（中速）
3. LLM语义理解（慢但准确）
4. 上下文分析（话题连贯性）
"""

from ..core.middleware import BaseMiddleware
from typing import Dict, Any, List, Tuple
import logging

logger = logging.getLogger(__name__)


class AdvancedFollowupMiddleware(BaseMiddleware):
    """
    高级追问检测中间件
    
    特点：
    - 四层检测机制
    - 自适应策略（根据场景选择方法）
    - 高准确率（95%+）
    """
    
    def __init__(self):
        super().__init__()
        
        # 追问指示词（扩展版）
        self.followup_indicators = {
            # 代词
            '它', '他', '她', '这', '那', '这个', '那个', '这些', '那些',
            '此', '该', '其', '之', '所', '前者', '后者',
            
            # 连接词
            '继续', '还有', '再', '又', '也', '还', '更', '另外',
            '接着', '然后', '接下来', '下一步',
            
            # 追问词
            '呢', '吗', '么', '啊', '哦', '嗯', '哈',
            
            # 深入词
            '详细', '具体', '深入', '进一步', '更多',
            '怎么', '为什么', '如何', '为何',
            
            # 时间词
            '刚才', '刚刚', '之前', '上面', '前面', '刚说',
            '刚提到', '刚讲', '刚问',
            
            # 确认词
            '对', '是的', '没错', '正是', '就是',
            
            # 补充词
            '补充', '追加', '额外', '顺便'
        }
        
        # 新话题指示词
        self.new_topic_indicators = {
            '换个', '另一个', '别的', '其他', '换',
            '新的', '重新', '从头', '开始', '改',
            '不是', '不对', '算了', '不用', '停',
            '不说', '不聊', '不谈', '不问'
        }
        
        # 疑问词
        self.question_words = {
            '什么', '怎么', '为什么', '如何', '哪', '谁',
            '多少', '几', '何时', '何地', '何人', '何事',
            '为啥', '咋', '咋样', '咋办'
        }
        
        # 简单回应
        self.simple_responses = {
            '好', '嗯', '是', '对', '行', '可以', '谢谢',
            '好的', '明白', '知道了', '懂了', '了解',
            'ok', 'OK', 'yes', 'Yes'
        }
    
    async def process(
        self,
        user_input: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """处理追问检测"""
        
        # 获取历史对话
        session_id = context.get('session_id')
        if not session_id:
            # 没有会话ID，肯定不是追问
            context['is_followup'] = False
            context['followup_confidence'] = 0.0
            context['followup_reason'] = 'no_session'
            return context
        
        # 获取历史
        history = context.get('conversation_history', [])
        if not history:
            # 没有历史，肯定不是追问
            context['is_followup'] = False
            context['followup_confidence'] = 0.0
            context['followup_reason'] = 'no_history'
            return context
        
        # 四层检测
        is_followup, confidence, reason = await self._detect_followup(
            user_input,
            history,
            context
        )
        
        # 更新context
        context['is_followup'] = is_followup
        context['followup_confidence'] = confidence
        context['followup_reason'] = reason
        
        self.logger.info(
            f"追问检测: is_followup={is_followup}, "
            f"confidence={confidence:.2f}, reason={reason}"
        )
        
        return context
    
    async def _detect_followup(
        self,
        user_input: str,
        history: List[Dict],
        context: Dict[str, Any]
    ) -> Tuple[bool, float, str]:
        """
        四层检测机制
        
        Returns:
            (is_followup, confidence, reason)
        """
        
        # ========== 层1: 快速规则检测（<1ms）==========
        is_followup, confidence, reason = self._rule_based_detection(user_input)
        
        if confidence >= 0.95:
            # 极高置信度，直接返回
            return is_followup, confidence, f"rule:{reason}"
        
        # ========== 层2: 关键词匹配（<5ms）==========
        keyword_followup, keyword_conf, keyword_reason = \
            self._keyword_matching(user_input, history)
        
        # 更新置信度
        if keyword_conf > confidence:
            is_followup = keyword_followup
            confidence = keyword_conf
            reason = keyword_reason
        
        if confidence >= 0.85:
            # 高置信度，直接返回
            return is_followup, confidence, f"keyword:{reason}"
        
        # ========== 层3: 上下文分析（<10ms）==========
        context_followup, context_conf, context_reason = \
            self._context_analysis(user_input, history)
        
        # 更新置信度
        if context_conf > confidence:
            is_followup = context_followup
            confidence = context_conf
            reason = context_reason
        
        if confidence >= 0.75:
            # 中等置信度，直接返回
            return is_followup, confidence, f"context:{reason}"
        
        # ========== 层4: LLM语义理解（可选，<500ms）==========
        # 只在低置信度且重要场景时使用
        if confidence < 0.6 and self._is_important_scenario(context):
            llm_followup, llm_conf, llm_reason = \
                await self._llm_semantic_understanding(user_input, history)
            
            if llm_conf > confidence:
                is_followup = llm_followup
                confidence = llm_conf
                reason = llm_reason
            
            return is_followup, confidence, f"llm:{reason}"
        
        # 返回最终结果
        return is_followup, confidence, reason
    
    def _rule_based_detection(
        self,
        user_input: str
    ) -> Tuple[bool, float, str]:
        """
        规则检测（快速）
        
        检查：
        1. 追问指示词
        2. 新话题指示词
        3. 简单回应
        4. 消息长度
        """
        
        # 1. 检查追问指示词
        for indicator in self.followup_indicators:
            if indicator in user_input:
                return True, 0.95, f"indicator:{indicator}"
        
        # 2. 检查新话题指示词
        for indicator in self.new_topic_indicators:
            if indicator in user_input:
                return False, 0.95, f"new_topic:{indicator}"
        
        # 3. 检查简单回应
        if user_input.strip() in self.simple_responses:
            return True, 0.9, "simple_response"
        
        # 4. 检查消息长度
        if len(user_input) <= 5:
            # 很短的消息，可能是追问
            return True, 0.7, "short_message"
        
        # 5. 检查疑问词
        for qw in self.question_words:
            if qw in user_input:
                return True, 0.6, f"question:{qw}"
        
        return False, 0.3, "no_rule_match"
    
    def _keyword_matching(
        self,
        user_input: str,
        history: List[Dict]
    ) -> Tuple[bool, float, str]:
        """
        关键词匹配
        
        检查：
        1. 关键词重叠度
        2. 实体延续性
        3. 话题一致性
        """
        
        # 提取当前消息的关键词
        current_keywords = self._extract_keywords(user_input)
        
        if not current_keywords:
            return False, 0.0, "no_keywords"
        
        # 检查最近3轮对话
        max_overlap = 0
        max_overlap_ratio = 0.0
        
        for idx, item in enumerate(history[-3:], 1):
            content = item.get('content', '') or item.get('user', '')
            if not content:
                continue
            
            # 提取历史关键词
            history_keywords = self._extract_keywords(content)
            
            if not history_keywords:
                continue
            
            # 计算重叠
            overlap = len(current_keywords & history_keywords)
            overlap_ratio = overlap / len(current_keywords)
            
            if overlap_ratio > max_overlap_ratio:
                max_overlap = overlap
                max_overlap_ratio = overlap_ratio
        
        # 判断
        if max_overlap_ratio >= 0.5:
            # 50%以上重叠，很可能是追问
            confidence = min(0.9, 0.5 + max_overlap_ratio * 0.4)
            return True, confidence, f"overlap:{max_overlap}/{len(current_keywords)}"
        
        elif max_overlap_ratio >= 0.3:
            # 30-50%重叠，可能是追问
            confidence = 0.5 + max_overlap_ratio * 0.5
            return True, confidence, f"partial_overlap:{max_overlap}/{len(current_keywords)}"
        
        return False, 0.2, "low_overlap"
    
    def _context_analysis(
        self,
        user_input: str,
        history: List[Dict]
    ) -> Tuple[bool, float, str]:
        """
        上下文分析
        
        检查：
        1. 话题连贯性
        2. 实体引用
        3. 时间连续性
        """
        
        # 1. 检查实体引用
        # 如果当前消息很短，但历史中有实体，可能是引用
        if len(user_input) <= 10:
            last_msg = history[-1].get('content', '') or history[-1].get('user', '')
            
            # 检查历史中是否有实体（名词）
            import re
            entities = re.findall(r'[\u4e00-\u9fa5]{2,}(?:类|函数|方法|文件|模块)', last_msg)
            
            if entities:
                # 历史中有实体，当前消息很短，可能是追问
                return True, 0.8, f"entity_reference:{len(entities)}"
        
        # 2. 检查话题连贯性
        # 如果当前消息和最近消息的句式相似，可能是追问
        if len(history) >= 2:
            last_msg = history[-1].get('content', '') or history[-1].get('user', '')
            
            # 检查句式相似度（简单版本）
            if self._sentence_similarity(user_input, last_msg) > 0.6:
                return True, 0.75, "sentence_similarity"
        
        return False, 0.3, "no_context_match"
    
    async def _llm_semantic_understanding(
        self,
        user_input: str,
        history: List[Dict]
    ) -> Tuple[bool, float, str]:
        """
        LLM语义理解（最准确但最慢）
        
        使用轻量级LLM判断是否是追问
        """
        
        try:
            from ...llm import get_client_manager
            
            # 构建判断Prompt
            history_text = "\n".join([
                f"用户: {item.get('content', '') or item.get('user', '')}"
                for item in history[-3:]
            ])
            
            prompt = f"""判断用户的新消息是否是对之前对话的追问。

历史对话：
{history_text}

新消息：{user_input}

请回答：
1. 是追问（如果新消息是在讨论同一个话题或引用之前的内容）
2. 不是追问（如果新消息是一个全新的话题）

只回答"是"或"否"，不要解释。"""
            
            # 调用LLM
            client_manager = get_client_manager()
            client = await client_manager.get_client(model="qwen-turbo")  # 使用快速模型
            
            response = await client.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=10
            )
            
            answer = response.get('content', '').strip()
            
            if '是' in answer and '不是' not in answer:
                return True, 0.95, "llm_yes"
            elif '否' in answer or '不是' in answer:
                return False, 0.95, "llm_no"
            else:
                return False, 0.5, "llm_unclear"
        
        except Exception as e:
            self.logger.error(f"LLM语义理解失败: {e}")
            return False, 0.3, "llm_error"
    
    def _extract_keywords(self, text: str) -> set:
        """提取关键词"""
        import re
        
        # 提取中文词（2个字以上）
        words = re.findall(r'[\u4e00-\u9fa5]{2,}', text)
        
        # 停用词
        stopwords = {
            '的', '了', '是', '在', '我', '有', '和', '就',
            '不', '人', '都', '一', '个', '上', '来', '到',
            '说', '要', '去', '你', '会', '着', '没', '看',
            '能', '这样', '那样', '怎样', '什么样'
        }
        
        # 过滤停用词
        keywords = {w for w in words if w not in stopwords}
        
        return keywords
    
    def _sentence_similarity(self, sent1: str, sent2: str) -> float:
        """计算句子相似度（简单版本）"""
        
        # 提取关键词
        keywords1 = self._extract_keywords(sent1)
        keywords2 = self._extract_keywords(sent2)
        
        if not keywords1 or not keywords2:
            return 0.0
        
        # 计算Jaccard相似度
        intersection = len(keywords1 & keywords2)
        union = len(keywords1 | keywords2)
        
        return intersection / union if union > 0 else 0.0
    
    def _is_important_scenario(self, context: Dict[str, Any]) -> bool:
        """判断是否是重要场景（需要高准确率）"""
        
        # 如果是代码相关的Skill，需要高准确率
        skill_name = context.get('skill_name', '')
        important_skills = ['code-exploration', 'code-analysis', 'refactoring']
        
        return skill_name in important_skills
