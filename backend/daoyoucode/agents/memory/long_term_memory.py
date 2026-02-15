"""
长期记忆管理器

功能：
1. 对话摘要（每N轮自动生成）
2. 关键信息提取（症状、诊断、建议等）
3. 用户画像（偏好、历史问题等）

存储层次：
- 短期记忆：最近10轮对话（内存，1小时）
- 中期记忆：对话摘要（内存，1天）
- 长期记忆：用户画像（内存，30天）
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class LongTermMemory:
    """
    长期记忆管理器
    
    设计原则：
    1. 分层存储：短期、中期、长期
    2. 自动摘要：每5轮对话生成摘要
    3. 关键提取：结构化信息提取
    4. 用户画像：偏好、历史问题
    5. 缓存层：减少文件I/O
    """
    
    def __init__(self, storage=None):
        """
        初始化长期记忆管理器
        
        Args:
            storage: MemoryStorage实例（用于存储）
        """
        self.storage = storage
        self.summary_interval = 5  # 每N轮生成一次摘要（可配置）
        self.summary_min_messages = 3  # 最少需要N轮才生成摘要
        
        # 缓存层
        from ..core.cache import get_profile_cache, get_summary_cache
        self.profile_cache = get_profile_cache()
        self.summary_cache = get_summary_cache()
        
        logger.info("长期记忆管理器已初始化（带缓存）")
    
    async def generate_summary(
        self,
        session_id: str,
        history: List[Dict],
        llm_client
    ) -> str:
        """
        生成对话摘要
        
        Args:
            session_id: 会话ID
            history: 对话历史
            llm_client: LLM客户端（用于生成摘要）
        
        Returns:
            摘要文本
        """
        if not history:
            return ""
        
        # 构建摘要prompt
        conversation = []
        for item in history:
            user_msg = item.get('user', '')
            ai_resp = item.get('ai', '')
            
            conversation.append(f"用户: {user_msg}")
            conversation.append(f"AI: {ai_resp}")
        
        conversation_text = "\n".join(conversation)
        
        summary_prompt = f"""请对以下对话进行简洁的摘要，提取关键信息：

{conversation_text}

要求：
1. 提取主要讨论的话题
2. 提取关键问题和答案
3. 提取已给出的建议
4. 控制在200字以内

摘要格式：
【主要话题】...
【关键问题】...
【已给建议】...
"""
        
        try:
            # 调用LLM生成摘要
            from ..llm.base import LLMRequest
            request = LLMRequest(
                prompt=summary_prompt,
                model=llm_client.model,
                temperature=0.3,
                max_tokens=300
            )
            response = await llm_client.chat(request)
            
            summary = response.content.strip()
            
            # 保存摘要到存储
            if self.storage:
                self.storage.save_summary(session_id, summary)
            
            # 缓存摘要（TTL: 30分钟）
            self.summary_cache.set(session_id, summary, ttl=1800)
            
            logger.info(f"✅ 生成对话摘要: session={session_id}, length={len(summary)}")
            return summary
        
        except Exception as e:
            logger.error(f"❌ 生成摘要失败: {e}", exc_info=True)
            return ""
    
    def get_summary(self, session_id: str) -> Optional[str]:
        """
        获取会话摘要（带缓存）
        
        Args:
            session_id: 会话ID
        
        Returns:
            摘要文本
        """
        # 尝试从缓存获取
        cached = self.summary_cache.get(session_id)
        if cached is not None:
            logger.debug(f"摘要缓存命中: {session_id}")
            return cached
        
        # 从存储获取
        if not self.storage:
            return None
        
        summary = self.storage.get_summary(session_id)
        
        # 缓存结果（TTL: 30分钟）
        if summary:
            self.summary_cache.set(session_id, summary, ttl=1800)
        
        return summary
    
    async def extract_key_info(
        self,
        session_id: str,
        history: List[Dict],
        llm_client
    ) -> Dict[str, Any]:
        """
        提取关键信息（结构化）
        
        Returns:
            {
                "main_topics": ["话题1", "话题2"],
                "key_questions": ["问题1", "问题2"],
                "suggestions": ["建议1", "建议2"],
                "decisions": ["决策1", "决策2"]
            }
        """
        if not history:
            return {}
        
        # 构建提取prompt
        conversation = []
        for item in history[-5:]:  # 只看最近5轮
            user_msg = item.get('user', '')
            ai_resp = item.get('ai', '')
            
            conversation.append(f"用户: {user_msg}")
            conversation.append(f"AI: {ai_resp}")
        
        conversation_text = "\n".join(conversation)
        
        extract_prompt = f"""从以下对话中提取关键信息，以JSON格式返回：

{conversation_text}

请提取：
1. main_topics: 主要讨论的话题列表
2. key_questions: 关键问题列表
3. suggestions: 已给出的建议列表
4. decisions: 做出的决策列表

返回JSON格式，如果某项信息没有则为空列表。
"""
        
        try:
            # 调用LLM提取关键信息
            response = await llm_client.chat(
                messages=[{"role": "user", "content": extract_prompt}],
                temperature=0.1,
                max_tokens=500
            )
            
            # 解析JSON
            import re
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                key_info = json.loads(json_match.group())
                
                # 保存到存储
                if self.storage:
                    self.storage.save_key_info(session_id, key_info)
                
                logger.info(f"✅ 提取关键信息: session={session_id}")
                return key_info
            
        except Exception as e:
            logger.error(f"❌ 提取关键信息失败: {e}", exc_info=True)
        
        return {}
    
    def get_key_info(self, session_id: str) -> Optional[Dict]:
        """获取关键信息"""
        if not self.storage:
            return None
        
        return self.storage.get_key_info(session_id)
    
    async def build_user_profile(
        self,
        user_id: str,
        all_sessions: List[str] = None,
        llm_client = None
    ) -> Dict[str, Any]:
        """
        构建用户画像（跨session）
        
        Args:
            user_id: 用户ID
            all_sessions: 该用户的所有session列表（可选，自动收集）
            llm_client: LLM客户端（可选，用于智能分析）
        
        Returns:
            {
                "user_id": "user_123",
                "common_topics": ["话题1", "话题2"],
                "skill_level": "intermediate",
                "preferred_style": "functional",
                "activity_pattern": "evening",
                "total_conversations": 10,
                "total_sessions": 5,
                "last_updated": "2026-02-15T12:00:00"
            }
        """
        # 1. 收集所有会话数据
        if all_sessions is None:
            all_sessions = self._collect_user_sessions(user_id)
        
        # 2. 基础统计
        profile = {
            "user_id": user_id,
            "total_sessions": len(all_sessions),
            "total_conversations": 0,
            "last_updated": datetime.now().isoformat()
        }
        
        # 3. 聚合所有session的数据
        all_conversations = []
        all_key_info = []
        
        for session_id in all_sessions:
            # 获取对话历史
            history = self.storage.get_conversation_history(session_id) if self.storage else []
            all_conversations.extend(history)
            profile['total_conversations'] += len(history)
            
            # 获取关键信息
            key_info = self.get_key_info(session_id)
            if key_info:
                all_key_info.append(key_info)
        
        # 4. 提取常见话题
        profile['common_topics'] = self._extract_common_topics(all_conversations, all_key_info)
        
        # 5. 分析技能水平
        profile['skill_level'] = self._analyze_skill_level(all_conversations)
        
        # 6. 分析偏好风格
        profile['preferred_style'] = self._analyze_preferred_style(all_conversations)
        
        # 7. 分析活动模式
        profile['activity_pattern'] = self._analyze_activity_pattern(all_conversations)
        
        # 8. 提取最近项目
        profile['recent_projects'] = self._extract_recent_projects(all_conversations)
        
        # 9. 如果有LLM，进行深度分析
        if llm_client and all_conversations:
            try:
                deep_analysis = await self._deep_analyze_with_llm(
                    user_id, all_conversations, llm_client
                )
                profile.update(deep_analysis)
            except Exception as e:
                logger.warning(f"LLM深度分析失败: {e}")
        
        # 10. 保存到存储
        if self.storage:
            self.storage.save_user_profile(user_id, profile)
        
        # 缓存画像（TTL: 1小时）
        self.profile_cache.set(user_id, profile, ttl=3600)
        
        logger.info(
            f"✅ 构建用户画像: user_id={user_id}, "
            f"sessions={len(all_sessions)}, "
            f"conversations={profile['total_conversations']}, "
            f"topics={len(profile['common_topics'])}"
        )
        
        return profile
    
    def _collect_user_sessions(self, user_id: str) -> List[str]:
        """
        收集用户的所有会话ID
        
        Args:
            user_id: 用户ID
        
        Returns:
            会话ID列表
        """
        if not self.storage:
            return []
        
        return self.storage.get_user_sessions(user_id)
    
    def _extract_common_topics(
        self,
        conversations: List[Dict],
        key_info_list: List[Dict]
    ) -> List[str]:
        """提取常见话题"""
        from collections import Counter
        
        all_topics = []
        
        # 从关键信息中提取
        for info in key_info_list:
            topics = info.get('main_topics', [])
            all_topics.extend(topics)
        
        # 从对话中提取关键词
        keywords = [
            'python', 'javascript', 'java', 'go', 'rust',
            'testing', 'refactoring', 'performance', 'debugging',
            'api', 'database', 'frontend', 'backend',
            'docker', 'kubernetes', 'ci/cd'
        ]
        
        for conv in conversations:
            user_msg = conv.get('user', '').lower()
            for keyword in keywords:
                if keyword in user_msg:
                    all_topics.append(keyword)
        
        # 统计频率，返回前5个
        topic_counter = Counter(all_topics)
        return [t for t, _ in topic_counter.most_common(5)]
    
    def _analyze_skill_level(self, conversations: List[Dict]) -> str:
        """分析技能水平"""
        if not conversations:
            return 'unknown'
        
        # 简单启发式规则
        total = len(conversations)
        
        # 统计复杂问题的比例
        complex_indicators = [
            'architecture', 'design pattern', 'optimization',
            'performance', 'scalability', 'concurrency'
        ]
        
        complex_count = 0
        for conv in conversations:
            user_msg = conv.get('user', '').lower()
            if any(indicator in user_msg for indicator in complex_indicators):
                complex_count += 1
        
        complex_ratio = complex_count / total if total > 0 else 0
        
        if complex_ratio > 0.3:
            return 'advanced'
        elif complex_ratio > 0.1:
            return 'intermediate'
        else:
            return 'beginner'
    
    def _analyze_preferred_style(self, conversations: List[Dict]) -> str:
        """分析偏好风格"""
        if not conversations:
            return 'unknown'
        
        # 统计风格关键词
        style_keywords = {
            'functional': ['functional', 'lambda', 'map', 'filter', 'reduce'],
            'oop': ['class', 'object', 'inheritance', 'polymorphism'],
            'procedural': ['function', 'procedure', 'step by step']
        }
        
        style_counts = {style: 0 for style in style_keywords}
        
        for conv in conversations:
            user_msg = conv.get('user', '').lower()
            for style, keywords in style_keywords.items():
                if any(kw in user_msg for kw in keywords):
                    style_counts[style] += 1
        
        # 返回最常见的风格
        max_style = max(style_counts, key=style_counts.get)
        return max_style if style_counts[max_style] > 0 else 'unknown'
    
    def _analyze_activity_pattern(self, conversations: List[Dict]) -> str:
        """分析活动模式"""
        if not conversations:
            return 'unknown'
        
        # 统计时间戳（如果有）
        from collections import Counter
        
        hours = []
        for conv in conversations:
            timestamp = conv.get('timestamp')
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp)
                    hours.append(dt.hour)
                except:
                    pass
        
        if not hours:
            return 'unknown'
        
        # 分析时段
        hour_counter = Counter(hours)
        avg_hour = sum(hours) / len(hours)
        
        if 6 <= avg_hour < 12:
            return 'morning'
        elif 12 <= avg_hour < 18:
            return 'afternoon'
        elif 18 <= avg_hour < 24:
            return 'evening'
        else:
            return 'night'
    
    def _extract_recent_projects(self, conversations: List[Dict]) -> List[str]:
        """提取最近项目"""
        projects = []
        
        # 查找项目相关的关键词
        project_indicators = ['project', '项目', 'working on', '在做']
        
        for conv in conversations[-20:]:  # 只看最近20轮
            user_msg = conv.get('user', '')
            
            # 简单提取（实际应该用NER）
            if any(indicator in user_msg.lower() for indicator in project_indicators):
                # 提取项目名称（简化实现）
                words = user_msg.split()
                for i, word in enumerate(words):
                    if word.lower() in project_indicators and i + 1 < len(words):
                        project_name = words[i + 1].strip(',.!?')
                        if project_name and len(project_name) > 2:
                            projects.append(project_name)
        
        # 去重并返回最近3个
        seen = set()
        unique_projects = []
        for p in reversed(projects):
            if p not in seen:
                seen.add(p)
                unique_projects.append(p)
        
        return unique_projects[:3]
    
    async def _deep_analyze_with_llm(
        self,
        user_id: str,
        conversations: List[Dict],
        llm_client
    ) -> Dict[str, Any]:
        """使用LLM进行深度分析"""
        # 采样对话（避免token过多）
        sample_size = min(20, len(conversations))
        sampled = conversations[-sample_size:]
        
        # 构建分析prompt
        conv_text = "\n".join([
            f"User: {c.get('user', '')}\nAI: {c.get('ai', '')[:100]}..."
            for c in sampled
        ])
        
        prompt = f"""
分析以下用户的对话记录，提取用户画像信息：

{conv_text}

请以JSON格式返回：
{{
    "interests": ["兴趣1", "兴趣2"],
    "learning_goals": ["目标1", "目标2"],
    "pain_points": ["痛点1", "痛点2"],
    "communication_style": "简洁/详细/技术性"
}}
"""
        
        try:
            from ..llm.base import LLMRequest
            
            request = LLMRequest(
                prompt=prompt,
                model=llm_client.model,
                temperature=0.3
            )
            
            response = await llm_client.chat(request)
            
            # 解析JSON响应
            import json
            analysis = json.loads(response.content)
            
            return {
                'interests': analysis.get('interests', []),
                'learning_goals': analysis.get('learning_goals', []),
                'pain_points': analysis.get('pain_points', []),
                'communication_style': analysis.get('communication_style', 'unknown')
            }
        
        except Exception as e:
            logger.warning(f"LLM深度分析失败: {e}")
            return {}
    
    def should_update_profile(
        self,
        user_id: str,
        current_conversation_count: int
    ) -> bool:
        """
        判断是否应该更新用户画像
        
        Args:
            user_id: 用户ID
            current_conversation_count: 当前对话总数
        
        Returns:
            是否应该更新
        """
        # 获取现有画像
        profile = self.get_user_profile(user_id)
        
        if not profile:
            # 没有画像，且对话数>=10，创建画像
            return current_conversation_count >= 10
        
        # 有画像，检查是否需要更新
        last_count = profile.get('total_conversations', 0)
        
        # 每增加20轮对话，更新一次
        return current_conversation_count - last_count >= 20
    
    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """
        获取用户画像（带缓存）
        
        Args:
            user_id: 用户ID
        
        Returns:
            用户画像字典
        """
        # 尝试从缓存获取
        cached = self.profile_cache.get(user_id)
        if cached is not None:
            logger.debug(f"画像缓存命中: {user_id}")
            return cached
        
        # 从存储获取
        if not self.storage:
            return None
        
        profile = self.storage.get_user_profile(user_id)
        
        # 缓存结果（TTL: 1小时）
        if profile:
            self.profile_cache.set(user_id, profile, ttl=3600)
        
        return profile
    
    def should_generate_summary(
        self,
        session_id: str,
        current_round: int
    ) -> bool:
        """
        判断是否应该生成摘要（智能触发）
        
        策略：
        1. 至少N轮对话（避免太早生成）
        2. 每N轮生成一次
        3. 如果已有摘要，检查是否需要更新
        
        Args:
            session_id: 会话ID
            current_round: 当前轮数
        
        Returns:
            是否应该生成摘要
        """
        # 1. 至少需要最少轮数
        if current_round < self.summary_min_messages:
            return False
        
        # 2. 每N轮生成一次
        if current_round % self.summary_interval == 0:
            return True
        
        # 3. 检查是否已有摘要
        existing_summary = self.get_summary(session_id)
        
        # 如果没有摘要，且轮数>=最少轮数，生成一次
        if not existing_summary and current_round >= self.summary_min_messages:
            return True
        
        return False
    
    def get_context_with_memory(
        self,
        session_id: str,
        user_id: str,
        recent_history: List[Dict],
        current_message: str
    ) -> str:
        """
        获取完整上下文（短期 + 中期 + 长期）
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            recent_history: 最近的对话历史
            current_message: 当前消息
        
        Returns:
            格式化的上下文文本
        """
        context_parts = []
        
        # 1. 长期记忆：用户画像
        profile = self.get_user_profile(user_id)
        if profile and profile.get('common_topics'):
            topics = ", ".join(profile['common_topics'][:3])
            context_parts.append(f"【用户画像】常讨论的话题：{topics}")
        
        # 2. 中期记忆：对话摘要
        summary = self.get_summary(session_id)
        if summary:
            context_parts.append(f"【对话摘要】\n{summary}")
        
        # 3. 短期记忆：最近对话
        if recent_history:
            recent_lines = []
            for idx, item in enumerate(recent_history[-3:], 1):
                user_msg = item.get('user', '')
                ai_text = item.get('ai', '')[:200]
                
                recent_lines.append(f"[第{idx}轮]")
                recent_lines.append(f"用户: {user_msg}")
                recent_lines.append(f"AI: {ai_text}")
            
            context_parts.append(f"【最近对话】\n" + "\n".join(recent_lines))
        
        return "\n\n".join(context_parts)


# 单例
_long_term_memory = None

def get_long_term_memory(storage=None) -> LongTermMemory:
    """获取长期记忆管理器单例"""
    global _long_term_memory
    if _long_term_memory is None:
        _long_term_memory = LongTermMemory(storage)
    return _long_term_memory
