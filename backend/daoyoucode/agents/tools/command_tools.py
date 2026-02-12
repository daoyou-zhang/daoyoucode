"""
命令执行工具

提供shell命令执行功能
"""

from typing import Dict, Any, Optional
import subprocess
import asyncio
from .base import BaseTool, ToolResult


class RunCommandTool(BaseTool):
    """运行命令工具"""
    
    def __init__(self):
        super().__init__(
            name="run_command",
            description="执行shell命令"
        )
    
    async def execute(
        self,
        command: str,
        cwd: Optional[str] = None,
        timeout: int = 30,
        shell: bool = True
    ) -> ToolResult:
        """
        执行命令
        
        Args:
            command: 命令字符串
            cwd: 工作目录
            timeout: 超时时间（秒）
            shell: 是否使用shell
        """
        try:
            # 使用asyncio.create_subprocess_shell实现异步执行
            if shell:
                process = await asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=cwd
                )
            else:
                process = await asyncio.create_subprocess_exec(
                    *command.split(),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=cwd
                )
            
            # 等待完成（带超时）
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ToolResult(
                    success=False,
                    content=None,
                    error=f"Command timed out after {timeout} seconds"
                )
            
            # 解码输出
            stdout_str = stdout.decode('utf-8', errors='ignore')
            stderr_str = stderr.decode('utf-8', errors='ignore')
            
            success = process.returncode == 0
            
            return ToolResult(
                success=success,
                content={
                    'stdout': stdout_str,
                    'stderr': stderr_str,
                    'returncode': process.returncode
                },
                error=stderr_str if not success else None,
                metadata={
                    'command': command,
                    'cwd': cwd,
                    'returncode': process.returncode
                }
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content=None,
                error=str(e)
            )
    
    def get_function_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "要执行的命令"
                    },
                    "cwd": {
                        "type": "string",
                        "description": "工作目录"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "超时时间（秒）",
                        "default": 30
                    },
                    "shell": {
                        "type": "boolean",
                        "description": "是否使用shell",
                        "default": True
                    }
                },
                "required": ["command"]
            }
        }


class RunTestTool(BaseTool):
    """运行测试工具"""
    
    def __init__(self):
        super().__init__(
            name="run_test",
            description="运行测试（支持pytest、unittest等）"
        )
    
    async def execute(
        self,
        test_path: Optional[str] = None,
        test_framework: str = "pytest",
        cwd: Optional[str] = None,
        timeout: int = 60
    ) -> ToolResult:
        """
        运行测试
        
        Args:
            test_path: 测试文件或目录路径
            test_framework: 测试框架（pytest/unittest/jest等）
            cwd: 工作目录
            timeout: 超时时间（秒）
        """
        try:
            # 构建命令
            if test_framework == "pytest":
                command = "pytest"
                if test_path:
                    command += f" {test_path}"
                command += " -v"
            elif test_framework == "unittest":
                command = "python -m unittest"
                if test_path:
                    command += f" {test_path}"
            elif test_framework == "jest":
                command = "npm test"
                if test_path:
                    command += f" -- {test_path}"
            else:
                return ToolResult(
                    success=False,
                    content=None,
                    error=f"Unsupported test framework: {test_framework}"
                )
            
            # 执行命令
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ToolResult(
                    success=False,
                    content=None,
                    error=f"Test timed out after {timeout} seconds"
                )
            
            stdout_str = stdout.decode('utf-8', errors='ignore')
            stderr_str = stderr.decode('utf-8', errors='ignore')
            
            success = process.returncode == 0
            
            # 解析测试结果
            result_info = self._parse_test_output(
                stdout_str,
                stderr_str,
                test_framework
            )
            
            return ToolResult(
                success=success,
                content={
                    'stdout': stdout_str,
                    'stderr': stderr_str,
                    'returncode': process.returncode,
                    **result_info
                },
                error=stderr_str if not success else None,
                metadata={
                    'test_path': test_path,
                    'test_framework': test_framework,
                    'cwd': cwd
                }
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content=None,
                error=str(e)
            )
    
    def _parse_test_output(
        self,
        stdout: str,
        stderr: str,
        framework: str
    ) -> Dict[str, Any]:
        """解析测试输出"""
        result = {
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'total': 0
        }
        
        if framework == "pytest":
            # 解析pytest输出
            import re
            match = re.search(r'(\d+) passed', stdout)
            if match:
                result['passed'] = int(match.group(1))
            match = re.search(r'(\d+) failed', stdout)
            if match:
                result['failed'] = int(match.group(1))
            match = re.search(r'(\d+) skipped', stdout)
            if match:
                result['skipped'] = int(match.group(1))
            result['total'] = result['passed'] + result['failed'] + result['skipped']
        
        return result
    
    def get_function_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "test_path": {
                        "type": "string",
                        "description": "测试文件或目录路径"
                    },
                    "test_framework": {
                        "type": "string",
                        "description": "测试框架（pytest/unittest/jest）",
                        "default": "pytest"
                    },
                    "cwd": {
                        "type": "string",
                        "description": "工作目录"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "超时时间（秒）",
                        "default": 60
                    }
                },
                "required": []
            }
        }
