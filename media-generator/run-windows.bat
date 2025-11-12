@echo off
REM ############################################################################
REM Media Generator - Windows Batch Launcher
REM
REM This batch file calls the PowerShell launcher script.
REM It's provided for convenience - you can double-click this file.
REM
REM Usage: run.bat [media-generator arguments]
REM Example: run.bat 10 -t mp4 --embed-audio
REM ############################################################################

REM Get the directory where this batch file is located
set SCRIPT_DIR=%~dp0

REM Check if PowerShell is available
where powershell >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo ERROR: PowerShell is not found!
    echo Please install PowerShell or run run.ps1 directly.
    pause
    exit /b 1
)

REM Run PowerShell script with all arguments
powershell -ExecutionPolicy Bypass -File "%SCRIPT_DIR%run-windows.ps1" %*

REM Capture exit code
set EXIT_CODE=%ERRORLEVEL%

REM If no arguments were provided (help shown), pause for user to read
if "%~1"=="" (
    pause
)

exit /b %EXIT_CODE%
