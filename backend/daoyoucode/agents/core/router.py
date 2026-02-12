"""
智能路由器

根据任务特征自动选择最优编排器和Agent
"""

from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
import logging
import re

logger = logging.getLogger(__name__)


@dataclass
class TaskFeatures:
    """任务特征"""
    is_exploration: bool = False      # 是否是探索任务
    is_multi_step: bool = False       # 是否是多步骤任务
    is_parallel: bool = False         # 是否是并行任务
    is_conditional: bool = False      # 是否是条件任务
    is_debate: bool = False           # 是否需要辩论
    complexity: int = 1               # 复杂度（1-5）
    domain: Optional[str] = None      # 领域（code, doc, test等）
    keywords: List[str] = None        # 关键词
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []


@dataclass
class RoutingDecision:
    """路由决策"""
    orchestrator: str                 # 选择的编排器
    agent: Optional[str] = None       # 选择的Agent
    confidence: float = 0.0           # 置信度（0-1）
    reasoning: str = ""               # 决策理由
    alternatives: List[Tuple[str, float]] = None  # 备选方案
    
    def __post_init__(self):
        if self.alternatives is None:
            self.alternatives = []


class IntelligentRouter:
    """
    智能路由器
    
    职责：
    1. 分析任务特征
    2. 选择最优编排器
    3. 选择合适的Agent
    4. 提供决策理由
    
    支持：
    - 自动发现已注册的Agent
    - 通过配置文件定义Agent关键词
    - 动态适配新增Agent
    """
    
    def __init__(self, agent_config_path: Optional[str] = None):
        """
        初始化智能路由器
        
        Args:
            agent_config_path: Agent配置文件路径（可选）
                如果不提供，使用默认配置
        """
        # 编排器特征匹配规则
        self.orchestrator_rules = {
            'parallel_explore': {
                'keywords': ['查找', '搜索', '探索', '发现', '列出', '所有', '哪些'],
                'features': ['is_exploration', 'is_parallel'],
                'complexity_range': (2, 5),
                'description': '并行探索编排器，适合代码探索和搜索任务'
            },
            'workflow': {
                'keywords': ['步骤', '流程', '先', '然后', '最后', '依次', '顺序'],
                'features': ['is_multi_step'],
                'complexity_range': (3, 5),
                'description': '工作流编排器，适合多步骤复杂任务'
            },
            'conditional': {
                'keywords': ['如果', '根据', '判断', '条件', '否则', '选择'],
                'features': ['is_conditional'],
                'complexity_range': (2, 4),
                'description': '条件编排器，适合需要条件判断的任务'
            },
            'multi_agent': {
                'keywords': ['讨论', '辩论', '对比', '多角度', '综合'],
                'features': ['is_debate'],
                'complexity_range': (3, 5),
                'description': '多智能体编排器，适合需要多角度分析的任务'
            },
            'parallel': {
                'keywords': ['批量', '多个', '同时', '并行'],
                'features': ['is_parallel'],
                'complexity_range': (2, 4),
                'description': '并行编排器，适合批量处理任务'
            },
            'simple': {
                'keywords': ['简单', '快速', '直接'],
                'features': [],
                'complexity_range': (1, 2),
                'description': '简单编排器，适合单一简单任务'
            }
        }
        
        # Agent领域匹配规则（按优先级排序）
        # 支持从配置文件加载或使用默认配置
        self.agent_domains = self._load_agent_config(agent_config_path)
        
        logger.info("智能路由器已初始化")
    
    def _load_agent_config(self, config_path: Optional[str] = None) -> Dict[str, List[str]]:
        """
        加载Agent配置
        
        Args:
            config_path: 配置文件路径（可选）
        
        Returns:
            Agent关键词映射
        """
        # 如果提供了配置文件，尝试加载
        if config_path:
            try:
                import yaml
                from pathlib import Path
                
                path = Path(config_path)
                if path.exists():
                    with open(path, 'r', encoding='utf-8') as f:
                        config = yaml.safe_load(f)
                        logger.info(f"从配置文件加载Agent规则: {config_path}")
                        return config.get('agent_domains', self._get_default_agent_config())
            except Exception as e:
                logger.warning(f"加载Agent配置失败: {e}，使用默认配置")
        
        # 使用默认配置
        return self._get_default_agent_config()
    
    def _get_default_agent_config(self) -> Dict[str, List[str]]:
        """获取默认Agent配置"""
        return {
            'test_writer': ['测试', 'test', '用例', '单元测试'],
            'doc_writer': ['文档', '说明', 'readme', 'api'],
            'debugger': ['调试', 'bug', '错误', '修复', '问题'],
            'code_reviewer': ['审查', '检查', '优化', '改进', '重构'],
            'code_writer': ['编写', '生成', '创建', '实现', '写', 'hello', 'world'],
            'code_analyzer': ['分析', '结构', '查看', '理解'],
        }
    
    def register_agent_keywords(self, agent_name: str, keywords: List[str]):
        """
        动态注册Agent关键词
        
        Args:
            agent_name: Agent名称
            keywords: 关键词列表
        
        Example:
            router.register_agent_keywords('data_scientist', ['数据', '分析', '统计', '机器学习'])
        """
        self.agent_domains[agent_name] = keywords
        logger.info(f"注册Agent关键词: {agent_name} -> {keywords}")
    
    def unregister_agent(self, agent_name: str):
        """
        取消注册Agent
        
        Args:
            agent_name: Agent名称
        """
        if agent_name in self.agent_domains:
            del self.agent_domains[agent_name]
            logger.info(f"取消注册Agent: {agent_name}")
    
    def list_registered_agents(self) -> List[str]:
        """
        列出所有已注册的Agent
        
        Returns:
            Agent名称列表
        """
        return list(self.agent_domains.keys())
    
    def auto_discover_agents(self):
        """
        自动发现已注册的Agent
        
        从AgentRegistry中获取所有已注册的Agent，
        如果Agent不在配置中，使用Agent的description作为关键词
        """
        from .agent import get_agent_registry
        
        registry = get_agent_registry()
        registered_agents = registry.list_agents()
        
        discovered_count = 0
        
        for agent_name in registered_agents:
            if agent_name not in self.agent_domains:
                # 获取Agent实例
                agent = registry.get_agent(agent_name)
                
                if agent and agent.config.description:
                    # 从description提取关键词（简单分词）
                    keywords = self._extract_keywords_from_description(
                        agent.config.description
                    )
                    
                    if keywords:
                        self.agent_domains[agent_name] = keywords
                        discovered_count += 1
                        logger.info(f"自动发现Agent: {agent_name} -> {keywords}")
        
        if discovered_count > 0:
            logger.info(f"自动发现了 {discovered_count} 个新Agent")
        
        return discovered_count
    
    def _extract_keywords_from_description(self, description: str) -> List[str]:
        """
        从Agent描述中提取关键词
        
        Args:
            description: Agent描述
        
        Returns:
            关键词列表
        """
        import re
        
        # 提取中文词（2-4个字）
        chinese_words = re.findall(r'[\u4e00-\u9fa5]{2,4}', description.lower())
        
        # 提取英文词
        english_words = re.findall(r'[a-z]{3,}', description.lower())
        
        # 合并并去重
        keywords = list(set(chinese_words + english_words))
        
        # 限制数量
        return keywords[:10]
    
    async def route(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> RoutingDecision:
        """
        智能路由
        
        Args:
            user_input: 用户输入
            context: 上下文（可选）
        
        Returns:
            路由决策
        """
        if context is None:
            context = {}
        
        # 1. 提取任务特征
        features = self._extract_features(user_input, context)
        
        logger.info(f"任务特征: 探索={features.is_exploration}, "
                   f"多步骤={features.is_multi_step}, "
                   f"并行={features.is_parallel}, "
                   f"条件={features.is_conditional}, "
                   f"复杂度={features.complexity}")
        
        # 2. 计算编排器匹配分数
        orchestrator_scores = self._calculate_orchestrator_scores(features, user_input)
        
        # 3. 选择最优编排器
        best_orchestrator = max(orchestrator_scores.items(), key=lambda x: x[1])
        orchestrator_name = best_orchestrator[0]
        confidence = best_orchestrator[1]
        
        # 4. 选择Agent
        agent = self._select_agent(user_input, features)
        
        # 5. 生成决策理由
        reasoning = self._generate_reasoning(
            orchestrator_name,
            agent,
            features,
            user_input
        )
        
        # 6. 获取备选方案
        alternatives = sorted(
            [(k, v) for k, v in orchestrator_scores.items() if k != orchestrator_name],
            key=lambda x: x[1],
            reverse=True
        )[:3]  # 前3个备选
        
        decision = RoutingDecision(
            orchestrator=orchestrator_name,
            agent=agent,
            confidence=confidence,
            reasoning=reasoning,
            alternatives=alternatives
        )
        
        logger.info(f"路由决策: {orchestrator_name} (置信度: {confidence:.2f})")
        if agent:
            logger.info(f"选择Agent: {agent}")
        
        return decision
    
    def _extract_features(
        self,
        user_input: str,
        context: Dict[str, Any]
    ) -> TaskFeatures:
        """提取任务特征"""
        
        user_input_lower = user_input.lower()
        
        # 检测探索任务
        is_exploration = any(
            kw in user_input_lower
            for kw in ['查找', '搜索', '探索', '发现', '列出', '哪些']
        )
        
        # 检测多步骤任务
        is_multi_step = any(
            kw in user_input_lower
            for kw in ['步骤', '流程', '先', '然后', '最后', '依次']
        ) or user_input.count('，') >= 2 or user_input.count('。') >= 2
        
        # 检测并行任务
        is_parallel = any(
            kw in user_input_lower
            for kw in ['批量', '多个', '所有', '同时', '并行']
        )
        
        # 检测条件任务
        is_conditional = any(
            kw in user_input_lower
            for kw in ['如果', '根据', '判断', '条件', '否则']
        )
        
        # 检测辩论任务
        is_debate = any(
            kw in user_input_lower
            for kw in ['讨论', '辩论', '对比', '多角度', '综合']
        )
        
        # 计算复杂度
        complexity = self._calculate_complexity(
            user_input,
            is_multi_step,
            is_parallel,
            is_conditional
        )
        
        # 识别领域
        domain = self._identify_domain(user_input_lower)
        
        # 提取关键词
        keywords = self._extract_keywords(user_input_lower)
        
        return TaskFeatures(
            is_exploration=is_exploration,
            is_multi_step=is_multi_step,
            is_parallel=is_parallel,
            is_conditional=is_conditional,
            is_debate=is_debate,
            complexity=complexity,
            domain=domain,
            keywords=keywords
        )
    
    def _calculate_complexity(
        self,
        user_input: str,
        is_multi_step: bool,
        is_parallel: bool,
        is_conditional: bool
    ) -> int:
        """计算任务复杂度（1-5）"""
        
        complexity = 1
        
        # 基于长度
        if len(user_input) > 100:
            complexity += 1
        if len(user_input) > 200:
            complexity += 1
        
        # 基于特征
        if is_multi_step:
            complexity += 1
        if is_parallel:
            complexity += 1
        if is_conditional:
            complexity += 1
        
        # 基于分句数
        sentence_count = user_input.count('。') + user_input.count('，')
        if sentence_count >= 3:
            complexity += 1
        
        return min(complexity, 5)
    
    def _identify_domain(self, user_input_lower: str) -> Optional[str]:
        """识别任务领域"""
        
        domain_keywords = {
            'code': ['代码', '函数', '类', '方法', 'python', 'javascript', 'java', '文件', '结构'],
            'doc': ['文档', '说明', '注释', 'readme', 'api文档'],
            'test': ['测试', 'test', '用例', '单元测试'],
            'debug': ['调试', 'bug', '错误', '修复'],
            'refactor': ['重构', '优化', '改进']
        }
        
        for domain, keywords in domain_keywords.items():
            if any(kw in user_input_lower for kw in keywords):
                return domain
        
        return 'code'  # 默认为code领域
    
    def _extract_keywords(self, user_input_lower: str) -> List[str]:
        """提取关键词"""
        
        # 简单的关键词提取（可以用更复杂的NLP方法）
        keywords = []
        
        # 提取所有中文词（2-4个字）
        chinese_words = re.findall(r'[\u4e00-\u9fa5]{2,4}', user_input_lower)
        keywords.extend(chinese_words[:10])  # 限制数量
        
        return keywords
    
    def _calculate_orchestrator_scores(
        self,
        features: TaskFeatures,
        user_input: str
    ) -> Dict[str, float]:
        """计算编排器匹配分数"""
        
        scores = {}
        user_input_lower = user_input.lower()
        
        for orch_name, rules in self.orchestrator_rules.items():
            score = 0.0
            
            # 1. 关键词匹配（权重：0.4）
            keyword_matches = sum(
                1 for kw in rules['keywords']
                if kw in user_input_lower
            )
            if rules['keywords']:
                keyword_score = keyword_matches / len(rules['keywords'])
                score += keyword_score * 0.4
            
            # 2. 特征匹配（权重：0.4）
            feature_matches = sum(
                1 for feature in rules['features']
                if getattr(features, feature, False)
            )
            if rules['features']:
                feature_score = feature_matches / len(rules['features'])
                score += feature_score * 0.4
            else:
                # 如果没有特定特征要求，给基础分
                score += 0.2
            
            # 3. 复杂度匹配（权重：0.2）
            min_complexity, max_complexity = rules['complexity_range']
            if min_complexity <= features.complexity <= max_complexity:
                complexity_score = 1.0
            else:
                # 超出范围，分数递减
                if features.complexity < min_complexity:
                    complexity_score = features.complexity / min_complexity
                else:
                    complexity_score = max_complexity / features.complexity
            score += complexity_score * 0.2
            
            scores[orch_name] = score
        
        return scores
    
    def _select_agent(
        self,
        user_input: str,
        features: TaskFeatures
    ) -> Optional[str]:
        """选择Agent"""
        
        user_input_lower = user_input.lower()
        
        # 计算每个Agent的匹配分数
        agent_scores = {}
        
        for agent_name, keywords in self.agent_domains.items():
            score = sum(1 for kw in keywords if kw in user_input_lower)
            if score > 0:
                agent_scores[agent_name] = score
        
        if not agent_scores:
            # 如果没有匹配，根据domain选择默认Agent
            if features.domain == 'code':
                return 'code_analyzer'
            elif features.domain == 'test':
                return 'test_writer'
            elif features.domain == 'doc':
                return 'doc_writer'
            elif features.domain == 'debug':
                return 'debugger'
            return None
        
        # 返回最高分的Agent
        best_agent = max(agent_scores.items(), key=lambda x: x[1])
        return best_agent[0]
    
    def _generate_reasoning(
        self,
        orchestrator: str,
        agent: Optional[str],
        features: TaskFeatures,
        user_input: str
    ) -> str:
        """生成决策理由"""
        
        reasons = []
        
        # 编排器理由
        orch_rule = self.orchestrator_rules.get(orchestrator, {})
        reasons.append(f"选择{orchestrator}编排器：{orch_rule.get('description', '')}")
        
        # 特征理由
        feature_reasons = []
        if features.is_exploration:
            feature_reasons.append("任务涉及探索和搜索")
        if features.is_multi_step:
            feature_reasons.append("任务包含多个步骤")
        if features.is_parallel:
            feature_reasons.append("任务可以并行处理")
        if features.is_conditional:
            feature_reasons.append("任务需要条件判断")
        if features.is_debate:
            feature_reasons.append("任务需要多角度分析")
        
        if feature_reasons:
            reasons.append("任务特征：" + "、".join(feature_reasons))
        
        # 复杂度理由
        reasons.append(f"任务复杂度：{features.complexity}/5")
        
        # Agent理由
        if agent:
            reasons.append(f"选择{agent}处理{features.domain}相关任务")
        
        return "；".join(reasons)


# 单例模式
_router_instance = None


def get_intelligent_router(
    config_path: Optional[str] = None,
    auto_discover: bool = True
) -> IntelligentRouter:
    """
    获取智能路由器单例
    
    Args:
        config_path: Agent配置文件路径（可选）
        auto_discover: 是否自动发现已注册的Agent（默认True）
    
    Returns:
        智能路由器实例
    """
    global _router_instance
    
    if _router_instance is None:
        _router_instance = IntelligentRouter(config_path)
        
        # 自动发现Agent
        if auto_discover:
            _router_instance.auto_discover_agents()
        
        logger.info("智能路由器单例已创建")
    
    return _router_instance
