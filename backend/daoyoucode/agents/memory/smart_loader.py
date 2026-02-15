"""
智能记忆加载器

核心思想：
1. 按需加载 - 只在需要时加载
2. 分层加载 - 根据对话深度选择策略
3. 成本优化 - 避免每次都加载所有记忆
4. 树结构 - 支持基于对话树的智能检索

加载策略：
- 新对话：不加载任何记忆（成本0）
- 简单追问：只加载最近2轮（成本低）
- 复杂追问：加载相关分支 + 摘要（成本中）
- 跨session：加载用户画像（成本高，但必要）

树结构支持：
- 自动检测话题切换
- 维护多分支对话
- 智能检索相关分支
"""

from typing import Dict, List, Optional, Any, Tuple, Set
import logging

logger = logging.getLogger(__name__)


class SmartLoader:
    """
    智能记忆加载器
    
    职责：
    1. 根据对话深度决定加载策略
    2. 最小化LLM prompt长度
    3. 降低成本
    4. 支持基于树结构的智能检索
    """
    
    def __init__(self, enable_tree: bool = True):
        """
        初始化智能加载器
        
        Args:
            enable_tree: 是否启用对话树（默认启用）
        """
        self.enable_tree = enable_tree
        
        # 对话树（可选）
        self._conversation_tree = None
        if enable_tree:
            from .conversation_tree import get_conversation_tree
            self._conversation_tree = get_conversation_tree(enabled=True)
            logger.info("对话树已启用")
        
        # 加载策略配置
        self.config = {
            # 新对话：不加载
            'new_conversation': {
                'load_history': False,
                'load_summary': False,
                'load_profile': False,
                'cost': 0
            },
            # 简单追问（2轮内）
            'simple_followup': {
                'load_history': True,
                'history_limit': 2,
                'load_summary': False,
                'load_profile': False,
                'cost': 1
            },
            # 中等追问（3-5轮）
            'medium_followup': {
                'load_history': True,
                'history_limit': 3,
                'load_summary': False,
                'cost': 2
            },
            # 复杂追问（>5轮）
            'complex_followup': {
                'load_history': True,
                'history_limit': 2,  # 只加载最近2轮
                'load_summary': True,  # 加载摘要代替早期对话
                'cost': 3
            },
            # 跨session（需要向量检索）
            'cross_session': {
                'load_history': True,
                'history_limit': 3,
                'load_summary': True,
                'use_vector_search': True,  # 使用向量检索
                'cost': 5
            }
        }
        
        # 统计
        self.stats = {
            'total_loads': 0,
            'new_conversation': 0,
            'simple_followup': 0,
            'medium_followup': 0,
            'complex_followup': 0,
            'cross_session': 0,
            'total_cost': 0
        }
    
    async def decide_load_strategy(
        self,
        is_followup: bool,
        confidence: float,
        history_count: int,
        has_summary: bool = False,
        is_new_user: bool = False,
        current_message: str = ""
    ) -> Tuple[str, Dict[str, Any]]:
        """
        决定加载策略
        
        Args:
            is_followup: 是否为追问
            confidence: 追问置信度
            history_count: 历史对话数量
            has_summary: 是否有摘要
            is_new_user: 是否为新用户
            current_message: 当前消息
        
        Returns:
            (策略名称, 策略配置)
        """
        self.stats['total_loads'] += 1
        
        # 1. 新对话：但如果有历史，尝试智能筛选
        if not is_followup:
            if history_count > 0:
                # 有历史记录，使用简单追问策略
                self.stats['simple_followup'] += 1
                strategy = 'simple_followup'
                cost = self.config[strategy]['cost']
                self.stats['total_cost'] += cost
                logger.info(
                    f"📊 判断为新话题但有历史，尝试筛选: "
                    f"策略={strategy}, 成本={cost}"
                )
                return strategy, self.config[strategy]
            else:
                # 真的没有历史，不加载
                self.stats['new_conversation'] += 1
                strategy = 'new_conversation'
                logger.debug(f"📊 加载策略: {strategy} (成本: 0)")
                return strategy, self.config[strategy]
        
        # 2. 简单追问（历史少于3轮）
        if history_count <= 2:
            self.stats['simple_followup'] += 1
            strategy = 'simple_followup'
            cost = self.config[strategy]['cost']
            self.stats['total_cost'] += cost
            logger.debug(f"📊 加载策略: {strategy} (成本: {cost})")
            return strategy, self.config[strategy]
        
        # 3. 中等追问（3-5轮）
        if history_count <= 5:
            self.stats['medium_followup'] += 1
            strategy = 'medium_followup'
            cost = self.config[strategy]['cost']
            self.stats['total_cost'] += cost
            logger.debug(f"📊 加载策略: {strategy} (成本: {cost})")
            return strategy, self.config[strategy]
        
        # 4. 复杂追问（>5轮，有摘要）
        if has_summary:
            self.stats['complex_followup'] += 1
            strategy = 'complex_followup'
            cost = self.config[strategy]['cost']
            self.stats['total_cost'] += cost
            logger.debug(f"📊 加载策略: {strategy} (成本: {cost}, 使用摘要)")
            return strategy, self.config[strategy]
        
        # 5. 复杂追问（>5轮，无摘要）- 降级为中等策略
        self.stats['medium_followup'] += 1
        strategy = 'medium_followup'
        cost = self.config[strategy]['cost']
        self.stats['total_cost'] += cost
        logger.debug(f"📊 加载策略: {strategy} (成本: {cost}, 无摘要降级)")
        return strategy, self.config[strategy]
    
    async def load_context(
        self,
        strategy_name: str,
        strategy_config: Dict[str, Any],
        memory_manager,
        session_id: str,
        user_id: str,
        current_message: str = ""
    ) -> Dict[str, Any]:
        """
        根据策略加载上下文
        
        Args:
            strategy_name: 策略名称
            strategy_config: 策略配置
            memory_manager: 记忆管理器
            session_id: 会话ID
            user_id: 用户ID
            current_message: 当前消息
        
        Returns:
            加载的上下文数据
        """
        context = {
            'strategy': strategy_name,
            'history': [],
            'summary': None,
            'profile': None,
            'cost': strategy_config.get('cost', 0),
            'filtered': False,
            'tree_based': False
        }
        
        # 1. 加载历史对话
        if strategy_config.get('load_history'):
            limit = strategy_config.get('history_limit', 10)
            
            # 获取全部历史
            full_history = memory_manager.get_conversation_history(session_id, limit=50)
            
            # 如果启用了对话树，使用树结构检索
            if self.enable_tree and self._conversation_tree and current_message:
                # 从历史重建树结构（如果还没有）
                if not self._conversation_tree._nodes:
                    self._conversation_tree.load_from_history(full_history)
                
                # 使用树结构检索
                relevant_history = self._conversation_tree.get_relevant_conversations(
                    current_message=current_message,
                    limit=limit,
                    strategy='auto'  # 自动选择最佳策略
                )
                
                if relevant_history:
                    context['history'] = relevant_history
                    context['tree_based'] = True
                    context['filtered'] = True
                    
                    tree_stats = self._conversation_tree.get_tree_stats()
                    logger.info(
                        f"🌳 树结构检索: 从{len(full_history)}轮中筛选出{len(relevant_history)}轮, "
                        f"分支数={tree_stats['total_branches']}, "
                        f"当前分支={tree_stats['current_branch_id']}"
                    )
                else:
                    # 降级：使用最近N轮
                    context['history'] = full_history[-limit:]
                    logger.debug(f"📚 降级加载最近{limit}轮")
            
            # 如果历史较多，尝试关键词筛选（降级方案）
            elif current_message and full_history and len(full_history) > limit:
                relevant_history = await self._filter_relevant_history(
                    current_message=current_message,
                    full_history=full_history,
                    limit=limit
                )
                
                if relevant_history:
                    context['history'] = relevant_history
                    context['filtered'] = True
                    logger.info(
                        f"🔍 关键词筛选: 从{len(full_history)}轮中筛选出{len(relevant_history)}轮相关对话"
                    )
                else:
                    # 降级：使用最近N轮
                    context['history'] = full_history[-limit:]
                    logger.debug(f"📚 降级加载最近{limit}轮")
            else:
                # 历史较少，直接使用
                context['history'] = full_history[-limit:]
                logger.debug(f"📚 加载历史: {len(context['history'])}轮")
        
        # 2. 加载摘要
        if strategy_config.get('load_summary'):
            summary = memory_manager.long_term_memory.get_summary(session_id)
            context['summary'] = summary
            if summary:
                logger.debug(f"📝 加载摘要: {len(summary)}字符")
        
        # 3. 向量检索（如果启用）
        if strategy_config.get('use_vector_search'):
            # 这里可以添加向量检索逻辑
            # 暂时跳过，因为向量检索默认禁用
            logger.debug("🔍 跳过向量检索（未启用）")
        
        return context
    
    async def _filter_relevant_history(
        self,
        current_message: str,
        full_history: List[Dict],
        limit: int
    ) -> List[Dict]:
        """
        智能筛选相关对话（关键词匹配）
        
        策略：
        1. 提取当前消息的关键词
        2. 在历史中查找包含相同关键词的对话
        3. 按相关性排序，返回top N
        4. 始终包含最近2轮（保证连贯性）
        
        Args:
            current_message: 当前消息
            full_history: 完整历史
            limit: 最多返回多少轮
        
        Returns:
            筛选后的相关对话
        """
        try:
            # 提取关键词
            keywords = self._extract_keywords(current_message)
            
            if not keywords:
                return full_history[-limit:]
            
            logger.debug(f"🔍 提取关键词: {keywords}")
            
            # 在历史中查找包含相同关键词的对话
            relevant_indices = []
            
            for idx, item in enumerate(full_history):
                user_msg = item.get('user', '')
                if not user_msg:
                    continue
                
                # 提取历史消息的关键词
                msg_keywords = self._extract_keywords(user_msg)
                
                # 计算关键词重叠度
                overlap = len(keywords & msg_keywords)
                
                if overlap > 0:
                    # 计算相关性分数
                    score = overlap / len(keywords)
                    relevant_indices.append((idx, score))
                    logger.debug(f"  ✓ 匹配第{idx+1}轮: {user_msg[:30]}... (重叠: {overlap}, 分数: {score:.2f})")
            
            # 按分数排序
            relevant_indices.sort(key=lambda x: x[1], reverse=True)
            top_indices = {idx for idx, score in relevant_indices[:limit-2]}
            
            # 加上最近2轮（保证连贯性）
            recent_indices = set(range(max(0, len(full_history) - 2), len(full_history)))
            
            # 合并并排序
            all_indices = sorted(top_indices | recent_indices)
            
            # 限制数量
            if len(all_indices) > limit:
                all_indices = all_indices[-limit:]
            
            relevant_history = [full_history[i] for i in all_indices]
            
            logger.info(
                f"📦 构建结果: {len(top_indices)}轮相关 + {len(recent_indices)}轮最近 = {len(relevant_history)}轮"
            )
            
            return relevant_history
        
        except Exception as e:
            logger.warning(f"⚠️ 筛选失败，降级到最近N轮: {e}", exc_info=True)
            return full_history[-limit:]
    
    def _extract_keywords(self, text: str) -> Set[str]:
        """
        提取关键词
        
        策略：
        1. 优先使用jieba分词（如果可用）
        2. 降级到简单分词
        
        Args:
            text: 文本
        
        Returns:
            关键词集合
        """
        try:
            # 尝试使用jieba（更准确）
            import jieba.posseg as pseg
            
            words = pseg.cut(text)
            # 只保留名词(n)、动词(v)、形容词(a)
            keywords = {
                w for w, flag in words 
                if (flag.startswith('n') or flag.startswith('v') or flag.startswith('a'))
                and len(w) > 1
            }
            
            if keywords:
                logger.debug(f"  📝 jieba分词: {keywords}")
                return keywords
        
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"  ⚠️ jieba分词失败: {e}")
        
        # 降级到简单分词
        import re
        words = re.findall(r'[\u4e00-\u9fa5]+', text)
        stopwords = {'的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '个', '么', '吗', '呢', '啊'}
        keywords = {w for w in words if w not in stopwords and len(w) > 1}
        
        logger.debug(f"  📝 简单分词: {keywords}")
        return keywords
    
    def format_context_for_prompt(
        self,
        context: Dict[str, Any],
        current_message: str
    ) -> str:
        """
        格式化上下文为LLM prompt
        
        Args:
            context: 加载的上下文
            current_message: 当前消息
        
        Returns:
            格式化的prompt文本
        """
        parts = []
        
        # 1. 用户画像（如果有）
        if context.get('profile'):
            profile = context['profile']
            topics = profile.get('common_topics', [])
            if topics:
                topics_str = ", ".join(topics[:3])
                parts.append(f"【用户画像】常讨论的话题：{topics_str}")
        
        # 2. 对话摘要（如果有）
        if context.get('summary'):
            parts.append(f"【对话摘要】\n{context['summary']}")
        
        # 3. 最近对话
        history = context.get('history', [])
        if history:
            history_lines = []
            for idx, item in enumerate(history, 1):
                user_msg = item.get('user', '')
                ai_text = item.get('ai', '')[:300]  # 限制长度
                
                history_lines.append(f"[第{idx}轮]")
                history_lines.append(f"用户: {user_msg}")
                history_lines.append(f"AI: {ai_text}")
                history_lines.append("")
            
            parts.append(f"【最近对话（共{len(history)}轮）】\n" + "\n".join(history_lines))
        
        # 4. 当前问题
        parts.append(f"【当前问题】\n{current_message}")
        
        # 组合
        if len(parts) > 1:  # 有上下文
            return "\n\n".join(parts)
        else:  # 无上下文
            return f"用户问题：{current_message}"
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        avg_cost = (
            self.stats['total_cost'] / self.stats['total_loads']
            if self.stats['total_loads'] > 0
            else 0
        )
        
        return {
            **self.stats,
            'average_cost': round(avg_cost, 2)
        }
    
    def reset_stats(self):
        """重置统计"""
        self.stats = {
            'total_loads': 0,
            'new_conversation': 0,
            'simple_followup': 0,
            'medium_followup': 0,
            'complex_followup': 0,
            'cross_session': 0,
            'total_cost': 0
        }


# 单例
_smart_loader = None

def get_smart_loader() -> SmartLoader:
    """获取智能加载器单例"""
    global _smart_loader
    if _smart_loader is None:
        _smart_loader = SmartLoader()
    return _smart_loader
