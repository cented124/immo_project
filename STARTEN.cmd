@echo off
setlocal DisableDelayedExpansion
chcp 65001 >nul
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\windows-start.ps1"
set "RW_RESULT=%errorlevel%"
pause
exit /b %RW_RESULT%
