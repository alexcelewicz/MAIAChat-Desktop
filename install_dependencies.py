#!/usr/bin/env python3
# install_dependencies.py - Cross-platform script to install all required dependencies

import os
import sys
import subprocess
import platform
import logging
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("install_dependencies.log", encoding='utf-8')
    ]
)

logger = logging.getLogger("InstallDependencies")

def is_windows():
    """Check if the current platform is Windows."""
    return platform.system().lower() == "windows"

def is_macos():
    """Check if the current platform is macOS."""
    return platform.system().lower() == "darwin"

def run_command(command, timeout=300):
    """Run a command with timeout and return the result."""
    try:
        logger.info(f"Running command: {command}")
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        if result.returncode != 0:
            logger.error(f"Command failed with code {result.returncode}")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            return False
        else:
            logger.info(f"Command completed successfully")
            return True
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out after {timeout} seconds")
        return False
    except Exception as e:
        logger.error(f"Error running command: {str(e)}")
        return False

def install_python_packages():
    """Install required Python packages from requirements.txt."""
    try:
        # Read packages from requirements.txt
        requirements_file = "requirements.txt"
        if not os.path.exists(requirements_file):
            logger.error(f"Requirements file {requirements_file} not found")
            return False
        
        with open(requirements_file, 'r') as f:
            requirements_content = f.read()
        
        # Parse requirements and extract package names
        packages = []
        for line in requirements_content.split('\n'):
            line = line.strip()
            # Skip empty lines, comments, and lines with special syntax
            if line and not line.startswith('#') and not line.startswith('--'):
                # Extract package name (remove version specifiers)
                package = line.split('>=')[0].split('==')[0].split('<')[0].split('>')[0].split('!=')[0].split('~=')[0].strip()
                if package:
                    packages.append(package)
        
        if not packages:
            logger.error("No packages found in requirements.txt")
            return False
        
        logger.info(f"Found {len(packages)} packages in requirements.txt")
        
        # Install packages
        for package in packages:
            logger.info(f"Installing {package}...")
            if not run_command(f"{sys.executable} -m pip install {package}"):
                logger.error(f"Failed to install {package}")
                return False
        
        logger.info("All Python packages installed successfully")
        return True
    except Exception as e:
        logger.error(f"Error installing Python packages: {str(e)}")
        return False

def download_nltk_data():
    """Download required NLTK data using the standardized script."""
    try:
        # Use the standardized download_nltk_once.py script
        script_path = "download_nltk_once.py"
        if not os.path.exists(script_path):
            logger.error(f"NLTK download script {script_path} not found")
            return False
        
        logger.info("Running standardized NLTK download script...")
        if not run_command(f"{sys.executable} {script_path}"):
            logger.error("Failed to download NLTK data using standardized script")
            return False
        
        logger.info("NLTK data downloaded successfully using standardized script")
        return True
    except Exception as e:
        logger.error(f"Error downloading NLTK data: {str(e)}")
        return False

def setup_platform_specific():
    """Setup platform-specific configurations."""
    try:
        if is_windows():
            logger.info("Setting up Windows-specific configurations...")
            # No special setup needed for Windows at the moment
        elif is_macos():
            logger.info("Setting up macOS-specific configurations...")
            # Force CPU usage for SentenceTransformer on macOS
            # This is already handled in our fix scripts
        else:
            logger.info("Setting up Linux-specific configurations...")
            # No special setup needed for Linux at the moment
        
        logger.info("Platform-specific setup completed")
        return True
    except Exception as e:
        logger.error(f"Error in platform-specific setup: {str(e)}")
        return False

def main():
    """Main function to install all dependencies."""
    try:
        logger.info(f"Starting dependency installation on {platform.system()} {platform.release()}")
        
        # Install Python packages
        if not install_python_packages():
            logger.error("Failed to install Python packages")
            return False
        
        # Download NLTK data
        if not download_nltk_data():
            logger.error("Failed to download NLTK data")
            return False
        
        # Setup platform-specific configurations
        if not setup_platform_specific():
            logger.error("Failed to setup platform-specific configurations")
            return False
        
        logger.info("All dependencies installed successfully")
        return True
    except Exception as e:
        logger.error(f"Error installing dependencies: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n" + "=" * 80)
        print("All dependencies installed successfully!")
        print("You can now run the application using:")
        print("python start_app.py")
        print("=" * 80 + "\n")
        sys.exit(0)
    else:
        print("\n" + "=" * 80)
        print("Failed to install some dependencies.")
        print("Please check the install_dependencies.log file for details.")
        print("=" * 80 + "\n")
        sys.exit(1)
