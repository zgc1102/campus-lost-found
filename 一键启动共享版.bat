@echo off
chcp 65001 >nul
cd /d "%~dp0"
title 清华校园拾光里 · 共享版
set SG_OPEN=1
echo.
echo   正在启动共享版...
echo.
where python >nul 2>nul
if %errorlevel%==0 (
  python server.py
  goto end
)
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 server.py
  goto end
)
echo   [!] 没有找到 Python。
echo       请到 https://www.python.org/downloads/ 安装，
echo       安装时勾选 "Add python.exe to PATH"。
echo.
:end
pause
