@echo off
cd /d "%~dp0"
docker compose stop
if errorlevel 1 (
  echo Stoppen fehlgeschlagen. Bitte Docker Desktop und die Fehlermeldung pruefen.
  pause
  exit /b 1
)
echo Die Anwendung ist gestoppt. Ihre Daten bleiben erhalten.
pause
