#!/usr/bin/env python
"""
DaoyouCode CLI 入口
"""

import sys
from pathlib import Path

# 添加backend到路径
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# 导入并运行
from cli.app import main

if __name__ == "__main__":
    main()
