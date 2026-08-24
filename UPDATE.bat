@echo off
cd /d "%~dp0"
if not exist "%~dp0tools\update.ps1" (
  echo   tools\update.ps1 not found. Run:  git pull
  pause
  exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\update.ps1"
