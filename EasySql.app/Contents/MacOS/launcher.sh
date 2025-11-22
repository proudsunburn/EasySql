#!/bin/bash

# EasySql One-Click Launcher for macOS
# Automatically installs uv, sets up environment, and launches the application

set -e  # Exit on error

# Determine the project directory (where this .app bundle is located)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/../../.." && pwd )"

echo "=== EasySql Launcher ==="
echo "Project directory: $PROJECT_DIR"

# Change to project directory
cd "$PROJECT_DIR"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "uv not found. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Add uv to PATH for current session
    export PATH="$HOME/.local/bin:$PATH"

    # Verify installation
    if ! command -v uv &> /dev/null; then
        echo "Error: uv installation failed. Please install manually."
        echo "Visit: https://github.com/astral-sh/uv"
        read -p "Press Enter to exit..."
        exit 1
    fi

    echo "uv installed successfully!"
else
    echo "uv is already installed ($(uv --version))"
fi

# Ensure PATH includes uv
export PATH="$HOME/.local/bin:$PATH"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating new virtual environment with uv..."
    uv venv .venv
    echo "Virtual environment created!"
else
    echo "Using existing virtual environment (.venv)"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install/update requirements
if [ -f "requirements.txt" ]; then
    echo "Installing requirements with uv pip..."
    uv pip install -r requirements.txt
    echo "Requirements installed!"
else
    echo "Warning: requirements.txt not found"
fi

# Launch the application
echo "Launching EasySql..."
echo "================================"
echo ""

# Run the application
python easySql.py

# Keep terminal open on error
if [ $? -ne 0 ]; then
    echo ""
    echo "================================"
    echo "Application exited with error"
    read -p "Press Enter to exit..."
fi
