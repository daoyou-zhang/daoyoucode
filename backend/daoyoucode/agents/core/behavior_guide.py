"""
Agent行为指南

提供结构化的Agent行为指导，让Agent行为更可预测。
灵感来源：oh-my-opencode的Sisyphus行为指南
"""

from typing import Dict, List, Any, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class Phase(Enum):
    """执行阶段"""
    INTENT_GATE = "intent_gate"                    # 意图识别
    CODEBASE_ASSESSMENT = "codebase_assessment"    # 代码库评估
    EXPLORATION = "exploration"                     # 探索研究
    IMPLEMENTATION = "implementation"               # 实现
    FAILURE_RECOVERY = "failure_recovery"          # 失败恢复
    COMPLETION = "completion"                       # 完成


class RequestType(Enum):
    """请求类型"""
    SKILL_MATCH = "skill_match"      # 匹配Skill
    TRIVIAL = "trivial"              # 简单任务
    EXPLICIT = "explicit"            # 明确任务
    EXPLORATORY = "exploratory"      # 探索性任务
    OPEN_ENDED = "open_ended"        # 开放性任务
    GITHUB_WORK = "github_work"      # GitHub工作
    AMBIGUOUS = "ambiguous"          # 模糊任务


class CodebaseState(Enum):
    """代码库状态"""
    DISCIPLINED = "disciplined"      # 规范的
    TRANSITIONAL = "transitional"    # 过渡的
    LEGACY = "legacy"                # 遗留的
    CHAOTIC = "chaotic"              # 混乱的
    GREENFIELD = "greenfield"        # 新项目


class BehaviorGuide:
    """Agent行为指南"""
    
    # 阶段定义
    PHASES = {
        Phase.INTENT_GATE: {
            'description': '意图识别和分类',
            'steps': [
                '检查是否匹配Skill触发器',
                '分类请求类型',
                '验证假设和范围',
                '检查是否需要澄清',
            ],
            'decision_rules': {
                RequestType.SKILL_MATCH: 'invoke_skill_immediately',
                RequestType.TRIVIAL: 'use_direct_tools',
                RequestType.EXPLICIT: 'execute_directly',
                RequestType.EXPLORATORY: 'fire_explore_parallel',
                RequestType.OPEN_ENDED: 'assess_codebase_first',
                RequestType.GITHUB_WORK: 'full_cycle_workflow',
                RequestType.AMBIGUOUS: 'ask_clarification',
            }
        },
        Phase.CODEBASE_ASSESSMENT: {
            'description': '评估代码库状态',
            'steps': [
                '检查配置文件（linter, formatter, type config）',
                '采样2-3个相似文件检查一致性',
                '识别项目成熟度信号',
                '分类代码库状态',
            ],
            'state_behaviors': {
                CodebaseState.DISCIPLINED: 'follow_existing_patterns_strictly',
                CodebaseState.TRANSITIONAL: 'ask_which_pattern_to_follow',
                CodebaseState.LEGACY: 'modernize_with_caution',
                CodebaseState.CHAOTIC: 'propose_best_practices',
                CodebaseState.GREENFIELD: 'apply_modern_standards',
            }
        },
        Phase.EXPLORATION: {
            'description': '探索和研究',
            'steps': [
                '选择合适的工具（grep/glob/lsp/explore）',
                '并行执行探索任务',
                '收集背景任务结果',
                '判断是否需要更多信息',
            ],
            'stop_conditions': [
                '有足够的上下文可以自信地继续',
                '相同信息在多个来源中出现',
                '2次搜索迭代没有新的有用数据',
                '找到直接答案',
            ]
        },
        Phase.IMPLEMENTATION: {
            'description': '实现',
            'steps': [
                '如果任务有2+步骤，立即创建todo列表',
                '开始前标记任务为in_progress',
                '完成后立即标记为completed',
                '验证结果',
            ],
            'verification_requirements': {
                'file_edit': 'lsp_diagnostics_clean',
                'build_command': 'exit_code_0',
                'test_run': 'all_pass_or_note_preexisting',
                'delegation': 'agent_result_verified',
            }
        },
        Phase.FAILURE_RECOVERY: {
            'description': '失败恢复',
            'steps': [
                '修复根本原因，而非症状',
                '每次修复尝试后重新验证',
                '避免随机调试',
            ],
            'after_3_failures': [
                'STOP所有进一步的编辑',
                'REVERT到最后已知的工作状态',
                'DOCUMENT尝试了什么以及失败了什么',
                'CONSULT Oracle或ASK USER',
            ]
        },
        Phase.COMPLETION: {
            'description': '完成',
            'completion_criteria': [
                '所有计划的todo项目标记为完成',
                '变更文件的诊断清洁',
                '构建通过（如果适用）',
                '用户的原始请求完全满足',
            ],
            'before_final_answer': [
                '取消所有运行中的背景任务',
                '保存资源并确保清洁的工作流完成',
            ]
        }
    }
    
    @classmethod
    def get_phase_guide(cls, phase: Phase) -> Dict[str, Any]:
        """获取阶段指南"""
        return cls.PHASES.get(phase, {})
    
    @classmethod
    def classify_request(cls, instruction: str) -> RequestType:
        """
        分类请求类型
        
        Args:
            instruction: 用户指令
        
        Returns:
            请求类型
        """
        instruction_lower = instruction.lower()
        
        # 检查GitHub工作模式
        github_patterns = [
            'look into',
            'create pr',
            'make pr',
            'investigate',
            '@',  # 提及
        ]
        if any(pattern in instruction_lower for pattern in github_patterns):
            return RequestType.GITHUB_WORK
        
        # 检查探索性任务
        exploratory_patterns = [
            'how does',
            'find',
            'search',
            'locate',
            '如何',
            '查找',
            '搜索',
        ]
        if any(pattern in instruction_lower for pattern in exploratory_patterns):
            return RequestType.EXPLORATORY
        
        # 检查开放性任务
        open_ended_patterns = [
            'improve',
            'refactor',
            'add feature',
            'optimize',
            '改进',
            '重构',
            '添加功能',
            '优化',
        ]
        if any(pattern in instruction_lower for pattern in open_ended_patterns):
            return RequestType.OPEN_ENDED
        
        # 检查明确任务
        explicit_patterns = [
            'file:',
            'line:',
            'function:',
            'class:',
        ]
        if any(pattern in instruction_lower for pattern in explicit_patterns):
            return RequestType.EXPLICIT
        
        # 检查简单任务
        if len(instruction) < 50:
            return RequestType.TRIVIAL
        
        # 默认为模糊任务
        return RequestType.AMBIGUOUS
    
    @classmethod
    def get_action_for_request(cls, request_type: RequestType) -> str:
        """获取请求类型对应的行动"""
        phase_guide = cls.get_phase_guide(Phase.INTENT_GATE)
        return phase_guide['decision_rules'].get(request_type, 'ask_clarification')
    
    @classmethod
    def should_ask_clarification(
        cls,
        instruction: str,
        multiple_interpretations: bool = False,
        effort_difference: float = 1.0,
        missing_critical_info: bool = False
    ) -> bool:
        """
        判断是否需要澄清
        
        Args:
            instruction: 指令
            multiple_interpretations: 是否有多种解释
            effort_difference: 不同解释的工作量差异（倍数）
            missing_critical_info: 是否缺少关键信息
        
        Returns:
            是否需要澄清
        """
        # 缺少关键信息，必须询问
        if missing_critical_info:
            return True
        
        # 多种解释且工作量差异大（2倍以上），必须询问
        if multiple_interpretations and effort_difference >= 2.0:
            return True
        
        # 指令太短且模糊
        if len(instruction) < 20 and cls.classify_request(instruction) == RequestType.AMBIGUOUS:
            return True
        
        return False
    
    @classmethod
    def format_clarification_question(
        cls,
        understood: str,
        unsure_about: str,
        options: List[Dict[str, str]],
        recommendation: Optional[str] = None
    ) -> str:
        """
        格式化澄清问题
        
        Args:
            understood: 理解的内容
            unsure_about: 不确定的内容
            options: 选项列表 [{'option': '...', 'implications': '...'}]
            recommendation: 推荐方案
        """
        lines = [
            "我想确保我理解正确。",
            "",
            f"**我理解的内容**: {understood}",
            f"**我不确定的内容**: {unsure_about}",
            "",
            "**我看到的选项**:",
        ]
        
        for i, option in enumerate(options, 1):
            lines.append(f"{i}. {option['option']} - {option['implications']}")
        
        if recommendation:
            lines.append("")
            lines.append(f"**我的建议**: {recommendation}")
        
        lines.append("")
        lines.append("您希望我按照哪个方案进行？")
        
        return "\n".join(lines)


# 便捷函数
def get_behavior_guide() -> BehaviorGuide:
    """获取行为指南实例"""
    return BehaviorGuide()
