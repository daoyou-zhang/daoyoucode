@echo off
REM DaoyouCode CLI 演示脚本

echo ========================================
echo DaoyouCode CLI 演示
echo ========================================
echo.

call venv\Scripts\activate.bat

echo [1/6] 查看帮助
python daoyoucode.py --help
echo.
pause

echo [2/6] 查看版本
python daoyoucode.py version
echo.
pause

echo [3/6] 环境诊断
python daoyoucode.py doctor
echo.
pause

echo [4/6] 列出Agent
python daoyoucode.py agent
echo.
pause

echo [5/6] 列出模型
python daoyoucode.py models
echo.
pause

echo [6/6] 查看会话列表
python daoyoucode.py session list
echo.

echo ========================================
echo 演示完成！
echo ========================================
pause
