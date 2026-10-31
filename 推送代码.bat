@echo off
chcp 65001>nul
title 推送代码到 Gitee / GitHub
cd /d "%~dp0.."
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0push.ps1"
