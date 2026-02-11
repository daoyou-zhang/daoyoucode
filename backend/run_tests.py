"""
运行测试脚本
"""

import sys
import subprocess


def run_tests(args=None):
    """运行pytest测试"""
    cmd = ["pytest"]
    
    if args:
        cmd.extend(args)
    else:
        # 默认参数
        cmd.extend([
            "tests/llm",
            "-v",
            "--tb=short",
            "--cov=daoyoucode.llm",
            "--cov-report=term-missing",
            "--cov-report=html"
        ])
    
    print(f"运行命令: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode


if __name__ == "__main__":
    sys.exit(run_tests(sys.argv[1:]))
