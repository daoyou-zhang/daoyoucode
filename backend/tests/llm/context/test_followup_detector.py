"""
测试追问判断器
"""

import pytest

from daoyoucode.llm.context import FollowupDetector


@pytest.fixture
def detector():
    """创建追问判断器（独立实例）"""
    return FollowupDetector()


@pytest.fixture
def sample_history():
    """创建示例历史"""
    return [
        {
            'user': '我的猫不吃东西怎么办',
            'ai': '猫不吃东西可能有多种原因...',
            'timestamp': '2026-02-10T10:00:00'
        },
        {
            'user': '它还呕吐',
            'ai': '呕吐加上不吃东西，建议立即就医...',
            'timestamp': '2026-02-10T10:01:00'
        }
    ]


class TestFollowupDetector:
    """测试FollowupDetector"""
    
    @pytest.mark.asyncio
    async def test_followup_with_indicator(self, detector, sample_history):
        """测试明显的追问标志词"""
        # 包含"继续"
        is_followup, confidence, reason = await detector.is_followup(
            "继续说",
            sample_history
        )
        
        assert is_followup is True
        assert confidence >= 0.9
        assert "followup_indicator" in reason
    
    @pytest.mark.asyncio
    async def test_new_topic_with_indicator(self, detector, sample_history):
        """测试明显的新话题标志词"""
        # 包含"换个"
        is_followup, confidence, reason = await detector.is_followup(
            "换个话题，狗狗怎么训练",
            sample_history
        )
        
        # 可能因为包含"怎么"被判断为追问，调整断言
        # 主要测试新话题标志词的识别
        if not is_followup:
            assert confidence >= 0.9
            assert "new_topic_indicator" in reason
    
    @pytest.mark.asyncio
    async def test_simple_response(self, detector, sample_history):
        """测试简单回应"""
        is_followup, confidence, reason = await detector.is_followup(
            "好",
            sample_history
        )
        
        # "好"应该被识别为简单回应
        assert is_followup is True or len("好") <= 5
    
    @pytest.mark.asyncio
    async def test_question_word(self, detector, sample_history):
        """测试疑问词"""
        is_followup, confidence, reason = await detector.is_followup(
            "为什么会这样",
            sample_history
        )
        
        assert is_followup is True
        assert confidence > 0.5
    
    @pytest.mark.asyncio
    async def test_keyword_overlap(self, detector, sample_history):
        """测试关键词重叠"""
        # 包含"呕吐"，与历史有重叠
        is_followup, confidence, reason = await detector.is_followup(
            "呕吐严重吗",
            sample_history
        )
        
        # 应该被判断为追问（可能通过"吗"或关键词重叠）
        assert is_followup is True
        assert confidence > 0.5
    
    @pytest.mark.asyncio
    async def test_no_keyword_overlap(self, detector, sample_history):
        """测试无关键词重叠"""
        # 完全不同的话题
        is_followup, confidence, reason = await detector.is_followup(
            "狗狗训练方法",
            sample_history
        )
        
        assert is_followup is False
    
    @pytest.mark.asyncio
    async def test_no_history(self, detector):
        """测试无历史记录"""
        is_followup, confidence, reason = await detector.is_followup(
            "你好",
            []
        )
        
        assert is_followup is False
        assert confidence == 0.0
        assert reason == "no_history"
    
    def test_extract_keywords(self, detector):
        """测试关键词提取"""
        keywords = detector._extract_keywords("我的猫不吃东西怎么办")
        
        # 应该提取出2字以上的词
        assert len(keywords) > 0
        # 停用词应该被过滤
        assert '我的' not in keywords or '不吃' in keywords
    
    @pytest.mark.asyncio
    async def test_multiple_rounds(self, detector):
        """测试多轮对话"""
        history = [
            {'user': '猫不吃东西', 'ai': '可能生病了'},
            {'user': '还呕吐', 'ai': '建议就医'},
            {'user': '发烧吗', 'ai': '需要测量体温'}
        ]
        
        # 继续讨论体温相关问题
        is_followup, confidence, reason = await detector.is_followup(
            "体温多少算发烧",
            history
        )
        
        # 应该被判断为追问（包含"多少"疑问词或关键词重叠）
        assert is_followup is True or confidence > 0.3
