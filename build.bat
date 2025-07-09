@echo off
echo ========================================
echo MAIAChat Desktop - Executable Builder
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

echo Python found. Checking build requirements...
echo.

REM Install build requirements if needed
echo Installing/updating build requirements...
python -m pip install -r requirements-build-minimal.txt
if errorlevel 1 (
    echo Failed to install from requirements-build-minimal.txt, trying direct install...
    python -m pip install "pyinstaller>=5.0.0"
    if errorlevel 1 (
        echo ERROR: Failed to install build requirements
        pause
        exit /b 1
    )
)

echo.
echo Starting build process...
echo.

REM Run the build script
python build_exe.py
if errorlevel 1 (
    echo.
    echo ERROR: Build failed. Check the output above for details.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build completed successfully!
echo ========================================
echo.
echo Your executable is ready at: dist\MAIAChat\MAIAChat.exe
echo.
echo To distribute your application:
echo 1. Zip the entire 'dist\MAIAChat' folder
echo 2. Share the zip file with users
echo 3. Users should extract and run MAIAChat.exe
echo.
echo Press any key to open the output folder...
pause >nul

REM Open the output folder
if exist "dist\MAIAChat" (
    explorer "dist\MAIAChat"
) else (
    echo Output folder not found. Build may have failed.
)

echo.
echo Build process complete!
pause 