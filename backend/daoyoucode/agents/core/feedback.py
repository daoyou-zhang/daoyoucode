"""
反馈循环

执行后的评估和学习系统：
1. 结果质量评估
2. 问题识别
3. 改进建议生成
4. 失败分析和学习
5. 策略调整

注意：FeedbackLoop是可选的，不影响原有的执行流程
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class Evaluation:
    """评估结果"""
    quality_score: float  # 0-1
    issues: List[str]
    suggestions: List[str]
    strengths: List[str]
    weaknesses: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'quality_score': self.quality_score,
            'issues': self.issues,
            'suggestions': self.suggestions,
            'strengths': self.strengths,
            'weaknesses': self.weaknesses,
            'metadata': self.metadata
        }


@dataclass
class FailureAnalysis:
    """失败分析"""
    root_cause: str
    error_type: str
    affected_components: List[str]
    recovery_suggestions: List[str]
    prevention_suggestions: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'root_cause': self.root_cause,
            'error_type': self.error_type,
            'affected_components': self.affected_components,
            'recovery_suggestions': self.recovery_suggestions,
            'prevention_suggestions': self.prevention_suggestions
        }


class FeedbackLoop:
    """
    反馈循环
    
    职责：
    1. 评估执行结果质量
    2. 识别问题和优点
    3. 生成改进建议
    4. 分析失败原因
    5. 学习和调整策略
    
    注意：这是可选功能，不影响原有的执行流程
    """
    
    def __init__(self):
        # 质量评估规则
        self.quality_rules = {
            'completeness': 0.3,  # 完整性权重
            'correctness': 0.3,   # 正确性权重
            'efficiency': 0.2,    # 效率权重
            'clarity': 0.2        # 清晰度权重
        }
        
        # 常见问题模式
        self.issue_patterns = {
            'incomplete': ['未完成', '不完整', '缺少', '遗漏'],
            'incorrect': ['错误', '不正确', '有误', '问题'],
            'inefficient': ['慢', '耗时', '性能', '优化'],
            'unclear': ['不清楚', '模糊', '难懂', '混乱']
        }
        
        # 错误类型分类
        self.error_types = {
            'timeout': ['超时', 'timeout', 'time out'],
            'resource': ['内存', '资源', 'resource', 'memory'],
            'permission': ['权限', '拒绝', 'permission', 'denied'],
            'network': ['网络', '连接', 'network', 'connection'],
            'syntax': ['语法', 'syntax', 'parse'],
            'logic': ['逻辑', 'logic', '业务']
        }
        
        # 学习历史（用于策略调整）
        self.learning_history: List[Dict[str, Any]] = []
        self.max_history = 100
        
        logger.info("反馈循环已初始化")
    
    async def evaluate(
        self,
        task_description: str,
        result: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Evaluation:
        """
        评估执行结果
        
        Args:
            task_description: 任务描述
            result: 执行结果
            context: 上下文（可选）
        
        Returns:
            评估结果
        """
        if context is None:
            context = {}
        
        logger.info(f"评估任务结果: {task_description[:50]}...")
        
        # 1. 计算质量分数
        quality_score = self._calculate_quality_score(
            task_description,
            result,
            context
        )
        
        # 2. 识别问题
        issues = self._identify_issues(result, context)
        
        # 3. 识别优点
        strengths = self._identify_strengths(result, context)
        
        # 4. 识别弱点
        weaknesses = self._identify_weaknesses(result, context)
        
        # 5. 生成改进建议
        suggestions = self._generate_suggestions(
            task_description,
            result,
            issues,
            weaknesses,
            context
        )
        
        evaluation = Evaluation(
            quality_score=quality_score,
            issues=issues,
            suggestions=suggestions,
            strengths=strengths,
            weaknesses=weaknesses,
            metadata={
                'task_description': task_description[:100],
                'evaluated_at': datetime.now().isoformat()
            }
        )
        
        # 6. 记录到学习历史
        self._record_learning(task_description, result, evaluation)
        
        logger.info(f"评估完成: 质量分数={quality_score:.2f}")
        
        return evaluation
    
    async def analyze_failure(
        self,
        task_description: str,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> FailureAnalysis:
        """
        分析失败原因
        
        Args:
            task_description: 任务描述
            error: 错误异常
            context: 上下文（可选）
        
        Returns:
            失败分析
        """
        if context is None:
            context = {}
        
        logger.info(f"分析失败: {task_description[:50]}...")
        
        error_str = str(error).lower()
        
        # 1. 识别错误类型
        error_type = self._classify_error(error_str)
        
        # 2. 分析根本原因
        root_cause = self._analyze_root_cause(
            task_description,
            error_str,
            error_type,
            context
        )
        
        # 3. 识别受影响的组件
        affected_components = self._identify_affected_components(
            error_str,
            context
        )
        
        # 4. 生成恢复建议
        recovery_suggestions = self._generate_recovery_suggestions(
            error_type,
            root_cause,
            context
        )
        
        # 5. 生成预防建议
        prevention_suggestions = self._generate_prevention_suggestions(
            error_type,
            root_cause,
            context
        )
        
        analysis = FailureAnalysis(
            root_cause=root_cause,
            error_type=error_type,
            affected_components=affected_components,
            recovery_suggestions=recovery_suggestions,
            prevention_suggestions=prevention_suggestions
        )
        
        # 6. 记录失败到学习历史
        self._record_failure(task_description, error, analysis)
        
        logger.info(f"失败分析完成: 类型={error_type}")
        
        return analysis
    
    def _calculate_quality_score(
        self,
        task_description: str,
        result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> float:
        """
        计算质量分数（0-1）
        
        Args:
            task_description: 任务描述
            result: 执行结果
            context: 上下文
        
        Returns:
            质量分数
        """
        score = 0.0
        
        # 1. 完整性评分
        completeness = self._evaluate_completeness(result)
        score += completeness * self.quality_rules['completeness']
        
        # 2. 正确性评分
        correctness = self._evaluate_correctness(result)
        score += correctness * self.quality_rules['correctness']
        
        # 3. 效率评分
        efficiency = self._evaluate_efficiency(result, context)
        score += efficiency * self.quality_rules['efficiency']
        
        # 4. 清晰度评分
        clarity = self._evaluate_clarity(result)
        score += clarity * self.quality_rules['clarity']
        
        return min(max(score, 0.0), 1.0)
    
    def _evaluate_completeness(self, result: Dict[str, Any]) -> float:
        """评估完整性"""
        score = 0.5  # 基础分
        
        # 有内容
        if result.get('content'):
            score += 0.3
        
        # 成功标志
        if result.get('success'):
            score += 0.2
        
        return min(score, 1.0)
    
    def _evaluate_correctness(self, result: Dict[str, Any]) -> float:
        """评估正确性"""
        # 简化版：基于success标志
        if result.get('success'):
            return 0.9
        elif result.get('error'):
            return 0.3
        else:
            return 0.6
    
    def _evaluate_efficiency(
        self,
        result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> float:
        """评估效率"""
        score = 0.7  # 基础分
        
        # 检查tokens使用
        tokens_used = result.get('tokens_used', 0)
        if tokens_used > 0:
            if tokens_used < 1000:
                score += 0.2
            elif tokens_used > 5000:
                score -= 0.2
        
        # 检查工具使用
        tools_used = result.get('tools_used', [])
        if len(tools_used) > 10:
            score -= 0.1  # 工具使用过多
        
        return min(max(score, 0.0), 1.0)
    
    def _evaluate_clarity(self, result: Dict[str, Any]) -> float:
        """评估清晰度"""
        score = 0.7  # 基础分
        
        content = result.get('content', '')
        
        # 内容长度适中
        if 50 < len(content) < 2000:
            score += 0.2
        elif len(content) > 5000:
            score -= 0.1  # 太长
        
        # 有结构（简单检测）
        if '\n' in content:
            score += 0.1
        
        return min(max(score, 0.0), 1.0)
    
    def _identify_issues(
        self,
        result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[str]:
        """识别问题"""
        issues = []
        
        # 检查失败
        if not result.get('success'):
            issues.append("任务执行失败")
        
        # 检查错误
        if result.get('error'):
            issues.append(f"错误: {result['error'][:100]}")
        
        # 检查内容
        content = result.get('content', '')
        if not content:
            issues.append("结果内容为空")
        elif len(content) < 10:
            issues.append("结果内容过短")
        
        # 检查tokens使用
        tokens_used = result.get('tokens_used', 0)
        if tokens_used > 10000:
            issues.append(f"tokens使用过多: {tokens_used}")
        
        # 检查成本
        cost = result.get('cost', 0)
        if cost > 1.0:
            issues.append(f"成本较高: ${cost:.2f}")
        
        return issues
    
    def _identify_strengths(
        self,
        result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[str]:
        """识别优点"""
        strengths = []
        
        # 成功完成
        if result.get('success'):
            strengths.append("任务成功完成")
        
        # 内容丰富
        content = result.get('content', '')
        if len(content) > 500:
            strengths.append("结果内容详细")
        
        # 效率高
        tokens_used = result.get('tokens_used', 0)
        if 0 < tokens_used < 1000:
            strengths.append("tokens使用高效")
        
        # 使用了工具
        tools_used = result.get('tools_used', [])
        if tools_used:
            strengths.append(f"有效使用了{len(tools_used)}个工具")
        
        return strengths
    
    def _identify_weaknesses(
        self,
        result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[str]:
        """识别弱点"""
        weaknesses = []
        
        # 内容过长
        content = result.get('content', '')
        if len(content) > 5000:
            weaknesses.append("结果内容过长，可能不够精炼")
        
        # tokens使用多
        tokens_used = result.get('tokens_used', 0)
        if tokens_used > 5000:
            weaknesses.append("tokens使用较多，可以优化")
        
        # 工具使用多
        tools_used = result.get('tools_used', [])
        if len(tools_used) > 10:
            weaknesses.append("工具调用次数较多，可能效率不高")
        
        return weaknesses
    
    def _generate_suggestions(
        self,
        task_description: str,
        result: Dict[str, Any],
        issues: List[str],
        weaknesses: List[str],
        context: Dict[str, Any]
    ) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        # 基于问题的建议
        if "任务执行失败" in str(issues):
            suggestions.append("建议检查任务描述是否清晰")
            suggestions.append("建议检查Agent配置是否正确")
        
        if "内容为空" in str(issues):
            suggestions.append("建议优化prompt，提供更多上下文")
        
        if "tokens使用过多" in str(issues):
            suggestions.append("建议精简prompt，减少不必要的上下文")
            suggestions.append("建议考虑分步执行")
        
        # 基于弱点的建议
        if "内容过长" in str(weaknesses):
            suggestions.append("建议在prompt中要求简洁回答")
        
        if "工具调用次数较多" in str(weaknesses):
            suggestions.append("建议优化工具使用策略")
        
        # 通用建议
        if not suggestions:
            suggestions.append("结果整体良好，继续保持")
        
        return suggestions
    
    def _classify_error(self, error_str: str) -> str:
        """分类错误类型"""
        for error_type, keywords in self.error_types.items():
            if any(kw in error_str for kw in keywords):
                return error_type
        
        return 'unknown'
    
    def _analyze_root_cause(
        self,
        task_description: str,
        error_str: str,
        error_type: str,
        context: Dict[str, Any]
    ) -> str:
        """分析根本原因"""
        if error_type == 'timeout':
            return "任务执行超时，可能是任务过于复杂或资源不足"
        elif error_type == 'resource':
            return "资源不足，可能是内存或CPU使用过高"
        elif error_type == 'permission':
            return "权限不足，需要检查访问权限配置"
        elif error_type == 'network':
            return "网络连接问题，可能是API不可达或网络不稳定"
        elif error_type == 'syntax':
            return "语法错误，可能是prompt格式不正确或参数错误"
        elif error_type == 'logic':
            return "业务逻辑错误，需要检查任务逻辑"
        else:
            return f"未知错误: {error_str[:100]}"
    
    def _identify_affected_components(
        self,
        error_str: str,
        context: Dict[str, Any]
    ) -> List[str]:
        """识别受影响的组件"""
        components = []
        
        # 从上下文获取
        if context.get('orchestrator'):
            components.append(f"编排器: {context['orchestrator']}")
        
        if context.get('agent'):
            components.append(f"Agent: {context['agent']}")
        
        if context.get('skill_name'):
            components.append(f"Skill: {context['skill_name']}")
        
        # 从错误信息推断
        if 'llm' in error_str or 'model' in error_str:
            components.append("LLM客户端")
        
        if 'tool' in error_str:
            components.append("工具系统")
        
        return components if components else ["未知组件"]
    
    def _generate_recovery_suggestions(
        self,
        error_type: str,
        root_cause: str,
        context: Dict[str, Any]
    ) -> List[str]:
        """生成恢复建议"""
        suggestions = []
        
        if error_type == 'timeout':
            suggestions.append("增加超时时间")
            suggestions.append("简化任务或分步执行")
        elif error_type == 'resource':
            suggestions.append("释放资源后重试")
            suggestions.append("减少并发任务数")
        elif error_type == 'permission':
            suggestions.append("检查并更新权限配置")
        elif error_type == 'network':
            suggestions.append("检查网络连接")
            suggestions.append("稍后重试")
        elif error_type == 'syntax':
            suggestions.append("检查prompt格式")
            suggestions.append("验证参数正确性")
        else:
            suggestions.append("查看详细错误日志")
            suggestions.append("联系技术支持")
        
        return suggestions
    
    def _generate_prevention_suggestions(
        self,
        error_type: str,
        root_cause: str,
        context: Dict[str, Any]
    ) -> List[str]:
        """生成预防建议"""
        suggestions = []
        
        if error_type == 'timeout':
            suggestions.append("使用ExecutionPlanner预估执行时间")
            suggestions.append("对复杂任务设置合理的超时时间")
        elif error_type == 'resource':
            suggestions.append("监控资源使用情况")
            suggestions.append("设置资源使用限制")
        elif error_type == 'permission':
            suggestions.append("在部署时验证所有权限")
        elif error_type == 'network':
            suggestions.append("实现重试机制")
            suggestions.append("添加网络健康检查")
        elif error_type == 'syntax':
            suggestions.append("使用prompt模板")
            suggestions.append("添加参数验证")
        else:
            suggestions.append("添加更详细的日志记录")
            suggestions.append("实现错误监控和告警")
        
        return suggestions
    
    def _record_learning(
        self,
        task_description: str,
        result: Dict[str, Any],
        evaluation: Evaluation
    ):
        """记录学习历史"""
        self.learning_history.append({
            'task_description': task_description[:100],
            'success': result.get('success', False),
            'quality_score': evaluation.quality_score,
            'issues_count': len(evaluation.issues),
            'timestamp': datetime.now().isoformat()
        })
        
        # 保持历史大小
        if len(self.learning_history) > self.max_history:
            self.learning_history = self.learning_history[-self.max_history:]
    
    def _record_failure(
        self,
        task_description: str,
        error: Exception,
        analysis: FailureAnalysis
    ):
        """记录失败历史"""
        self.learning_history.append({
            'task_description': task_description[:100],
            'success': False,
            'error_type': analysis.error_type,
            'root_cause': analysis.root_cause[:100],
            'timestamp': datetime.now().isoformat()
        })
        
        # 保持历史大小
        if len(self.learning_history) > self.max_history:
            self.learning_history = self.learning_history[-self.max_history:]
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """获取学习统计"""
        if not self.learning_history:
            return {
                'total_tasks': 0,
                'success_rate': 0.0,
                'average_quality': 0.0
            }
        
        total = len(self.learning_history)
        successes = sum(1 for h in self.learning_history if h.get('success'))
        
        quality_scores = [
            h.get('quality_score', 0)
            for h in self.learning_history
            if 'quality_score' in h
        ]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        return {
            'total_tasks': total,
            'success_rate': successes / total if total > 0 else 0.0,
            'average_quality': avg_quality,
            'recent_failures': [
                h for h in self.learning_history[-10:]
                if not h.get('success')
            ]
        }


# 单例模式（可选）
_feedback_loop_instance = None


def get_feedback_loop() -> FeedbackLoop:
    """获取反馈循环单例"""
    global _feedback_loop_instance
    
    if _feedback_loop_instance is None:
        _feedback_loop_instance = FeedbackLoop()
        logger.info("反馈循环单例已创建")
    
    return _feedback_loop_instance
