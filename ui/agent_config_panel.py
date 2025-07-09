"""
Agent Configuration Panel component.
This panel contains the agent configuration controls and settings.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
                            QPushButton, QLabel, QSpinBox, QScrollArea,
                            QFrame, QCheckBox, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
import os


class AgentConfigPanel(QWidget):
    """Panel for agent configuration."""

    # Define signals
    save_json_clicked = pyqtSignal()
    load_json_clicked = pyqtSignal()
    profiles_clicked = pyqtSignal()
    mcp_config_clicked = pyqtSignal()
    agent_count_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.collapsed = False  # Revert to not collapsed by default
        self.initUI()

    def initUI(self):
        """Initialize the UI components."""
        self.main_layout = QVBoxLayout(self)

        # Header with collapse button
        header_layout = QHBoxLayout()

        # Title label
        title_label = QLabel("Agent Configuration")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #212121;
                padding: 5px;
            }
        """)
        header_layout.addWidget(title_label)

        # Collapse button
        self.collapse_btn = QPushButton()
        self.collapse_btn.setIcon(QIcon(os.path.join("icons", "collapse.svg")))
        self.collapse_btn.setToolTip("Collapse/Expand configuration panel")
        self.collapse_btn.setFixedSize(24, 24)
        self.collapse_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border-radius: 12px;
            }
        """)
        self.collapse_btn.clicked.connect(self.toggle_collapse)
        header_layout.addWidget(self.collapse_btn)

        self.main_layout.addLayout(header_layout)

        # Content widget that can be collapsed
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)

        # Create top controls layout with modern styling
        top_controls = QHBoxLayout()

        # Helper function to create small buttons
        def create_small_button(text, icon_name, tooltip):
            icon_path = os.path.join("icons", f"{icon_name}.svg")
            button = QPushButton(text)
            if os.path.exists(icon_path):
                button.setIcon(QIcon(icon_path))
            button.setToolTip(tooltip)
            button.setStyleSheet("""
                QPushButton {
                    background-color: #f0f0f0;
                    border: 1px solid #dcdcdc;
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-size: 12px;
                    color: #333333;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
                QPushButton:pressed {
                    background-color: #d0d0d0;
                }
            """)
            return button

        # Create JSON buttons with modern styling
        self.save_json_btn = create_small_button("Save", "save", "Save configuration to JSON")
        self.load_json_btn = create_small_button("Load", "load", "Load configuration from JSON")
        self.profiles_btn = create_small_button("Example Profiles", "profile", "Load example agent profiles")
        self.mcp_btn = create_small_button("MCP Config", "database", "Configure MCP servers")

        # Add buttons to layout - Example Profiles button is positioned next to load/save buttons
        top_controls.addWidget(self.save_json_btn)
        top_controls.addWidget(self.load_json_btn)
        top_controls.addWidget(self.profiles_btn)
        top_controls.addWidget(self.mcp_btn)

        self.content_layout.addLayout(top_controls)

        # Agent count control
        agents_layout = QHBoxLayout()
        agents_layout.addWidget(QLabel("Number of Agents:"))

        self.agent_count = QSpinBox()
        self.agent_count.setRange(1, 5)
        self.agent_count.setValue(1)
        self.agent_count.setStyleSheet("""
            QSpinBox {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 6px;
                padding: 6px;
                font-size: 13px;
                min-width: 80px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                border: none;
                background: #F5F5F5;
                width: 20px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background: #E0E0E0;
            }
        """)
        self.agent_count.valueChanged.connect(self.agent_count_changed)
        agents_layout.addWidget(self.agent_count)

        self.content_layout.addLayout(agents_layout)

        # General instructions
        self.content_layout.addWidget(QLabel("General Instructions:"))

        self.general_instructions = QTextEdit()
        self.general_instructions.setPlaceholderText("Enter general instructions for all agents...")
        # Import the font constants from main_window_ui
        from ui.main_window_ui import DEFAULT_FONT_FAMILY

        self.general_instructions.setStyleSheet(f"""
            QTextEdit {{
                background-color: white;
                color: #000000;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                padding: 12px;
                font-family: '{DEFAULT_FONT_FAMILY}', 'Roboto', sans-serif;
                font-size: 13px;
                line-height: 1.5;
            }}
            QTextEdit:focus {{
                border: 1px solid #2196F3;
            }}
        """)
        self.general_instructions.setMaximumHeight(75)  # Limit height to half of previous size
        self.content_layout.addWidget(self.general_instructions)

        # Agent configs - add scroll area for many agents
        self.agent_scroll_area = QScrollArea()
        self.agent_scroll_area.setWidgetResizable(True)
        self.agent_scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        # Create a widget to hold the agent configs
        self.agent_config_widget = QWidget()
        self.agent_config_layout = QVBoxLayout(self.agent_config_widget)

        # Add the widget to the scroll area
        self.agent_scroll_area.setWidget(self.agent_config_widget)

        # Add the scroll area to the content layout
        self.content_layout.addWidget(self.agent_scroll_area)

        # Add content widget to main layout
        self.main_layout.addWidget(self.content_widget)

        # Connect button signals
        self.save_json_btn.clicked.connect(self.save_json_clicked)
        self.load_json_btn.clicked.connect(self.load_json_clicked)
        self.profiles_btn.clicked.connect(self.profiles_clicked)
        self.mcp_btn.clicked.connect(self.mcp_config_clicked)

    def toggle_collapse(self):
        """Toggle the collapsed state of the panel."""
        self.collapsed = not self.collapsed

        if self.collapsed:
            self.content_widget.hide()
            self.collapse_btn.setIcon(QIcon(os.path.join("icons", "expand.svg")))
        else:
            self.content_widget.show()
            self.collapse_btn.setIcon(QIcon(os.path.join("icons", "collapse.svg")))

    def get_general_instructions(self):
        """Get the general instructions text."""
        return self.general_instructions.toPlainText()

    def set_general_instructions(self, text):
        """Set the general instructions text."""
        self.general_instructions.setPlainText(text)
