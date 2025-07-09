#!/usr/bin/env python3
"""
Test script to verify the built executable works correctly.
Run this after building the executable to perform basic functionality tests.
"""

import os
import sys
import subprocess
import time
import json
from pathlib import Path

def test_executable_exists():
    """Test if the executable file exists."""
    exe_path = Path("dist/MAIAChat/MAIAChat.exe")
    if exe_path.exists():
        print("✓ Executable file exists")
        return True
    else:
        print("✗ Executable file not found")
        return False

def test_required_files():
    """Test if all required files are present."""
    base_path = Path("dist/MAIAChat")
    required_files = [
        "config.json",
        "api_keys.json",
        "pricing.json",
        "USER_GUIDE.txt",
        "Start_MAIAChat.bat"
    ]
    
    required_dirs = [
        "ui",
        "handlers",
        "knowledge_base",
        "_internal"
    ]
    
    missing_files = []
    missing_dirs = []
    
    for file in required_files:
        if not (base_path / file).exists():
            missing_files.append(file)
    
    for dir in required_dirs:
        if not (base_path / dir).exists():
            missing_dirs.append(dir)
    
    if not missing_files and not missing_dirs:
        print("✓ All required files and directories present")
        return True
    else:
        if missing_files:
            print(f"✗ Missing files: {', '.join(missing_files)}")
        if missing_dirs:
            print(f"✗ Missing directories: {', '.join(missing_dirs)}")
        return False

def test_executable_launch():
    """Test if the executable can launch (basic startup test)."""
    exe_path = Path("dist/MAIAChat/MAIAChat.exe")
    
    if not exe_path.exists():
        print("✗ Cannot test launch - executable not found")
        return False
    
    try:
        print("Testing executable launch (will timeout after 10 seconds)...")
        
        # Start the process
        process = subprocess.Popen(
            [str(exe_path)],
            cwd=exe_path.parent,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        
        # Wait a few seconds to see if it starts successfully
        time.sleep(5)
        
        # Check if process is still running (good sign)
        if process.poll() is None:
            print("✓ Executable launched successfully")
            # Terminate the process
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            return True
        else:
            # Process exited, check return code
            stdout, stderr = process.communicate()
            print(f"✗ Executable exited with code {process.returncode}")
            if stderr:
                print(f"Error output: {stderr.decode()}")
            return False
            
    except Exception as e:
        print(f"✗ Failed to launch executable: {e}")
        return False

def test_file_sizes():
    """Test if file sizes are reasonable."""
    exe_path = Path("dist/MAIAChat/MAIAChat.exe")
    
    if not exe_path.exists():
        print("✗ Cannot test file size - executable not found")
        return False
    
    exe_size = exe_path.stat().st_size
    exe_size_mb = exe_size / (1024 * 1024)
    
    # Check total directory size
    total_size = 0
    for file_path in Path("dist/MAIAChat").rglob("*"):
        if file_path.is_file():
            total_size += file_path.stat().st_size
    
    total_size_mb = total_size / (1024 * 1024)
    
    print(f"Executable size: {exe_size_mb:.1f} MB")
    print(f"Total package size: {total_size_mb:.1f} MB")
    
    # Reasonable size checks
    if exe_size_mb > 1000:  # 1GB
        print("⚠ Warning: Executable is very large (>1GB)")
    elif exe_size_mb > 500:  # 500MB
        print("⚠ Warning: Executable is large (>500MB)")
    else:
        print("✓ Executable size is reasonable")
    
    if total_size_mb > 2000:  # 2GB
        print("⚠ Warning: Total package is very large (>2GB)")
    elif total_size_mb > 1000:  # 1GB
        print("⚠ Warning: Total package is large (>1GB)")
    else:
        print("✓ Total package size is reasonable")
    
    return True

def test_config_files():
    """Test if configuration files are valid."""
    base_path = Path("dist/MAIAChat")
    
    # Test config.json
    config_path = base_path / "config.json"
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                json.load(f)
            print("✓ config.json is valid JSON")
        except json.JSONDecodeError as e:
            print(f"✗ config.json is invalid: {e}")
            return False
    else:
        print("✗ config.json not found")
        return False
    
    # Test api_keys.json
    api_keys_path = base_path / "api_keys.json"
    if api_keys_path.exists():
        try:
            with open(api_keys_path, 'r') as f:
                json.load(f)
            print("✓ api_keys.json is valid JSON")
        except json.JSONDecodeError as e:
            print(f"✗ api_keys.json is invalid: {e}")
            return False
    else:
        print("✗ api_keys.json not found")
        return False
    
    return True

def main():
    """Run all tests."""
    print("MAIAChat Executable Build Test")
    print("=" * 40)
    
    tests = [
        ("Executable exists", test_executable_exists),
        ("Required files present", test_required_files),
        ("File sizes reasonable", test_file_sizes),
        ("Configuration files valid", test_config_files),
        ("Executable launch test", test_executable_launch),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\nTesting: {test_name}")
        try:
            if test_func():
                passed += 1
            else:
                print(f"Test failed: {test_name}")
        except Exception as e:
            print(f"Test error: {test_name} - {e}")
    
    print("\n" + "=" * 40)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed! Your executable is ready for distribution.")
        return True
    else:
        print("✗ Some tests failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    
    print("\nPress Enter to exit...")
    input()
    
    sys.exit(0 if success else 1) 