@echo off
REM =========================================================================
REM Solaraeus — Master Reproduction Script (Windows Batch)
REM =========================================================================

echo [Solaraeus] Starting full project reproduction...

REM 1. Activate Python virtual environment if present
if exist ".venv\Scripts\activate.bat" (
    echo [Solaraeus] Activating virtual environment in .venv...
    call .venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    echo [Solaraeus] Activating virtual environment in venv...
    call venv\Scripts\activate.bat
)

REM 2. Run master reproduction script
python scripts\reproduce_all.py %*

if %ERRORLEVEL% NEQ 0 (
    echo [Solaraeus] Reproduction encountered an error.
    pause
    exit /b %ERRORLEVEL%
)

echo [Solaraeus] Reproduction completed successfully!
pause
