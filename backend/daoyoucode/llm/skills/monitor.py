"""
Skill监控模块
提供Skill执行的统计、监控和分析功能
"""

import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class SkillExecutionRecord:
    """Skill执行记录"""
    skill_name: str
    timestamp: float
    duration: float
    success: bool
    model: str
    tokens_used: int
    cost: float
    mode: str  # 'full' or 'followup'
    error: Optional[str] = None


class SkillMonitor:
    """
    Skill监控器
    
    功能：
    1. 记录每次Skill执行
    2. 统计成功率、平均耗时
    3. 分析热门Skill
    4. 成本分析
    5. 性能告警
    """
    
    def __init__(self, max_records: int = 10000):
        """
        初始化监控器
        
        Args:
            max_records: 最大记录数（超过后自动清理旧记录）
        """
        self.max_records = max_records
        self.records: List[SkillExecutionRecord] = []
        
        # 实时统计
        self.stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'total_tokens': 0,
            'total_cost': 0.0,
            'total_time': 0.0,
            'by_skill': {},
            'by_model': {},
            'by_mode': {'full': 0, 'followup': 0}
        }
        
        logger.info(f"Skill监控器已初始化，最大记录数: {max_records}")
    
    def record_execution(
        self,
        skill_name: str,
        duration: float,
        success: bool,
        model: str,
        tokens_used: int,
        cost: float,
        mode: str = 'full',
        error: Optional[str] = None
    ):
        """
        记录Skill执行
        
        Args:
            skill_name: Skill名称
            duration: 执行时长（秒）
            success: 是否成功
            model: 使用的模型
            tokens_used: 使用的tokens
            cost: 成本
            mode: 执行模式
            error: 错误信息（如果失败）
        """
        # 创建记录
        record = SkillExecutionRecord(
            skill_name=skill_name,
            timestamp=time.time(),
            duration=duration,
            success=success,
            model=model,
            tokens_used=tokens_used,
            cost=cost,
            mode=mode,
            error=error
        )
        
        self.records.append(record)
        
        # 清理旧记录
        if len(self.records) > self.max_records:
            self.records = self.records[-self.max_records:]
        
        # 更新统计
        self._update_stats(record)
    
    def _update_stats(self, record: SkillExecutionRecord):
        """更新统计信息"""
        # 总体统计
        self.stats['total_executions'] += 1
        if record.success:
            self.stats['successful_executions'] += 1
        else:
            self.stats['failed_executions'] += 1
        
        self.stats['total_tokens'] += record.tokens_used
        self.stats['total_cost'] += record.cost
        self.stats['total_time'] += record.duration
        
        # 按Skill统计
        if record.skill_name not in self.stats['by_skill']:
            self.stats['by_skill'][record.skill_name] = {
                'executions': 0,
                'successes': 0,
                'failures': 0,
                'total_time': 0.0,
                'avg_time': 0.0,
                'total_tokens': 0,
                'total_cost': 0.0
            }
        
        skill_stats = self.stats['by_skill'][record.skill_name]
        skill_stats['executions'] += 1
        if record.success:
            skill_stats['successes'] += 1
        else:
            skill_stats['failures'] += 1
        
        skill_stats['total_time'] += record.duration
        skill_stats['avg_time'] = skill_stats['total_time'] / skill_stats['executions']
        skill_stats['total_tokens'] += record.tokens_used
        skill_stats['total_cost'] += record.cost
        
        # 按模型统计
        if record.model not in self.stats['by_model']:
            self.stats['by_model'][record.model] = {
                'executions': 0,
                'total_tokens': 0,
                'total_cost': 0.0
            }
        
        model_stats = self.stats['by_model'][record.model]
        model_stats['executions'] += 1
        model_stats['total_tokens'] += record.tokens_used
        model_stats['total_cost'] += record.cost
        
        # 按模式统计
        self.stats['by_mode'][record.mode] += 1
    
    def get_stats(self, skill_name: Optional[str] = None) -> Dict:
        """
        获取统计信息
        
        Args:
            skill_name: 指定Skill名称（可选）
        
        Returns:
            统计信息字典
        """
        if skill_name:
            return self.stats['by_skill'].get(skill_name, {})
        
        return self.stats
    
    def get_top_skills(self, limit: int = 10, metric: str = 'executions') -> List[Dict]:
        """
        获取热门Skill
        
        Args:
            limit: 返回数量
            metric: 排序指标 ('executions', 'cost', 'tokens')
        
        Returns:
            Skill列表
        """
        skills = []
        for name, stats in self.stats['by_skill'].items():
            skills.append({
                'name': name,
                'executions': stats['executions'],
                'success_rate': stats['successes'] / stats['executions'] if stats['executions'] > 0 else 0,
                'avg_time': stats['avg_time'],
                'total_cost': stats['total_cost'],
                'total_tokens': stats['total_tokens']
            })
        
        # 排序
        if metric == 'executions':
            skills.sort(key=lambda x: x['executions'], reverse=True)
        elif metric == 'cost':
            skills.sort(key=lambda x: x['total_cost'], reverse=True)
        elif metric == 'tokens':
            skills.sort(key=lambda x: x['total_tokens'], reverse=True)
        
        return skills[:limit]
    
    def get_recent_failures(self, limit: int = 10) -> List[Dict]:
        """
        获取最近的失败记录
        
        Args:
            limit: 返回数量
        
        Returns:
            失败记录列表
        """
        failures = [
            {
                'skill_name': r.skill_name,
                'timestamp': datetime.fromtimestamp(r.timestamp).isoformat(),
                'model': r.model,
                'error': r.error
            }
            for r in reversed(self.records)
            if not r.success
        ]
        
        return failures[:limit]
    
    def get_performance_report(self, time_range: Optional[int] = None) -> Dict:
        """
        生成性能报告
        
        Args:
            time_range: 时间范围（秒），None表示全部
        
        Returns:
            性能报告
        """
        # 过滤时间范围
        if time_range:
            cutoff_time = time.time() - time_range
            filtered_records = [r for r in self.records if r.timestamp >= cutoff_time]
        else:
            filtered_records = self.records
        
        if not filtered_records:
            return {'message': 'No data available'}
        
        # 计算指标
        total = len(filtered_records)
        successes = sum(1 for r in filtered_records if r.success)
        failures = total - successes
        
        total_time = sum(r.duration for r in filtered_records)
        total_tokens = sum(r.tokens_used for r in filtered_records)
        total_cost = sum(r.cost for r in filtered_records)
        
        return {
            'time_range': f'{time_range}s' if time_range else 'all',
            'total_executions': total,
            'success_rate': successes / total if total > 0 else 0,
            'failure_rate': failures / total if total > 0 else 0,
            'avg_duration': total_time / total if total > 0 else 0,
            'total_tokens': total_tokens,
            'avg_tokens': total_tokens / total if total > 0 else 0,
            'total_cost': total_cost,
            'avg_cost': total_cost / total if total > 0 else 0,
            'mode_distribution': {
                'full': sum(1 for r in filtered_records if r.mode == 'full'),
                'followup': sum(1 for r in filtered_records if r.mode == 'followup')
            }
        }
    
    def check_alerts(self) -> List[Dict]:
        """
        检查告警条件
        
        Returns:
            告警列表
        """
        alerts = []
        
        # 检查成功率
        if self.stats['total_executions'] > 10:
            success_rate = self.stats['successful_executions'] / self.stats['total_executions']
            if success_rate < 0.9:
                alerts.append({
                    'type': 'low_success_rate',
                    'severity': 'warning',
                    'message': f'整体成功率较低: {success_rate:.2%}'
                })
        
        # 检查各Skill成功率
        for skill_name, stats in self.stats['by_skill'].items():
            if stats['executions'] > 5:
                success_rate = stats['successes'] / stats['executions']
                if success_rate < 0.8:
                    alerts.append({
                        'type': 'skill_low_success_rate',
                        'severity': 'warning',
                        'skill': skill_name,
                        'message': f'Skill {skill_name} 成功率较低: {success_rate:.2%}'
                    })
        
        # 检查平均耗时
        for skill_name, stats in self.stats['by_skill'].items():
            if stats['avg_time'] > 10.0:
                alerts.append({
                    'type': 'slow_skill',
                    'severity': 'info',
                    'skill': skill_name,
                    'message': f'Skill {skill_name} 平均耗时较长: {stats["avg_time"]:.2f}s'
                })
        
        # 检查成本
        if self.stats['total_cost'] > 100.0:
            alerts.append({
                'type': 'high_cost',
                'severity': 'warning',
                'message': f'总成本较高: ¥{self.stats["total_cost"]:.2f}'
            })
        
        return alerts
    
    def reset_stats(self):
        """重置统计信息"""
        self.records.clear()
        self.stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'total_tokens': 0,
            'total_cost': 0.0,
            'total_time': 0.0,
            'by_skill': {},
            'by_model': {},
            'by_mode': {'full': 0, 'followup': 0}
        }
        logger.info("统计信息已重置")


def get_skill_monitor() -> SkillMonitor:
    """获取Skill监控器单例"""
    if not hasattr(get_skill_monitor, '_instance'):
        get_skill_monitor._instance = SkillMonitor()
    return get_skill_monitor._instance
