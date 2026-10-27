@echo off
cd /d "%~dp0"
echo Optionaler Docker-Start. Fuer den normalen Windows-Start STARTEN.cmd verwenden.
docker compose up -d --build
pause
