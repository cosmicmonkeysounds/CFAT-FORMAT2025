#!/bin/bash
################################################################################
# Media Generator - macOS/Linux Launcher
#
# This script automatically:
# - Installs Python 3 if not found (via Homebrew on macOS, apt on Linux)
# - Creates a virtual environment if needed
# - Installs dependencies if needed
# - Runs the media generator with your arguments
#
# Usage: ./run.sh [media-generator arguments]
# Example: ./run.sh 10 -t mp4 --embed-audio
################################################################################

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
REQUIREMENTS_FILE="$SCRIPT_DIR/requirements.txt"
VENV_MARKER="$VENV_DIR/.setup_complete"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored message
print_status() {
    echo -e "${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}!${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    else
        echo "unknown"
    fi
}

# Install Homebrew on macOS
install_homebrew() {
    print_status "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

    # Add Homebrew to PATH for Apple Silicon
    if [[ -f "/opt/homebrew/bin/brew" ]]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
    fi

    print_success "Homebrew installed successfully"
}

# Install Python 3
install_python() {
    local os_type=$(detect_os)

    print_status "Python 3 not found. Installing..."

    if [[ "$os_type" == "macos" ]]; then
        # macOS: Use Homebrew
        if ! command_exists brew; then
            install_homebrew
        fi

        print_status "Installing Python 3 via Homebrew..."
        brew install python3

    elif [[ "$os_type" == "linux" ]]; then
        # Linux: Try to detect package manager
        if command_exists apt-get; then
            print_status "Installing Python 3 via apt..."
            sudo apt-get update
            sudo apt-get install -y python3 python3-pip python3-venv

        elif command_exists yum; then
            print_status "Installing Python 3 via yum..."
            sudo yum install -y python3 python3-pip

        elif command_exists dnf; then
            print_status "Installing Python 3 via dnf..."
            sudo dnf install -y python3 python3-pip

        elif command_exists pacman; then
            print_status "Installing Python 3 via pacman..."
            sudo pacman -S --noconfirm python python-pip

        else
            print_error "Could not detect package manager. Please install Python 3 manually."
            exit 1
        fi

    else
        print_error "Unsupported operating system. Please install Python 3 manually."
        exit 1
    fi

    print_success "Python 3 installed successfully"
}

# Check Python installation
check_python() {
    if command_exists python3; then
        PYTHON_CMD="python3"
    elif command_exists python; then
        # Check if it's Python 3
        if python --version 2>&1 | grep -q "Python 3"; then
            PYTHON_CMD="python"
        else
            return 1
        fi
    else
        return 1
    fi

    return 0
}

# Create virtual environment
create_venv() {
    print_status "Creating virtual environment..."
    $PYTHON_CMD -m venv "$VENV_DIR"
    print_success "Virtual environment created"
}

# Install requirements
install_requirements() {
    print_status "Installing dependencies..."

    # Activate virtual environment
    source "$VENV_DIR/bin/activate"

    # Upgrade pip
    pip install --upgrade pip --quiet

    # Install requirements
    pip install -r "$REQUIREMENTS_FILE" --quiet

    # Mark setup as complete
    touch "$VENV_MARKER"

    print_success "Dependencies installed successfully"
}

# Main setup logic
setup() {
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "  Media Generator Setup"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""

    # Check for Python
    if ! check_python; then
        install_python

        # Re-check after installation
        if ! check_python; then
            print_error "Python installation failed. Please install Python 3 manually."
            exit 1
        fi
    fi

    print_success "Python found: $($PYTHON_CMD --version)"

    # Check if venv exists
    if [[ ! -d "$VENV_DIR" ]]; then
        create_venv
        install_requirements
    elif [[ ! -f "$VENV_MARKER" ]]; then
        # Venv exists but setup not complete
        print_warning "Virtual environment incomplete, reinstalling dependencies..."
        install_requirements
    else
        # Check if requirements.txt has changed
        if [[ "$REQUIREMENTS_FILE" -nt "$VENV_MARKER" ]]; then
            print_warning "Requirements updated, reinstalling dependencies..."
            install_requirements
        else
            print_success "Virtual environment ready"
        fi
    fi

    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
}

# Run the program
run_program() {
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"

    # Run media generator with all arguments
    python -m media_generator "$@"

    # Capture exit code
    EXIT_CODE=$?

    # Deactivate virtual environment
    deactivate

    return $EXIT_CODE
}

# Main execution
main() {
    # Run setup
    setup

    # Check if any arguments were provided
    if [[ $# -eq 0 ]]; then
        print_warning "No arguments provided. Showing help:"
        echo ""
        run_program --help
    else
        # Run program with arguments
        run_program "$@"
    fi
}

# Execute main function with all script arguments
main "$@"
