@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"
title DEEPX AGENT

:: ------------------------------------------------------------------
:: 1. CHECK EXISTING VIRTUAL ENVIRONMENT
:: ------------------------------------------------------------------
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -c "import sys" >nul 2>&1
    if not errorlevel 1 goto RUN
    echo [!] Found .venv from another PC or with invalid paths.
    echo [!] Removing outdated environment and preparing fresh setup...
    rmdir /s /q ".venv" >nul 2>&1
)

:: ------------------------------------------------------------------
:: 2. DETECT WORKING PYTHON (>= 3.10)
:: ------------------------------------------------------------------
set "SYSTEM_PY="
set "SYSTEM_PY_ARGS="

:: Check python in PATH
for /f "tokens=*" %%i in ('where python 2^>nul') do (
    if not defined SYSTEM_PY (
        "%%i" -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
        if not errorlevel 1 set "SYSTEM_PY=%%i"
    )
)

:: Check py launcher
if not defined SYSTEM_PY (
    where py >nul 2>&1
    if not errorlevel 1 (
        py -3.11 -c "import sys; sys.exit(0)" >nul 2>&1
        if not errorlevel 1 (
            set "SYSTEM_PY=py"
            set "SYSTEM_PY_ARGS=-3.11"
        ) else (
            py -3.12 -c "import sys; sys.exit(0)" >nul 2>&1
            if not errorlevel 1 (
                set "SYSTEM_PY=py"
                set "SYSTEM_PY_ARGS=-3.12"
            ) else (
                py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
                if not errorlevel 1 (
                    set "SYSTEM_PY=py"
                    set "SYSTEM_PY_ARGS=-3"
                )
            )
        )
    )
)

:: Check standard Windows AppData paths
if not defined SYSTEM_PY (
    for %%p in (
        "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
        "%ProgramFiles%\Python312\python.exe"
        "%ProgramFiles%\Python311\python.exe"
        "%ProgramFiles%\Python310\python.exe"
    ) do (
        if not defined SYSTEM_PY (
            if exist "%%~p" (
                "%%~p" -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
                if not errorlevel 1 set "SYSTEM_PY=%%~p"
            )
        )
    )
)

:: ------------------------------------------------------------------
:: 3. AUTO-DOWNLOAD & SILENT INSTALL PYTHON 3.11 IF MISSING
:: ------------------------------------------------------------------
if not defined SYSTEM_PY (
    echo ================================================================
    echo [i] Python 3.10+ was not found on this computer.
    echo [i] Automatically downloading official Python 3.11.9 (25 MB)...
    echo ================================================================
    
    where curl.exe >nul 2>&1
    if errorlevel 1 (
        echo [X] curl.exe is missing. Please install Python manually from python.org.
        pause
        exit /b 1
    )
    
    curl.exe -fSL -o "%TEMP%\python-3.11.9-amd64.exe" "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
    if errorlevel 1 (
        echo [X] Failed to download Python. Check your internet connection.
        pause
        exit /b 1
    )
    
    echo [i] Installing Python 3.11 silently (user-level, no admin required)...
    start /wait "" "%TEMP%\python-3.11.9-amd64.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 Include_pip=1
    del /f /q "%TEMP%\python-3.11.9-amd64.exe" >nul 2>&1
    
    set "PATH=%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts;!PATH!"
    
    if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
        set "SYSTEM_PY=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    ) else (
        set "SYSTEM_PY=python"
    )
    echo [+] Python 3.11 installed successfully!
)

:: ------------------------------------------------------------------
:: 4. RUN AUTOMATED DEPENDENCY SETUP
:: ------------------------------------------------------------------
echo [i] Configuring virtual environment and installing dependencies...
echo [i] Please wait 1-2 minutes...
set PYTHONDONTWRITEBYTECODE=1
"!SYSTEM_PY!" !SYSTEM_PY_ARGS! "deepx\install.py"
if errorlevel 1 (
    echo.
    echo [X] Setup failed during dependency installation.
    pause
    exit /b 1
)

:: ------------------------------------------------------------------
:: 5. LAUNCH DEEPX AGENT
:: ------------------------------------------------------------------
:RUN
set PYTHONDONTWRITEBYTECODE=1
".venv\Scripts\python.exe" "deepx\deep_cli.py" %*
if errorlevel 1 (
    echo.
    echo [i] Session finished with code %ERRORLEVEL%.
    pause
)
