"""
执行计划器

在执行前进行智能规划：
1. 任务复杂度分析
2. 执行步骤生成
3. 成本预估（tokens、时间）
4. 风险识别
5. 编排器智能选择（与Router配合）

注意：ExecutionPlanner是可选的，不影响原有的直接执行流程
"""

from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class ExecutionStep:
    """执行步骤"""
    step_id: int
    description: str
    orchestrator: str
    agent: Optional[str] = None
    estimated_tokens: int = 0
    estimated_time: float = 0.0  # 秒
    dependencies: List[int] = field(default_factory=list)  # 依赖的步骤ID
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'step_id': self.step_id,
            'description': self.description,
            'orchestrator': self.orchestrator,
            'agent': self.agent,
            'estimated_tokens': self.estimated_tokens,
            'estimated_time': self.estimated_time,
            'dependencies': self.dependencies
        }


@dataclass
class ExecutionPlan:
    """执行计划"""
    plan_id: str
    task_description: str
    complexity: int  # 1-5
    steps: List[ExecutionStep]
    total_estimated_tokens: int
    total_estimated_time: float  # 秒
    risks: List[str]
    recommendations: List[str]
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'plan_id': self.plan_id,
            'task_description': self.task_description,
            'complexity': self.complexity,
            'steps': [s.to_dict() for s in self.steps],
            'total_estimated_tokens': self.total_estimated_tokens,
            'total_estimated_time': self.total_estimated_time,
            'risks': self.risks,
            'recommendations': self.recommendations,
            'created_at': self.created_at.isoformat()
        }


class ExecutionPlanner:
    """
    执行计划器
    
    职责：
    1. 分析任务复杂度
    2. 生成执行步骤
    3. 预估成本（tokens、时间）
    4. 识别风险
    5. 提供建议
    
    注意：这是可选功能，不影响原有的直接执行流程
    """
    
    def __init__(self, use_router: bool = True):
        """
        初始化执行计划器
        
        Args:
            use_router: 是否使用IntelligentRouter（可选）
        """
        self.use_router = use_router
        
        # 复杂度评估规则
        self.complexity_rules = {
            'keywords': {
                'simple': ['简单', '快速', '直接', '查看'],
                'medium': ['分析', '生成', '修改', '优化'],
                'complex': ['重构', '设计', '架构', '完整'],
                'very_complex': ['系统', '全面', '深度', '复杂']
            },
            'length_thresholds': {
                'simple': 20,
                'medium': 50,
                'complex': 100,
                'very_complex': 200
            }
        }
        
        # 成本估算规则（基于经验值）
        self.cost_rules = {
            'simple': {'tokens': 500, 'time': 2.0},
            'workflow': {'tokens': 2000, 'time': 10.0},
            'parallel': {'tokens': 1500, 'time': 5.0},
            'multi_agent': {'tokens': 3000, 'time': 15.0},
            'conditional': {'tokens': 1000, 'time': 5.0},
            'parallel_explore': {'tokens': 2500, 'time': 12.0}
        }
        
        logger.info("执行计划器已初始化")
    
    async def create_plan(
        self,
        task_description: str,
        context: Optional[Dict[str, Any]] = None,
        orchestrator: Optional[str] = None
    ) -> ExecutionPlan:
        """
        创建执行计划
        
        Args:
            task_description: 任务描述
            context: 上下文（可选）
            orchestrator: 指定的编排器（可选，如果不指定则自动选择）
        
        Returns:
            执行计划
        """
        if context is None:
            context = {}
        
        import uuid
        plan_id = str(uuid.uuid4())
        
        # 1. 分析任务复杂度
        complexity = self._analyze_complexity(task_description, context)
        
        logger.info(f"任务复杂度: {complexity}/5")
        
        # 2. 选择编排器（如果未指定）
        if not orchestrator:
            orchestrator = await self._select_orchestrator(
                task_description,
                complexity,
                context
            )
        
        logger.info(f"选择编排器: {orchestrator}")
        
        # 3. 生成执行步骤
        steps = await self._generate_steps(
            task_description,
            orchestrator,
            complexity,
            context
        )
        
        # 4. 预估成本
        total_tokens, total_time = self._estimate_cost(steps, orchestrator)
        
        # 5. 识别风险
        risks = self._identify_risks(
            task_description,
            orchestrator,
            complexity,
            steps
        )
        
        # 6. 生成建议
        recommendations = self._generate_recommendations(
            task_description,
            orchestrator,
            complexity,
            risks
        )
        
        plan = ExecutionPlan(
            plan_id=plan_id,
            task_description=task_description,
            complexity=complexity,
            steps=steps,
            total_estimated_tokens=total_tokens,
            total_estimated_time=total_time,
            risks=risks,
            recommendations=recommendations
        )
        
        logger.info(f"执行计划已创建: {plan_id[:8]}...")
        logger.info(f"  步骤数: {len(steps)}")
        logger.info(f"  预估tokens: {total_tokens}")
        logger.info(f"  预估时间: {total_time:.1f}秒")
        
        return plan
    
    def _analyze_complexity(
        self,
        task_description: str,
        context: Dict[str, Any]
    ) -> int:
        """
        分析任务复杂度（1-5）
        
        Args:
            task_description: 任务描述
            context: 上下文
        
        Returns:
            复杂度（1-5）
        """
        complexity = 1
        task_lower = task_description.lower()
        
        # 1. 基于关键词
        for level, keywords in self.complexity_rules['keywords'].items():
            if any(kw in task_lower for kw in keywords):
                if level == 'simple':
                    complexity = max(complexity, 1)
                elif level == 'medium':
                    complexity = max(complexity, 2)
                elif level == 'complex':
                    complexity = max(complexity, 3)
                elif level == 'very_complex':
                    complexity = max(complexity, 4)
        
        # 2. 基于长度
        length = len(task_description)
        if length > self.complexity_rules['length_thresholds']['very_complex']:
            complexity = max(complexity, 5)
        elif length > self.complexity_rules['length_thresholds']['complex']:
            complexity = max(complexity, 4)
        elif length > self.complexity_rules['length_thresholds']['medium']:
            complexity = max(complexity, 3)
        
        # 3. 基于分句数
        sentence_count = task_description.count('。') + task_description.count('，')
        if sentence_count >= 5:
            complexity = max(complexity, 4)
        elif sentence_count >= 3:
            complexity = max(complexity, 3)
        
        # 4. 基于上下文
        if context.get('has_dependencies'):
            complexity += 1
        
        if context.get('requires_multiple_agents'):
            complexity += 1
        
        return min(complexity, 5)
    
    async def _select_orchestrator(
        self,
        task_description: str,
        complexity: int,
        context: Dict[str, Any]
    ) -> str:
        """
        选择最优编排器
        
        Args:
            task_description: 任务描述
            complexity: 复杂度
            context: 上下文
        
        Returns:
            编排器名称
        """
        # 如果启用了Router，使用Router选择
        if self.use_router:
            try:
                from .router import get_intelligent_router
                router = get_intelligent_router()
                decision = await router.route(task_description, context)
                return decision.orchestrator
            except Exception as e:
                logger.warning(f"Router选择失败: {e}，使用默认规则")
        
        # 否则使用简单规则
        task_lower = task_description.lower()
        
        # 探索任务
        if any(kw in task_lower for kw in ['查找', '搜索', '探索', '列出']):
            return 'parallel_explore'
        
        # 多步骤任务
        if any(kw in task_lower for kw in ['步骤', '流程', '先', '然后']):
            return 'workflow'
        
        # 条件任务
        if any(kw in task_lower for kw in ['如果', '根据', '判断']):
            return 'conditional'
        
        # 辩论任务
        if any(kw in task_lower for kw in ['讨论', '辩论', '对比']):
            return 'multi_agent'
        
        # 并行任务
        if any(kw in task_lower for kw in ['批量', '多个', '所有']):
            return 'parallel'
        
        # 默认：简单任务
        return 'simple'
    
    async def _generate_steps(
        self,
        task_description: str,
        orchestrator: str,
        complexity: int,
        context: Dict[str, Any]
    ) -> List[ExecutionStep]:
        """
        生成执行步骤
        
        Args:
            task_description: 任务描述
            orchestrator: 编排器
            complexity: 复杂度
            context: 上下文
        
        Returns:
            执行步骤列表
        """
        steps = []
        
        # 根据编排器类型生成步骤
        if orchestrator == 'simple':
            # 简单任务：单步骤
            steps.append(ExecutionStep(
                step_id=1,
                description=task_description,
                orchestrator='simple',
                agent=None,  # 由Skill配置决定
                estimated_tokens=500,
                estimated_time=2.0
            ))
        
        elif orchestrator == 'workflow':
            # 工作流：多步骤
            # 简化版：假设3个步骤
            steps.extend([
                ExecutionStep(
                    step_id=1,
                    description="分析和理解任务",
                    orchestrator='simple',
                    estimated_tokens=500,
                    estimated_time=3.0
                ),
                ExecutionStep(
                    step_id=2,
                    description="生成执行计划",
                    orchestrator='simple',
                    estimated_tokens=800,
                    estimated_time=4.0,
                    dependencies=[1]
                ),
                ExecutionStep(
                    step_id=3,
                    description="执行任务",
                    orchestrator='simple',
                    estimated_tokens=1200,
                    estimated_time=6.0,
                    dependencies=[2]
                )
            ])
        
        elif orchestrator == 'parallel':
            # 并行任务：多个并行步骤
            num_parallel = min(complexity, 5)
            for i in range(num_parallel):
                steps.append(ExecutionStep(
                    step_id=i + 1,
                    description=f"并行任务 {i + 1}",
                    orchestrator='simple',
                    estimated_tokens=500,
                    estimated_time=3.0
                ))
        
        elif orchestrator == 'multi_agent':
            # 多智能体：辩论轮次
            rounds = min(complexity, 3)
            for i in range(rounds):
                steps.append(ExecutionStep(
                    step_id=i + 1,
                    description=f"辩论第 {i + 1} 轮",
                    orchestrator='multi_agent',
                    estimated_tokens=1000,
                    estimated_time=5.0,
                    dependencies=[i] if i > 0 else []
                ))
        
        elif orchestrator == 'parallel_explore':
            # 并行探索：探索 + 聚合
            steps.extend([
                ExecutionStep(
                    step_id=1,
                    description="并行探索",
                    orchestrator='parallel',
                    estimated_tokens=2000,
                    estimated_time=8.0
                ),
                ExecutionStep(
                    step_id=2,
                    description="聚合结果",
                    orchestrator='simple',
                    estimated_tokens=500,
                    estimated_time=2.0,
                    dependencies=[1]
                )
            ])
        
        elif orchestrator == 'conditional':
            # 条件任务：判断 + 分支
            steps.extend([
                ExecutionStep(
                    step_id=1,
                    description="条件判断",
                    orchestrator='simple',
                    estimated_tokens=300,
                    estimated_time=2.0
                ),
                ExecutionStep(
                    step_id=2,
                    description="执行分支",
                    orchestrator='simple',
                    estimated_tokens=700,
                    estimated_time=4.0,
                    dependencies=[1]
                )
            ])
        
        return steps
    
    def _estimate_cost(
        self,
        steps: List[ExecutionStep],
        orchestrator: str
    ) -> Tuple[int, float]:
        """
        预估成本
        
        Args:
            steps: 执行步骤
            orchestrator: 编排器
        
        Returns:
            (总tokens, 总时间)
        """
        # 基于步骤的估算
        total_tokens = sum(step.estimated_tokens for step in steps)
        total_time = sum(step.estimated_time for step in steps)
        
        # 添加编排器开销
        orch_cost = self.cost_rules.get(orchestrator, {'tokens': 0, 'time': 0})
        total_tokens += orch_cost['tokens'] * 0.1  # 10%开销
        total_time += orch_cost['time'] * 0.1
        
        return int(total_tokens), total_time
    
    def _identify_risks(
        self,
        task_description: str,
        orchestrator: str,
        complexity: int,
        steps: List[ExecutionStep]
    ) -> List[str]:
        """
        识别风险
        
        Args:
            task_description: 任务描述
            orchestrator: 编排器
            complexity: 复杂度
            steps: 执行步骤
        
        Returns:
            风险列表
        """
        risks = []
        
        # 1. 复杂度风险
        if complexity >= 4:
            risks.append("任务复杂度较高，可能需要多次迭代")
        
        # 2. 步骤数风险
        if len(steps) > 5:
            risks.append(f"执行步骤较多（{len(steps)}步），可能耗时较长")
        
        # 3. 依赖风险
        has_dependencies = any(step.dependencies for step in steps)
        if has_dependencies:
            risks.append("存在步骤依赖，前置步骤失败会影响后续步骤")
        
        # 4. 编排器特定风险
        if orchestrator == 'multi_agent':
            risks.append("多智能体协作可能产生不一致的观点")
        
        if orchestrator == 'parallel':
            risks.append("并行执行可能导致资源竞争")
        
        # 5. 成本风险
        total_tokens = sum(step.estimated_tokens for step in steps)
        if total_tokens > 5000:
            risks.append(f"预估tokens较高（{total_tokens}），成本较大")
        
        return risks
    
    def _generate_recommendations(
        self,
        task_description: str,
        orchestrator: str,
        complexity: int,
        risks: List[str]
    ) -> List[str]:
        """
        生成建议
        
        Args:
            task_description: 任务描述
            orchestrator: 编排器
            complexity: 复杂度
            risks: 风险列表
        
        Returns:
            建议列表
        """
        recommendations = []
        
        # 1. 基于复杂度的建议
        if complexity >= 4:
            recommendations.append("建议分阶段执行，每阶段验证结果")
        
        # 2. 基于编排器的建议
        if orchestrator == 'workflow':
            recommendations.append("建议在关键步骤设置检查点")
        
        if orchestrator == 'multi_agent':
            recommendations.append("建议设置明确的评判标准")
        
        if orchestrator == 'parallel':
            recommendations.append("建议控制并行度，避免资源耗尽")
        
        # 3. 基于风险的建议
        if "tokens较高" in str(risks):
            recommendations.append("建议优化prompt，减少不必要的上下文")
        
        if "步骤较多" in str(risks):
            recommendations.append("建议考虑是否可以合并某些步骤")
        
        # 4. 通用建议
        recommendations.append("建议启用日志记录，便于调试")
        
        return recommendations


# 单例模式（可选）
_planner_instance = None


def get_execution_planner(use_router: bool = True) -> ExecutionPlanner:
    """
    获取执行计划器单例
    
    Args:
        use_router: 是否使用IntelligentRouter
    
    Returns:
        执行计划器实例
    """
    global _planner_instance
    
    if _planner_instance is None:
        _planner_instance = ExecutionPlanner(use_router)
        logger.info("执行计划器单例已创建")
    
    return _planner_instance
