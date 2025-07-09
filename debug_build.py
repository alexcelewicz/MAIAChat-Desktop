#!/usr/bin/env python3
"""
MAIAChat Desktop - Build Environment Diagnostic Tool

Created by Aleksander Celewicz
Website: MAIAChat.com

This diagnostic tool helps troubleshoot build environment issues
for the MAIAChat Desktop application. Use this when experiencing
build failures or dependency problems.

Usage: python debug_build.py
"""

import os
import sys
from pathlib import Path

def debug_environment():
    """Analyze the build environment and dependencies."""
    print("=== BUILD ENVIRONMENT ANALYSIS ===")
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Python executable: {sys.executable}")

    # Check PyInstaller
    try:
        import PyInstaller
        print(f"PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        print("PyInstaller: NOT INSTALLED")
        print("Install with: pip install pyinstaller>=6.0.0")
        return False

    # Check main entry point
    entry_points = ["start_app.py", "main.py"]
    entry_found = False
    for entry in entry_points:
        if os.path.exists(entry):
            print(f"Entry point: {entry} EXISTS")
            entry_found = True
            break

    if not entry_found:
        print("Entry point: MISSING (looking for start_app.py or main.py)")
        return False

    return True

def debug_directories():
    """Debug directory structure."""
    print("\n=== DIRECTORY STRUCTURE DEBUG ===")
    
    DATA_DIRS = [
        "ui", "handlers", "managers", "rag_components", "core", "api", 
        "utils", "mcp_config", "icons", "images", "docs", "example_profiles", 
        "nltk_data", "models"
    ]
    
    existing_dirs = []
    missing_dirs = []
    
    for dir_name in DATA_DIRS:
        if os.path.exists(dir_name) and os.path.isdir(dir_name):
            existing_dirs.append(dir_name)
            print(f"✓ {dir_name}")
        else:
            missing_dirs.append(dir_name)
            print(f"✗ {dir_name}")
    
    print(f"\nSummary: {len(existing_dirs)} existing, {len(missing_dirs)} missing")
    
    # Check user data directories
    print("\n=== USER DATA DIRECTORIES ===")
    user_dirs = ["knowledge_base", "conversation_history", "profiles", "model_settings", "cache"]
    
    for dir_name in user_dirs:
        if os.path.exists(dir_name) and os.path.isdir(dir_name):
            print(f"✓ {dir_name}")
        else:
            print(f"✗ {dir_name}")
    
    return len(existing_dirs) > 0

def debug_files():
    """Debug important files."""
    print("\n=== IMPORTANT FILES DEBUG ===")
    
    DATA_FILES = [
        "config.json", "api_keys.json", "pricing.json", "custom_models.json",
        "disabled_models.json", "quickdash_config.json", "instruction_templates.py",
        "requirements.txt", "README.md"
    ]
    
    for file_name in DATA_FILES:
        if os.path.exists(file_name) and os.path.isfile(file_name):
            size = os.path.getsize(file_name)
            print(f"✓ {file_name} ({size} bytes)")
        else:
            print(f"✗ {file_name}")

def debug_imports():
    """Debug critical imports."""
    print("\n=== CRITICAL IMPORTS DEBUG ===")
    
    critical_modules = [
        "PyQt6.QtCore", "PyQt6.QtWidgets", "PyQt6.QtGui",
        "sentence_transformers", "torch", "transformers", "numpy",
        "pandas", "requests", "openai"
    ]
    
    working_imports = []
    failed_imports = []
    
    for module in critical_modules:
        try:
            __import__(module)
            working_imports.append(module)
            print(f"✓ {module}")
        except ImportError as e:
            failed_imports.append(module)
            print(f"✗ {module}: {e}")
    
    print(f"\nImport summary: {len(working_imports)} working, {len(failed_imports)} failed")
    return len(failed_imports) == 0

def debug_spec_generation():
    """Debug spec file generation."""
    print("\n=== SPEC FILE GENERATION DEBUG ===")
    
    try:
        # Import the build script functions
        sys.path.insert(0, '.')
        from build_exe import BUILD_CONFIG, DATA_DIRS, DATA_FILES, HIDDEN_IMPORTS
        
        print(f"Build config: {BUILD_CONFIG}")
        print(f"Data dirs count: {len(DATA_DIRS)}")
        print(f"Data files count: {len(DATA_FILES)}")
        print(f"Hidden imports count: {len(HIDDEN_IMPORTS)}")
        
        # Test spec file creation
        spec_content_preview = f"""
Analysis target: {BUILD_CONFIG['main_script']}
App name: {BUILD_CONFIG['app_name']}
Icon file: {BUILD_CONFIG.get('icon_file', 'None')}
"""
        print(f"Spec preview: {spec_content_preview}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error in spec generation: {e}")
        return False

def main():
    """Run all debug checks."""
    print("MAIAChat Build Debug Tool")
    print("=" * 50)
    
    checks = [
        ("Environment", debug_environment),
        ("Directories", debug_directories),
        ("Files", debug_files),
        ("Imports", debug_imports),
        ("Spec Generation", debug_spec_generation),
    ]
    
    passed = 0
    for check_name, check_func in checks:
        print(f"\n{'='*20} {check_name.upper()} {'='*20}")
        try:
            if check_func():
                passed += 1
                print(f"✓ {check_name} check PASSED")
            else:
                print(f"✗ {check_name} check FAILED")
        except Exception as e:
            print(f"✗ {check_name} check ERROR: {e}")
    
    print("\n" + "=" * 50)
    print(f"DEBUG SUMMARY: {passed}/{len(checks)} checks passed")
    
    if passed == len(checks):
        print("✓ Environment looks ready for building!")
        print("Try running: python build_exe.py")
    else:
        print("✗ Issues found that may prevent successful building")
        print("Fix the issues above before attempting to build")
    
    return passed == len(checks)

if __name__ == "__main__":
    success = main()
    
    print("\nPress Enter to exit...")
    input()
    
    sys.exit(0 if success else 1) 