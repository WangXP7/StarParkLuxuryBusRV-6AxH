@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 打开 http://localhost:8863/ 查看星泊房车。关闭此窗口可停止服务器。
where py >nul 2>nul
if not errorlevel 1 (
  start "" "http://localhost:8863/"
  py -m http.server 8863 --bind 127.0.0.1
  exit /b
)
where python >nul 2>nul
if not errorlevel 1 (
  start "" "http://localhost:8863/"
  python -m http.server 8863 --bind 127.0.0.1
  exit /b
)
if exist "C:\Users\USER\.cache\PRIVACY-REDACTED\codex-primary-runtime\dependencies\python\python.exe" (
  start "" "http://localhost:8863/"
  "C:\Users\USER\.cache\PRIVACY-REDACTED\codex-primary-runtime\dependencies\python\python.exe" -m http.server 8863 --bind 127.0.0.1
  exit /b
)
echo 未检测到 Python。可双击本目录中的 standalone.html，或将此目录上传到网站。
pause
