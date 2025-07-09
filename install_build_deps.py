#!/usr/bin/env python3
"""
Install build dependencies for MAIAChat executable creation.
This script handles various Python versions and compatibility issues.
"""

import sys
import subprocess
import importlib.util

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("ERROR: Python 3.8 or higher is required")
        return False
    
    if version.major == 3 and version.minor >= 12:
        print("Note: Python 3.12+ detected. Some packages may have limited compatibility.")
    
    return True

def install_package(package_spec, description=""):
    """Install a package with error handling."""
    print(f"Installing {description or package_spec}...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "--upgrade", package_spec
        ], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install {package_spec}: {e}")
        return False

def check_package_installed(package_name):
    """Check if a package is already installed."""
    spec = importlib.util.find_spec(package_name)
    return spec is not None

def main():
    """Main installation process."""
    print("MAIAChat Build Dependencies Installer")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        return False
    
    print("\nChecking and installing build dependencies...")
    
    # Essential packages for building
    essential_packages = [
        ("pyinstaller>=5.0.0,<7.0.0", "PyInstaller (executable builder)"),
    ]
    
    # Optional packages (install if possible)
    optional_packages = [
        ("pyinstaller-hooks-contrib", "PyInstaller hooks for better compatibility"),
    ]
    
    # Install essential packages
    print("\n1. Installing essential packages...")
    all_essential_installed = True
    
    for package_spec, description in essential_packages:
        if not install_package(package_spec, description):
            all_essential_installed = False
    
    if not all_essential_installed:
        print("\nERROR: Failed to install essential build dependencies.")
        print("Please try installing PyInstaller manually:")
        print("  pip install pyinstaller")
        return False
    
    # Install optional packages
    print("\n2. Installing optional packages...")
    for package_spec, description in optional_packages:
        install_package(package_spec, description)
    
    # Verify PyInstaller installation
    print("\n3. Verifying installation...")
    if check_package_installed("PyInstaller"):
        try:
            import PyInstaller
            print(f"✓ PyInstaller {PyInstaller.__version__} installed successfully")
        except ImportError:
            print("✗ PyInstaller import failed")
            return False
    else:
        print("✗ PyInstaller not found after installation")
        return False
    
    print("\n" + "=" * 40)
    print("✓ Build dependencies installed successfully!")
    print("\nYou can now build your executable with:")
    print("  python build_exe.py")
    print("  or")
    print("  build.bat")
    
    return True

if __name__ == "__main__":
    success = main()
    
    if not success:
        print("\nInstallation failed. Please check the errors above.")
        print("You may need to:")
        print("1. Update pip: python -m pip install --upgrade pip")
        print("2. Install PyInstaller manually: pip install pyinstaller")
        print("3. Check your Python version compatibility")
    
    print("\nPress Enter to exit...")
    input()
    
    sys.exit(0 if success else 1) 