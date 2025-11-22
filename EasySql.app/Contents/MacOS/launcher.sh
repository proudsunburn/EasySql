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

# Install/update requirements only if needed
if [ -f "requirements.txt" ]; then
    echo "Checking if requirements are already installed..."
    
    # Activate virtual environment to check for installed packages
    source .venv/bin/activate
    
    # Check if each package in requirements.txt is already installed
    REQUIREMENTS_SATISFIED=true
    
    while IFS= read -r requirement; do
        # Skip empty lines and comments
        if [[ -z "$requirement" || "$requirement" =~ ^[[:space:]]*# ]]; then
            continue
        fi
        
        # Extract package name (before any version specifier)
        PACKAGE_NAME=$(echo "$requirement" | sed 's/[>=<~!].*//' | sed 's/[[:space:]]*$//')
        if [ -z "$PACKAGE_NAME" ]; then
            continue
        fi
        
        # Check if package is installed
        if ! .venv/bin/python -c "import $PACKAGE_NAME" &>/dev/null; then
            # For packages with hyphens, try with underscores as well (like PyQt6)
            PACKAGE_NAME_UNDERSCORES=${PACKAGE_NAME//-/_}
            if ! .venv/bin/python -c "import $PACKAGE_NAME_UNDERSCORES" &>/dev/null; then
                REQUIREMENTS_SATISFIED=false
                echo "Package '$PACKAGE_NAME' is not installed or importable"
                break
            fi
        fi
    done < requirements.txt
    
    if [ "$REQUIREMENTS_SATISFIED" = true ]; then
        echo "All requirements are already installed and importable. Skipping installation."
    else
        echo "Installing/updating requirements with uv pip..."
        uv pip install -r requirements.txt
        echo "Requirements installed/updated!"
    fi
else
    echo "Warning: requirements.txt not found"
fi

# Launch the application
echo "Launching EasySql..."
echo "================================"
echo ""

# Run the application
.venv/bin/python easySql.py

# Keep terminal open on error
if [ $? -ne 0 ]; then
    echo ""
    echo "================================"
    echo "Application exited with error"
    read -p "Press Enter to exit..."
fi
