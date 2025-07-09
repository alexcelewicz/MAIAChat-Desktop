#!/usr/bin/env python3
# start_app.py - A script to start the application

import os
import sys
import logging
import subprocess
from error_handler import show_error_message

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("start_app.log", encoding='utf-8')
    ]
)

logger = logging.getLogger("StartApp")

def check_pdf_dependencies():
    """Check if PDF processing dependencies are available."""
    try:
        import fitz
        logger.info("PyMuPDF available - PDF processing enabled")
        return True
    except ImportError:
        logger.warning("PyMuPDF not available - PDF processing features will be limited")
        try:
            import pdfplumber
            logger.info("pdfplumber available as fallback")
            return True
        except ImportError:
            logger.error("No PDF processing libraries available - install PyMuPDF>=1.23.0 for full PDF support")
            return False

def run_main_app():
    """Run the main application by executing main.py."""
    try:
        # Display startup banner
        print("\n" + "="*60)
        print("🤖 MAIAChat Desktop - Multi-Agent AI Assistant")
        print("Created by Aleksander Celewicz")
        print("📺 YouTube: AIex The AI Workbench - https://www.youtube.com/@AIexTheAIWorkbench")
        print("🌐 Website: https://maiachat.com")
        print("="*60 + "\n")

        logger.info("Starting the main application (main.py)...")

        # Check PDF dependencies
        pdf_available = check_pdf_dependencies()
        if not pdf_available:
            logger.warning("Running without PDF processing capabilities")

        # Get the path to the main.py file
        main_path = os.path.join(os.path.dirname(__file__), 'main.py')

        # Run main.py using the current Python executable
        # Use Popen to allow the main application to run independently
        process = subprocess.Popen([sys.executable, main_path])

        # Wait for the main application process to complete
        # The main application itself will handle its event loop and exit conditions
        process.wait()

        if process.returncode != 0:
            logger.error(f"Main application exited with code {process.returncode}")
            return False
        else:
            logger.info("Main application completed successfully")
            return True
    except Exception as e:
        logger.error(f"Error trying to run main application: {str(e)}")
        return False

if __name__ == "__main__":
    # This script's sole purpose is to launch main.py
    if not run_main_app():
        logger.error("Failed to launch main application")
        sys.exit(1)

    logger.info("start_app.py finished execution.")
    sys.exit(0)
