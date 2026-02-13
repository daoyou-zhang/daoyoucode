@echo off
cd /d %~dp0
echo 测试实际的chat命令
echo.
echo 输入: 你好
echo.
echo 你好 | python -m cli.app chat
