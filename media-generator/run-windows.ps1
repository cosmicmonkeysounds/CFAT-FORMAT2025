################################################################################
# Media Generator - Windows PowerShell Launcher
#
# This script automatically:
# - Installs Python 3 if not found (via winget or chocolatey)
# - Creates a virtual environment if needed
# - Installs dependencies if needed
# - Runs the media generator with your arguments
#
# Usage: .\run.ps1 [media-generator arguments]
# Example: .\run.ps1 10 -t mp4 --embed-audio
################################################################################

# Enable strict mode
$ErrorActionPreference = "Stop"

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvDir = Join-Path $ScriptDir "venv"
$RequirementsFile = Join-Path $ScriptDir "requirements.txt"
$VenvMarker = Join-Path $VenvDir ".setup_complete"

# Color output functions
function Write-Status {
    param([string]$Message)
    Write-Host "==> " -NoNewline -ForegroundColor Blue
    Write-Host $Message
}

function Write-Success {
    param([string]$Message)
    Write-Host "✓ " -NoNewline -ForegroundColor Green
    Write-Host $Message
}

function Write-Warning {
    param([string]$Message)
    Write-Host "! " -NoNewline -ForegroundColor Yellow
    Write-Host $Message
}

function Write-Error {
    param([string]$Message)
    Write-Host "✗ " -NoNewline -ForegroundColor Red
    Write-Host $Message
}

# Check if command exists
function Test-CommandExists {
    param([string]$Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

# Install Python via winget
function Install-PythonWinget {
    Write-Status "Installing Python 3 via winget..."
    try {
        winget install Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements

        # Add Python to PATH for current session
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

        Write-Success "Python installed via winget"
        return $true
    } catch {
        Write-Warning "winget installation failed: $_"
        return $false
    }
}

# Install Python via Chocolatey
function Install-PythonChoco {
    Write-Status "Installing Python 3 via Chocolatey..."

    # Check if Chocolatey is installed
    if (-not (Test-CommandExists choco)) {
        Write-Status "Installing Chocolatey..."
        try {
            Set-ExecutionPolicy Bypass -Scope Process -Force
            [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
            Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
            Write-Success "Chocolatey installed"
        } catch {
            Write-Error "Failed to install Chocolatey: $_"
            return $false
        }
    }

    try {
        choco install python -y

        # Refresh environment variables
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

        Write-Success "Python installed via Chocolatey"
        return $true
    } catch {
        Write-Warning "Chocolatey installation failed: $_"
        return $false
    }
}

# Install Python
function Install-Python {
    Write-Status "Python 3 not found. Installing..."

    # Try winget first (Windows 10+)
    if (Test-CommandExists winget) {
        if (Install-PythonWinget) {
            return $true
        }
    }

    # Try Chocolatey as fallback
    if (Install-PythonChoco) {
        return $true
    }

    # Manual installation prompt
    Write-Error "Automatic installation failed."
    Write-Host ""
    Write-Host "Please install Python manually:"
    Write-Host "  1. Visit https://www.python.org/downloads/"
    Write-Host "  2. Download Python 3.11 or later"
    Write-Host "  3. Run the installer and check 'Add Python to PATH'"
    Write-Host "  4. Run this script again"
    Write-Host ""

    exit 1
}

# Find Python command
function Get-PythonCommand {
    # Try py launcher first (Windows Python launcher)
    if (Test-CommandExists py) {
        try {
            $version = py --version 2>&1
            if ($version -match "Python 3") {
                return "py"
            }
        } catch {}
    }

    # Try python3
    if (Test-CommandExists python3) {
        return "python3"
    }

    # Try python
    if (Test-CommandExists python) {
        try {
            $version = python --version 2>&1
            if ($version -match "Python 3") {
                return "python"
            }
        } catch {}
    }

    return $null
}

# Create virtual environment
function New-VirtualEnvironment {
    Write-Status "Creating virtual environment..."
    & $script:PythonCmd -m venv $VenvDir
    Write-Success "Virtual environment created"
}

# Install requirements
function Install-Requirements {
    Write-Status "Installing dependencies..."

    # Activate virtual environment
    $activateScript = Join-Path $VenvDir "Scripts\Activate.ps1"
    & $activateScript

    # Upgrade pip
    python -m pip install --upgrade pip --quiet

    # Install requirements
    pip install -r $RequirementsFile --quiet

    # Mark setup as complete
    New-Item -ItemType File -Path $VenvMarker -Force | Out-Null

    Write-Success "Dependencies installed successfully"
}

# Main setup logic
function Invoke-Setup {
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════"
    Write-Host "  Media Generator Setup"
    Write-Host "═══════════════════════════════════════════════════════════════"
    Write-Host ""

    # Check for Python
    $script:PythonCmd = Get-PythonCommand

    if ($null -eq $script:PythonCmd) {
        Install-Python

        # Re-check after installation
        $script:PythonCmd = Get-PythonCommand

        if ($null -eq $script:PythonCmd) {
            Write-Error "Python installation failed. Please install Python 3 manually."
            exit 1
        }
    }

    $pythonVersion = & $script:PythonCmd --version
    Write-Success "Python found: $pythonVersion"

    # Check if venv exists
    if (-not (Test-Path $VenvDir)) {
        New-VirtualEnvironment
        Install-Requirements
    } elseif (-not (Test-Path $VenvMarker)) {
        # Venv exists but setup not complete
        Write-Warning "Virtual environment incomplete, reinstalling dependencies..."
        Install-Requirements
    } else {
        # Check if requirements.txt has changed
        $reqModified = (Get-Item $RequirementsFile).LastWriteTime
        $markerModified = (Get-Item $VenvMarker).LastWriteTime

        if ($reqModified -gt $markerModified) {
            Write-Warning "Requirements updated, reinstalling dependencies..."
            Install-Requirements
        } else {
            Write-Success "Virtual environment ready"
        }
    }

    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════"
    Write-Host ""
}

# Run the program
function Invoke-Program {
    param([string[]]$Arguments)

    # Activate virtual environment
    $activateScript = Join-Path $VenvDir "Scripts\Activate.ps1"
    & $activateScript

    # Run media generator with all arguments
    python -m media_generator @Arguments

    $exitCode = $LASTEXITCODE

    # Deactivate is automatic in PowerShell when script ends

    return $exitCode
}

# Main execution
function Main {
    param([string[]]$Arguments)

    try {
        # Run setup
        Invoke-Setup

        # Run program with arguments (or without for interactive mode)
        $exitCode = Invoke-Program $Arguments
        exit $exitCode
    } catch {
        Write-Error "An error occurred: $_"
        Write-Host $_.ScriptStackTrace
        exit 1
    }
}

# Execute main function with all script arguments
Main $args
