@echo off
REM
REM Carpet Hotel - Comprehensive Setup & Launch Script (Windows)
REM
REM This script will automatically:
REM - Check for Python3 (install if needed)
REM - Check for SuperCollider (install if needed)
REM - Check for Processing (install if needed)
REM - Create Python virtual environment
REM - Install Python dependencies
REM - Launch Carpet Hotel
REM
REM Usage: launch_windows.bat [options]
REM        Options are passed to run_carpet_hotel.py (--build, --sc-only, --help)
REM

setlocal enabledelayedexpansion

cd /d "%~dp0"
set SCRIPT_DIR=%CD%

echo.
echo ========================================================
echo   CARPET HOTEL - Setup ^& Launcher (Windows)
echo ========================================================
echo.

REM ============================================================================
REM 1. Check/Install Python3
REM ============================================================================
echo [*] Checking for Python3...

python --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('python --version') do set PYTHON_VER=%%i
    echo [+] Python3 found: !PYTHON_VER!
    set PYTHON_CMD=python
    goto :python_found
)

python3 --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('python3 --version') do set PYTHON_VER=%%i
    echo [+] Python3 found: !PYTHON_VER!
    set PYTHON_CMD=python3
    goto :python_found
)

echo [!] Python3 not found. Installing...
echo.
echo Downloading Python installer...

set PYTHON_URL=https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe
set PYTHON_INSTALLER=%TEMP%\python-installer.exe

powershell -Command "& {Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%PYTHON_INSTALLER%'}"

if not exist "%PYTHON_INSTALLER%" (
    echo [X] Failed to download Python installer
    echo Please install Python3 manually from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Installing Python3...
"%PYTHON_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0

echo Cleaning up...
del "%PYTHON_INSTALLER%"

echo [+] Python3 installed. Please restart this script.
echo     Close this window and run launch_windows.bat again.
pause
exit /b 0

:python_found

REM ============================================================================
REM 2. Check/Install SuperCollider
REM ============================================================================
echo [*] Checking for SuperCollider...

set SC_PATH_1=C:\Program Files\SuperCollider\SuperCollider.exe
set SC_PATH_2=C:\Program Files (x86)\SuperCollider\SuperCollider.exe

if exist "%SC_PATH_1%" (
    echo [+] SuperCollider found at: %SC_PATH_1%
    goto :sc_found
)

if exist "%SC_PATH_2%" (
    echo [+] SuperCollider found at: %SC_PATH_2%
    goto :sc_found
)

echo [!] SuperCollider not found. Installing...
echo.
echo Downloading SuperCollider installer...

set SC_URL=https://github.com/supercollider/supercollider/releases/download/Version-3.13.0/SuperCollider-3.13.0_Release-x64-VS-95ceecf.exe
set SC_INSTALLER=%TEMP%\supercollider-installer.exe

powershell -Command "& {Invoke-WebRequest -Uri '%SC_URL%' -OutFile '%SC_INSTALLER%'}"

if not exist "%SC_INSTALLER%" (
    echo [X] Failed to download SuperCollider installer
    echo Please install SuperCollider manually from: https://supercollider.github.io/downloads
    pause
    exit /b 1
)

echo Installing SuperCollider...
echo (This may take a few minutes...)
"%SC_INSTALLER%" /S

echo Cleaning up...
del "%SC_INSTALLER%"

echo [+] SuperCollider installed
:sc_found

REM ============================================================================
REM 3. Check/Install Processing
REM ============================================================================
echo [*] Checking for Processing...

set PROCESSING_PATH_1=C:\Program Files\Processing\processing-java.exe
set PROCESSING_PATH_2=C:\Program Files (x86)\Processing\processing-java.exe
set PROCESSING_PATH_3=%LOCALAPPDATA%\Programs\Processing\processing-java.exe

if exist "%PROCESSING_PATH_1%" (
    echo [+] Processing found at: %PROCESSING_PATH_1%
    set "PATH=%PATH%;C:\Program Files\Processing"
    goto :processing_found
)

if exist "%PROCESSING_PATH_2%" (
    echo [+] Processing found at: %PROCESSING_PATH_2%
    set "PATH=%PATH%;C:\Program Files (x86)\Processing"
    goto :processing_found
)

if exist "%PROCESSING_PATH_3%" (
    echo [+] Processing found at: %PROCESSING_PATH_3%
    set "PATH=%PATH%;%LOCALAPPDATA%\Programs\Processing"
    goto :processing_found
)

echo [!] Processing not found. Installing...
echo.
echo Downloading Processing...

set PROCESSING_URL=https://github.com/processing/processing4/releases/download/processing-1293-4.3/processing-4.3-windows-x64.zip
set PROCESSING_ZIP=%TEMP%\processing.zip
set PROCESSING_EXTRACT=%TEMP%\processing_extract

powershell -Command "& {Invoke-WebRequest -Uri '%PROCESSING_URL%' -OutFile '%PROCESSING_ZIP%'}"

if not exist "%PROCESSING_ZIP%" (
    echo [X] Failed to download Processing
    echo Please install Processing manually from: https://processing.org/download
    pause
    exit /b 1
)

echo Extracting Processing...
powershell -Command "& {Expand-Archive -Path '%PROCESSING_ZIP%' -DestinationPath '%PROCESSING_EXTRACT%' -Force}"

echo Installing Processing to Program Files...
if not exist "%LOCALAPPDATA%\Programs" mkdir "%LOCALAPPDATA%\Programs"
xcopy /E /I /Y "%PROCESSING_EXTRACT%\processing-4.3" "%LOCALAPPDATA%\Programs\Processing"

echo Cleaning up...
del "%PROCESSING_ZIP%"
rmdir /S /Q "%PROCESSING_EXTRACT%"

set "PATH=%PATH%;%LOCALAPPDATA%\Programs\Processing"
echo [+] Processing installed

:processing_found

REM ============================================================================
REM 4. Create Python virtual environment
REM ============================================================================
echo [*] Setting up Python virtual environment...

set VENV_DIR=%SCRIPT_DIR%\app\venv

if not exist "%VENV_DIR%" (
    echo [!] Creating virtual environment...
    %PYTHON_CMD% -m venv "%VENV_DIR%"
    echo [+] Virtual environment created at %VENV_DIR%
) else (
    echo [+] Virtual environment found at %VENV_DIR%
)

REM ============================================================================
REM 5. Activate virtual environment
REM ============================================================================
echo [*] Activating virtual environment...
call "%VENV_DIR%\Scripts\activate.bat"
echo [+] Virtual environment activated

REM ============================================================================
REM 6. Install Python dependencies
REM ============================================================================
echo [*] Installing Python dependencies...
python -m pip install --upgrade pip >nul 2>&1
if exist "%SCRIPT_DIR%\app\requirements.txt" (
    python -m pip install -r "%SCRIPT_DIR%\app\requirements.txt" >nul 2>&1
    echo [+] Dependencies installed from requirements.txt
) else (
    echo [!] requirements.txt not found, skipping dependency installation
)

REM ============================================================================
REM 7. Check for oscP5 library in Processing
REM ============================================================================
echo [*] Checking Processing libraries...

set PROCESSING_SKETCHBOOK=%USERPROFILE%\Documents\Processing
set OSC_LIB_PATH=%PROCESSING_SKETCHBOOK%\libraries\oscP5

if not exist "%OSC_LIB_PATH%" (
    echo [!] oscP5 library not found.
    echo.
    echo   Please install oscP5 manually:
    echo   1. Open Processing IDE
    echo   2. Go to Sketch ^> Import Library ^> Add Library...
    echo   3. Search for 'oscP5' and click Install
    echo.
    pause
) else (
    echo [+] oscP5 library found
)

REM ============================================================================
REM 8. Launch Carpet Hotel
REM ============================================================================
echo.
echo ========================================================
echo   Launching Carpet Hotel
echo ========================================================
echo.

REM Run the main script with all arguments passed through
python app\run_carpet_hotel.py %*

REM Note: The venv will be deactivated when the script exits
