@echo off
title VidCode AI Studio
echo.
echo  =====================================================
echo   VidCode AI Studio — Interactive Video Generator
echo  =====================================================
echo.
cd /d "%~dp0"
backend\.venv\Scripts\python.exe vidcode_cli.py
pause

