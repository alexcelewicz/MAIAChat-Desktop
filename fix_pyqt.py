import subprocess
import sys
import os

def run_command(command):
    print(f"Running: {command}")
    process = subprocess.run(command, shell=True, capture_output=True, text=True)
    print(f"Return code: {process.returncode}")
    if process.stdout:
        print(f"Output: {process.stdout}")
    if process.stderr:
        print(f"Error: {process.stderr}")
    return process.returncode == 0

def main():
    # Use sys.executable to get the current Python interpreter (cross-platform)
    python_executable = sys.executable
    
    # Uninstall current PyQt6 packages
    print("Uninstalling current PyQt6 packages...")
    run_command(f'"{python_executable}" -m pip uninstall -y PyQt6 PyQt6-Qt6 PyQt6-sip PyQt6-WebEngine PyQt6-WebEngine-Qt6')
    
    # Install Visual C++ Redistributable (this is often needed for PyQt)
    print("\nMake sure you have the Microsoft Visual C++ Redistributable installed.")
    print("You can download it from: https://aka.ms/vs/17/release/vc_redist.x64.exe")
    print("Please install it if you haven't already.\n")
    
    # Install an older, more stable version of PyQt6
    print("Installing PyQt6 version 6.5.0 (more stable version)...")
    run_command(f'"{python_executable}" -m pip install PyQt6==6.5.0')
    
    # Install PyQt6-sip explicitly
    print("\nInstalling PyQt6-sip explicitly...")
    run_command(f'"{python_executable}" -m pip install PyQt6-sip')
    
    # Install PyQt6-WebEngine if needed
    print("\nInstalling PyQt6-WebEngine...")
    run_command(f'"{python_executable}" -m pip install PyQt6-WebEngine')
    
    print("\nPyQt6 reinstallation completed!")
    print("\nIf you still encounter issues, please try the following:")
    print("1. Install the Microsoft Visual C++ Redistributable if you haven't already")
    print("2. Try using PyQt5 instead of PyQt6 (modify the code to import from PyQt5 instead of PyQt6)")
    print("3. Check if there are any system-specific dependencies missing")
    
    return True

if __name__ == "__main__":
    main()
