@echo off
chcp 936 >nul
title ThunderPig - 打包
setlocal
cd /d "%~dp0"

echo.
echo   ==============================================
echo    ThunderPig 打包
echo   ==============================================
echo.

echo   [1/5] 检查 Python...
where python >nul 2>nul
if errorlevel 1 (
  echo         找不到 python。先去 python.org 装一个，装的时候勾
  echo         "Add Python to PATH"。
  goto :fail
)
for /f "delims=" %%v in ('python --version 2^>^&1') do echo         %%v

echo.
echo   [2/5] 检查 PyInstaller...
python -c "import PyInstaller" >nul 2>nul
if errorlevel 1 (
  echo         没装，正在装...
  python -m pip install --upgrade pyinstaller
  if errorlevel 1 goto :fail
) else (
  echo         已装
)

echo.
echo   [3/5] 检查图标文件...
if not exist "ThunderPig.ico" (
  echo         缺 ThunderPig.ico，先跑一次：python 生成图标.py
  goto :fail
)
if not exist "ThunderPig-64.png" (
  echo         缺 ThunderPig-64.png，先跑一次：python 生成图标.py
  goto :fail
)
echo         两个都在

echo.
echo   [4/5] 先把正在跑的老 exe 关掉...
taskkill /f /im ThunderPig.exe >nul 2>nul
if errorlevel 1 (
  echo         没有在跑的进程
) else (
  echo         已关闭
  timeout /t 1 >nul
)

echo.
echo   [5/5] 开始打包（一分钟左右，别关窗口）...
echo.
python -m PyInstaller --noconfirm --onefile --noconsole --name "ThunderPig" ^
  --icon "%~dp0ThunderPig.ico" ^
  --add-data "%~dp0ThunderPig.ico;." ^
  --add-data "%~dp0ThunderPig-64.png;." ^
  --distpath build_typer\dist ^
  --workpath build_typer\work ^
  --specpath build_typer ^
  thunderpig.py
if errorlevel 1 goto :fail

echo.
echo   复制到当前目录...
copy /y "build_typer\dist\ThunderPig.exe" "ThunderPig.exe" >nul
if errorlevel 1 (
  echo         复制失败。如果提示文件被占用，把 ThunderPig.exe 关掉再来。
  goto :fail
)

echo.
echo   ==============================================
echo    好了：ThunderPig.exe
echo   ==============================================
for %%f in ("ThunderPig.exe") do echo    大小 %%~zf 字节
echo.
echo   想验证它能不能跑（不弹窗口、只测按键序列）：
echo       ThunderPig.exe --selftest selftest.log
echo.
goto :done

:fail
echo.
echo   ==============================================
echo    失败了，看上面哪一步报的红字
echo   ==============================================

:done
echo.
pause
endlocal
