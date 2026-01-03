#!/bin/bash
# Fantasy Manager Editor v4.0 - Linux Launcher
# =============================================

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "Fantasy Manager Editor v4.0 - Complete Edition"
echo ""
echo "Features:"
echo "  - Whoremaster Import"
echo "  - GIF to WebM conversion"
echo "  - Workers, Traits, Events, Items editors"
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.6+ to run the editor"
    echo ""
    echo "On Ubuntu/Debian: sudo apt install python3 python3-tk"
    echo "On Fedora: sudo dnf install python3 python3-tkinter"
    echo "On Arch: sudo pacman -S python tk"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.6"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "Error: Python 3.6+ is required, but found Python $PYTHON_VERSION"
    exit 1
fi

# Check if tkinter is available
if ! python3 -c "import tkinter" 2>/dev/null; then
    echo "Warning: tkinter is not available"
    echo "The editor may not work properly without tkinter"
    echo ""
    echo "Please install tkinter:"
    echo "  On Ubuntu/Debian: sudo apt install python3-tk"
    echo "  On Fedora: sudo dnf install python3-tkinter"
    echo "  On Arch: sudo pacman -S tk"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if DISPLAY is set (for X11/Wayland)
if [ -z "$DISPLAY" ] && [ -z "$WAYLAND_DISPLAY" ]; then
    echo "Warning: No display server detected (DISPLAY or WAYLAND_DISPLAY not set)"
    echo "The editor may not work properly without a display server"
    echo ""
    echo "If you're using SSH, try:"
    echo "  - X11 forwarding: ssh -X user@host"
    echo "  - Or use the text input fallback (will be used automatically)"
    echo ""
fi

# Run the editor (Linux compatible version)
echo "Starting Fantasy Manager Editor (Linux Compatible Edition)..."
echo ""
python3 fantasy_manager_editor_v4_linux.py

# Check exit status
if [ $? -ne 0 ]; then
    echo ""
    echo "Error: The editor encountered an error"
    echo ""
    echo "Common issues:"
    echo "  - Missing dependencies: pip install Pillow (for image preview)"
    echo "  - Display issues: Make sure X11/Wayland is running"
    echo "  - File dialog issues: The editor will use text input as fallback"
    echo ""
    read -p "Press Enter to exit..."
fi

