@echo off
chcp 65001>nul
title 重置启动密码
cd /d "%~dp0"
python 重置启动密码.py
