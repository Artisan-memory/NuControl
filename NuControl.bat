@echo off
cd /d "%~dp0"

rem First run: install dependencies once, then leave a marker so autostart
rem boots go straight to launching without touching pip.
if not exist ".deps_installed" (
    echo Installing dependencies, this only happens once...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo Failed to install dependencies. Install Python 3.10+ and pip, then retry.
        pause
        exit /b 1
    )
    type nul > ".deps_installed"
)

rem pythonw keeps the app windowless; python is the fallback when it is missing,
rem otherwise autostart silently does nothing.
where pythonw >nul 2>&1
if errorlevel 1 (
    start "" python "%~dp0main.py"
) else (
    start "" pythonw "%~dp0main.py"
)
