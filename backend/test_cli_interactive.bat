@echo off
chcp 65001 >nul
echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║                                                          ║
echo ║     🧪 DaoyouCode CLI 交互式测试                        ║
echo ║                                                          ║
echo ╚══════════════════════════════════════════════════════════╝
echo.
echo 选择测试模式:
echo.
echo [1] 测试 chat 命令 (模拟模式)
echo [2] 测试 edit 命令 (模拟模式)
echo [3] 测试 doctor 命令
echo [4] 测试 models 命令
echo [5] 测试 agent 命令
echo [6] 查看帮助
echo [0] 退出
echo.
set /p choice="请选择 (0-6): "

if "%choice%"=="1" goto test_chat
if "%choice%"=="2" goto test_edit
if "%choice%"=="3" goto test_doctor
if "%choice%"=="4" goto test_models
if "%choice%"=="5" goto test_agent
if "%choice%"=="6" goto test_help
if "%choice%"=="0" goto end

echo 无效选择
goto end

:test_chat
echo.
echo ========== 测试 chat 命令 ==========
echo.
echo 提示: 这将启动交互式对话
echo       输入 /help 查看命令
echo       输入 /exit 退出
echo.
pause
.\venv\Scripts\python.exe daoyoucode.py chat
goto end

:test_edit
echo.
echo ========== 测试 edit 命令 ==========
echo.
echo 创建测试文件...
echo # TODO: Add code here > test_temp.py
echo.
echo 执行编辑命令...
.\venv\Scripts\python.exe daoyoucode.py edit test_temp.py "添加一个hello world函数"
echo.
echo 查看结果...
type test_temp.py
echo.
echo 清理测试文件...
del test_temp.py
goto end

:test_doctor
echo.
echo ========== 测试 doctor 命令 ==========
echo.
.\venv\Scripts\python.exe daoyoucode.py doctor
goto end

:test_models
echo.
echo ========== 测试 models 命令 ==========
echo.
.\venv\Scripts\python.exe daoyoucode.py models
goto end

:test_agent
echo.
echo ========== 测试 agent 命令 ==========
echo.
.\venv\Scripts\python.exe daoyoucode.py agent
goto end

:test_help
echo.
echo ========== 查看帮助 ==========
echo.
.\venv\Scripts\python.exe daoyoucode.py --help
goto end

:end
echo.
pause
