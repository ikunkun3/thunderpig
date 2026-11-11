@echo off
title PTA 逐字输入 - 一键安装
setlocal enabledelayedexpansion
set "F=%~dp0thunderpig.user.js"
if not exist "%F%" (
  echo.
  echo   [X] 没找到 thunderpig.user.js
  echo       请把这个 bat 和 thunderpig.user.js 放在同一个文件夹里。
  echo.
  pause
  exit /b 1
)
echo.
echo   正在找浏览器...
set "B="
for %%P in (
  "%ProgramFiles%\Google\Chrome\Application\chrome.exe"
  "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
  "%LocalAppData%\Google\Chrome\Application\chrome.exe"
  "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"
  "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"
) do (
  if not defined B if exist %%P set "B=%%~P"
)
if defined B (
  echo   用 !B!
  start "" "!B!" "%F%"
) else (
  echo   没找到 Chrome / Edge，改用系统默认浏览器。
  start "" "%F%"
)
echo.
echo   ----------------------------------------------
echo   浏览器里应该弹出「安装脚本」的页面，点【安装】就完事。
echo   如果只看到满屏代码，说明还没装 Tampermonkey（油猴），
echo   先双击 安装.html 按提示装插件。
echo   ----------------------------------------------
echo.
timeout /t 8 >nul
exit /b 0
