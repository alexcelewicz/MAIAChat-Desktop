# MAIAChat Desktop - Cross-Platform Build Guide

**Created by Aleksander Celewicz**

This guide will help you convert the MAIAChat Desktop application into standalone executable files that can be distributed and run on Windows, macOS, and Linux systems without requiring Python installation.

## Overview

The build process creates:
- **Platform-specific executables** - MAIAChat.exe (Windows), MAIAChat.app (macOS), MAIAChat (Linux)
- **Supporting folder structure** - All necessary files and dependencies
- **User data preservation** - Knowledge base, conversations, and settings
- **Cross-platform compatibility** - Native performance on each operating system

## Prerequisites

### 1. Python Environment
- **Python 3.8 or higher** (Python 3.9-3.11 recommended for best compatibility)
- **All application dependencies installed** via `python install_dependencies.py`
- **Virtual environment strongly recommended** for clean builds

### 2. Build Tools
Install the build requirements using one of these methods:

**Option A: Automated installer (Recommended)**
```bash
python install_build_deps.py
```

**Option B: Manual installation**
```bash
pip install -r requirements-build-minimal.txt
```

**Option C: Direct PyInstaller installation**
```bash
pip install pyinstaller>=6.0.0
```

### 3. System Requirements

#### Windows
- **Windows 10/11** (Windows 10 1809+ recommended)
- **At least 4GB free disk space** for build process
- **8GB+ RAM recommended** for large applications
- **Visual Studio Build Tools** (for some dependencies)

#### macOS
- **macOS 10.14+** (macOS 11+ recommended)
- **Xcode Command Line Tools** installed
- **At least 4GB free disk space** for build process
- **8GB+ RAM recommended** for large applications

#### Linux
- **Ubuntu 18.04+, CentOS 7+, or equivalent**
- **Build essentials** installed (`sudo apt-get install build-essential`)
- **At least 4GB free disk space** for build process
- **8GB+ RAM recommended** for large applications

## Quick Start

### Option 1: Automated Build (Recommended)

#### Windows
```cmd
python build_exe.py
```

#### macOS/Linux
```bash
python build_exe.py
```

This script will:
- **Check all dependencies** and system compatibility
- **Create the PyInstaller configuration** for your platform
- **Build the executable** with optimized settings
- **Create user documentation** and installation guides
- **Clean up build artifacts** to save disk space

### Option 2: Manual Cross-Platform Build

#### Windows Build
```cmd
# Install PyInstaller
pip install pyinstaller

# Create Windows executable
pyinstaller --onedir --windowed --name MAIAChat --icon=icons/app_icon.ico start_app.py

# Alternative: Single file (larger but portable)
pyinstaller --onefile --windowed --name MAIAChat --icon=icons/app_icon.ico start_app.py
```

#### macOS Build
```bash
# Install PyInstaller
pip install pyinstaller

# Create macOS app bundle
pyinstaller --onedir --windowed --name MAIAChat --icon=icons/app_icon.icns start_app.py

# Create DMG (requires additional tools)
# hdiutil create -volname "MAIAChat" -srcfolder dist/MAIAChat.app -ov -format UDZO MAIAChat.dmg
```

#### Linux Build
```bash
# Install PyInstaller
pip install pyinstaller

# Create Linux executable
pyinstaller --onedir --windowed --name MAIAChat start_app.py

# Alternative: Console version (for debugging)
pyinstaller --onedir --console --name MAIAChat-debug start_app.py
```

### Option 3: Platform-Specific Optimizations

#### Windows with UPX Compression
```cmd
# Install UPX first: https://upx.github.io/
pyinstaller --onedir --windowed --upx-dir=C:\upx --name MAIAChat start_app.py
```

#### macOS with Code Signing
```bash
# Requires Apple Developer account
pyinstaller --onedir --windowed --name MAIAChat start_app.py
codesign --force --verify --verbose --sign "Developer ID Application: Your Name" dist/MAIAChat.app
```

#### Linux with AppImage
```bash
# Build standard executable first
pyinstaller --onedir --windowed --name MAIAChat start_app.py

# Then create AppImage (requires additional tools)
# See: https://appimage.org/ for AppImage creation tools
```

## Detailed Cross-Platform Build Process

### Step 1: Prepare Your Environment

#### Windows
```cmd
# Remove any previous builds
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

# Verify all dependencies
pip check
python -c "import start_app; print('All imports successful')"
```

#### macOS/Linux
```bash
# Remove any previous builds
rm -rf dist/
rm -rf build/

# Verify all dependencies
pip check
python -c "import start_app; print('All imports successful')"
```

### Step 2: Configure the Build

The `build_exe.py` script includes comprehensive cross-platform configuration:

- **Application metadata** (name, version, description, creator attribution)
- **Platform detection** (Windows, macOS, Linux specific settings)
- **Data files inclusion** (UI, handlers, configs, documentation)
- **Hidden imports** (ML libraries, PyQt6 components, platform-specific modules)
- **User data preservation** (knowledge base, conversations, settings)
- **Icon handling** (ICO for Windows, ICNS for macOS, PNG for Linux)

### Step 3: Execute the Build

#### All Platforms
```bash
python build_exe.py
```

**Expected output (Windows)**:
```
Building MAIAChat executable for Windows...
==================================================
Checking build dependencies...
✓ PyInstaller 6.x.x found
✓ Windows build tools available
✓ All dependencies checked
Preparing build environment...
✓ Build environment prepared
Creating version info file...
✓ Version info file created
Creating PyInstaller spec file...
✓ Spec file MAIAChat.spec created
Building executable...
Running: python -m PyInstaller --clean --noconfirm MAIAChat.spec
✓ Executable built successfully!
Creating user guide...
✓ User guide created
Creating batch launcher...
✓ Batch launcher created
Cleaning up build artifacts...
✓ Build artifacts cleaned up
==================================================
✓ Build completed successfully!
✓ Executable location: dist/MAIAChat/
✓ Run: dist/MAIAChat/MAIAChat.exe
```

**Expected output (macOS)**:
```
Building MAIAChat executable for macOS...
==================================================
Checking build dependencies...
✓ PyInstaller 6.x.x found
✓ Xcode Command Line Tools available
✓ All dependencies checked
Preparing build environment...
✓ Build environment prepared
Creating PyInstaller spec file...
✓ Spec file MAIAChat.spec created
Building executable...
Running: python -m PyInstaller --clean --noconfirm MAIAChat.spec
✓ App bundle built successfully!
Creating user guide...
✓ User guide created
Cleaning up build artifacts...
✓ Build artifacts cleaned up
==================================================
✓ Build completed successfully!
✓ App bundle location: dist/MAIAChat.app/
✓ Run: open dist/MAIAChat.app
```

**Expected output (Linux)**:
```
Building MAIAChat executable for Linux...
==================================================
Checking build dependencies...
✓ PyInstaller 6.x.x found
✓ Build essentials available
✓ All dependencies checked
Preparing build environment...
✓ Build environment prepared
Creating PyInstaller spec file...
✓ Spec file MAIAChat.spec created
Building executable...
Running: python -m PyInstaller --clean --noconfirm MAIAChat.spec
✓ Executable built successfully!
Creating user guide...
✓ User guide created
Creating launcher script...
✓ Launcher script created
Cleaning up build artifacts...
✓ Build artifacts cleaned up
==================================================
✓ Build completed successfully!
✓ Executable location: dist/MAIAChat/
✓ Run: ./dist/MAIAChat/MAIAChat
```

### Step 4: Test the Executable

#### Windows
```cmd
cd dist\MAIAChat
MAIAChat.exe
```

#### macOS
```bash
open dist/MAIAChat.app
# Or from terminal:
dist/MAIAChat.app/Contents/MacOS/MAIAChat
```

#### Linux
```bash
cd dist/MAIAChat
./MAIAChat
# Or make it executable first:
chmod +x MAIAChat
./MAIAChat
```

### Step 5: Verify Cross-Platform Functionality

Test these features on each platform:
- ✅ **Application starts** without errors
- ✅ **UI loads correctly** with proper scaling
- ✅ **API connections work** with all configured providers
- ✅ **RAG functionality operates** with knowledge base
- ✅ **File operations work** (save/load conversations)
- ✅ **Settings are preserved** between sessions
- ✅ **Platform-specific features** (notifications, file associations)
- ✅ **Performance is acceptable** (startup time, response speed)

## Output Structure

After successful build, you'll have:

```
dist/MAIAChat/
├── MAIAChat.exe                 # Main executable
├── _internal/                   # PyInstaller dependencies
│   ├── *.dll                   # System libraries
│   ├── *.pyd                   # Python extensions
│   └── ...                     # Other dependencies
├── knowledge_base/              # User's knowledge base
├── conversation_history/        # Chat history
├── profiles/                    # Agent profiles
├── config.json                  # Application settings
├── api_keys.json               # API configurations
├── USER_GUIDE.txt              # User documentation
└── Start_MAIAChat.bat          # Batch launcher
```

## Distribution

### What to Include
Distribute the **entire `MAIAChat` folder**, including:
- The executable file
- All supporting files and folders
- User documentation

### What NOT to Include
- Build artifacts (`build/` folder)
- Source code (unless desired)
- Virtual environment files
- Development tools

### Packaging Options

1. **ZIP Archive** (Recommended):
   ```bash
   # Create a ZIP file of the entire folder
   powershell Compress-Archive -Path "dist/MAIAChat" -DestinationPath "MAIAChat-v1.0.0.zip"
   ```

2. **Installer Creation** (Advanced):
   - Use NSIS, Inno Setup, or similar tools
   - Create proper Windows installer
   - Handle registry entries and shortcuts

## Troubleshooting

### Common Build Issues

#### 1. Missing Dependencies
**Error**: `ModuleNotFoundError` during build
**Solution**: 
- Add missing modules to `HIDDEN_IMPORTS` in `build_exe.py`
- Verify all requirements are installed

#### 1a. Build Dependency Installation Issues
**Error**: `ERROR: Could not find a version that satisfies the requirement` or Python version conflicts
**Solutions**:
- Use the automated installer: `python install_build_deps.py`
- Install only PyInstaller: `pip install pyinstaller>=5.0.0`
- Update pip first: `python -m pip install --upgrade pip`
- Check Python version compatibility (3.8+ required)
- For Python 3.12+, some packages may have limited versions available

#### 2. Large Executable Size
**Issue**: Executable is very large (>500MB)
**Solutions**:
- Enable UPX compression (requires separate UPX installation)
- Exclude unnecessary modules in the spec file
- Use `--exclude-module` for unused libraries

#### 3. Slow Startup
**Issue**: Executable takes long to start
**Solutions**:
- Use `--onedir` instead of `--onefile` (already default)
- Exclude debug symbols with `--strip`
- Consider lazy imports in your code

#### 4. Missing Data Files
**Error**: Application can't find configuration or data files
**Solution**:
- Verify all data files are listed in `DATA_FILES` and `DATA_DIRS`
- Check file paths are relative to the executable

#### 5. API/Network Issues
**Error**: Network requests fail in executable
**Solutions**:
- Ensure certificates are included
- Check firewall/antivirus settings
- Verify API keys are properly loaded

### Runtime Issues

#### 1. Application Won't Start
**Debugging steps**:
1. Run from command prompt to see error messages
2. Check `app.log` for detailed errors
3. Verify all files are in the same directory
4. Test on a clean Windows system

#### 2. Missing Features
**Common causes**:
- API keys not configured
- Missing data files
- Incorrect file permissions

#### 3. Performance Issues
**Solutions**:
- Ensure adequate system resources
- Clear cache directory if corrupted
- Check disk space availability

## Advanced Configuration

### Custom Icon
1. Create or obtain a `.ico` file
2. Place it at `icons/app_icon.ico`
3. The build script will automatically include it

### Version Information
Modify the `BUILD_CONFIG` in `build_exe.py`:
```python
BUILD_CONFIG = {
    "app_name": "MAIAChat",
    "version": "1.0.0",
    "description": "Your custom description",
    "company": "Your Company",
    "copyright": "© 2024 Your Company"
}
```

### Excluding Modules
To reduce size, exclude unnecessary modules:
```python
excludes=[
    'tkinter',
    'matplotlib',
    'IPython',
    'jupyter',
    'notebook',
    'your_unused_module'
]
```

### Adding Custom Data
Add your own data files or directories:
```python
DATA_DIRS.append("your_custom_directory")
DATA_FILES.append("your_custom_file.json")
```

## Performance Optimization

### Build Time Optimization
- Use SSD for build process
- Close unnecessary applications
- Use `--clean` flag sparingly (only when needed)

### Runtime Optimization
- Enable UPX compression for smaller size
- Use `--strip` to remove debug symbols
- Consider lazy loading for large modules

### Memory Optimization
- Monitor memory usage during build
- Use `--exclude-module` for unused libraries
- Consider splitting large modules

## Security Considerations for Open Source Builds

### API Keys and Sensitive Data
- ✅ **Never hardcode API keys** in the source code
- ✅ **Use config.json.example** template for user configuration
- ✅ **Verify config.json is in .gitignore** to prevent accidental commits
- ✅ **Provide clear setup instructions** for API key configuration
- ✅ **Use encrypted storage** via the built-in config_manager

### Code Signing (Recommended for Distribution)

#### Windows Code Signing
```cmd
# Requires code signing certificate
signtool sign /f "certificate.p12" /p "password" /t "http://timestamp.digicert.com" dist/MAIAChat/MAIAChat.exe
```

#### macOS Code Signing
```bash
# Requires Apple Developer account
codesign --force --verify --verbose --sign "Developer ID Application: Your Name" dist/MAIAChat.app
```

#### Linux Package Signing
```bash
# For .deb packages
dpkg-sig --sign builder package.deb

# For .rpm packages
rpm --addsign package.rpm
```

### Open Source Security Best Practices
- ✅ **Regular dependency updates** via `pip-audit` or similar tools
- ✅ **Vulnerability scanning** of dependencies before builds
- ✅ **Reproducible builds** with pinned dependency versions
- ✅ **Build environment isolation** using virtual environments
- ✅ **Checksum verification** for distributed executables

## Maintenance and Updates

### Version Management
1. **Update version numbers** in `build_exe.py` and `CHANGELOG.md`
2. **Tag releases** in Git with semantic versioning (v1.0.0, v1.1.0, etc.)
3. **Create GitHub releases** with compiled binaries
4. **Update documentation** to reflect new features and changes

### User Data Migration
```python
# Example migration script for user data
def migrate_user_data(old_version, new_version):
    """Migrate user data between versions."""
    if old_version < "1.1.0":
        # Migrate knowledge base format
        migrate_knowledge_base()
    if old_version < "1.2.0":
        # Update configuration schema
        update_config_schema()
```

### Cross-Platform Testing
- ✅ **Windows**: Test on Windows 10 and 11
- ✅ **macOS**: Test on Intel and Apple Silicon Macs
- ✅ **Linux**: Test on Ubuntu, CentOS, and Arch Linux
- ✅ **Virtual machines** for clean environment testing
- ✅ **Automated testing** with GitHub Actions or similar CI/CD

## Distribution and Packaging

### Windows Distribution
```cmd
# Create installer with NSIS or Inno Setup
# Package as ZIP for portable version
powershell Compress-Archive -Path "dist/MAIAChat" -DestinationPath "MAIAChat-v1.0.0-Windows.zip"
```

### macOS Distribution
```bash
# Create DMG for easy installation
hdiutil create -volname "MAIAChat" -srcfolder dist/MAIAChat.app -ov -format UDZO MAIAChat-v1.0.0-macOS.dmg
```

### Linux Distribution
```bash
# Create tarball
tar -czf MAIAChat-v1.0.0-Linux.tar.gz -C dist MAIAChat

# Or create AppImage for universal compatibility
# See: https://appimage.org/ for AppImage creation tools
```

## Community Support and Contribution

### User Support Channels
- 📚 **Documentation**: README.md, SETUP.md, SECURITY.md
- 🐛 **Bug Reports**: GitHub Issues with provided templates
- 💬 **Community Discussion**: GitHub Discussions
- 🔒 **Security Issues**: See SECURITY.md for responsible disclosure

### Developer Support
- 🤝 **Contributing**: See CONTRIBUTING.md for guidelines
- 🔧 **Build Issues**: GitHub Issues with "build" label
- 📖 **Documentation Updates**: Pull requests welcome
- 🧪 **Testing**: Help test on different platforms and configurations

### Build Script Maintenance
- **Regular PyInstaller updates** for compatibility
- **Platform-specific optimizations** as needed
- **Dependency management** and conflict resolution
- **Performance improvements** and size optimization

## Troubleshooting Common Build Issues

### Import Errors
```bash
# Add missing modules to hidden imports
pyinstaller --hidden-import=missing_module start_app.py
```

### Missing Data Files
```bash
# Add data files explicitly
pyinstaller --add-data "source_path;dest_path" start_app.py
```

### Platform-Specific Issues
- **Windows**: Antivirus false positives (add exclusions)
- **macOS**: Gatekeeper warnings (code signing required)
- **Linux**: Missing system libraries (install dev packages)

## Conclusion

This comprehensive build guide enables you to create professional, cross-platform executables for MAIAChat Desktop. The open source nature allows for community contributions to improve the build process and support additional platforms.

**Key Benefits of Open Source Builds**:
- 🌍 **Cross-platform compatibility** out of the box
- 🔒 **Transparent security** with auditable build process
- 🤝 **Community contributions** for improvements and fixes
- 📈 **Continuous improvement** through user feedback

### Resources and Support

- **PyInstaller Documentation**: https://pyinstaller.org/
- **MAIAChat Repository**: GitHub repository with latest code
- **Build Issues**: GitHub Issues for build-related problems
- **Community Chat**: GitHub Discussions for general help
- **Creator Contact**: Aleksander Celewicz via MAIAChat.com

### Attribution

**MAIAChat Desktop** created by **Aleksander Celewicz**
- Website: [MAIAChat.com](https://MAIAChat.com)
- License: MIT (see LICENSE file)
- Commercial use: Attribution required (see LICENSE for details)

---

**Remember**: Always test your executable on clean systems before distribution, and consider code signing for professional deployment!