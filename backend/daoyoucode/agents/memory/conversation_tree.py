"""
对话树（Conversation Tree）

核心功能：
1. 维护对话的树形结构（分支、话题切换）
2. 支持多分支对话（用户可以在不同话题间切换）
3. 智能识别话题切换和分支创建
4. 提供基于树结构的上下文检索

设计原则：
- 轻量级：通过元数据标记，不改变核心数据结构
- 可扩展：支持多种检索策略（树结构、关键词、向量）
- 可选：不强制依赖，可以禁用
- 通用：可以被其他Agent复用

数据结构：
```
conversation = {
    'user': '用户消息',
    'ai': 'AI响应',
    'timestamp': '2026-02-15T12:00:00',
    'metadata': {
        'conversation_id': 'conv-1',      # 对话ID
        'parent_id': None,                # 父对话ID
        'branch_id': 'branch-1',          # 分支ID
        'topic': '猫-肠胃问题',           # 话题标签
        'depth': 0,                       # 树深度
        'is_branch_start': False          # 是否为分支起点
    }
}
```

树结构示例：
```
Root
├─ Branch-1: 猫-肠胃问题
│  ├─ Conv-1: 我的猫不吃饭
│  ├─ Conv-2: 可能是什么原因？
│  └─ Conv-3: 需要去医院吗？
│
└─ Branch-2: 狗-皮肤问题
   ├─ Conv-4: 那狗呢？（话题切换）
   └─ Conv-5: 狗的皮肤有红点
```
"""

from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime
import logging
import uuid

logger = logging.getLogger(__name__)


class ConversationNode:
    """
    对话节点
    
    表示树中的一个对话
    """
    
    def __init__(
        self,
        conversation_id: str,
        user_message: str,
        ai_response: str,
        parent_id: Optional[str] = None,
        branch_id: Optional[str] = None,
        topic: Optional[str] = None,
        timestamp: Optional[str] = None
    ):
        self.conversation_id = conversation_id
        self.user_message = user_message
        self.ai_response = ai_response
        self.parent_id = parent_id
        self.branch_id = branch_id or self._generate_branch_id()
        self.topic = topic
        self.timestamp = timestamp or datetime.now().isoformat()
        
        # 树结构
        self.children: List[str] = []  # 子节点ID列表
        self.depth = 0
        self.is_branch_start = False
    
    def _generate_branch_id(self) -> str:
        """生成分支ID"""
        return f"branch-{uuid.uuid4().hex[:8]}"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'user': self.user_message,
            'ai': self.ai_response,
            'timestamp': self.timestamp,
            'metadata': {
                'conversation_id': self.conversation_id,
                'parent_id': self.parent_id,
                'branch_id': self.branch_id,
                'topic': self.topic,
                'depth': self.depth,
                'is_branch_start': self.is_branch_start
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationNode':
        """从字典创建节点"""
        metadata = data.get('metadata', {})
        
        node = cls(
            conversation_id=metadata.get('conversation_id', f"conv-{uuid.uuid4().hex[:8]}"),
            user_message=data.get('user', ''),
            ai_response=data.get('ai', ''),
            parent_id=metadata.get('parent_id'),
            branch_id=metadata.get('branch_id'),
            topic=metadata.get('topic'),
            timestamp=data.get('timestamp')
        )
        
        node.depth = metadata.get('depth', 0)
        node.is_branch_start = metadata.get('is_branch_start', False)
        
        return node


class ConversationTree:
    """
    对话树管理器
    
    职责：
    1. 维护对话的树形结构
    2. 识别话题切换和分支创建
    3. 提供基于树结构的检索
    4. 支持多种检索策略
    """
    
    def __init__(self, enabled: bool = True):
        """
        初始化对话树
        
        Args:
            enabled: 是否启用树结构（可选）
        """
        self.enabled = enabled
        
        # 节点存储：conversation_id -> ConversationNode
        self._nodes: Dict[str, ConversationNode] = {}
        
        # 分支存储：branch_id -> [conversation_ids]
        self._branches: Dict[str, List[str]] = {}
        
        # 当前活跃分支
        self._current_branch_id: Optional[str] = None
        
        # 话题关键词缓存（用于快速话题识别）
        self._topic_keywords: Dict[str, Set[str]] = {}
        
        # BM25匹配器（用于话题相似度计算）
        from .bm25_matcher import get_bm25_matcher
        self._bm25_matcher = get_bm25_matcher()
        
        logger.info(f"对话树已初始化（启用: {enabled}）")
    
    def add_conversation(
        self,
        user_message: str,
        ai_response: str,
        conversation_id: Optional[str] = None,
        detect_topic_switch: bool = True
    ) -> ConversationNode:
        """
        添加对话到树中
        
        Args:
            user_message: 用户消息
            ai_response: AI响应
            conversation_id: 对话ID（可选，自动生成）
            detect_topic_switch: 是否检测话题切换
        
        Returns:
            创建的对话节点
        """
        if not self.enabled:
            # 树结构未启用，创建简单节点
            node = ConversationNode(
                conversation_id=conversation_id or f"conv-{uuid.uuid4().hex[:8]}",
                user_message=user_message,
                ai_response=ai_response
            )
            return node
        
        # 生成对话ID
        if conversation_id is None:
            conversation_id = f"conv-{uuid.uuid4().hex[:8]}"
        
        # 检测话题切换
        is_topic_switch = False
        new_topic = None
        parent_id = None
        branch_id = self._current_branch_id
        
        if detect_topic_switch and self._nodes:
            is_topic_switch, new_topic = self._detect_topic_switch(user_message)
            
            if is_topic_switch:
                # 话题切换，创建新分支
                branch_id = f"branch-{uuid.uuid4().hex[:8]}"
                parent_id = None  # 新分支没有父节点
                logger.info(f"🌿 检测到话题切换: {new_topic}")
            else:
                # 同一话题，继续当前分支
                parent_id = self._get_last_conversation_id()
                # 更新当前分支的话题关键词
                if self._current_branch_id:
                    self._update_topic_keywords(self._current_branch_id, user_message)
        else:
            # 第一个对话，创建根分支
            branch_id = f"branch-{uuid.uuid4().hex[:8]}"
            parent_id = None
        
        # 创建节点
        node = ConversationNode(
            conversation_id=conversation_id,
            user_message=user_message,
            ai_response=ai_response,
            parent_id=parent_id,
            branch_id=branch_id,
            topic=new_topic
        )
        
        # 设置深度
        if parent_id and parent_id in self._nodes:
            node.depth = self._nodes[parent_id].depth + 1
        else:
            node.depth = 0
        
        # 标记分支起点
        node.is_branch_start = is_topic_switch or (not self._nodes)
        
        # 添加到存储
        self._nodes[conversation_id] = node
        
        # 更新分支
        if branch_id not in self._branches:
            self._branches[branch_id] = []
        self._branches[branch_id].append(conversation_id)
        
        # 更新父节点的子节点列表
        if parent_id and parent_id in self._nodes:
            self._nodes[parent_id].children.append(conversation_id)
        
        # 更新当前分支
        self._current_branch_id = branch_id
        
        # 更新话题关键词缓存
        if branch_id:
            self._update_topic_keywords(branch_id, user_message)
        
        logger.debug(
            f"添加对话: id={conversation_id}, branch={branch_id}, "
            f"depth={node.depth}, topic_switch={is_topic_switch}"
        )
        
        return node
    
    def _detect_topic_switch(self, current_message: str) -> Tuple[bool, Optional[str]]:
        """
        检测话题切换（使用BM25算法）
        
        策略：
        1. 使用BM25算法计算与当前分支所有消息的相似度
        2. 应用时间衰减权重（越近的消息权重越高）
        3. 动态阈值（根据分支对话数量调整）
        4. 如果相似度低，判断为话题切换
        
        Args:
            current_message: 当前消息
        
        Returns:
            (是否切换, 新话题)
        """
        if not self._current_branch_id:
            return False, None
        
        # 获取当前分支的所有对话
        branch_conversations = self._branches.get(self._current_branch_id, [])
        
        if not branch_conversations:
            # 当前分支没有对话，不判断为切换
            return False, None
        
        # 收集历史文本和时间戳
        history_texts = []
        history_timestamps = []
        
        for conv_id in branch_conversations:
            if conv_id in self._nodes:
                node = self._nodes[conv_id]
                history_texts.append(node.user_message)
                try:
                    history_timestamps.append(datetime.fromisoformat(node.timestamp))
                except:
                    history_timestamps.append(datetime.now())
        
        if not history_texts:
            return False, None
        
        # 使用BM25计算相似度
        avg_similarity, max_similarity = self._bm25_matcher.calculate_similarity(
            current_text=current_message,
            history_texts=history_texts,
            history_timestamps=history_timestamps,
            current_time=datetime.now()
        )
        
        # 动态阈值
        threshold = self._bm25_matcher.calculate_dynamic_threshold(len(branch_conversations))
        
        logger.debug(
            f"话题检测: avg_sim={avg_similarity:.2f}, max_sim={max_similarity:.2f}, "
            f"threshold={threshold:.2f}, convs={len(branch_conversations)}"
        )
        
        # 判断是否切换（使用平均加权相似度）
        if avg_similarity < threshold:
            # 生成新话题标签（使用前3个关键词）
            keywords = self._extract_keywords(current_message)
            new_topic = "-".join(list(keywords)[:3]) if keywords else "new-topic"
            
            logger.debug(
                f"话题切换: avg_sim={avg_similarity:.2f} < {threshold}"
            )
            return True, new_topic
        
        logger.debug(
            f"话题延续: avg_sim={avg_similarity:.2f} >= {threshold}"
        )
        return False, None
    
    def _extract_keywords(self, text: str) -> Set[str]:
        """
        提取关键词（多粒度）
        
        策略：
        1. 优先使用jieba分词 + bigram
        2. 降级到滑动窗口
        
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
            # 注意：保留单字名词（如"猫"、"狗"），但过滤单字动词和形容词
            tokens = [
                w for w, flag in words 
                if (flag.startswith('n') or flag.startswith('v') or flag.startswith('a'))
                and (len(w) > 1 or flag.startswith('n'))  # 名词可以是单字
            ]
            
            if tokens:
                keywords = set(tokens)
                
                # 添加bigram（2-gram）提高准确性
                if len(tokens) >= 2:
                    bigrams = {f"{tokens[i]}_{tokens[i+1]}" for i in range(len(tokens)-1)}
                    keywords.update(bigrams)
                
                logger.debug(f"jieba分词: {keywords}")
                return keywords
        
        except ImportError:
            logger.debug("jieba未安装，使用简单分词")
        except Exception as e:
            logger.debug(f"jieba分词失败: {e}")
        
        # 降级到滑动窗口
        import re
        # 提取所有中文字符
        chinese_chars = re.findall(r'[\u4e00-\u9fa5]', text)
        
        if not chinese_chars:
            return set()
        
        stopwords = {'的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '个', '么', '吗', '呢', '啊', '这', '那', '什么', '怎么', '可以', '需要', '去'}
        
        keywords = set()
        
        # 提取所有2-3字的连续组合（滑动窗口）
        for i in range(len(chinese_chars)):
            # 2字词
            if i + 1 < len(chinese_chars):
                word2 = ''.join(chinese_chars[i:i+2])
                if word2 not in stopwords:
                    keywords.add(word2)
            
            # 3字词
            if i + 2 < len(chinese_chars):
                word3 = ''.join(chinese_chars[i:i+3])
                if word3 not in stopwords:
                    keywords.add(word3)
        
        logger.debug(f"简单分词(滑动窗口): {keywords}")
        return keywords
    
    def _update_topic_keywords(self, branch_id: str, message: str):
        """
        更新分支的话题关键词
        
        Args:
            branch_id: 分支ID
            message: 消息
        """
        keywords = self._extract_keywords(message)
        
        if branch_id not in self._topic_keywords:
            self._topic_keywords[branch_id] = set()
        
        self._topic_keywords[branch_id].update(keywords)
    
    def _get_last_conversation_id(self) -> Optional[str]:
        """获取最后一个对话的ID"""
        if not self._current_branch_id or self._current_branch_id not in self._branches:
            return None
        
        branch_conversations = self._branches[self._current_branch_id]
        return branch_conversations[-1] if branch_conversations else None
    
    def get_branch_conversations(
        self,
        branch_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取分支的所有对话
        
        Args:
            branch_id: 分支ID（None表示当前分支）
            limit: 最多返回多少个（None表示全部）
        
        Returns:
            对话列表
        """
        if branch_id is None:
            branch_id = self._current_branch_id
        
        if not branch_id or branch_id not in self._branches:
            return []
        
        conversation_ids = self._branches[branch_id]
        
        if limit:
            conversation_ids = conversation_ids[-limit:]
        
        conversations = []
        for conv_id in conversation_ids:
            if conv_id in self._nodes:
                conversations.append(self._nodes[conv_id].to_dict())
        
        return conversations
    
    def get_relevant_conversations(
        self,
        current_message: str,
        limit: int = 5,
        strategy: str = 'auto'
    ) -> List[Dict[str, Any]]:
        """
        获取相关对话（智能检索）
        
        策略：
        - 'current_branch': 只返回当前分支的对话
        - 'keyword': 基于关键词匹配
        - 'tree': 基于树结构（当前分支 + 相关分支）
        - 'auto': 自动选择（推荐）
        
        Args:
            current_message: 当前消息
            limit: 最多返回多少个
            strategy: 检索策略
        
        Returns:
            相关对话列表
        """
        if not self.enabled or not self._nodes:
            return []
        
        # 自动选择策略
        if strategy == 'auto':
            if len(self._branches) == 1:
                # 只有一个分支，使用current_branch
                strategy = 'current_branch'
            elif len(self._branches) <= 3:
                # 分支较少，使用tree
                strategy = 'tree'
            else:
                # 分支较多，使用keyword
                strategy = 'keyword'
        
        # 执行检索
        if strategy == 'current_branch':
            return self._get_current_branch_conversations(limit)
        
        elif strategy == 'keyword':
            return self._get_keyword_matched_conversations(current_message, limit)
        
        elif strategy == 'tree':
            return self._get_tree_based_conversations(current_message, limit)
        
        else:
            logger.warning(f"未知的检索策略: {strategy}，使用current_branch")
            return self._get_current_branch_conversations(limit)
    
    def _get_current_branch_conversations(self, limit: int) -> List[Dict[str, Any]]:
        """获取当前分支的对话"""
        return self.get_branch_conversations(limit=limit)
    
    def _get_keyword_matched_conversations(
        self,
        current_message: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        基于关键词匹配的检索
        
        策略：
        1. 提取当前消息的关键词
        2. 在所有对话中查找包含相同关键词的对话
        3. 按相关性排序
        4. 始终包含最近2轮（保证连贯性）
        """
        keywords = self._extract_keywords(current_message)
        
        if not keywords:
            return self._get_current_branch_conversations(limit)
        
        # 计算每个对话的相关性分数
        scored_conversations = []
        
        for conv_id, node in self._nodes.items():
            msg_keywords = self._extract_keywords(node.user_message)
            overlap = len(keywords & msg_keywords)
            
            if overlap > 0:
                score = overlap / len(keywords)
                scored_conversations.append((conv_id, score))
        
        # 按分数排序
        scored_conversations.sort(key=lambda x: x[1], reverse=True)
        
        # 提取top N-2个
        top_ids = {conv_id for conv_id, _ in scored_conversations[:limit-2]}
        
        # 加上最近2个（保证连贯性）
        all_ids = list(self._nodes.keys())
        recent_ids = set(all_ids[-2:]) if len(all_ids) >= 2 else set(all_ids)
        
        # 合并并排序（按时间）
        final_ids = sorted(top_ids | recent_ids, key=lambda x: self._nodes[x].timestamp)
        
        # 限制数量
        if len(final_ids) > limit:
            final_ids = final_ids[-limit:]
        
        return [self._nodes[conv_id].to_dict() for conv_id in final_ids]
    
    def _get_tree_based_conversations(
        self,
        current_message: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        基于树结构的检索
        
        策略：
        1. 优先返回当前分支的对话
        2. 如果当前分支对话不足，查找相关分支
        3. 相关分支：话题关键词重叠度高的分支
        """
        # 1. 获取当前分支的对话
        current_branch_convs = self.get_branch_conversations(limit=limit)
        
        if len(current_branch_convs) >= limit:
            return current_branch_convs[-limit:]
        
        # 2. 需要从其他分支补充
        needed = limit - len(current_branch_convs)
        
        # 提取当前消息的关键词
        keywords = self._extract_keywords(current_message)
        
        if not keywords:
            return current_branch_convs
        
        # 3. 查找相关分支
        scored_branches = []
        
        for branch_id, branch_keywords in self._topic_keywords.items():
            if branch_id == self._current_branch_id:
                continue
            
            overlap = len(keywords & branch_keywords)
            if overlap > 0:
                score = overlap / len(keywords)
                scored_branches.append((branch_id, score))
        
        # 按分数排序
        scored_branches.sort(key=lambda x: x[1], reverse=True)
        
        # 4. 从相关分支中提取对话
        additional_convs = []
        
        for branch_id, _ in scored_branches:
            if len(additional_convs) >= needed:
                break
            
            branch_convs = self.get_branch_conversations(branch_id, limit=needed)
            additional_convs.extend(branch_convs)
        
        # 5. 合并并限制数量
        all_convs = current_branch_convs + additional_convs[:needed]
        
        return all_convs[-limit:]
    
    def get_tree_stats(self) -> Dict[str, Any]:
        """获取树的统计信息"""
        return {
            'enabled': self.enabled,
            'total_conversations': len(self._nodes),
            'total_branches': len(self._branches),
            'current_branch_id': self._current_branch_id,
            'max_depth': max((node.depth for node in self._nodes.values()), default=0),
            'branches': {
                branch_id: len(conv_ids)
                for branch_id, conv_ids in self._branches.items()
            }
        }
    
    def load_from_history(self, history: List[Dict[str, Any]]):
        """
        从历史对话中重建树结构
        
        Args:
            history: 对话历史列表
        """
        if not self.enabled:
            return
        
        for item in history:
            metadata = item.get('metadata', {})
            
            # 如果已有树结构元数据，直接加载
            if 'conversation_id' in metadata:
                node = ConversationNode.from_dict(item)
                self._nodes[node.conversation_id] = node
                
                # 更新分支
                if node.branch_id not in self._branches:
                    self._branches[node.branch_id] = []
                self._branches[node.branch_id].append(node.conversation_id)
                
                # 更新当前分支
                self._current_branch_id = node.branch_id
            else:
                # 没有元数据，重新构建
                self.add_conversation(
                    user_message=item.get('user', ''),
                    ai_response=item.get('ai', ''),
                    detect_topic_switch=True
                )
        
        logger.info(f"从历史重建树结构: {len(self._nodes)}个对话, {len(self._branches)}个分支")
    
    def export_to_history(self) -> List[Dict[str, Any]]:
        """
        导出为历史对话格式
        
        Returns:
            对话历史列表（包含树结构元数据）
        """
        if not self.enabled:
            return []
        
        # 按时间排序
        sorted_nodes = sorted(
            self._nodes.values(),
            key=lambda x: x.timestamp
        )
        
        return [node.to_dict() for node in sorted_nodes]


# 单例
_conversation_tree = None


def get_conversation_tree(enabled: bool = True) -> ConversationTree:
    """获取对话树单例"""
    global _conversation_tree
    
    if _conversation_tree is None:
        _conversation_tree = ConversationTree(enabled=enabled)
    
    return _conversation_tree
