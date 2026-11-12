@echo off
title PTA - 一键打开
setlocal enabledelayedexpansion
set "U=https://pintia.cn/problem-sets"
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
  start "" "!B!" "%U%"
) else (
  start "" "%U%"
)
echo.
echo   ----------------------------------------------
echo   进去以后：
echo     1. 点开一道编程题，进到能填代码的那一页
echo     2. 装了油猴脚本：右下角面板自己弹出来
echo        只装了书签：点一下书签栏里的那个书签
echo     3. 把代码粘进面板，点【敲进去】（书签版叫【写进代码框】）
echo     4. 打完自己去点【提交本题作答】
echo   ----------------------------------------------
echo.
timeout /t 8 >nul
exit /b 0
