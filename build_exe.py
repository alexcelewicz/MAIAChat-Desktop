#!/usr/bin/env python3
"""
MAIAChat Desktop - Executable Build Script
This script creates a standalone executable for the MAIAChat Desktop application.
Created by Aleksander Celewicz
"""

import os
import sys
import shutil
import subprocess
import json
from pathlib import Path

# Import version information
try:
    from version import __version__, APP_NAME, APP_DESCRIPTION, APP_COMPANY, APP_COPYRIGHT
except ImportError:
    # Fallback values if version.py is not available
    __version__ = "1.0.0"
    APP_NAME = "MAIAChat"
    APP_DESCRIPTION = "MAIAChat Desktop - Multi-Agent AI Assistant by Aleksander Celewicz"
    APP_COMPANY = "MAIAChat.com"
    APP_COPYRIGHT = "© 2025 Aleksander Celewicz"

# Build configuration using centralized version information
BUILD_CONFIG = {
    "app_name": APP_NAME,
    "main_script": "main.py",
    "icon_file": "icons/app_icon.ico",  # You'll need to create this
    "version": __version__,
    "description": APP_DESCRIPTION,
    "company": APP_COMPANY,
    "copyright": APP_COPYRIGHT
}

# Directories and files that need to be included with the executable
DATA_DIRS = [
    "ui",
    "handlers", 
    "managers",
    "rag_components",
    "core",
    "api",
    "utils",
    "mcp_config",
    "icons",
    "images",
    "docs",
    "example_profiles",
    "nltk_data",
    "models"
]

DATA_FILES = [
    "config.json",
    "api_keys.json", 
    "pricing.json",
    "custom_models.json",
    "disabled_models.json",
    "quickdash_config.json",
    "instruction_templates.py",
    "requirements.txt",
    "README.md",
    "AMD_OPTIMIZATION_GUIDE.md",
    "CODE_FORMATTING_IMPROVEMENTS.md",
    "OPTIMIZATIONS.md"
]

# Hidden imports that PyInstaller might miss
HIDDEN_IMPORTS = [
    'PyQt6.QtCore',
    'PyQt6.QtWidgets', 
    'PyQt6.QtGui',
    'sentence_transformers',
    'transformers',
    'torch',
    'faiss',
    'nltk',
    'chromadb',
    'openai',
    'anthropic',
    'google.generativeai',
    'google.cloud.aiplatform',
    'tiktoken',
    'rank_bm25',
    'sklearn',
    'pandas',
    'numpy',
    'requests',
    'beautifulsoup4',
    'docx',
    'PyMuPDF',
    'pdfplumber',
    'openpyxl',
    'html2text',
    'tqdm',
    'chardet',
    'keyring',
    'pygments',
    'langdetect',
    'python_frontmatter'
]

def check_dependencies():
    """Check if all required tools are installed."""
    print("Checking build dependencies...")
    
    try:
        import PyInstaller
        print(f"✓ PyInstaller {PyInstaller.__version__} found")
    except ImportError:
        print("✗ PyInstaller not found. Installing...")
        try:
            # Try minimal requirements first
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements-build-minimal.txt"])
            print("✓ Build dependencies installed")
        except subprocess.CalledProcessError:
            print("Failed to install from requirements-build-minimal.txt, trying direct install...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller>=5.0.0"])
                print("✓ PyInstaller installed")
            except subprocess.CalledProcessError as e:
                print(f"✗ Failed to install PyInstaller: {e}")
                return False
    
    # Check if main script exists
    if not os.path.exists(BUILD_CONFIG["main_script"]):
        print(f"✗ Main script {BUILD_CONFIG['main_script']} not found!")
        return False
    
    print("✓ All dependencies checked")
    return True

def create_spec_file():
    """Create a PyInstaller spec file with all necessary configurations."""
    print("Creating PyInstaller spec file...")
    
    # Build data files list
    datas = []
    
    print("Checking data directories and files...")
    
    # Add data directories
    for dir_name in DATA_DIRS:
        if os.path.exists(dir_name) and os.path.isdir(dir_name):
            datas.append(f"('{dir_name}', '{dir_name}')")
            print(f"  ✓ Including directory: {dir_name}")
        else:
            print(f"  ⚠ Skipping missing directory: {dir_name}")
    
    # Add individual data files
    for file_name in DATA_FILES:
        if os.path.exists(file_name) and os.path.isfile(file_name):
            datas.append(f"('{file_name}', '.')")
            print(f"  ✓ Including file: {file_name}")
        else:
            print(f"  ⚠ Skipping missing file: {file_name}")
    
    # Add user data directories
    user_data_dirs = [
        "knowledge_base",
        "conversation_history", 
        "profiles",
        "model_settings",
        "cache"
    ]
    
    for dir_name in user_data_dirs:
        if os.path.exists(dir_name) and os.path.isdir(dir_name):
            datas.append(f"('{dir_name}', '{dir_name}')")
            print(f"  ✓ Including user data directory: {dir_name}")
        else:
            print(f"  ⚠ Skipping missing user data directory: {dir_name}")
    
    if not datas:
        print("  ⚠ Warning: No data files or directories found to include!")
        # Add at least the basic required files
        datas.append("('*.py', '.')")  # Include all Python files as fallback

    # Determine icon path
    icon_path = BUILD_CONFIG.get("icon_file", "")
    icon_line = f"icon='{icon_path}'," if icon_path and os.path.exists(icon_path) else "# icon=None,"

    # Create the spec file content
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None

a = Analysis(
    ['{BUILD_CONFIG["main_script"]}'],
    pathex=[],
    binaries=[],
    datas=[
        {','.join(datas)}
    ],
    hiddenimports={HIDDEN_IMPORTS},
    hookspath=['hooks'],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'IPython',
        'jupyter',
        'notebook'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='{BUILD_CONFIG["app_name"]}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Set to True for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    {icon_line}
    version='version_info.txt'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='{BUILD_CONFIG["app_name"]}'
)
'''
    
    spec_filename = f'{BUILD_CONFIG["app_name"]}.spec'
    
    try:
        with open(spec_filename, 'w', encoding='utf-8') as f:
            f.write(spec_content)
        
        print(f"✓ Spec file {spec_filename} created")
        
        # Verify the spec file was created and is readable
        if os.path.exists(spec_filename):
            with open(spec_filename, 'r', encoding='utf-8') as f:
                content = f.read()
                if len(content) > 100:  # Basic sanity check
                    print(f"✓ Spec file verified ({len(content)} characters)")
                else:
                    print(f"⚠ Spec file seems too short ({len(content)} characters)")
        else:
            print(f"✗ Spec file was not created successfully")
            return False
            
    except Exception as e:
        print(f"✗ Failed to create spec file: {e}")
        return False
    
    return True

def create_version_info():
    """Create version info file for Windows executable."""
    print("Creating version info file...")
    
    version_info = f'''# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1,0,0,0),
    prodvers=(1,0,0,0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'{BUILD_CONFIG["company"]}'),
        StringStruct(u'FileDescription', u'{BUILD_CONFIG["description"]}'),
        StringStruct(u'FileVersion', u'{BUILD_CONFIG["version"]}'),
        StringStruct(u'InternalName', u'{BUILD_CONFIG["app_name"]}'),
        StringStruct(u'LegalCopyright', u'{BUILD_CONFIG["copyright"]}'),
        StringStruct(u'OriginalFilename', u'{BUILD_CONFIG["app_name"]}.exe'),
        StringStruct(u'ProductName', u'{BUILD_CONFIG["app_name"]}'),
        StringStruct(u'ProductVersion', u'{BUILD_CONFIG["version"]}')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
'''
    
    with open('version_info.txt', 'w') as f:
        f.write(version_info)
    
    print("✓ Version info file created")

def create_app_icon():
    """Create a default app icon if none exists."""
    icon_path = BUILD_CONFIG.get("icon_file", "")
    if icon_path and not os.path.exists(icon_path):
        print(f"Warning: Icon file {icon_path} not found. Executable will use default icon.")
        print("To add a custom icon, place an .ico file at the specified path.")

def prepare_build_environment():
    """Prepare the build environment."""
    print("Preparing build environment...")
    
    # Create necessary directories if they don't exist
    os.makedirs("icons", exist_ok=True)
    os.makedirs("hooks", exist_ok=True)
    
    # Clean previous build
    if os.path.exists("dist"):
        print("Cleaning previous build...")
        shutil.rmtree("dist")
    
    if os.path.exists("build"):
        shutil.rmtree("build")
    
    # Clean up any previous spec files
    for spec_file in Path(".").glob("*.spec"):
        if spec_file.name != f"{BUILD_CONFIG['app_name']}.spec":
            spec_file.unlink()
    
    print("✓ Build environment prepared")

def build_executable():
    """Build the executable using PyInstaller."""
    print("Building executable...")
    
    # Verify spec file exists
    spec_file = f"{BUILD_CONFIG['app_name']}.spec"
    if not os.path.exists(spec_file):
        print(f"✗ Spec file {spec_file} not found!")
        return False
    
    try:
        # Run PyInstaller with the spec file
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--clean",
            "--noconfirm", 
            spec_file
        ]
        
        print(f"Running: {' '.join(cmd)}")
        print("This may take several minutes...")
        
        # Run with real-time output for better user experience
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Print output in real-time
        output_lines = []
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
                output_lines.append(output)
        
        return_code = process.poll()
        
        if return_code == 0:
            print("✓ Executable built successfully!")
            return True
        else:
            print("✗ Build failed!")
            print(f"Exit code: {return_code}")
            
            # Save full output to log file for debugging
            with open("build_error.log", "w") as f:
                f.write("".join(output_lines))
            print("Full build log saved to build_error.log")
            return False
            
    except FileNotFoundError:
        print("✗ PyInstaller not found! Please install it first:")
        print("  python install_build_deps.py")
        return False
    except Exception as e:
        print(f"✗ Build error: {e}")
        return False

def create_user_guide():
    """Create a user guide for the executable."""
    print("Creating user guide...")
    
    guide_content = f"""# {BUILD_CONFIG['app_name']} - Standalone Executable

## Installation and Setup

1. **Extract the Application**
   - Extract the entire `{BUILD_CONFIG['app_name']}` folder to your desired location
   - Do NOT move individual files - keep the entire folder structure intact

2. **First Run**
   - Run `{BUILD_CONFIG['app_name']}.exe` from the extracted folder
   - The application will create necessary configuration files on first run
   - Configure your API keys in the settings

## Important Files and Folders

### User Data (Safe to modify/backup):
- `config.json` - Main application configuration
- `api_keys.json` - Your API keys (keep secure!)
- `knowledge_base/` - Your indexed documents and embeddings
- `conversation_history/` - Your chat history
- `profiles/` - Your saved agent profiles
- `model_settings/` - Custom model configurations
- `cache/` - Application cache (can be deleted if needed)

### Application Files (Do NOT modify):
- `{BUILD_CONFIG['app_name']}.exe` - Main executable
- `_internal/` - Application dependencies and libraries
- Other .dll and support files

## Backup Recommendations

Regularly backup these important folders:
- `knowledge_base/`
- `conversation_history/`
- `profiles/`
- `config.json`
- `api_keys.json`

## Troubleshooting

1. **Application won't start**
   - Check that all files are in the same folder
   - Run from command prompt to see error messages
   - Check `app.log` for detailed error information

2. **Missing API functionality**
   - Verify your API keys in settings
   - Check internet connection
   - Review `app.log` for API-related errors

3. **RAG/Knowledge Base issues**
   - Ensure `knowledge_base/` folder exists and is writable
   - Check `rag_handler.log` for indexing errors
   - Try rebuilding the knowledge base if corrupted

4. **Performance issues**
   - Close other resource-intensive applications
   - Check available disk space
   - Consider clearing the `cache/` folder

## Updates

To update the application:
1. Backup your user data (see above)
2. Replace the application files with new version
3. Keep your user data folders intact

For support and updates, visit: [Your support URL]
"""
    
    with open(f"dist/{BUILD_CONFIG['app_name']}/USER_GUIDE.txt", 'w') as f:
        f.write(guide_content)
    
    print("✓ User guide created")

def create_batch_launcher():
    """Create a batch file launcher for easier execution."""
    print("Creating batch launcher...")
    
    batch_content = f'''@echo off
cd /d "%~dp0"
echo Starting {BUILD_CONFIG['app_name']}...
"{BUILD_CONFIG['app_name']}.exe"
if errorlevel 1 (
    echo.
    echo Application encountered an error. Check app.log for details.
    echo Press any key to exit...
    pause >nul
)
'''
    
    with open(f"dist/{BUILD_CONFIG['app_name']}/Start_{BUILD_CONFIG['app_name']}.bat", 'w') as f:
        f.write(batch_content)
    
    print("✓ Batch launcher created")

def post_build_cleanup():
    """Clean up build artifacts."""
    print("Cleaning up build artifacts...")
    
    # Remove spec file
    spec_file = f"{BUILD_CONFIG['app_name']}.spec"
    if os.path.exists(spec_file):
        os.remove(spec_file)
    
    # Remove version info file
    if os.path.exists("version_info.txt"):
        os.remove("version_info.txt")
    
    # Remove build directory
    if os.path.exists("build"):
        shutil.rmtree("build")
    
    print("✓ Build artifacts cleaned up")

def main():
    """Main build process."""
    print(f"Building {BUILD_CONFIG['app_name']} executable...")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        return False
    
    # Prepare build environment
    prepare_build_environment()
    
    # Create build files
    create_app_icon()
    create_version_info()
    if not create_spec_file():
        return False
    
    # Build executable
    if not build_executable():
        return False
    
    # Post-build tasks
    create_user_guide()
    create_batch_launcher()
    post_build_cleanup()
    
    print("=" * 50)
    print(f"✓ Build completed successfully!")
    print(f"✓ Executable location: dist/{BUILD_CONFIG['app_name']}/")
    print(f"✓ Run: dist/{BUILD_CONFIG['app_name']}/{BUILD_CONFIG['app_name']}.exe")
    print("\nIMPORTANT: Distribute the entire folder, not just the .exe file!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 