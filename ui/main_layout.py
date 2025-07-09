"""
Main Layout component.
This component manages the overall layout of the application.
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QSplitter, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt

from .unified_response_panel import UnifiedResponsePanel
from .agent_config_panel import AgentConfigPanel
from .terminal_panel import TerminalPanel


class MainLayout(QWidget):
    """Main layout manager for the application."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        """Initialize the UI components."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create the main splitter
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Create the unified response panel and agent config panel
        self.unified_response_panel = UnifiedResponsePanel()
        self.agent_config_panel = AgentConfigPanel()
        self.terminal_panel = TerminalPanel()

        # Create a vertical splitter for the unified response panel and terminal
        self.left_splitter = QSplitter(Qt.Orientation.Vertical)
        self.left_splitter.addWidget(self.unified_response_panel)
        self.left_splitter.addWidget(self.terminal_panel)
        self.left_splitter.setSizes([800, 200])  # Give more space to unified response

        # Add panels to the main splitter
        self.main_splitter.addWidget(self.left_splitter)
        self.main_splitter.addWidget(self.agent_config_panel)

        # Set initial sizes (70%, 30%) - balanced layout for main content and agent config
        # Fix: Convert float values to integers
        total_width = 1000  # Arbitrary base width
        self.main_splitter.setSizes([
            int(total_width * 0.7),  # Convert to int - unified response gets more space
            int(total_width * 0.3)   # Convert to int - agent config gets appropriate space
        ])

        # Add splitter to layout
        layout.addWidget(self.main_splitter)

        # Set splitter style
        splitter_style = """
            QSplitter::handle {
                background-color: #E0E0E0;
                width: 2px;
            }
            QSplitter::handle:hover {
                background-color: #2196F3;
            }
        """
        self.main_splitter.setStyleSheet(splitter_style)
        self.left_splitter.setStyleSheet(splitter_style)

    def get_unified_response_panel(self):
        """Get the unified response panel."""
        return self.unified_response_panel

    def get_agent_config_panel(self):
        """Get the agent configuration panel."""
        return self.agent_config_panel

    def get_terminal_panel(self):
        """Get the terminal panel."""
        return self.terminal_panel
