# main.py
from main_window import MainWindow
import sys
import os
import nltk
import logging
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt
from config import config_manager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log", encoding='utf-8')
    ]
)

logger = logging.getLogger("Main")

def main(app=None):
    try:
        # If app is not provided, create it (usually done by the caller)
        if app is None:
            app = QApplication(sys.argv)
            app.setStyle('Fusion')  # Consistent look across platforms
            # Set light mode palette for the entire application (move from main_window.py)
            palette = app.palette()
            palette.setColor(palette.ColorRole.Window, Qt.GlobalColor.white)
            palette.setColor(palette.ColorRole.WindowText, Qt.GlobalColor.black)
            palette.setColor(palette.ColorRole.Base, Qt.GlobalColor.white)
            palette.setColor(palette.ColorRole.AlternateBase, Qt.GlobalColor.lightGray)
            palette.setColor(palette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
            palette.setColor(palette.ColorRole.ToolTipText, Qt.GlobalColor.black)
            palette.setColor(palette.ColorRole.Text, Qt.GlobalColor.black)
            palette.setColor(palette.ColorRole.Button, Qt.GlobalColor.lightGray)
            palette.setColor(palette.ColorRole.ButtonText, Qt.GlobalColor.black)
            palette.setColor(palette.ColorRole.BrightText, Qt.GlobalColor.red)
            palette.setColor(palette.ColorRole.Link, Qt.GlobalColor.blue)
            palette.setColor(palette.ColorRole.Highlight, Qt.GlobalColor.blue)
            palette.setColor(palette.ColorRole.HighlightedText, Qt.GlobalColor.white)
            app.setPalette(palette)

        main_window = MainWindow()
        main_window.show()
        sys.exit(app.exec())
    except Exception as e:
        # Handle unexpected errors gracefully at the top level
        if app is None:  # If app wasn't created, create a minimal one for the QMessageBox
            app = QApplication(sys.argv)
        QMessageBox.critical(None, "Error", f"An unexpected error occurred: {str(e)}\n\nPlease check app.log for details.")
        logger.critical(f"Fatal error in main application loop: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    # This block is the sole entry point for running the GUI
    logger.info("main.py is being executed directly.")
    main()  # Call the main function without arguments