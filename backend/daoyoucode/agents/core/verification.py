"""
独立验证机制

不信任子Agent的输出，通过独立验证确保结果可靠性。
灵感来自daoyouCodePilot的验证机制。
"""

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class VerificationLevel(Enum):
    """验证级别"""
    NONE = "none"           # 不验证
    BASIC = "basic"         # 基础验证（语法检查）
    STANDARD = "standard"   # 标准验证（语法+构建）
    STRICT = "strict"       # 严格验证（语法+构建+测试）


@dataclass
class VerificationResult:
    """验证结果"""
    passed: bool                          # 是否通过
    level: VerificationLevel              # 验证级别
    diagnostics_passed: bool = True       # 诊断是否通过
    build_passed: bool = True             # 构建是否通过
    tests_passed: bool = True             # 测试是否通过
    file_check_passed: bool = True        # 文件检查是否通过
    errors: List[str] = None              # 错误列表
    warnings: List[str] = None            # 警告列表
    details: Dict[str, Any] = None        # 详细信息
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.details is None:
            self.details = {}


class VerificationManager:
    """
    验证管理器
    
    不信任子Agent的输出，通过独立验证确保结果可靠性：
    1. 运行LSP诊断（语法、类型检查）
    2. 运行构建命令
    3. 运行测试套件
    4. 检查修改的文件
    """
    
    _instance = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化验证管理器"""
        if self._initialized:
            return
        
        self.project_root: Optional[Path] = None
        self.build_command: Optional[str] = None
        self.test_command: Optional[str] = None
        self.timeout: int = 300  # 5分钟超时
        
        self._initialized = True
        logger.info("验证管理器初始化完成")
    
    def configure(
        self,
        project_root: Path,
        build_command: Optional[str] = None,
        test_command: Optional[str] = None,
        timeout: int = 300
    ):
        """
        配置验证管理器
        
        Args:
            project_root: 项目根目录
            build_command: 构建命令（如 "npm run build", "python -m build"）
            test_command: 测试命令（如 "npm test", "pytest"）
            timeout: 超时时间（秒）
        """
        self.project_root = project_root
        self.build_command = build_command
        self.test_command = test_command
        self.timeout = timeout
        
        logger.info(f"验证管理器配置完成: root={project_root}, build={build_command}, test={test_command}")
    
    async def verify(
        self,
        result: Dict[str, Any],
        level: VerificationLevel = VerificationLevel.STANDARD,
        modified_files: Optional[List[Path]] = None
    ) -> VerificationResult:
        """
        验证执行结果
        
        Args:
            result: 执行结果
            level: 验证级别
            modified_files: 修改的文件列表
        
        Returns:
            验证结果
        """
        if level == VerificationLevel.NONE:
            return VerificationResult(
                passed=True,
                level=level,
                details={'message': '跳过验证'}
            )
        
        logger.info(f"开始验证，级别: {level.value}")
        
        verification = VerificationResult(passed=True, level=level)
        
        # 1. 运行诊断（所有级别都需要）
        if level in [VerificationLevel.BASIC, VerificationLevel.STANDARD, VerificationLevel.STRICT]:
            diagnostics_result = await self._run_diagnostics(modified_files)
            verification.diagnostics_passed = diagnostics_result['passed']
            if not diagnostics_result['passed']:
                verification.passed = False
                verification.errors.extend(diagnostics_result.get('errors', []))
            verification.details['diagnostics'] = diagnostics_result
        
        # 2. 运行构建（标准和严格级别）
        if level in [VerificationLevel.STANDARD, VerificationLevel.STRICT]:
            if self.build_command:
                build_result = await self._run_build()
                verification.build_passed = build_result['passed']
                if not build_result['passed']:
                    verification.passed = False
                    verification.errors.extend(build_result.get('errors', []))
                verification.details['build'] = build_result
            else:
                verification.warnings.append("未配置构建命令，跳过构建验证")
        
        # 3. 运行测试（严格级别）
        if level == VerificationLevel.STRICT:
            if self.test_command:
                test_result = await self._run_tests()
                verification.tests_passed = test_result['passed']
                if not test_result['passed']:
                    verification.passed = False
                    verification.errors.extend(test_result.get('errors', []))
                verification.details['tests'] = test_result
            else:
                verification.warnings.append("未配置测试命令，跳过测试验证")
        
        # 4. 检查修改的文件
        if modified_files:
            file_check_result = await self._check_modified_files(modified_files)
            verification.file_check_passed = file_check_result['passed']
            if not file_check_result['passed']:
                verification.passed = False
                verification.errors.extend(file_check_result.get('errors', []))
            verification.details['file_check'] = file_check_result
        
        logger.info(f"验证完成: passed={verification.passed}, errors={len(verification.errors)}")
        return verification
    
    async def _run_diagnostics(self, files: Optional[List[Path]] = None) -> Dict[str, Any]:
        """
        运行LSP诊断
        
        检查语法错误、类型错误等
        """
        try:
            logger.info("运行LSP诊断...")
            
            # 这里应该调用实际的LSP诊断工具
            # 示例：使用pylint、mypy、eslint等
            
            # 模拟诊断结果
            errors = []
            warnings = []
            
            # TODO: 实际实现应该调用LSP工具
            # 例如：
            # if files:
            #     for file in files:
            #         result = await self._run_lsp_diagnostic(file)
            #         errors.extend(result['errors'])
            #         warnings.extend(result['warnings'])
            
            return {
                'passed': len(errors) == 0,
                'errors': errors,
                'warnings': warnings,
                'details': {
                    'files_checked': len(files) if files else 0,
                }
            }
        
        except Exception as e:
            logger.error(f"诊断失败: {e}")
            return {
                'passed': False,
                'errors': [f"诊断失败: {str(e)}"],
                'warnings': [],
            }
    
    async def _run_build(self) -> Dict[str, Any]:
        """运行构建命令"""
        try:
            logger.info(f"运行构建命令: {self.build_command}")
            
            # 运行构建命令
            process = await asyncio.create_subprocess_shell(
                self.build_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.project_root
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                return {
                    'passed': False,
                    'errors': [f"构建超时（{self.timeout}秒）"],
                    'warnings': [],
                }
            
            passed = process.returncode == 0
            
            return {
                'passed': passed,
                'errors': [] if passed else [stderr.decode('utf-8', errors='ignore')],
                'warnings': [],
                'details': {
                    'returncode': process.returncode,
                    'stdout': stdout.decode('utf-8', errors='ignore'),
                }
            }
        
        except Exception as e:
            logger.error(f"构建失败: {e}")
            return {
                'passed': False,
                'errors': [f"构建失败: {str(e)}"],
                'warnings': [],
            }
    
    async def _run_tests(self) -> Dict[str, Any]:
        """运行测试套件"""
        try:
            logger.info(f"运行测试命令: {self.test_command}")
            
            # 运行测试命令
            process = await asyncio.create_subprocess_shell(
                self.test_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.project_root
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                return {
                    'passed': False,
                    'errors': [f"测试超时（{self.timeout}秒）"],
                    'warnings': [],
                }
            
            passed = process.returncode == 0
            
            return {
                'passed': passed,
                'errors': [] if passed else [stderr.decode('utf-8', errors='ignore')],
                'warnings': [],
                'details': {
                    'returncode': process.returncode,
                    'stdout': stdout.decode('utf-8', errors='ignore'),
                }
            }
        
        except Exception as e:
            logger.error(f"测试失败: {e}")
            return {
                'passed': False,
                'errors': [f"测试失败: {str(e)}"],
                'warnings': [],
            }
    
    async def _check_modified_files(self, files: List[Path]) -> Dict[str, Any]:
        """
        检查修改的文件
        
        验证：
        1. 文件是否存在
        2. 文件是否可读
        3. 文件大小是否合理
        """
        try:
            logger.info(f"检查 {len(files)} 个修改的文件...")
            
            errors = []
            warnings = []
            
            for file in files:
                # 检查文件是否存在
                if not file.exists():
                    errors.append(f"文件不存在: {file}")
                    continue
                
                # 检查文件是否可读
                if not file.is_file():
                    errors.append(f"不是文件: {file}")
                    continue
                
                # 检查文件大小
                size = file.stat().st_size
                if size == 0:
                    warnings.append(f"文件为空: {file}")
                elif size > 10 * 1024 * 1024:  # 10MB
                    warnings.append(f"文件过大: {file} ({size / 1024 / 1024:.1f}MB)")
            
            return {
                'passed': len(errors) == 0,
                'errors': errors,
                'warnings': warnings,
                'details': {
                    'files_checked': len(files),
                    'files_ok': len(files) - len(errors),
                }
            }
        
        except Exception as e:
            logger.error(f"文件检查失败: {e}")
            return {
                'passed': False,
                'errors': [f"文件检查失败: {str(e)}"],
                'warnings': [],
            }


def get_verification_manager() -> VerificationManager:
    """获取验证管理器单例"""
    return VerificationManager()
