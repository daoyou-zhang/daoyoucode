@echo off
chcp 65001 >nul
echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║                                                          ║
echo ║     🎉 DaoyouCode CLI 演示                              ║
echo ║                                                          ║
echo ║     真实AI对话功能已就绪！                              ║
echo ║                                                          ║
echo ╚══════════════════════════════════════════════════════════╝
echo.
echo 准备启动交互式对话...
echo.
echo 💡 提示:
echo   • 输入 /help 查看所有命令
echo   • 输入 /exit 退出对话
echo   • 按 Ctrl+C 也可退出
echo.
pause
echo.
.\venv\Scripts\python.exe daoyoucode.py chat
