"""
测试Skill监控器
"""

import pytest
import time

from daoyoucode.llm.skills import SkillMonitor, SkillExecutionRecord


class TestSkillMonitor:
    """测试SkillMonitor"""
    
    def test_init(self):
        """测试初始化"""
        monitor = SkillMonitor(max_records=100)
        assert monitor.max_records == 100
        assert len(monitor.records) == 0
        assert monitor.stats['total_executions'] == 0
    
    def test_record_execution_success(self):
        """测试记录成功执行"""
        monitor = SkillMonitor()
        
        monitor.record_execution(
            skill_name="test_skill",
            duration=1.5,
            success=True,
            model="qwen-max",
            tokens_used=100,
            cost=0.002,
            mode="full"
        )
        
        assert len(monitor.records) == 1
        assert monitor.stats['total_executions'] == 1
        assert monitor.stats['successful_executions'] == 1
        assert monitor.stats['failed_executions'] == 0
        assert monitor.stats['total_tokens'] == 100
        assert monitor.stats['total_cost'] == 0.002
    
    def test_record_execution_failure(self):
        """测试记录失败执行"""
        monitor = SkillMonitor()
        
        monitor.record_execution(
            skill_name="test_skill",
            duration=0.5,
            success=False,
            model="qwen-max",
            tokens_used=0,
            cost=0.0,
            mode="full",
            error="Timeout"
        )
        
        assert len(monitor.records) == 1
        assert monitor.stats['total_executions'] == 1
        assert monitor.stats['successful_executions'] == 0
        assert monitor.stats['failed_executions'] == 1
    
    def test_record_cleanup(self):
        """测试记录清理"""
        monitor = SkillMonitor(max_records=5)
        
        # 添加10条记录
        for i in range(10):
            monitor.record_execution(
                skill_name=f"skill_{i}",
                duration=1.0,
                success=True,
                model="qwen-max",
                tokens_used=100,
                cost=0.002,
                mode="full"
            )
        
        # 应该只保留最后5条
        assert len(monitor.records) == 5
        assert monitor.records[0].skill_name == "skill_5"
    
    def test_stats_by_skill(self):
        """测试按Skill统计"""
        monitor = SkillMonitor()
        
        # 记录多次执行
        for i in range(3):
            monitor.record_execution(
                skill_name="skill_a",
                duration=1.0,
                success=True,
                model="qwen-max",
                tokens_used=100,
                cost=0.002,
                mode="full"
            )
        
        for i in range(2):
            monitor.record_execution(
                skill_name="skill_b",
                duration=2.0,
                success=True,
                model="qwen-plus",
                tokens_used=50,
                cost=0.001,
                mode="followup"
            )
        
        # 验证统计
        assert 'skill_a' in monitor.stats['by_skill']
        assert 'skill_b' in monitor.stats['by_skill']
        
        skill_a_stats = monitor.stats['by_skill']['skill_a']
        assert skill_a_stats['executions'] == 3
        assert skill_a_stats['successes'] == 3
        assert skill_a_stats['total_tokens'] == 300
        
        skill_b_stats = monitor.stats['by_skill']['skill_b']
        assert skill_b_stats['executions'] == 2
        assert skill_b_stats['avg_time'] == 2.0
    
    def test_stats_by_model(self):
        """测试按模型统计"""
        monitor = SkillMonitor()
        
        monitor.record_execution(
            skill_name="test",
            duration=1.0,
            success=True,
            model="qwen-max",
            tokens_used=100,
            cost=0.002,
            mode="full"
        )
        
        monitor.record_execution(
            skill_name="test",
            duration=1.0,
            success=True,
            model="qwen-plus",
            tokens_used=50,
            cost=0.001,
            mode="full"
        )
        
        assert 'qwen-max' in monitor.stats['by_model']
        assert 'qwen-plus' in monitor.stats['by_model']
        
        assert monitor.stats['by_model']['qwen-max']['executions'] == 1
        assert monitor.stats['by_model']['qwen-plus']['executions'] == 1
    
    def test_get_stats(self):
        """测试获取统计信息"""
        monitor = SkillMonitor()
        
        monitor.record_execution(
            skill_name="test_skill",
            duration=1.0,
            success=True,
            model="qwen-max",
            tokens_used=100,
            cost=0.002,
            mode="full"
        )
        
        # 全局统计
        stats = monitor.get_stats()
        assert stats['total_executions'] == 1
        
        # 特定Skill统计
        skill_stats = monitor.get_stats('test_skill')
        assert skill_stats['executions'] == 1
        
        # 不存在的Skill
        empty_stats = monitor.get_stats('nonexistent')
        assert empty_stats == {}
    
    def test_get_top_skills(self):
        """测试获取热门Skill"""
        monitor = SkillMonitor()
        
        # 添加不同执行次数的Skill
        for i in range(5):
            monitor.record_execution(
                skill_name="skill_a",
                duration=1.0,
                success=True,
                model="qwen-max",
                tokens_used=100,
                cost=0.002,
                mode="full"
            )
        
        for i in range(3):
            monitor.record_execution(
                skill_name="skill_b",
                duration=1.0,
                success=True,
                model="qwen-max",
                tokens_used=100,
                cost=0.002,
                mode="full"
            )
        
        # 按执行次数排序
        top_skills = monitor.get_top_skills(limit=2, metric='executions')
        assert len(top_skills) == 2
        assert top_skills[0]['name'] == 'skill_a'
        assert top_skills[0]['executions'] == 5
        assert top_skills[1]['name'] == 'skill_b'
    
    def test_get_recent_failures(self):
        """测试获取最近失败"""
        monitor = SkillMonitor()
        
        # 添加成功和失败记录
        monitor.record_execution(
            skill_name="skill_a",
            duration=1.0,
            success=True,
            model="qwen-max",
            tokens_used=100,
            cost=0.002,
            mode="full"
        )
        
        monitor.record_execution(
            skill_name="skill_b",
            duration=0.5,
            success=False,
            model="qwen-max",
            tokens_used=0,
            cost=0.0,
            mode="full",
            error="Timeout"
        )
        
        monitor.record_execution(
            skill_name="skill_c",
            duration=0.3,
            success=False,
            model="qwen-max",
            tokens_used=0,
            cost=0.0,
            mode="full",
            error="Rate limit"
        )
        
        failures = monitor.get_recent_failures(limit=5)
        assert len(failures) == 2
        assert failures[0]['skill_name'] == 'skill_c'
        assert failures[0]['error'] == 'Rate limit'
    
    def test_get_performance_report(self):
        """测试性能报告"""
        monitor = SkillMonitor()
        
        # 添加一些记录
        for i in range(10):
            monitor.record_execution(
                skill_name="test",
                duration=1.0,
                success=i < 8,  # 80%成功率
                model="qwen-max",
                tokens_used=100,
                cost=0.002,
                mode="full"
            )
        
        report = monitor.get_performance_report()
        
        assert report['total_executions'] == 10
        assert report['success_rate'] == 0.8
        assert report['failure_rate'] == 0.2
        assert report['avg_duration'] == 1.0
        assert report['total_tokens'] == 1000
    
    def test_get_performance_report_with_time_range(self):
        """测试带时间范围的性能报告"""
        monitor = SkillMonitor()
        
        # 添加旧记录
        old_record = SkillExecutionRecord(
            skill_name="old",
            timestamp=time.time() - 3600,  # 1小时前
            duration=1.0,
            success=True,
            model="qwen-max",
            tokens_used=100,
            cost=0.002,
            mode="full"
        )
        monitor.records.append(old_record)
        
        # 添加新记录
        monitor.record_execution(
            skill_name="new",
            duration=1.0,
            success=True,
            model="qwen-max",
            tokens_used=100,
            cost=0.002,
            mode="full"
        )
        
        # 只统计最近10分钟
        report = monitor.get_performance_report(time_range=600)
        assert report['total_executions'] == 1
    
    def test_check_alerts(self):
        """测试告警检查"""
        monitor = SkillMonitor()
        
        # 添加低成功率的记录
        for i in range(20):
            monitor.record_execution(
                skill_name="test",
                duration=1.0,
                success=i < 10,  # 50%成功率
                model="qwen-max",
                tokens_used=100,
                cost=0.002,
                mode="full"
            )
        
        alerts = monitor.check_alerts()
        
        # 应该有低成功率告警
        assert len(alerts) > 0
        assert any(a['type'] == 'low_success_rate' for a in alerts)
    
    def test_check_alerts_slow_skill(self):
        """测试慢Skill告警"""
        monitor = SkillMonitor()
        
        # 添加慢Skill
        for i in range(5):
            monitor.record_execution(
                skill_name="slow_skill",
                duration=15.0,  # 很慢
                success=True,
                model="qwen-max",
                tokens_used=100,
                cost=0.002,
                mode="full"
            )
        
        alerts = monitor.check_alerts()
        
        # 应该有慢Skill告警
        assert any(a['type'] == 'slow_skill' for a in alerts)
    
    def test_reset_stats(self):
        """测试重置统计"""
        monitor = SkillMonitor()
        
        # 添加一些记录
        monitor.record_execution(
            skill_name="test",
            duration=1.0,
            success=True,
            model="qwen-max",
            tokens_used=100,
            cost=0.002,
            mode="full"
        )
        
        assert len(monitor.records) > 0
        assert monitor.stats['total_executions'] > 0
        
        # 重置
        monitor.reset_stats()
        
        assert len(monitor.records) == 0
        assert monitor.stats['total_executions'] == 0
