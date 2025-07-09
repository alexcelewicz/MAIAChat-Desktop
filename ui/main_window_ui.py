# Standard library imports
import os
from datetime import datetime
from pathlib import Path

# Third-party imports
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel, QSpinBox, QTabWidget,
    QFileDialog, QMessageBox, QCheckBox, QSplitter, QSizePolicy, QToolButton,
    QListWidget, QListWidgetItem, QAbstractItemView, QMenu, QDialog, QDialogButtonBox,
    QScrollArea, QFrame, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSlot, QTimer, QThread, QSize, QUrl
from PyQt6.QtGui import QTextCursor, QFont, QIcon, QDesktopServices

# Local application imports
from instruction_templates import InstructionTemplates
from py_to_pdf_converter import py_to_pdf
from progress_dialog import ProgressDialog
from cache_manager import CacheManager
from config_manager import ConfigManager
from conversation_manager import ConversationManager
from signal_manager import SignalManager
from knowledge_base import KnowledgeBaseDialog
from api_key_manager import api_key_manager, ApiKeyDefinition
from profile_dialog import ProfileDialog
from profile_manager import profile_manager, Profile, AgentProfile
from mcp_client import mcp_client, add_default_servers_if_empty
from mcp_config_dialog import MCPConfigDialog, MCPExampleProfilesDialog

# Import the MainLayout class
try:
    from ui.main_layout import MainLayout
except ImportError as e:
    import logging
    logging.error(f"Error importing MainLayout: {e}. Please ensure ui/main_layout.py exists.")
    MainLayout = None

# Import token counter (optional)
try:
    from token_counter import token_counter
except ImportError:
    token_counter = None

# Import TokenDisplay
try:
    from ui.token_display import TokenDisplay
except ImportError:
    import logging
    logging.warning("Error importing TokenDisplay. Falling back to QLabel.")
    TokenDisplay = None

# --- Constants ---
ICON_DIR = Path("icons")
# Use system-appropriate fonts
import platform
if platform.system() == "Windows":
    DEFAULT_FONT_FAMILY = "Segoe UI"
    CONSOLE_FONT_FAMILY = "Consolas"
elif platform.system() == "Darwin":  # macOS
    DEFAULT_FONT_FAMILY = "SF Pro Text"
    CONSOLE_FONT_FAMILY = "Menlo"
else:  # Linux and others
    DEFAULT_FONT_FAMILY = "Roboto"
    CONSOLE_FONT_FAMILY = "DejaVu Sans Mono"
DEFAULT_FONT_SIZE = 10
CONSOLE_FONT_SIZE = 10

# --- Styling Constants ---
COLOR_LIGHT_BG = "#F5F5F5"
COLOR_DARK_TEXT = "#212121"
COLOR_MEDIUM_TEXT = "#424242"
COLOR_LIGHT_TEXT = "#757575"
COLOR_BORDER = "#E0E0E0"
COLOR_WHITE = "#FFFFFF"
COLOR_TAB_INACTIVE_BG = "#E0E0E0"
COLOR_PRIMARY_ACCENT = "#2196F3"
COLOR_PRIMARY_DARK = "#1976D2"
COLOR_PRIMARY_HOVER_LIGHT = "#42A5F5"
COLOR_PRIMARY_HOVER_DARK = "#1E88E5"
COLOR_DANGER = "#F44336"
COLOR_DANGER_DARK = "#D32F2F"
COLOR_DANGER_HOVER_LIGHT = "#EF5350"
COLOR_DANGER_HOVER_DARK = "#E53935"
COLOR_DANGER_BORDER = "#C62828"
COLOR_LIST_HOVER = "#E3F2FD"

GLOBAL_STYLE = f"""
    QMainWindow, QWidget {{
        background-color: {COLOR_LIGHT_BG};
        color: {COLOR_DARK_TEXT};
    }}
    QTabWidget::pane {{
        border: 1px solid {COLOR_BORDER};
        background-color: {COLOR_WHITE};
    }}
    QTabBar::tab {{
        background-color: {COLOR_TAB_INACTIVE_BG};
        color: {COLOR_MEDIUM_TEXT};
        padding: 8px 16px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }}
    QTabBar::tab:selected {{
        background-color: {COLOR_WHITE};
        color: {COLOR_DARK_TEXT};
        border: 1px solid {COLOR_BORDER};
        border-bottom: none;
    }}
    QTextEdit {{
        border: 1px solid {COLOR_BORDER};
        border-radius: 4px; /* Default border radius for text edits */
        padding: 5px;
         background-color: {COLOR_WHITE}; /* Ensure white background */
    }}
    QPushButton {{ /* Basic default style */
        background-color: {COLOR_TAB_INACTIVE_BG};
        color: {COLOR_DARK_TEXT};
        border: 1px solid {COLOR_BORDER};
        border-radius: 4px;
        padding: 5px 10px;
        font-size: 13px;
        font-weight: 500;
    }}
     QPushButton:hover {{
        background-color: #dcdcdc; /* Slightly darker gray */
    }}
     QPushButton:pressed {{
        background-color: #c8c8c8; /* Even darker gray */
    }}
"""

PRIMARY_BUTTON_STYLE = f"""
    QPushButton {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 {COLOR_PRIMARY_ACCENT}, stop:1 {COLOR_PRIMARY_DARK});
        color: {COLOR_WHITE};
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        font-size: 13px;
        font-weight: 500;
    }}
    QPushButton:hover {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 {COLOR_PRIMARY_HOVER_LIGHT}, stop:1 {COLOR_PRIMARY_ACCENT});
        border: 1px solid {COLOR_PRIMARY_HOVER_DARK};
    }}
    QPushButton:pressed {{
        background: {COLOR_PRIMARY_DARK};
        padding-top: 9px; /* Simulate press */
        padding-left: 17px;
    }}
    QPushButton:disabled {{
        background-color: #bdbdbd; /* Grey out when disabled */
        color: #757575;
    }}
"""

DANGER_BUTTON_STYLE = f"""
    QPushButton {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 {COLOR_DANGER}, stop:1 {COLOR_DANGER_DARK});
        color: {COLOR_WHITE};
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        font-size: 13px;
        font-weight: 500;
    }}
    QPushButton:hover {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 {COLOR_DANGER_HOVER_LIGHT}, stop:1 {COLOR_DANGER});
        border: 1px solid {COLOR_DANGER_BORDER};
    }}
    QPushButton:pressed {{
        background: {COLOR_DANGER_DARK};
        padding-top: 9px; /* Simulate press */
        padding-left: 17px;
    }}
     QPushButton:disabled {{
        background-color: #bdbdbd;
        color: #757575;
    }}
"""

TOOL_BUTTON_STYLE = f"""
    QToolButton {{
        border: none;
        padding: 3px;
        font-family: '{DEFAULT_FONT_FAMILY}', 'Roboto', sans-serif;
        background-color: transparent; /* Make background transparent */
    }}
    QToolButton:hover {{
        background-color: #e0e0e0;
        border-radius: 3px;
    }}
     QToolButton:pressed {{
        background-color: #c8c8c8;
    }}
"""

LIST_WIDGET_STYLE = f"""
    QListWidget {{
        background-color: {COLOR_WHITE};
        border: 1px solid {COLOR_BORDER};
        border-radius: 8px;
        padding: 8px;
        font-family: '{DEFAULT_FONT_FAMILY}', 'Roboto', sans-serif;
        font-size: 13px;
    }}
    QListWidget::item {{
        border-bottom: 1px solid {COLOR_BORDER};
        padding: 8px;
        margin: 2px 0;
    }}
    QListWidget::item:selected {{
        background-color: {COLOR_PRIMARY_ACCENT};
        color: {COLOR_WHITE};
        border-radius: 4px;
    }}
    QListWidget::item:hover:!selected {{
        background-color: {COLOR_LIST_HOVER};
        border-radius: 4px;
    }}
"""

TEXT_EDIT_READONLY_STYLE = f"""
    QTextEdit {{
        background-color: {COLOR_LIGHT_BG};
        border: 1px solid {COLOR_BORDER};
        border-radius: 8px;
        padding: 12px;
        font-family: '{DEFAULT_FONT_FAMILY}', 'Roboto', sans-serif;
        font-size: 13px;
        line-height: 1.5;
        color: {COLOR_DARK_TEXT}; /* Ensure text is visible */
    }}
"""

class MainWindowUI:
    """Handles the setup and layout of the main application window's UI components."""

    def __init__(self, main_window: QMainWindow):
        """
        Initialises the MainWindowUI.

        Args:
            main_window: The main window instance (QMainWindow) that this UI belongs to.
        """
        if MainLayout is None:
             # Handle the case where MainLayout failed to import
             QMessageBox.critical(main_window, "Initialization Error",
                                  "Failed to load critical UI component: MainLayout.\n"
                                  "Please check the installation and file paths.")
             # Optionally, prevent the application from continuing
             # sys.exit(1) # Or handle more gracefully depending on app structure
             # For now, let's try to proceed but warn the user things will be broken.
             print("WARNING: MainLayout not loaded, Chat Tab will be incomplete.")

        self.main_window = main_window
        self.initUI()

    def initUI(self) -> None:
        """Sets up the main UI structure, including tabs and global styling."""
        # Set the window title
        self.main_window.setWindowTitle("MAIAChat.com - Desktop Version")
        
        # Set window size to be larger by default (similar to second picture)
        self.main_window.setGeometry(100, 100, 1400, 900)  # x, y, width, height
        self.main_window.setMinimumSize(1200, 700)  # Minimum size to ensure usability
        
        # Ensure the icons directory exists
        ICON_DIR.mkdir(parents=True, exist_ok=True)

        main_widget = QWidget()
        self.main_window.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Apply global styling
        self.main_window.setStyleSheet(GLOBAL_STYLE)

        # Create tab widget
        self.main_window.tab_widget = QTabWidget()
        layout.addWidget(self.main_window.tab_widget)

        # Create menu bar
        self.create_menu_bar()

        # Create tabs
        self.create_chat_tab()
        self.create_history_tab()
        self.create_settings_tab()
        self.create_about_tab()

    def create_menu_bar(self) -> None:
        """Create the main menu bar with Help menu including social links."""
        menubar = self.main_window.menuBar()

        # Help Menu
        help_menu = menubar.addMenu('&Help')

        # YouTube Channel Action
        youtube_action = help_menu.addAction('📺 YouTube Channel - AIex The AI Workbench')
        youtube_action.setStatusTip('Visit the YouTube channel for tutorials and updates')
        youtube_action.triggered.connect(self._open_youtube_channel)

        # Website Action
        website_action = help_menu.addAction('🌐 Visit MAIAChat.com')
        website_action.setStatusTip('Visit the official MAIAChat website')
        website_action.triggered.connect(self._open_website)

        # GitHub Action
        github_action = help_menu.addAction('💻 View Source Code')
        github_action.setStatusTip('View the source code on GitHub')
        github_action.triggered.connect(self._open_github)

        help_menu.addSeparator()

        # About Action
        about_action = help_menu.addAction('ℹ️ About MAIAChat')
        about_action.setStatusTip('Show application information')
        about_action.triggered.connect(lambda: self.main_window.tab_widget.setCurrentIndex(3))  # Switch to About tab

    def create_chat_tab(self) -> None:
        """Creates the 'Chat' tab with its complex layout and widgets."""
        chat_tab = QWidget()
        layout = QVBoxLayout(chat_tab)

        if MainLayout is None:
            # If MainLayout didn't load, add a placeholder message
            error_label = QLabel("Chat UI could not be loaded (MainLayout missing).")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(error_label)
            self.main_window.tab_widget.addTab(chat_tab, "Chat (Error)")
            return # Stop creating the rest of the chat tab

        # Create the main layout with two columns using the imported class
        self.main_layout = MainLayout()
        layout.addWidget(self.main_layout)

        # --- Get references to panels from MainLayout ---
        unified_response_panel = self.main_layout.get_unified_response_panel()
        agent_config_panel = self.main_layout.get_agent_config_panel()
        terminal_panel = self.main_layout.get_terminal_panel()

        # --- Assign UI components to main_window attributes ---
        # Note: This creates coupling between MainWindowUI and MainWindow.
        # A cleaner approach might involve MainWindow pulling these references
        # after UI setup, but this maintains the original structure.
        self.main_window.unified_response = unified_response_panel.unified_response
        self.main_window.input_prompt = unified_response_panel.input_prompt
        self.main_window.terminal_console = terminal_panel.terminal_console

        # Assign button references
        self.main_window.load_file_btn = unified_response_panel.load_file_btn
        self.main_window.knowledge_base_btn = unified_response_panel.knowledge_base_btn
        self.main_window.send_btn = unified_response_panel.send_btn
        self.main_window.follow_up_btn = unified_response_panel.follow_up_btn
        self.main_window.stop_btn = unified_response_panel.stop_btn
        self.main_window.clear_btn = unified_response_panel.clear_btn
        self.main_window.save_pdf_btn = unified_response_panel.save_pdf_btn

        # Assign agent config panel references
        self.main_window.agent_count = agent_config_panel.agent_count
        self.main_window.general_instructions = agent_config_panel.general_instructions
        self.main_window.agent_config_layout = agent_config_panel.agent_config_layout
        self.main_window.agent_configs = []

        # Assign remaining buttons from agent config panel
        save_json_btn = agent_config_panel.save_json_btn
        load_json_btn = agent_config_panel.load_json_btn
        self.main_window.profiles_btn = agent_config_panel.profiles_btn
        self.main_window.mcp_btn = agent_config_panel.mcp_btn

        # Apply specific styles if needed (assuming MainLayout handles its own styles)
        self.main_window.send_btn.setStyleSheet(PRIMARY_BUTTON_STYLE)
        self.main_window.follow_up_btn.setStyleSheet(PRIMARY_BUTTON_STYLE)
        self.main_window.stop_btn.setStyleSheet(DANGER_BUTTON_STYLE)
        self.main_window.clear_btn.setStyleSheet(DANGER_BUTTON_STYLE)

        # --- Token Counter Setup ---
        token_counter_layout = QHBoxLayout()
        token_counter_label = QLabel("Token Usage:")
        token_counter_label.setStyleSheet(f"""
            font-size: 13px;
            font-weight: bold;
            color: {COLOR_MEDIUM_TEXT};
        """)
        token_counter_layout.addWidget(token_counter_label)

        # Use TokenDisplay if available, otherwise fallback to QLabel
        if TokenDisplay is not None:
            self.main_window.chat_token_display = TokenDisplay()
        else:
            self.main_window.chat_token_display = QLabel("Input+System: 0 | Output: 0 | Total: 0 | Cost: $0.00 | Tokens/s: 0.0")
            self.main_window.chat_token_display.setStyleSheet(f"""
                font-size: 13px;
                color: {COLOR_LIGHT_TEXT};
                font-weight: 500;
            """)
        token_counter_layout.addWidget(self.main_window.chat_token_display)
        token_counter_layout.addStretch()

        # Add token counter to the top of the unified response panel
        unified_response_panel.layout().insertLayout(0, token_counter_layout)

        # --- Connect Signals ---
        self.main_window.send_btn.clicked.connect(self.main_window.send_prompt)
        self.main_window.follow_up_btn.clicked.connect(self.main_window.send_follow_up)
        self.main_window.load_file_btn.clicked.connect(self.main_window.load_file)
        self.main_window.knowledge_base_btn.clicked.connect(self.main_window.access_knowledge_base)
        self.main_window.profiles_btn.clicked.connect(self.main_window.show_profiles_dialog)
        self.main_window.mcp_btn.clicked.connect(self.main_window.show_mcp_dialog)
        save_json_btn.clicked.connect(self.main_window.save_to_json)
        load_json_btn.clicked.connect(self.main_window.load_from_json)
        self.main_window.stop_btn.clicked.connect(self.main_window.stop_agents)
        # Connect clear actions
        self.main_window.clear_btn.clicked.connect(self.main_window.clear_outputs)
        self.main_window.clear_btn.clicked.connect(self.main_window.clear_chat)
        self.main_window.save_pdf_btn.clicked.connect(self.main_window.save_code_to_pdf)

        # Connect agent count signal
        agent_config_panel.agent_count_changed.connect(self.main_window.update_agent_config)

        # --- Initial State ---
        self.main_window.follow_up_btn.setEnabled(False)
        self.main_window.update_agent_config(1)  # Initial setup for 1 agent

        # Set default fonts
        default_font = QFont(DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE)
        console_font = QFont(CONSOLE_FONT_FAMILY, CONSOLE_FONT_SIZE)
        self.main_window.unified_response.setFont(default_font)
        self.main_window.input_prompt.setFont(default_font) # Apply to input too
        self.main_window.terminal_console.setFont(console_font)

        self.main_window.tab_widget.addTab(chat_tab, "Chat")

    def create_history_tab(self) -> None:
        """Creates the 'History' tab for Browse past conversations."""
        history_tab = QWidget()
        layout = QVBoxLayout(history_tab)
        layout.setSpacing(15) # Add some vertical spacing

        # --- Header ---
        header_layout = QHBoxLayout()
        header_label = QLabel("Conversation History")
        header_label.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {COLOR_DARK_TEXT};
            padding: 10px 0;
        """)
        header_layout.addWidget(header_label)
        header_layout.addStretch()

        refresh_btn = self._create_text_icon_tool_button(
            "Refresh", "refresh", "Refresh conversation list" # Assuming 'refresh.png'
        )
        refresh_btn.clicked.connect(self.main_window.refresh_conversation_list)
        header_layout.addWidget(refresh_btn)

        delete_all_btn = self._create_text_icon_tool_button(
             "Delete All", "delete_all", "Delete all conversations" # Assuming 'delete_all.png'
        )
        delete_all_btn.clicked.connect(self.main_window.delete_all_conversations)
        header_layout.addWidget(delete_all_btn)

        layout.addLayout(header_layout)

        # --- Conversation List ---
        self.main_window.conversation_list = QListWidget()
        self.main_window.conversation_list.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.main_window.conversation_list.setStyleSheet(LIST_WIDGET_STYLE)
        # Add context menu
        self.main_window.conversation_list.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.main_window.conversation_list.customContextMenuRequested.connect(
            self.main_window.show_conversation_context_menu
        )
        layout.addWidget(self.main_window.conversation_list)

        # --- Action Buttons ---
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        load_conv_btn = QPushButton("Load Conversation")
        load_conv_btn.clicked.connect(self.main_window.load_selected_conversation)
        load_conv_btn.setStyleSheet(PRIMARY_BUTTON_STYLE)
        button_layout.addWidget(load_conv_btn)

        delete_conv_btn = QPushButton("Delete Conversation")
        delete_conv_btn.clicked.connect(self.main_window.delete_selected_conversation)
        delete_conv_btn.setStyleSheet(DANGER_BUTTON_STYLE)
        button_layout.addWidget(delete_conv_btn)

        layout.addLayout(button_layout)

        # --- Token Statistics ---
        token_stats_label = QLabel("Token Usage Statistics (Selected Conversation)")
        token_stats_label.setStyleSheet(f"""
            font-size: 14px; /* Slightly smaller than header */
            font-weight: bold;
            color: {COLOR_DARK_TEXT};
            padding-top: 15px; /* Add space above */
        """)
        layout.addWidget(token_stats_label)

        self.main_window.token_stats_text = QTextEdit()
        self.main_window.token_stats_text.setReadOnly(True)
        self.main_window.token_stats_text.setFixedHeight(100) # Give it a fixed height
        self.main_window.token_stats_text.setStyleSheet(TEXT_EDIT_READONLY_STYLE)
        layout.addWidget(self.main_window.token_stats_text)

        self.main_window.tab_widget.addTab(history_tab, "History")

        # Initial population
        self.main_window.refresh_conversation_list()

    def create_settings_tab(self) -> None:
        """Creates the 'Settings' tab with a tabbed interface for different setting categories."""
        settings_tab = QWidget()
        main_layout = QVBoxLayout(settings_tab)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create tab widget for settings categories
        from PyQt6.QtWidgets import QTabWidget
        settings_tab_widget = QTabWidget()
        settings_tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #c0c0c0;
                border-radius: 4px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                border: 1px solid #c0c0c0;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 8px 16px;
                margin-right: 2px;
                font-weight: bold;
                color: #505050;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 1px solid white;
                color: #2c3e50;
            }
            QTabBar::tab:hover {
                background-color: #e8e8e8;
            }
        """)
        
        # Create individual setting tabs
        api_settings_tab = self._create_api_settings_tab()
        rag_settings_tab = self._create_rag_settings_tab()
        general_settings_tab = self._create_general_settings_tab()
        
        # Add tabs to tab widget
        settings_tab_widget.addTab(api_settings_tab, "API Settings")
        settings_tab_widget.addTab(rag_settings_tab, "RAG Settings")
        settings_tab_widget.addTab(general_settings_tab, "General Settings")
        
        main_layout.addWidget(settings_tab_widget)
        
        self.main_window.tab_widget.addTab(settings_tab, "Settings")

    def create_about_tab(self) -> None:
        """Creates the 'About' tab with comprehensive application information and attribution."""
        about_tab = QWidget()
        layout = QVBoxLayout(about_tab)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Create scroll area for the content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(25)

        # Application Title
        title_label = QLabel("MAIAChat.com Desktop")
        title_label.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(title_label)

        # Subtitle
        subtitle_label = QLabel("Multi-Agent AI Desktop Application")
        subtitle_label.setStyleSheet("""
            font-size: 16px;
            color: #34495e;
            font-style: italic;
            margin-bottom: 5px;
        """)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(subtitle_label)

        # Version and Build Information
        version_info_frame = QFrame()
        version_info_frame.setStyleSheet("""
            QFrame {
                background-color: #f1f3f4;
                border: 1px solid #d1d5db;
                border-radius: 8px;
                padding: 15px;
                margin: 10px 0;
            }
        """)
        version_info_layout = QVBoxLayout(version_info_frame)

        # Import version information
        try:
            from version import get_version_display
            version_text = get_version_display()
        except ImportError:
            version_text = "Version 1.0.0"

        version_label = QLabel(version_text)
        version_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #1f2937;
            margin-bottom: 5px;
        """)
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_info_layout.addWidget(version_label)

        # Release Date
        release_date_label = QLabel("Released: January 27, 2025")
        release_date_label.setStyleSheet("""
            font-size: 14px;
            color: #6b7280;
            margin-bottom: 5px;
        """)
        release_date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_info_layout.addWidget(release_date_label)

        # Build Information
        build_info_label = QLabel("Build: Open Source Release")
        build_info_label.setStyleSheet("""
            font-size: 12px;
            color: #9ca3af;
        """)
        build_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_info_layout.addWidget(build_info_label)

        content_layout.addWidget(version_info_frame)

        # Creator Attribution
        creator_frame = QFrame()
        creator_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 2px solid #007bff;
                border-radius: 10px;
                padding: 20px;
                margin: 10px 0;
            }
        """)
        creator_layout = QVBoxLayout(creator_frame)

        creator_title = QLabel("Created By")
        creator_title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #007bff;
            margin-bottom: 10px;
        """)
        creator_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        creator_layout.addWidget(creator_title)

        creator_name = QLabel("Aleksander Celewicz")
        creator_name.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 15px;
        """)
        creator_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        creator_layout.addWidget(creator_name)

        content_layout.addWidget(creator_frame)

        # Social Media & Links Section
        social_frame = QFrame()
        social_frame.setStyleSheet("""
            QFrame {
                background-color: #fff3cd;
                border: 2px solid #ffc107;
                border-radius: 10px;
                padding: 20px;
                margin: 10px 0;
            }
        """)
        social_layout = QVBoxLayout(social_frame)

        social_title = QLabel("📺 Follow for Tutorials & Updates")
        social_title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #856404;
            margin-bottom: 15px;
        """)
        social_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        social_layout.addWidget(social_title)

        # YouTube Channel Link
        youtube_button = QPushButton("🎥 AIex The AI Workbench - YouTube Channel")
        youtube_button.setStyleSheet("""
            QPushButton {
                background-color: #ff0000;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: bold;
                margin: 5px 0;
            }
            QPushButton:hover {
                background-color: #cc0000;
            }
            QPushButton:pressed {
                background-color: #990000;
            }
        """)
        youtube_button.clicked.connect(lambda: self._open_youtube_channel())
        social_layout.addWidget(youtube_button)

        # Website Link
        website_button = QPushButton("🌐 Visit MAIAChat.com")
        website_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: bold;
                margin: 5px 0;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
        """)
        website_button.clicked.connect(lambda: self._open_website())
        social_layout.addWidget(website_button)

        # GitHub Link
        github_button = QPushButton("💻 View Source Code on GitHub")
        github_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: bold;
                margin: 5px 0;
            }
            QPushButton:hover {
                background-color: #1e7e34;
            }
            QPushButton:pressed {
                background-color: #155724;
            }
        """)
        github_button.clicked.connect(lambda: self._open_github())
        social_layout.addWidget(github_button)

        # Social media description
        social_description = QLabel("""
        🎬 Subscribe to AIex The AI Workbench for:
        • MAIAChat tutorials and advanced usage tips
        • AI workflow demonstrations and best practices
        • Latest updates and feature announcements
        • Community discussions and Q&A sessions
        """)
        social_description.setStyleSheet("""
            font-size: 13px;
            color: #856404;
            line-height: 1.6;
            margin-top: 10px;
        """)
        social_description.setWordWrap(True)
        social_layout.addWidget(social_description)

        content_layout.addWidget(social_frame)

        # Description
        description = QLabel("""
        A powerful desktop application for multi-agent AI conversations with advanced RAG capabilities.
        Configure multiple AI agents with different personalities and capabilities to collaborate on
        complex tasks, research, and problem-solving. Features include knowledge base integration,
        conversation management, and support for 15+ AI providers.
        """)
        description.setStyleSheet("""
            font-size: 14px;
            color: #34495e;
            line-height: 1.6;
            margin: 15px 0;
        """)
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(description)

        # Key Features Section
        features_frame = QFrame()
        features_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 2px solid #6c757d;
                border-radius: 10px;
                padding: 20px;
                margin: 15px 0;
            }
        """)
        features_layout = QVBoxLayout(features_frame)

        features_title = QLabel("Key Features")
        features_title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #495057;
            margin-bottom: 10px;
        """)
        features_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        features_layout.addWidget(features_title)

        features_text = QLabel("""
        • Multi-Agent System: Up to 5 AI agents with different roles and capabilities
        • Advanced RAG: Knowledge base integration with FAISS vector search
        • 15+ AI Providers: OpenAI, Anthropic, Google, Ollama, OpenRouter, and more
        • Local Processing: All conversations and data stay on your machine
        • Cross-Platform: Windows, macOS, and Linux support
        • Real-time Streaming: Watch AI responses appear in real-time
        • Conversation Management: Save, load, and organize conversation sessions
        • Security First: Encrypted API key storage with no telemetry
        """)
        features_text.setStyleSheet("""
            font-size: 13px;
            color: #495057;
            line-height: 1.6;
        """)
        features_text.setWordWrap(True)
        features_layout.addWidget(features_text)

        content_layout.addWidget(features_frame)

        # System Information Section
        system_frame = QFrame()
        system_frame.setStyleSheet("""
            QFrame {
                background-color: #e3f2fd;
                border: 2px solid #2196f3;
                border-radius: 10px;
                padding: 20px;
                margin: 15px 0;
            }
        """)
        system_layout = QVBoxLayout(system_frame)

        system_title = QLabel("System Information")
        system_title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #1976d2;
            margin-bottom: 10px;
        """)
        system_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        system_layout.addWidget(system_title)

        # Get system information
        import platform
        import sys
        from PyQt6.QtCore import QT_VERSION_STR, PYQT_VERSION_STR

        system_info_text = f"""
        Operating System: {platform.system()} {platform.release()}
        Architecture: {platform.machine()}
        Python Version: {sys.version.split()[0]}
        PyQt6 Version: {PYQT_VERSION_STR}
        Qt Version: {QT_VERSION_STR}
        """

        system_info_label = QLabel(system_info_text)
        system_info_label.setStyleSheet("""
            font-size: 12px;
            color: #1976d2;
            font-family: 'Courier New', monospace;
            line-height: 1.4;
        """)
        system_info_label.setWordWrap(True)
        system_layout.addWidget(system_info_label)

        content_layout.addWidget(system_frame)

        # License Information
        license_frame = QFrame()
        license_frame.setStyleSheet("""
            QFrame {
                background-color: #e8f5e8;
                border: 2px solid #28a745;
                border-radius: 10px;
                padding: 20px;
                margin: 15px 0;
            }
        """)
        license_layout = QVBoxLayout(license_frame)

        license_title = QLabel("License & Usage")
        license_title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #28a745;
            margin-bottom: 10px;
        """)
        license_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        license_layout.addWidget(license_title)

        license_text = QLabel("""
        This software is released under the MIT License.

        • FREE for personal use
        • FREE for educational use
        • FREE for non-commercial use

        For COMMERCIAL use, proper attribution is required:
        "Powered by MAIAChat.com Desktop by Aleksander Celewicz"

        For commercial licensing without attribution requirements,
        please contact the creator.
        """)
        license_text.setStyleSheet("""
            font-size: 13px;
            color: #2c3e50;
            line-height: 1.5;
        """)
        license_text.setWordWrap(True)
        license_layout.addWidget(license_text)

        content_layout.addWidget(license_frame)

        # Contact Information
        contact_frame = QFrame()
        contact_frame.setStyleSheet("""
            QFrame {
                background-color: #fff3cd;
                border: 2px solid #ffc107;
                border-radius: 10px;
                padding: 20px;
                margin: 15px 0;
            }
        """)
        contact_layout = QVBoxLayout(contact_frame)

        contact_title = QLabel("Commercial Licensing & Contact")
        contact_title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #856404;
            margin-bottom: 10px;
        """)
        contact_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        contact_layout.addWidget(contact_title)

        contact_text = QLabel("""
        For commercial use without attribution requirements or
        for custom development and licensing inquiries,
        please contact Aleksander Celewicz.

        This ensures you get the proper licensing for your business needs
        while supporting continued development of this software.
        """)
        contact_text.setStyleSheet("""
            font-size: 13px;
            color: #856404;
            line-height: 1.5;
        """)
        contact_text.setWordWrap(True)
        contact_layout.addWidget(contact_text)

        content_layout.addWidget(contact_frame)

        # Contact & Support Information
        support_frame = QFrame()
        support_frame.setStyleSheet("""
            QFrame {
                background-color: #f3e5f5;
                border: 2px solid #9c27b0;
                border-radius: 10px;
                padding: 20px;
                margin: 15px 0;
            }
        """)
        support_layout = QVBoxLayout(support_frame)

        support_title = QLabel("Contact & Support")
        support_title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #7b1fa2;
            margin-bottom: 10px;
        """)
        support_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        support_layout.addWidget(support_title)

        support_text = QLabel("""
        🌐 Website: MAIAChat.com
        📧 Email: Contact through MAIAChat.com
        📚 Documentation: README.md, SETUP.md, SECURITY.md
        🐛 Bug Reports: GitHub Issues
        💬 Community: GitHub Discussions
        🔒 Security Issues: See SECURITY.md for reporting
        📋 Changelog: CHANGELOG.md for version history
        🤝 Contributing: CONTRIBUTING.md for guidelines
        """)
        support_text.setStyleSheet("""
            font-size: 13px;
            color: #7b1fa2;
            line-height: 1.6;
        """)
        support_text.setWordWrap(True)
        support_layout.addWidget(support_text)

        content_layout.addWidget(support_frame)

        # Quick Actions Section
        actions_frame = QFrame()
        actions_frame.setStyleSheet("""
            QFrame {
                background-color: #fff3e0;
                border: 2px solid #ff9800;
                border-radius: 10px;
                padding: 20px;
                margin: 15px 0;
            }
        """)
        actions_layout = QVBoxLayout(actions_frame)

        actions_title = QLabel("Quick Actions")
        actions_title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #f57c00;
            margin-bottom: 15px;
        """)
        actions_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        actions_layout.addWidget(actions_title)

        # Create buttons for quick actions

        buttons_layout = QHBoxLayout()

        # View Changelog Button
        changelog_btn = QPushButton("📋 View Changelog")
        changelog_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #f57c00;
            }
        """)
        changelog_btn.clicked.connect(lambda: self._open_file_in_default_app("CHANGELOG.md"))
        buttons_layout.addWidget(changelog_btn)

        # View Documentation Button
        docs_btn = QPushButton("📚 Documentation")
        docs_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
        """)
        docs_btn.clicked.connect(lambda: self._open_file_in_default_app("README.md"))
        buttons_layout.addWidget(docs_btn)

        # Visit Website Button
        website_btn = QPushButton("🌐 Visit Website")
        website_btn.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #388e3c;
            }
        """)
        website_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://MAIAChat.com")))
        buttons_layout.addWidget(website_btn)

        actions_layout.addLayout(buttons_layout)
        content_layout.addWidget(actions_frame)

        # Add stretch to push content to top
        content_layout.addStretch()

        # Set up scroll area
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)

        # Add the About tab
        self.main_window.tab_widget.addTab(about_tab, "About")

    def _open_file_in_default_app(self, filename: str) -> None:
        """Open a file in the default application (e.g., text editor, browser)."""
        try:
            from PyQt6.QtCore import QUrl
            from PyQt6.QtGui import QDesktopServices
            import os

            file_path = os.path.abspath(filename)
            if os.path.exists(file_path):
                QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
            else:
                # Show a message if file doesn't exist
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(
                    self.main_window,
                    "File Not Found",
                    f"The file '{filename}' was not found in the application directory.\n\n"
                    f"Please check the project repository for the latest documentation."
                )
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self.main_window,
                "Error Opening File",
                f"Could not open '{filename}':\n{str(e)}"
            )

    def _create_api_settings_tab(self) -> QWidget:
        """Creates the API Settings tab for managing API keys."""
        # Create content widget and layout using helper
        content_widget, layout = self._create_content_widget_with_layout()
        
        # Add header and description using helpers  
        layout.addWidget(self._create_section_header("API Key Management"))
        layout.addWidget(self._create_description_label(
            "Configure your API keys for various AI services. These keys are required to connect to external AI providers.",
            "#007bff"
        ))
        
        # Load API key definitions from the manager
        api_key_manager.load_definitions()
        categories = api_key_manager.get_definitions_by_category()
        self.main_window.api_inputs = {}
        
        # Create a section for each category
        for category, definitions in categories.items():
            # Category header using helper
            layout.addWidget(self._create_category_header(category))
            
            # Create input fields for each API key in this category
            for definition in definitions:
                # Create password field with toggle using helper
                key_layout, input_field = self._create_password_field_with_toggle(
                    definition.name, 
                    f"Enter {definition.name}",
                    tooltip=definition.description
                )
                
                # Add URL button if available
                if definition.url:
                    url_btn = self._create_button_with_url(
                        "Get Key", 
                        definition.url, 
                        "success", 
                        f"Visit {definition.url} to get your API key"
                    )
                    key_layout.insertWidget(key_layout.count() - 1, url_btn)  # Insert before stretch
                
                # Load existing value
                current_value = self.main_window.config_manager.get_api_key(definition.id)
                if current_value:
                    input_field.setText(current_value)
                
                # Store input field for later access
                self.main_window.api_inputs[definition.id] = input_field
                layout.addLayout(key_layout)
        
        # Add API Key Provider Button
        add_provider_btn = self._create_styled_button("Add Custom API Provider", "info")
        # TODO: Connect to a function that shows a dialog to add a new API provider
        
        # Save Button
        save_button = self._create_styled_button("Save API Keys", "primary")
        save_button.clicked.connect(self.main_window.save_api_keys)
        
        # Button container using helper
        button_container = self._create_input_row_layout([add_provider_btn], stretch_at_end=True)
        button_container.addWidget(save_button)
        layout.addLayout(button_container)
        
        layout.addStretch()
        
        # Return the tab with scroll area using helper
        return self._create_tab_with_scroll(content_widget)

    def _create_rag_settings_tab(self) -> QWidget:
        """Creates the RAG Settings tab."""
        # Create content widget and layout using helper
        content_widget, layout = self._create_content_widget_with_layout()
        
        # Add header and description using helpers
        layout.addWidget(self._create_section_header("RAG (Retrieval-Augmented Generation) Settings"))
        layout.addWidget(self._create_description_label(
            "Configure RAG quality settings to control how detailed and comprehensive your RAG responses will be. "
            "These settings affect the number of results retrieved, filtering criteria, and context limits.",
            "#28a745"
        ))
        
        # RAG Settings Button
        rag_settings_btn = self._create_styled_button("Configure RAG Quality Settings", "success", "large")
        rag_settings_btn.setToolTip("Open RAG settings dialog to configure quality parameters")
        rag_settings_btn.clicked.connect(self.main_window.open_rag_settings)
        
        # Current RAG Status
        self.main_window.rag_status_label = QLabel("RAG Status: Loading...")
        self.main_window.rag_status_label.setStyleSheet(f"""
            color: {COLOR_MEDIUM_TEXT};
            font-size: 13px;
            font-style: italic;
            padding: 10px 15px;
            background-color: #e9ecef;
            border-radius: 6px;
        """)
        
        # Layout using helper
        rag_settings_layout = self._create_input_row_layout([rag_settings_btn], stretch_at_end=True)
        rag_settings_layout.addWidget(self.main_window.rag_status_label)
        
        layout.addLayout(rag_settings_layout)
        
        # Response Settings Section using helper
        layout.addWidget(self._create_section_header("Response Settings", 16, with_border=True))
        
        # Max Response Context Size
        max_context_label = QLabel("Maximum Response Context Size (tokens):")
        max_context_label.setFixedWidth(300)
        max_context_label.setToolTip("Maximum number of tokens for response context. Higher values allow longer responses but use more memory.")
        max_context_label.setStyleSheet(f"""
            font-weight: bold;
            color: {COLOR_DARK_TEXT};
        """)
        
        # Create spinbox using helper
        max_context_input = self._create_numbered_spinbox(
            1000, 1000000, 1000, 
            self.main_window.config_manager.get_max_response_context()
        )
        
        self.main_window.max_context_input = max_context_input
        
        # Layout using helper
        max_context_layout = self._create_input_row_layout([max_context_label, max_context_input])
        layout.addLayout(max_context_layout)
        
        layout.addStretch()
        
        # Return the tab with scroll area using helper
        return self._create_tab_with_scroll(content_widget)

    def _create_general_settings_tab(self) -> QWidget:
        """Creates the General Settings tab."""
        # Create content widget and layout using helper
        content_widget, layout = self._create_content_widget_with_layout()
        
        # Add header and description using helpers
        layout.addWidget(self._create_section_header("General Settings"))
        layout.addWidget(self._create_description_label(
            "Configure API endpoint URLs and other general application settings. "
            "These settings control where the application connects to various AI services.",
            "#ffc107"
        ))
        
        # General Settings Button
        general_settings_btn = self._create_styled_button("Configure General Settings", "warning", "large")
        general_settings_btn.setToolTip("Open general settings dialog to configure API endpoints and other settings")
        general_settings_btn.clicked.connect(self.main_window.open_general_settings)
        
        # Layout using helper
        general_settings_layout = self._create_input_row_layout([general_settings_btn])
        layout.addLayout(general_settings_layout)
        
        layout.addStretch()
        
        # Return the tab with scroll area using helper
        return self._create_tab_with_scroll(content_widget)

    def _create_text_icon_tool_button(self, text: str, icon_name: str, tooltip: str) -> QToolButton:
        """
        Helper method to create a QToolButton with text beside an icon.

        Args:
            text: The text to display on the button.
            icon_name: The filename (without extension) of the icon in the ICON_DIR.
            tooltip: The tooltip text for the button.

        Returns:
            The configured QToolButton.
        """
        btn = QToolButton()
        icon_path = ICON_DIR / f"{icon_name}.svg"
        if icon_path.exists():
            btn.setIcon(QIcon(str(icon_path)))
        else:
            print(f"Warning: Icon not found at {icon_path}")
            # Optionally set a placeholder icon or text indicator
        btn.setText(text)
        btn.setToolTip(tooltip)
        btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        btn.setIconSize(QSize(16, 16)) # Small icons
        btn.setStyleSheet(TOOL_BUTTON_STYLE)
        return btn

    def _create_icon_tool_button(self, icon_name: str, tooltip: str, size: int = 24) -> QToolButton:
        """
        Helper method to create an icon-only QToolButton.

        Args:
            icon_name: The filename (without extension) of the icon in the ICON_DIR.
            tooltip: The tooltip text for the button.
            size: The size (width and height) for the icon.

        Returns:
            The configured QToolButton.
        """
        button = QToolButton()
        icon_path = ICON_DIR / f"{icon_name}.svg"
        if icon_path.exists():
             button.setIcon(QIcon(str(icon_path)))
        else:
             print(f"Warning: Icon not found at {icon_path}")
        button.setToolTip(tooltip)
        button.setIconSize(QSize(size, size))
        button.setStyleSheet(TOOL_BUTTON_STYLE) # Apply consistent tool button style
        # button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly) # Explicitly icon only
        return button

    # ========================================
    # STAGE 4: UI CREATION HELPER METHODS
    # ========================================
    
    def _create_tab_with_scroll(self, content_widget: QWidget) -> QWidget:
        """Create a tab widget with a scroll area containing the given content widget."""
        tab = QWidget()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")
        scroll_area.setWidget(content_widget)
        
        tab_layout = QVBoxLayout(tab)
        tab_layout.addWidget(scroll_area)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        
        return tab
    
    def _create_content_widget_with_layout(self, margins=(20, 20, 20, 20), spacing=15) -> tuple[QWidget, QVBoxLayout]:
        """Create a content widget with a properly configured VBoxLayout."""
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(*margins)
        layout.setSpacing(spacing)
        return content_widget, layout
    
    def _create_section_header(self, title: str, font_size=18, with_border=True) -> QLabel:
        """Create a styled section header label."""
        header_label = QLabel(title)
        border_style = f"border-bottom: 2px solid {COLOR_BORDER}; margin-bottom: 20px;" if with_border else ""
        header_label.setStyleSheet(f"""
            font-size: {font_size}px;
            font-weight: bold;
            color: {COLOR_DARK_TEXT};
            padding-bottom: 10px;
            {border_style}
        """)
        return header_label
    
    def _create_description_label(self, text: str, accent_color="#007bff") -> QLabel:
        """Create a styled description label with accent border."""
        description = QLabel(text)
        description.setWordWrap(True)
        description.setStyleSheet(f"""
            color: {COLOR_MEDIUM_TEXT};
            font-size: 14px;
            margin-bottom: 20px;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid {accent_color};
        """)
        return description
    
    def _create_category_header(self, title: str) -> QLabel:
        """Create a styled category header label."""
        category_label = QLabel(title)
        category_label.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {COLOR_DARK_TEXT};
            margin-top: 25px;
            margin-bottom: 15px;
            padding: 10px 15px;
            background-color: #e9ecef;
            border-radius: 6px;
        """)
        return category_label
    
    def _create_labeled_input_field(self, label_text: str, placeholder: str, 
                                   password=False, width=None, tooltip=None) -> tuple[QLabel, QLineEdit]:
        """Create a labeled input field with consistent styling."""
        
        # Create label
        label = QLabel(f"{label_text}:")
        label.setFixedWidth(200)
        label.setStyleSheet(f"""
            font-weight: bold;
            color: {COLOR_DARK_TEXT};
        """)
        if tooltip:
            label.setToolTip(tooltip)
        
        # Create input field
        input_field = QLineEdit()
        input_field.setFixedHeight(40)
        input_field.setPlaceholderText(placeholder)
        if password:
            input_field.setEchoMode(QLineEdit.EchoMode.Password)
        if width:
            input_field.setFixedWidth(width)
        
        input_field.setStyleSheet("""
            QLineEdit {
                border: 2px solid #dee2e6;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #007bff;
                outline: none;
            }
        """)
        
        return label, input_field
    
    def _create_styled_button(self, text: str, color_scheme="primary", size="normal") -> QPushButton:
        """Create a styled button with predefined color schemes and sizes."""
        button = QPushButton(text)
        
        # Size configurations
        if size == "large":
            padding = "15px 25px"
            font_size = "14px"
        elif size == "small":
            padding = "8px 12px"
            font_size = "12px"
        else:  # normal
            padding = "12px 20px"
            font_size = "13px"
        
        # Color scheme configurations
        color_schemes = {
            "primary": {
                "bg": "#007bff",
                "hover": "#0056b3",
                "color": "white"
            },
            "success": {
                "bg": "#28a745",
                "hover": "#218838",
                "color": "white"
            },
            "warning": {
                "bg": "#ffc107",
                "hover": "#e0a800",
                "color": "#212529"
            },
            "info": {
                "bg": "#17a2b8",
                "hover": "#138496",
                "color": "white"
            },
            "secondary": {
                "bg": "#6c757d",
                "hover": "#5a6268",
                "color": "white"
            },
            "danger": {
                "bg": "#dc3545",
                "hover": "#c82333",
                "color": "white"
            }
        }
        
        scheme = color_schemes.get(color_scheme, color_schemes["primary"])
        
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {scheme["bg"]};
                color: {scheme["color"]};
                border: none;
                border-radius: 6px;
                padding: {padding};
                font-weight: bold;
                font-size: {font_size};
            }}
            QPushButton:hover {{
                background-color: {scheme["hover"]};
            }}
        """)
        
        return button
    
    def _create_toggle_button(self, text_show="Show", text_hide="Hide", width=70) -> QPushButton:
        """Create a styled toggle button for show/hide functionality."""
        toggle_btn = QPushButton(text_show)
        toggle_btn.setFixedWidth(width)
        toggle_btn.setFixedHeight(40)
        toggle_btn.setCheckable(True)
        toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:checked {
                background-color: #dc3545;
            }
        """)
        
        # Store the texts for toggling
        toggle_btn.text_show = text_show
        toggle_btn.text_hide = text_hide
        
        return toggle_btn
    
    def _create_input_row_layout(self, components: list, stretch_at_end=True) -> QHBoxLayout:
        """Create a horizontal layout with the given components and optional stretch at the end."""
        layout = QHBoxLayout()
        layout.setSpacing(10)
        
        for component in components:
            layout.addWidget(component)
        
        if stretch_at_end:
            layout.addStretch()
        
        return layout
    
    def _create_numbered_spinbox(self, min_val: int, max_val: int, step: int, 
                                current_val: int, width=150, height=40) -> QSpinBox:
        """Create a styled spinbox with consistent appearance."""
        
        spinbox = QSpinBox()
        spinbox.setRange(min_val, max_val)
        spinbox.setSingleStep(step)
        spinbox.setValue(current_val)
        spinbox.setFixedHeight(height)
        spinbox.setFixedWidth(width)
        spinbox.setStyleSheet("""
            QSpinBox {
                border: 2px solid #dee2e6;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
                background-color: white;
            }
            QSpinBox:focus {
                border-color: #007bff;
            }
        """)
        
        return spinbox
    
    def _create_password_field_with_toggle(self, label_text: str, placeholder: str, 
                                         tooltip=None) -> tuple[QHBoxLayout, QLineEdit]:
        """Create a password field with a show/hide toggle button."""
        label, input_field = self._create_labeled_input_field(
            label_text, placeholder, password=True, tooltip=tooltip
        )
        toggle_btn = self._create_toggle_button()
        
        # Connect toggle functionality
        def toggle_visibility():
            if toggle_btn.isChecked():
                input_field.setEchoMode(input_field.EchoMode.Normal)
                toggle_btn.setText(toggle_btn.text_hide)
            else:
                input_field.setEchoMode(input_field.EchoMode.Password)
                toggle_btn.setText(toggle_btn.text_show)
        
        toggle_btn.clicked.connect(toggle_visibility)
        
        # Create the row layout
        row_layout = self._create_input_row_layout([label, input_field, toggle_btn])
        
        return row_layout, input_field
    
    def _create_button_with_url(self, text: str, url: str, color_scheme="success", 
                               tooltip=None, width=80) -> QPushButton:
        """Create a button that opens a URL when clicked."""
        button = self._create_styled_button(text, color_scheme, "normal")
        button.setFixedWidth(width)
        button.setFixedHeight(40)
        
        if tooltip:
            button.setToolTip(tooltip)
        
        def open_url():
            import webbrowser
            webbrowser.open(url)
        
        button.clicked.connect(open_url)
        return button

    def _open_youtube_channel(self) -> None:
        """Open the YouTube channel in the default browser."""
        try:
            from version import YOUTUBE_CHANNEL
            url = YOUTUBE_CHANNEL
        except ImportError:
            url = "https://www.youtube.com/@AIexTheAIWorkbench"

        QDesktopServices.openUrl(QUrl(url))

    def _open_website(self) -> None:
        """Open the MAIAChat website in the default browser."""
        try:
            from version import WEBSITE_URL
            url = WEBSITE_URL
        except ImportError:
            url = "https://maiachat.com"

        QDesktopServices.openUrl(QUrl(url))

    def _open_github(self) -> None:
        """Open the GitHub repository in the default browser."""
        try:
            from version import GITHUB_URL
            url = GITHUB_URL
        except ImportError:
            url = "https://github.com/AleksanderCelewicz/MAIAChat-Desktop"

        QDesktopServices.openUrl(QUrl(url))