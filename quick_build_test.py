#!/usr/bin/env python3
"""
Quick test to verify build environment before running full build.
This helps catch issues early without waiting for the full build process.
"""

import os
import sys
import importlib.util
from pathlib import Path

def test_python_version():
    """Test Python version compatibility."""
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("✗ Python 3.8+ required")
        return False
    
    print("✓ Python version compatible")
    return True

def test_pyinstaller():
    """Test if PyInstaller is available."""
    try:
        import PyInstaller
        print(f"✓ PyInstaller {PyInstaller.__version__} found")
        return True
    except ImportError:
        print("✗ PyInstaller not found")
        print("Run: python install_build_deps.py")
        return False

def test_main_script():
    """Test if main script exists and can be imported."""
    if not os.path.exists("main.py"):
        print("✗ main.py not found")
        return False
    
    try:
        # Try to import main components without running
        spec = importlib.util.spec_from_file_location("main", "main.py")
        if spec is None:
            print("✗ Cannot load main.py")
            return False
        
        print("✓ main.py found and loadable")
        return True
    except Exception as e:
        print(f"✗ Error loading main.py: {e}")
        return False

def test_critical_imports():
    """Test critical imports that PyInstaller needs."""
    critical_modules = [
        "PyQt6.QtCore",
        "PyQt6.QtWidgets",
        "PyQt6.QtGui"
    ]
    
    missing_modules = []
    for module in critical_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print(f"✗ Missing critical modules: {', '.join(missing_modules)}")
        return False
    
    print("✓ Critical modules available")
    return True

def test_data_files():
    """Test if important data files exist."""
    important_files = [
        "config.json",
        "api_keys.json",
        "requirements.txt"
    ]
    
    missing_files = []
    for file in important_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"⚠ Missing data files: {', '.join(missing_files)}")
        print("  These will be created during build if needed")
    else:
        print("✓ Important data files present")
    
    return True

def test_build_space():
    """Test if there's enough disk space for build."""
    try:
        import shutil
        free_space = shutil.disk_usage(".").free
        free_gb = free_space / (1024**3)
        
        if free_gb < 2:
            print(f"⚠ Low disk space: {free_gb:.1f}GB free")
            print("  Build may fail with insufficient space")
            return False
        
        print(f"✓ Sufficient disk space: {free_gb:.1f}GB free")
        return True
    except Exception:
        print("⚠ Could not check disk space")
        return True

def main():
    """Run all pre-build tests."""
    print("MAIAChat Build Environment Test")
    print("=" * 40)
    
    tests = [
        ("Python version", test_python_version),
        ("PyInstaller availability", test_pyinstaller),
        ("Main script", test_main_script),
        ("Critical imports", test_critical_imports),
        ("Data files", test_data_files),
        ("Disk space", test_build_space),
    ]
    
    passed = 0
    critical_failed = 0
    
    for test_name, test_func in tests:
        print(f"\nTesting: {test_name}")
        try:
            if test_func():
                passed += 1
            else:
                if test_name in ["Python version", "PyInstaller availability", "Main script", "Critical imports"]:
                    critical_failed += 1
        except Exception as e:
            print(f"Test error: {e}")
            if test_name in ["Python version", "PyInstaller availability", "Main script", "Critical imports"]:
                critical_failed += 1
    
    print("\n" + "=" * 40)
    print(f"Tests completed: {passed}/{len(tests)} passed")
    
    if critical_failed > 0:
        print("✗ Critical tests failed. Build will likely fail.")
        print("\nTo fix:")
        print("1. Install build dependencies: python install_build_deps.py")
        print("2. Ensure all application dependencies are installed")
        print("3. Check Python version (3.8+ required)")
        return False
    else:
        print("✓ Environment looks good for building!")
        print("\nYou can now run: python build_exe.py")
        return True

if __name__ == "__main__":
    success = main()
    
    print("\nPress Enter to exit...")
    input()
    
    sys.exit(0 if success else 1) 