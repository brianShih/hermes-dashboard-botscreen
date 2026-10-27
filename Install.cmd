@echo off
setlocal
chcp 65001 >nul
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install.ps1" %*
set "BOT_SCREEN_EXIT=%ERRORLEVEL%"
echo.
if "%BOT_SCREEN_EXIT%"=="0" (echo Bot Screen installation completed.) else (echo Review the result above. Exit code: %BOT_SCREEN_EXIT%)
pause
exit /b %BOT_SCREEN_EXIT%
