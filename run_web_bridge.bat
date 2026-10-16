@echo off
setlocal
title Gesture Racing - Local Game Input Bridge
cd /d "%~dp0gesture_racing_controller"
if not exist ".venv\Scripts\python.exe" (
  echo Python environment not found. Run the desktop controller setup first.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" local_input_bridge.py
pause
