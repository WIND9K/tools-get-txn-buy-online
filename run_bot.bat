@echo off
REM ============================
REM Onus Process Txn - Run B1
REM Double click để chạy listener
REM ============================

cd /d "%~dp0"
set "PY_EXE=python"
if exist ".\venv\Scripts\python.exe" set "PY_EXE=.\venv\Scripts\python.exe"

echo Starting listener (B1 - Telegram -> CSV) ...
echo Working dir: %CD%
echo Python exe : %PY_EXE%
echo -------------------------------------------

%PY_EXE% -m src.main --stage listen

echo.
echo Listener stopped. Nhan phim bat ky de thoat...
pause >nul
