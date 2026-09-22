@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0RUN_DEMO.ps1" %*
exit /b %errorlevel%
