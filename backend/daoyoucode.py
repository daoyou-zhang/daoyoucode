#!/usr/bin/env python
"""
DaoyouCode CLI 启动脚本

直接运行: python daoyoucode.py --help
"""

import sys
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

# 导入并运行
from cli.app import main

if __name__ == "__main__":
    main()
