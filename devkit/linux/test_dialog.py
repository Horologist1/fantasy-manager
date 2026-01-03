#!/usr/bin/env python3
"""
Simple test script to verify the directory dialog works on Linux
"""

import sys
import tkinter as tk
from pathlib import Path

# Import the dialog function
sys.path.insert(0, str(Path(__file__).parent))
from fantasy_manager_editor_v4_linux import ask_directory_crossplatform

def test_dialog():
    """Test the directory selection dialog"""
    root = tk.Tk()
    root.withdraw()  # Hide main window
    
    print("Testing directory selection dialog...")
    print("This should open a dialog where you can enter a folder path.")
    print("")
    
    path = ask_directory_crossplatform(
        parent=root,
        title="Test: Select a Folder",
        initialdir=str(Path.home())
    )
    
    if path:
        print(f"✓ Success! Selected path: {path}")
        return True
    else:
        print("✗ Cancelled or failed")
        return False

if __name__ == "__main__":
    try:
        test_dialog()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)



