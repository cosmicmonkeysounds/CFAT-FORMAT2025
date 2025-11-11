#!/bin/bash
#
# Carpet Hotel - Comprehensive Setup & Launch Script (macOS)
#
# This script will automatically:
# - Install Homebrew (if needed)
# - Install Python3 (if needed)
# - Install SuperCollider (if needed)
# - Install Processing (if needed)
# - Create Python virtual environment
# - Install Python dependencies
# - Launch Carpet Hotel
#
# Usage: ./launch_macos.sh [options]
#        Options are passed to run_carpet_hotel.py (--build, --sc-only, --help)
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Change to script directory
cd "$(dirname "$0")"
SCRIPT_DIR="$(pwd)"

echo ""
echo "========================================================"
echo "  CARPET HOTEL - Setup & Launcher (macOS)"
echo "========================================================"
echo ""

# Function to print colored status messages
print_status() {
    echo -e "${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# 1. Check/Install Homebrew
print_status "Checking for Homebrew..."
if ! command -v brew &> /dev/null; then
    print_warning "Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

    # Add Homebrew to PATH for Apple Silicon Macs
    if [[ $(uname -m) == 'arm64' ]]; then
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/opt/homebrew/bin/brew shellenv)"
    fi

    print_success "Homebrew installed"
else
    print_success "Homebrew found: $(brew --version | head -n1)"
fi

# 2. Check/Install Python3
print_status "Checking for Python3..."
if ! command -v python3 &> /dev/null; then
    print_warning "Python3 not found. Installing via Homebrew..."
    brew install python3
    print_success "Python3 installed"
else
    PYTHON_VERSION=$(python3 --version)
    print_success "Python3 found: $PYTHON_VERSION"
fi

# 3. Check/Install SuperCollider
print_status "Checking for SuperCollider..."
if [ ! -d "/Applications/SuperCollider.app" ]; then
    print_warning "SuperCollider not found. Installing via Homebrew..."
    brew install --cask supercollider
    print_success "SuperCollider installed"
else
    print_success "SuperCollider found at /Applications/SuperCollider.app"
fi

# 4. Check/Install Processing
print_status "Checking for Processing..."
if [ ! -d "/Applications/Processing.app" ]; then
    print_warning "Processing not found. Installing..."

    # Download Processing (latest version)
    PROCESSING_URL="https://github.com/processing/processing4/releases/download/processing-1293-4.3/processing-4.3-macos-x64.zip"
    TEMP_ZIP="/tmp/processing.zip"

    echo "  Downloading Processing from GitHub..."
    curl -L -o "$TEMP_ZIP" "$PROCESSING_URL"

    echo "  Extracting..."
    unzip -q "$TEMP_ZIP" -d /tmp/

    echo "  Moving to Applications..."
    mv /tmp/Processing.app /Applications/

    echo "  Cleaning up..."
    rm "$TEMP_ZIP"

    print_success "Processing installed"
else
    print_success "Processing found at /Applications/Processing.app"
fi

# 5. Add processing-java to PATH (for current session)
print_status "Setting up Processing command-line tools..."
export PATH="/Applications/Processing.app/Contents/MacOS:$PATH"

# Add to shell profile if not already there
SHELL_PROFILE="$HOME/.zshrc"
if [ -f "$HOME/.bash_profile" ]; then
    SHELL_PROFILE="$HOME/.bash_profile"
fi

if ! grep -q "Processing.app/Contents/MacOS" "$SHELL_PROFILE" 2>/dev/null; then
    echo '' >> "$SHELL_PROFILE"
    echo '# Processing command-line tools' >> "$SHELL_PROFILE"
    echo 'export PATH="/Applications/Processing.app/Contents/MacOS:$PATH"' >> "$SHELL_PROFILE"
    print_success "Added processing-java to $SHELL_PROFILE"
else
    print_success "processing-java already in PATH"
fi

# 6. Create Python virtual environment
print_status "Setting up Python virtual environment..."
VENV_DIR="$SCRIPT_DIR/app/venv"

if [ ! -d "$VENV_DIR" ]; then
    print_warning "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    print_success "Virtual environment created at $VENV_DIR"
else
    print_success "Virtual environment found at $VENV_DIR"
fi

# 7. Activate virtual environment
print_status "Activating virtual environment..."
source "$VENV_DIR/bin/activate"
print_success "Virtual environment activated"

# 8. Install Python dependencies
print_status "Installing Python dependencies..."
pip3 install --upgrade pip > /dev/null 2>&1
if [ -f "$SCRIPT_DIR/app/requirements.txt" ]; then
    pip3 install -r "$SCRIPT_DIR/app/requirements.txt" > /dev/null 2>&1
    print_success "Dependencies installed from requirements.txt"
else
    print_warning "requirements.txt not found, skipping dependency installation"
fi

# 9. Check for oscP5 library in Processing
print_status "Checking Processing libraries..."
PROCESSING_SKETCHBOOK="$HOME/Documents/Processing"
OSC_LIB_PATH="$PROCESSING_SKETCHBOOK/libraries/oscP5"

if [ ! -d "$OSC_LIB_PATH" ]; then
    print_warning "oscP5 library not found."
    echo ""
    echo "  Please install oscP5 manually:"
    echo "  1. Open Processing IDE"
    echo "  2. Go to Sketch > Import Library > Add Library..."
    echo "  3. Search for 'oscP5' and click Install"
    echo ""
    read -p "  Press Enter after installing oscP5 to continue..."
else
    print_success "oscP5 library found"
fi

# 10. Launch Carpet Hotel
echo ""
echo "========================================================"
echo "  Launching Carpet Hotel"
echo "========================================================"
echo ""

# Run the GUI control panel
python3 app/components/gui.py

# Note: We stay in the venv, but it will be deactivated when the script exits
