#!/bin/bash
# Fantasy Manager Editor v4.0 - Linux Build Script
# ================================================

set -e  # Exit on error

echo ""
echo "============================================================"
echo "   FANTASY MANAGER EDITOR v4.0 - BUILD LINUX EXECUTABLE"
echo "============================================================"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed or not in PATH"
    echo "Please install Python 3.6+ to build the executable"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.6"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "[ERROR] Python 3.6+ is required, but found Python $PYTHON_VERSION"
    exit 1
fi

# Check if PyInstaller is installed
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "PyInstaller is not installed. Installing..."
    python3 -m pip install pyinstaller
    if [ $? -ne 0 ]; then
        echo ""
        echo "[ERROR] Could not install PyInstaller"
        echo "Try manually: pip3 install pyinstaller"
        exit 1
    fi
fi

echo ""
echo "Building Fantasy Manager Editor v4.0 (Linux Edition)..."
echo "This may take a few minutes..."
echo ""

# Clean previous builds
if [ -d "build" ]; then
    echo "Cleaning previous build directory..."
    rm -rf build
fi

if [ -d "dist" ]; then
    echo "Cleaning previous dist directory..."
    rm -rf dist
fi

# Build with PyInstaller
# --onefile: Create a single executable file
# --name: Name of the executable
# --noconsole: Don't show console window (optional, remove if you want to see output)
# Note: --windowed is Windows-specific, we use --noconsole for Linux GUI apps
pyinstaller --onefile \
    --name "FantasyManager_Editor_v4_Linux" \
    --noconsole \
    fantasy_manager_editor_v4_linux.py

if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Build failed"
    exit 1
fi

echo ""
echo "============================================================"
echo "   BUILD COMPLETED"
echo "============================================================"
echo ""
echo "The executable is located at:"
echo "   dist/FantasyManager_Editor_v4_Linux"
echo ""

# Make it executable
if [ -f "dist/FantasyManager_Editor_v4_Linux" ]; then
    chmod +x "dist/FantasyManager_Editor_v4_Linux"
    echo "Made executable: dist/FantasyManager_Editor_v4_Linux"
    
    # Copy to current directory for convenience
    cp "dist/FantasyManager_Editor_v4_Linux" "FantasyManager_Editor_v4_Linux"
    chmod +x "FantasyManager_Editor_v4_Linux"
    echo ""
    echo "Also copied to: devkit/FantasyManager_Editor_v4_Linux"
    echo ""
    echo "You can run it with:"
    echo "   ./FantasyManager_Editor_v4_Linux"
    echo ""
else
    echo "[WARNING] Executable not found in dist/ directory"
    exit 1
fi

echo "Done!"
echo ""

