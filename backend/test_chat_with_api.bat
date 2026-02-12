@echo off
echo ========================================
echo 测试chat命令（真实API）
echo ========================================
echo.
echo 这将启动交互式对话，使用真实的通义千问API
echo.
echo 测试场景：
echo 1. 输入"你好" - 测试基本对话
echo 2. 输入"这个项目的结构是什么？" - 测试Agent是否主动调用repo_map工具
echo 3. 输入"backend/cli/commands/chat.py做什么的？" - 测试Agent是否主动调用read_file工具
echo.
echo 按任意键开始...
pause > nul
echo.

python -m cli.app chat

echo.
echo 测试完成！
pause
