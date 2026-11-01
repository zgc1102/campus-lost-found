@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ==========================================
echo  清华校园拾光里 - 线上压测
echo  目标：https://shiguangli.work
echo ==========================================
echo.

echo [1/2] 首页：300 请求 / 30 并发
python scripts\loadtest.py --base https://shiguangli.work --path / --requests 300 --concurrency 30 --connect-ip 104.21.15.101 --timeout 20 --out 压测-首页.json
if errorlevel 1 echo 压测失败，请确认已安装 Python 并在 PATH 中。

echo.
echo [2/2] 接口：200 请求 / 20 并发
python scripts\loadtest.py --base https://shiguangli.work --path /api/items --requests 200 --concurrency 20 --connect-ip 104.21.15.101 --timeout 20 --out 压测-接口.json

echo.
echo 结果已保存到：
echo   压测-首页.json
echo   压测-接口.json
echo.
pause
