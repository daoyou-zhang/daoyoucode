@echo off
echo ============================================================
echo DaoyouCode 代码修改功能测试
echo ============================================================

echo.
echo [1/5] 创建测试文件...
echo # Test File > backend\test_modify.md
echo version: 1.0 >> backend\test_modify.md
echo timeout: 1800 >> backend\test_modify.md
echo ✓ 测试文件已创建: backend\test_modify.md

echo.
echo [2/5] 显示原始内容...
type backend\test_modify.md

echo.
echo [3/5] 测试修改功能...
echo 请在 DaoyouCode 中运行以下命令：
echo   daoyoucode chat "修改 backend/test_modify.md 文件，将 timeout: 1800 改为 timeout: 3600"
echo.
pause

echo.
echo [4/5] 显示修改后的内容...
type backend\test_modify.md

echo.
echo [5/5] 清理测试文件...
del backend\test_modify.md
echo ✓ 测试文件已删除

echo.
echo ============================================================
echo 测试完成
echo ============================================================
pause
