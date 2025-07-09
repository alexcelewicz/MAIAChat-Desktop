"""
Terminal Panel component.
This panel displays terminal output and logs.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextCursor


class TerminalPanel(QWidget):
    """Panel for displaying terminal output and logs."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        
    def initUI(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        
        # Title label
        title_label = QLabel("Terminal Console")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #212121;
                padding: 5px;
            }
        """)
        layout.addWidget(title_label)
        
        # Terminal console with monospace font - light mode
        self.terminal_console = QTextEdit()
        self.terminal_console.setReadOnly(True)
        self.terminal_console.setPlaceholderText("Terminal console view (logging, errors, etc)")
        self.terminal_console.setStyleSheet("""
            QTextEdit {
                background-color: #F5F5F5;
                color: #212121;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                padding: 12px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                line-height: 1.4;
            }
        """)
        
        layout.addWidget(self.terminal_console)
        
    def append_text(self, text):
        """Append text to the terminal console."""
        self.terminal_console.append(text)
        
        # Auto-scroll to the bottom
        self.terminal_console.verticalScrollBar().setValue(
            self.terminal_console.verticalScrollBar().maximum()
        )
        
    def clear(self):
        """Clear the terminal console."""
        self.terminal_console.clear()
