@echo off
REM Test script for download detection
echo ================================================
echo Audio Download Manager - Download Detection Test
echo ================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found
    pause
    exit /b 1
)

REM Run the standalone test
echo Running download detection test...
echo.
python test_detection_standalone.py

echo.
echo Test complete! Check the log above for results.
echo.
pause
