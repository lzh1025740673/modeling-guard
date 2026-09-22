@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0INSTALL_STUDENT.ps1" %*
set "pack_exit=%ERRORLEVEL%"
if not "%STUDENT_PACK_NONINTERACTIVE%"=="1" pause
exit /b %pack_exit%
