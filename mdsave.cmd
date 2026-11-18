@echo off
rem ==============================================================================
rem MDsave - Windows CMD / Batch Launcher
rem ==============================================================================
setlocal enabledelayedexpansion

rem 1. Find Python executable
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PY_CMD=python"
    goto :find_script
)

where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PY_CMD=py -3"
    goto :find_script
)

where python3 >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PY_CMD=python3"
    goto :find_script
)

echo [!] Error: No se encontro Python 3 en PATH.
echo Por favor instala Python desde https://www.python.org/ y asegurate de marcar "Add Python to PATH".
exit /b 1

:find_script
set "SCRIPT_DIR=%~dp0"
set "REAL_SCRIPT="

if exist "%SCRIPT_DIR%mdsave.py" (
    set "REAL_SCRIPT=%SCRIPT_DIR%mdsave.py"
) else if exist "%LOCALAPPDATA%\mdsave\mdsave.py" (
    set "REAL_SCRIPT=%LOCALAPPDATA%\mdsave\mdsave.py"
) else if exist "%USERPROFILE%\.local\share\mdsave\mdsave.py" (
    set "REAL_SCRIPT=%USERPROFILE%\.local\share\mdsave\mdsave.py"
) else if exist "%USERPROFILE%\mdsave\mdsave.py" (
    set "REAL_SCRIPT=%USERPROFILE%\mdsave\mdsave.py"
)

if "%REAL_SCRIPT%"=="" (
    echo [!] Error: No se pudo encontrar mdsave.py
    echo Ejecuta el instalador install.sh (o install.ps1) para configurar MDsave.
    exit /b 1
)

rem 2. Execute script preserving working directory and arguments
%PY_CMD% "%REAL_SCRIPT%" %*
exit /b %ERRORLEVEL%
