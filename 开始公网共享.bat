@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Shiguangli Public Share
echo.
echo   Starting public share ... (any network can access)
echo.
where python >nul 2>nul
if %errorlevel%==0 (
  python 公网启动器.py
  goto end
)
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 公网启动器.py
  goto end
)
echo   [!] Python not found. Please install Python first.
echo.
:end
pause
