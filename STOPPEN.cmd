@echo off
setlocal DisableDelayedExpansion
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\windows-start.ps1" -Action stop
set "RW_RESULT=%errorlevel%"
pause
exit /b %RW_RESULT%
