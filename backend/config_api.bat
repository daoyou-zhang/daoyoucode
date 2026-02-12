@echo off
chcp 65001 >nul
echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║                                                          ║
echo ║     🔑 DaoyouCode API 配置向导                          ║
echo ║                                                          ║
echo ╚══════════════════════════════════════════════════════════╝
echo.
echo 请选择配置方式:
echo.
echo [1] 编辑配置文件 (推荐)
echo [2] 查看配置指南
echo [3] 测试当前配置
echo [0] 退出
echo.
set /p choice="请选择 (0-3): "

if "%choice%"=="1" goto edit_config
if "%choice%"=="2" goto view_guide
if "%choice%"=="3" goto test_config
if "%choice%"=="0" goto end

echo 无效选择
goto end

:edit_config
echo.
echo ========== 编辑配置文件 ==========
echo.
echo 正在打开配置文件...
echo 请按照以下步骤操作:
echo.
echo 1. 找到你要使用的提供商 (如 qwen)
echo 2. 将 api_key 替换为你的真实API密钥
echo 3. 将 enabled 改为 true
echo 4. 保存文件
echo.
pause
notepad config\llm_config.yaml
echo.
echo 配置文件已保存
goto test_config

:view_guide
echo.
echo ========== 配置指南 ==========
echo.
notepad config\API_CONFIG_GUIDE.md
goto end

:test_config
echo.
echo ========== 测试配置 ==========
echo.
.\venv\Scripts\python.exe daoyoucode.py doctor
echo.
echo ========== 测试Agent集成 ==========
echo.
.\venv\Scripts\python.exe test_agent_integration.py
goto end

:end
echo.
pause
