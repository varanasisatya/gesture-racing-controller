@echo off
setlocal
title Motion Cockpit - Gesture Racing Controller
cd /d "%~dp0gesture_racing_controller"
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Local Python environment was not found.
    echo Recreate it with Python 3.12: python -m venv .venv
    pause
    exit /b 1
)
".venv\Scripts\python.exe" main.py
if errorlevel 1 (
    echo.
    echo [ERROR] Motion Cockpit failed to start. Review the error above.
    echo Verify with: .venv\Scripts\python.exe -m unittest -v test_system.py
    pause
    exit /b 1
)
endlocal
