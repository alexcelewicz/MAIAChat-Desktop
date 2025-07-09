from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                            QLineEdit, QCheckBox, QPushButton, QListWidget,
                            QListWidgetItem, QFormLayout, QDialogButtonBox,
                            QTabWidget, QWidget, QTextEdit, QMessageBox,
                            QComboBox, QGroupBox, QTableWidget, QTableWidgetItem,
                            QHeaderView, QSizePolicy, QAbstractItemView,
                            QStyle, QStyleOptionButton, QApplication, QToolButton,
                            QFileDialog, QStyledItemDelegate, QTreeWidget, QTreeWidgetItem)
from PyQt6.QtCore import Qt, QSize, QRect, pyqtSignal
from PyQt6.QtGui import QIcon, QAction
from mcp_client import MCPServer, mcp_client # Import the improved client
from mcp_file_operations import MCPFileOperations
from typing import Optional, Dict, Any, List
import logging
import sys # Import sys to run the example
import traceback # Import traceback for error handling
import os
import platform
import json
from config import config_manager

# Set up logging for dialogs
logger = logging.getLogger("MCP Dialogs")

class CheckBoxDelegate(QStyledItemDelegate):
    """Custom delegate for rendering checkboxes in table cells."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def createEditor(self, parent, option, index):
        """Create a checkbox editor."""
        editor = QCheckBox(parent)
        editor.setStyleSheet("QCheckBox { margin-left: 50%; margin-right: 50%; }")
        return editor
    
    def setEditorData(self, editor, index):
        """Set the checkbox state based on model data."""
        value = index.model().data(index, Qt.ItemDataRole.EditRole)
        editor.setChecked(bool(value))
    
    def setModelData(self, editor, model, index):
        """Update model data from checkbox state."""
        model.setData(index, editor.isChecked(), Qt.ItemDataRole.EditRole)
    
    def paint(self, painter, option, index):
        """Paint the checkbox in the cell."""
        # Clear the cell background first
        painter.fillRect(option.rect, option.palette.base())
        
        # Use the style to draw a checkbox indicator
        checkbox_option = QStyleOptionButton()
        checkbox_option.state = QStyle.StateFlag.State_Enabled
        
        # Set checked state based on data
        if bool(index.data()):
            checkbox_option.state |= QStyle.StateFlag.State_On
        else:
            checkbox_option.state |= QStyle.StateFlag.State_Off
        
        # Handle selection highlighting
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        
        # Get checkbox size from style
        style = QApplication.style()
        checkbox_size = style.pixelMetric(QStyle.PixelMetric.PM_IndicatorWidth)
        
        # Center the checkbox in the cell
        checkbox_rect = QRect(
            option.rect.x() + (option.rect.width() - checkbox_size) // 2,
            option.rect.y() + (option.rect.height() - checkbox_size) // 2,
            checkbox_size,
            checkbox_size
        )
        checkbox_option.rect = checkbox_rect
        
        # Draw just the checkbox indicator (not the full checkbox with text)
        style.drawPrimitive(
            QStyle.PrimitiveElement.PE_IndicatorCheckBox, checkbox_option, painter
        )
    
    def editorEvent(self, event, model, option, index):
        """Handle checkbox click events."""
        if event.type() == event.Type.MouseButtonRelease:
            current_value = bool(index.data())
            model.setData(index, not current_value, Qt.ItemDataRole.EditRole)
            return True
        return super().editorEvent(event, model, option, index)

# --- Basic Stylesheet for Improved Look ---
# You can expand this stylesheet significantly for more customization
STYLESHEET = """
QDialog {
    background-color: #f0f0f0;
}
QGroupBox {
    border: 1px solid #d0d0d0;
    border-radius: 5px;
    margin-top: 10px;
    padding-top: 15px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 3px;
    left: 10px;
    color: #505050;
    font-weight: bold;
}
QLabel {
    color: #333;
}
QLineEdit, QTextEdit, QComboBox {
    padding: 5px;
    border: 1px solid #ccc;
    border-radius: 3px;
    background-color: #fff;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border-color: #0078d7;
    box-shadow: 0 0 5px rgba(0, 120, 215, 0.3);
}
QPushButton {
    padding: 8px 15px;
    border: 1px solid #0078d7;
    border-radius: 3px;
    background-color: #0078d7;
    color: white;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #005a9e;
    border-color: #005a9e;
}
QPushButton:pressed {
    background-color: #003f6a;
}
QPushButton:disabled {
    background-color: #cccccc;
    border-color: #cccccc;
    color: #666666;
}
QDialogButtonBox QPushButton {
    min-width: 80px;
}
QTabWidget::pane {
    border: 1px solid #d0d0d0;
    background-color: #ffffff;
}
QTabWidget::tab-bar {
    left: 5px; /* move to the right */
}
QTabBar::tab {
    background: #e0e0e0;
    border: 1px solid #d0d0d0;
    border-bottom-color: #d0d0d0; /* same as pane border */
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    padding: 8px 15px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background: #ffffff;
    border-bottom-color: #ffffff; /* make the selected tab look connected to the pane */
}
QTabBar::tab:hover {
    background: #f0f0f0;
}
QTableWidget {
    selection-background-color: #b0d8ff;
    selection-color: #333;
    border: 1px solid #d0d0d0;
    gridline-color: #e0e0e0;
}
QTableWidget::item {
    padding: 5px;
}
QTableWidget::item:selected {
    background-color: #b0d8ff;
    color: #333;
}
QHeaderView::section {
    background-color: #e8e8e8;
    padding: 5px;
    border: 1px solid #d0d0d0;
    border-bottom: 2px solid #0078d7;
    font-weight: bold;
}
QListWidget {
    selection-background-color: #b0d8ff;
    selection-color: #333;
    border: 1px solid #d0d0d0;
}
QListWidget::item {
    padding: 5px;
}
QListWidget::item:selected {
    background-color: #b0d8ff;
    color: #333;
}
QTextEdit[readOnly="true"] {
    background-color: #e8e8e8;
    border: 1px solid #d0d0d0;
}
"""


class MCPServerDialog(QDialog):
    """Dialog for adding or editing an MCP server."""

    def __init__(self, server: Optional[MCPServer] = None, parent=None):
        """Initialize the dialog.

        Args:
            server: The server to edit, or None to add a new server
            parent: The parent widget
        """
        super().__init__(parent)
        self.server = server
        self.discovered_capabilities: List[str] = [] # Store capabilities discovered during test
        self.initUI()
        self.apply_stylesheet()

    def apply_stylesheet(self):
        """Apply the defined stylesheet to the dialog."""
        self.setStyleSheet(STYLESHEET)

    def initUI(self):
        """Initialize the user interface."""
        self.setWindowTitle("Configure MCP Server")
        self.setMinimumWidth(450)
        self.setMinimumHeight(400) # Give a bit more space

        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Server Details Group Box
        details_group = QGroupBox("Server Details")
        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # Name field
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., My Awesome Search API")
        if self.server:
            self.name_edit.setText(self.server.name)
            self.name_edit.setEnabled(False) # Prevent changing name of existing server
        form_layout.addRow("Name:", self.name_edit)

        # URL field
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("e.g., https://api.example.com/mcp/v1")
        if self.server:
            self.url_edit.setText(self.server.url)
        form_layout.addRow("URL:", self.url_edit)

        # Description field
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Provide a brief description of the server's purpose.")
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setTabChangesFocus(True) # Allow Tab to move to the next widget
        if self.server:
            self.description_edit.setText(self.server.description)
        form_layout.addRow("Description:", self.description_edit)

        # Auth token field with show/hide toggle
        self.auth_token_edit = QLineEdit()
        self.auth_token_edit.setPlaceholderText("Enter API Key or Token if required")
        self.auth_token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        if self.server:
            self.auth_token_edit.setText(self.server.auth_token)

        self.password_toggle_button = QToolButton()
        self.password_toggle_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCloseButton)) # Placeholder icon
        self.password_toggle_button.setStyleSheet("border: none; padding: 0px;") # Make it look like part of the line edit
        self.password_toggle_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.password_toggle_button.clicked.connect(self.toggle_password_visibility)
        self.update_password_toggle_icon() # Set initial icon

        auth_layout = QHBoxLayout()
        auth_layout.addWidget(self.auth_token_edit)
        auth_layout.addWidget(self.password_toggle_button)
        auth_layout.setContentsMargins(0, 0, 0, 0)
        auth_layout.setSpacing(0)

        form_layout.addRow("Auth Token:", auth_layout)


        # Custom Search Engine ID field (for Google Search)
        self.cx_edit = QLineEdit()
        self.cx_edit.setPlaceholderText("Required for Google Search API (Optional for others)")
        if self.server:
            self.cx_edit.setText(getattr(self.server, 'cx', ''))
        form_layout.addRow("Custom Search Engine ID (cx):", self.cx_edit)
        self.cx_edit.setToolTip("Required for Google Search API. Find it in your Google Custom Search Engine settings.")

        # Enabled checkbox
        self.enabled_checkbox = QCheckBox("Enabled")
        if self.server:
            self.enabled_checkbox.setChecked(self.server.enabled)
        else:
            self.enabled_checkbox.setChecked(True) # Default to enabled for new servers
        form_layout.addRow("", self.enabled_checkbox)

        details_group.setLayout(form_layout)
        layout.addWidget(details_group)

        # Test Connection & Capabilities Group Box
        test_group = QGroupBox("Test Connection")
        test_layout = QVBoxLayout()

        test_button = QPushButton("Test Connection")
        test_button.clicked.connect(self.test_connection)
        test_layout.addWidget(test_button)

        self.capabilities_label = QLabel("Discovered Capabilities:")
        self.capabilities_display = QTextEdit()
        self.capabilities_display.setReadOnly(True)
        self.capabilities_display.setMaximumHeight(60)
        self.capabilities_display.setPlaceholderText("Run 'Test Connection' to see capabilities.")
        test_layout.addWidget(self.capabilities_label)
        test_layout.addWidget(self.capabilities_display)

        test_group.setLayout(test_layout)
        layout.addWidget(test_group)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addWidget(button_box)

        self.setLayout(layout)

        # If editing, populate capabilities display if server has them
        if self.server and self.server.capabilities:
             self.discovered_capabilities = self.server.capabilities
             self.update_capabilities_display()

    def toggle_password_visibility(self):
        """Toggle the visibility of the auth token field."""
        if self.auth_token_edit.echoMode() == QLineEdit.EchoMode.Password:
            self.auth_token_edit.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.auth_token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.update_password_toggle_icon()

    def update_password_toggle_icon(self):
        """Update the icon of the password toggle button."""
        if self.auth_token_edit.echoMode() == QLineEdit.EchoMode.Password:
            # Eye icon (or similar) for 'show password'
            self.password_toggle_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogYesButton)) # Using YesButton as a stand-in eye icon
            self.password_toggle_button.setToolTip("Show Auth Token")
        else:
            # Crossed-out eye icon (or similar) for 'hide password'
            self.password_toggle_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogNoButton)) # Using NoButton as a stand-in crossed-out eye icon
            self.password_toggle_button.setToolTip("Hide Auth Token")

    def update_capabilities_display(self):
        """Update the capabilities display QTextEdit."""
        if self.discovered_capabilities:
            self.capabilities_display.setText(", ".join(self.discovered_capabilities))
            self.capabilities_display.setStyleSheet("") # Clear placeholder style if any
        else:
            self.capabilities_display.setText("No capabilities discovered.")
            self.capabilities_display.setStyleSheet("color: gray;") # Indicate no capabilities

    def test_connection(self):
        """Test the connection to the MCP server."""
        url = self.url_edit.text().strip()
        name = self.name_edit.text().strip()
        auth_token = self.auth_token_edit.text().strip()
        cx = self.cx_edit.text().strip()

        if not url:
            QMessageBox.warning(self, "Input Error", "Please enter a URL.")
            return
        if not name:
             # Use a default name for testing if none is provided
             name = "Temporary Test Server"

        # Create a temporary server object for testing
        temp_server = MCPServer(
            name=name,
            url=url,
            auth_token=auth_token,
            cx=cx,
            description="Temporary server for connection test"
        )

        # Set up logging handler to capture logs for the test
        log_capture = []
        class LogHandler(logging.Handler):
            def emit(self, record):
                # Capture messages from the MCP Client logger
                if record.name == "MCP Client":
                    log_capture.append(self.format(record))

        temp_handler = LogHandler()
        temp_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        logger_mcp_client = logging.getLogger("MCP Client")
        logger_mcp_client.addHandler(temp_handler)

        self.capabilities_display.setText("Testing connection...")
        self.capabilities_display.setStyleSheet("color: orange;")
        QApplication.processEvents() # Update UI

        try:
            # Discover capabilities using the client method
            discovered_caps = mcp_client.discover_capabilities(temp_server)
            self.discovered_capabilities = discovered_caps # Store for saving

            if discovered_caps:
                self.update_capabilities_display()
                QMessageBox.information(
                    self,
                    "Connection Successful",
                    f"Successfully connected to MCP server '{name}'.\n\nDiscovered Capabilities: {', '.join(discovered_caps) or 'None'}"
                )
            else:
                self.capabilities_display.setText("Connection failed or no capabilities discovered.")
                self.capabilities_display.setStyleSheet("color: red;")

                # Prepare detailed error message from captured logs
                error_details = "\n".join(log_capture[-5:]) if log_capture else "No specific error details available."

                # Provide specific guidance based on the URL/Server Name
                guidance = ""
                url_lower = url.lower()
                name_lower = name.lower()

                if "google" in url_lower or "google search" in name_lower:
                    guidance = "\n\nFor Google Custom Search API:\n- Make sure your API key is correct.\n- You MUST provide a Custom Search Engine ID (cx) in the field above.\n- You can find your cx in the Google Custom Search Engine control panel."
                elif "github" in url_lower or "github" in name_lower:
                    guidance = "\n\nFor GitHub API:\n- Make sure your Personal Access Token is correct and has the necessary permissions (e.g., read:user, read:org, read:repo)."
                elif "serper.dev" in url_lower or "serper search" in name_lower:
                    guidance = "\n\nFor Serper.dev API:\n- Make sure your API key is correct and active."
                elif "context7" in url_lower or "context7" in name_lower:
                    guidance = "\n\nFor Context7 API:\n- Make sure your API token is correct."
                elif "unsplash" in url_lower or "unsplash" in name_lower:
                     guidance = "\n\nFor Unsplash API:\n- Make sure your API key is correct."
                elif "slack" in url_lower or "slack" in name_lower:
                     guidance = "\n\nFor Slack API:\n- Make sure your API token is correct and has the necessary scopes."
                elif "brave.com" in url_lower or "brave search" in name_lower:
                     guidance = "\n\nFor Brave Search API:\n- Make sure your Subscription Token is correct."


                QMessageBox.warning(
                    self,
                    "Connection Failed",
                    f"Failed to connect or discover capabilities for '{name}'. Please check the URL and auth token.{guidance}\n\nRecent Logs:\n{error_details}"
                )

        except Exception as e:
             logger.error(f"An unexpected error occurred during test connection: {e}")
             logger.error(traceback.format_exc())
             self.capabilities_display.setText(f"Error during test: {e}")
             self.capabilities_display.setStyleSheet("color: red;")
             QMessageBox.critical(self, "Test Error", f"An unexpected error occurred during the connection test: {e}")

        finally:
            # Remove the temporary handler
            logger_mcp_client.removeHandler(temp_handler)


    def accept(self):
        """Save the server configuration and close the dialog."""
        name = self.name_edit.text().strip()
        url = self.url_edit.text().strip()
        description = self.description_edit.toPlainText().strip()
        auth_token = self.auth_token_edit.text().strip()
        cx = self.cx_edit.text().strip()
        enabled = self.enabled_checkbox.isChecked()

        if not name:
            QMessageBox.warning(self, "Input Error", "Please enter a server name.")
            return

        if not url:
            QMessageBox.warning(self, "Input Error", "Please enter a server URL.")
            return

        # Create or update the server object
        server = MCPServer(
            name=name,
            url=url,
            description=description,
            enabled=enabled,
            auth_token=auth_token,
            cx=cx
        )

        # If capabilities were discovered during the test, save them.
        # Otherwise, if editing, keep the existing capabilities.
        if self.discovered_capabilities:
            server.capabilities = self.discovered_capabilities
        elif self.server and self.server.capabilities:
             server.capabilities = self.server.capabilities
        else:
             # If no test was run and no existing capabilities, try a quick discovery?
             # Or just leave them empty and rely on later discovery?
             # Let's leave them empty unless tested or existing, to avoid blocking save.
             server.capabilities = []


        # Add/update the server using the client
        mcp_client.add_server(server)

        super().accept()


class MCPConfigDialog(QDialog):
    """Dialog for configuring MCP servers."""

    def __init__(self, parent=None):
        """Initialize the dialog.

        Args:
            parent: The parent widget
        """
        super().__init__(parent)
        self.initUI()
        self.apply_stylesheet()

    def apply_stylesheet(self):
        """Apply the defined stylesheet to the dialog."""
        self.setStyleSheet(STYLESHEET)

    def initUI(self):
        """Initialize the user interface."""
        self.setWindowTitle("MCP Server Configuration")
        self.setMinimumWidth(700) # Wider window
        self.setMinimumHeight(500) # Taller window

        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # General MCP Settings Group Box
        general_group = QGroupBox("General MCP Settings")
        general_layout = QFormLayout()
        
        # Double-pass mode checkbox
        self.double_pass_checkbox = QCheckBox("Enable Double-Pass Mode")
        self.double_pass_checkbox.setToolTip(
            "Double-pass mode processes MCP commands in two passes for higher accuracy.\n"
            "This improves reliability but may be slower. Recommended for better results."
        )
        # Load current setting from config
        current_single_pass = config_manager.get('MCP_SINGLE_PASS_MODE', True)
        self.double_pass_checkbox.setChecked(not current_single_pass)  # Invert since we're showing "double-pass"
        self.double_pass_checkbox.stateChanged.connect(self.on_double_pass_changed)
        
        general_layout.addRow("Processing Mode:", self.double_pass_checkbox)
        general_group.setLayout(general_layout)
        layout.addWidget(general_group)

        # Tab widget
        tab_widget = QTabWidget()

        # --- Configured Servers Tab ---
        configured_tab = QWidget()
        configured_layout = QVBoxLayout(configured_tab)
        configured_layout.setContentsMargins(10, 10, 10, 10)
        configured_layout.setSpacing(10)

        # Table of configured servers
        self.server_table = QTableWidget()
        self.server_table.setColumnCount(4)
        self.server_table.setHorizontalHeaderLabels(["Name", "URL", "Enabled", "Capabilities"])
        self.server_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) # Name
        self.server_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) # URL
        self.server_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents) # Enabled
        self.server_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch) # Capabilities
        self.server_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.server_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.server_table.setEditTriggers(QAbstractItemView.EditTrigger.CurrentChanged | QAbstractItemView.EditTrigger.SelectedClicked) # Allow checkbox editing
        self.server_table.verticalHeader().setVisible(False) # Hide row numbers
        
        # Set up checkbox delegate for Enabled column (column 2)
        self.checkbox_delegate = CheckBoxDelegate(self.server_table)
        self.server_table.setItemDelegateForColumn(2, self.checkbox_delegate)

        self.refresh_server_list() # Populate the table
        configured_layout.addWidget(self.server_table)
        
        # Connect table data changes to update server enabled status
        self.server_table.itemChanged.connect(self.on_server_enabled_changed)

        # Server Details Display
        self.configured_details_label = QLabel("Details:")
        self.configured_details_display = QTextEdit()
        self.configured_details_display.setReadOnly(True)
        self.configured_details_display.setMaximumHeight(100)
        self.configured_details_display.setPlaceholderText("Select a server above to see details.")
        self.configured_details_display.setStyleSheet("color: gray;")
        configured_layout.addWidget(self.configured_details_label)
        configured_layout.addWidget(self.configured_details_display)

        # Connect selection change to update details
        self.server_table.itemSelectionChanged.connect(self.update_configured_details)
        self.server_table.doubleClicked.connect(self.edit_server) # Double-click to edit

        # Buttons for configured servers
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        add_button = QPushButton(QIcon.fromTheme("list-add"), "Add") # Use theme icon
        add_button.clicked.connect(self.add_server)
        button_layout.addWidget(add_button)

        edit_button = QPushButton(QIcon.fromTheme("document-edit"), "Edit") # Use theme icon
        edit_button.clicked.connect(self.edit_server)
        button_layout.addWidget(edit_button)

        remove_button = QPushButton(QIcon.fromTheme("list-remove"), "Remove") # Use theme icon
        remove_button.clicked.connect(self.remove_server)
        button_layout.addWidget(remove_button)
        
        move_to_available_button = QPushButton(QIcon.fromTheme("go-next"), "Move to Available") # Use theme icon
        move_to_available_button.clicked.connect(self.move_to_available)
        button_layout.addWidget(move_to_available_button)

        button_layout.addStretch() # Push buttons to the left

        configured_layout.addLayout(button_layout)

        # --- Available Servers Tab ---
        available_tab = QWidget()
        available_layout = QVBoxLayout(available_tab)
        available_layout.setContentsMargins(10, 10, 10, 10)
        available_layout.setSpacing(10)

        available_description = QLabel(
            "Select from popular pre-configured MCP server types to add them to your list. "
            "You will need to configure the specific URL, API keys, etc., after adding."
        )
        available_description.setWordWrap(True)
        available_layout.addWidget(available_description)

        # List of available servers
        self.available_list = QListWidget()
        self.refresh_available_list()
        available_layout.addWidget(self.available_list)

        # Available Server Details Display
        self.available_details_label = QLabel("Details:")
        self.available_details_display = QTextEdit()
        self.available_details_display.setReadOnly(True)
        self.available_details_display.setMaximumHeight(100)
        self.available_details_display.setPlaceholderText("Select an available server above to see details.")
        self.available_details_display.setStyleSheet("color: gray;")
        available_layout.addWidget(self.available_details_label)
        available_layout.addWidget(self.available_details_display)

        # Connect selection change to update details
        self.available_list.itemSelectionChanged.connect(self.update_available_details)
        self.available_list.doubleClicked.connect(self.add_available_server) # Double-click to add

        # Buttons for available servers
        available_button_layout = QHBoxLayout()
        
        add_available_button = QPushButton(QIcon.fromTheme("list-add"), "Add Selected Server") # Use theme icon
        add_available_button.clicked.connect(self.add_available_server)
        available_button_layout.addWidget(add_available_button)
        
        move_to_configured_button = QPushButton(QIcon.fromTheme("go-previous"), "Move to Configured") # Use theme icon
        move_to_configured_button.clicked.connect(self.move_to_configured)
        available_button_layout.addWidget(move_to_configured_button)
        
        available_button_layout.addStretch() # Push buttons to the left
        available_layout.addLayout(available_button_layout)

        # --- Folder Permissions Tab ---
        permissions_tab = QWidget()
        permissions_layout = QVBoxLayout(permissions_tab)
        permissions_layout.setContentsMargins(10, 10, 10, 10)
        permissions_layout.setSpacing(10)

        permissions_description = QLabel(
            "Configure folder permissions for MCP file operations. Each folder can have specific permissions "
            "for different file operations. These permissions are used by filesystem-based MCP servers."
        )
        permissions_description.setWordWrap(True)
        permissions_layout.addWidget(permissions_description)

        # Initialize file operations handler
        self.file_ops = MCPFileOperations()

        # Create folder permissions table
        self.create_folder_permissions_table()
        permissions_layout.addWidget(self.permissions_table)

        # Buttons for folder permissions
        permissions_button_layout = QHBoxLayout()
        permissions_button_layout.setSpacing(10)

        add_folder_button = QPushButton(QIcon.fromTheme("folder-new"), "Add Folder")
        add_folder_button.clicked.connect(self.add_folder_permission)
        permissions_button_layout.addWidget(add_folder_button)

        remove_folder_button = QPushButton(QIcon.fromTheme("edit-delete"), "Remove Folder")
        remove_folder_button.clicked.connect(self.remove_folder_permission)
        permissions_button_layout.addWidget(remove_folder_button)

        permissions_button_layout.addStretch()
        permissions_layout.addLayout(permissions_button_layout)

        # Add tabs
        tab_widget.addTab(configured_tab, QIcon.fromTheme("preferences-system"), "Configured Servers") # Use theme icon
        tab_widget.addTab(available_tab, QIcon.fromTheme("network-server"), "Available Servers") # Use theme icon
        tab_widget.addTab(permissions_tab, QIcon.fromTheme("folder"), "Folder Permissions") # Use theme icon

        layout.addWidget(tab_widget)

        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def on_double_pass_changed(self, state):
        """Handle double-pass mode checkbox state change."""
        # Convert checkbox state to single-pass mode setting (inverted)
        # Use cross-platform compatible approach
        is_checked = (state == Qt.CheckState.Checked)
        single_pass_mode = not is_checked
        
        # Save to config
        config_manager.set('MCP_SINGLE_PASS_MODE', single_pass_mode, save=True)
        
        # Log the change
        mode_name = "Double-Pass" if not single_pass_mode else "Single-Pass"
        logger.info(f"MCP processing mode changed to: {mode_name}")

    def refresh_server_list(self):
        """Refresh the table of configured servers."""
        self.server_table.setRowCount(0) # Clear existing rows

        servers = sorted(mcp_client.servers.values(), key=lambda s: s.name.lower()) # Sort by name

        for row, server in enumerate(servers):
            self.server_table.insertRow(row)

            # Name Item
            name_item = QTableWidgetItem(server.name)
            name_item.setData(Qt.ItemDataRole.UserRole, server.name) # Store server name in data
            if not server.enabled:
                name_item.setForeground(Qt.GlobalColor.gray)
            self.server_table.setItem(row, 0, name_item)

            # URL Item
            url_item = QTableWidgetItem(server.url)
            if not server.enabled:
                url_item.setForeground(Qt.GlobalColor.gray)
            self.server_table.setItem(row, 1, url_item)

            # Enabled Item (using boolean for checkbox delegate)
            enabled_item = QTableWidgetItem()
            enabled_item.setData(Qt.ItemDataRole.EditRole, server.enabled)
            enabled_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.server_table.setItem(row, 2, enabled_item)

            # Capabilities Item
            capabilities_text = ", ".join(server.capabilities) if server.capabilities else "None Discovered"
            caps_item = QTableWidgetItem(capabilities_text)
            if not server.enabled:
                caps_item.setForeground(Qt.GlobalColor.gray)
            self.server_table.setItem(row, 3, caps_item)

        self.server_table.resizeColumnsToContents() # Adjust column widths after populating

    def on_server_enabled_changed(self, item):
        """Handle changes to server enabled status via checkbox."""
        if item.column() == 2:  # Only handle Enabled column changes
            row = item.row()
            server_name_item = self.server_table.item(row, 0)
            if server_name_item:
                server_name = server_name_item.data(Qt.ItemDataRole.UserRole)
                server = mcp_client.get_server(server_name)
                if server:
                    # Update server enabled status
                    new_enabled = bool(item.data(Qt.ItemDataRole.EditRole))
                    
                    # Check filesystem server permissions before enabling
                    if new_enabled and hasattr(server, 'server_type') and server.server_type == 'filesystem':
                        permitted_folders = [path for path, perms in self.file_ops.folder_permissions.items() 
                                           if any(perms.values())]
                        if not permitted_folders:
                            reply = QMessageBox.question(
                                self, "Filesystem Server Warning",
                                f"Filesystem server '{server_name}' is being enabled but no folder permissions are configured.\n\n"
                                "Without folder permissions, the server will not be able to access any files.\n\n"
                                "Do you want to enable it anyway? You can configure folder permissions in the 'Folder Permissions' tab.",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                QMessageBox.StandardButton.No
                            )
                            
                            if reply == QMessageBox.StandardButton.No:
                                # Revert the checkbox state
                                item.setData(Qt.ItemDataRole.EditRole, False)
                                return
                    
                    server.enabled = new_enabled
                    mcp_client.save_servers()  # Save changes
                    
                    # Update row styling based on enabled status
                    self.update_row_styling(row, new_enabled)
                    
                    logger.info(f"Server '{server_name}' {'enabled' if new_enabled else 'disabled'}")

    def update_row_styling(self, row, enabled):
        """Update the styling of a table row based on enabled status."""
        color = Qt.GlobalColor.black if enabled else Qt.GlobalColor.gray
        for col in range(self.server_table.columnCount()):
            item = self.server_table.item(row, col)
            if item and col != 2:  # Don't change checkbox column styling
                item.setForeground(color)

    def update_configured_details(self):
        """Update the details display for the selected configured server."""
        selected_items = self.server_table.selectedItems()
        if not selected_items:
            self.configured_details_display.clear()
            self.configured_details_display.setPlaceholderText("Select a server above to see details.")
            self.configured_details_display.setStyleSheet("color: gray;")
            return

        # Get the server name from the data of the first item in the selected row
        row = selected_items[0].row()
        server_name_item = self.server_table.item(row, 0)
        if not server_name_item:
             self.configured_details_display.clear()
             self.configured_details_display.setPlaceholderText("Error retrieving server details.")
             self.configured_details_display.setStyleSheet("color: red;")
             return

        server_name = server_name_item.data(Qt.ItemDataRole.UserRole)
        server = mcp_client.get_server(server_name)

        if server:
            details = f"Name: {server.name}\n"
            details += f"URL: {server.url}\n"
            details += f"Enabled: {'Yes' if server.enabled else 'No'}\n"
            details += f"Capabilities: {', '.join(server.capabilities) if server.capabilities else 'None Discovered'}\n"
            if server.description:
                 details += f"Description: {server.description}\n"
            if server.cx:
                 details += f"CX: {server.cx}\n"
            
            # Show filesystem-specific information
            if hasattr(server, 'server_type') and server.server_type == 'filesystem':
                details += f"\n--- Filesystem Server ---\n"
                config_data = getattr(server, 'config_data', {})
                if config_data.get('allowed_directory'):
                    details += f"Allowed Directory: {config_data['allowed_directory']}\n"
                
                # Show folder permissions summary
                permitted_folders = [path for path, perms in self.file_ops.folder_permissions.items() 
                                   if any(perms.values())]
                if permitted_folders:
                    details += f"Permitted Folders: {len(permitted_folders)} configured\n"
                    details += "  • " + "\n  • ".join(permitted_folders[:3])
                    if len(permitted_folders) > 3:
                        details += f"\n  • ... and {len(permitted_folders) - 3} more"
                else:
                    details += "Permitted Folders: None configured (access denied to all folders)"
            
            # Note: Do not display sensitive auth_token here

            self.configured_details_display.setText(details)
            self.configured_details_display.setStyleSheet("") # Clear placeholder style
        else:
            self.configured_details_display.clear()
            self.configured_details_display.setPlaceholderText("Error: Server not found.")
            self.configured_details_display.setStyleSheet("color: red;")


    def refresh_available_list(self):
        """Refresh the list of available servers."""
        self.available_list.clear()

        available_servers = mcp_client.get_available_mcp_servers()
        configured_names = set(mcp_client.servers.keys())

        for server_data in available_servers:
            # Only add if not already configured
            if server_data["name"] not in configured_names:
                item = QListWidgetItem(f"{server_data['name']} - {server_data['description']}")
                item.setData(Qt.ItemDataRole.UserRole, server_data) # Store the dict data
                self.available_list.addItem(item)

    def update_available_details(self):
        """Update the details display for the selected available server."""
        selected_items = self.available_list.selectedItems()
        if not selected_items:
            self.available_details_display.clear()
            self.available_details_display.setPlaceholderText("Select an available server above to see details.")
            self.available_details_display.setStyleSheet("color: gray;")
            return

        server_data = selected_items[0].data(Qt.ItemDataRole.UserRole)

        if server_data:
            details = f"Name: {server_data.get('name', 'N/A')}\n"
            details += f"URL: {server_data.get('url', 'N/A')}\n"
            details += f"Description: {server_data.get('description', 'N/A')}\n"
            # Note: Available servers typically don't have auth tokens or specific CX pre-filled

            self.available_details_display.setText(details)
            self.available_details_display.setStyleSheet("") # Clear placeholder style
        else:
            self.available_details_display.clear()
            self.available_details_display.setPlaceholderText("Error: Available server data not found.")
            self.available_details_display.setStyleSheet("color: red;")


    def add_server(self):
        """Add a new MCP server."""
        dialog = MCPServerDialog(parent=self)
        if dialog.exec(): # exec() returns QDialog.Accepted or QDialog.Rejected
            self.refresh_server_list()
            self.refresh_available_list() # Refresh available list as a server might have been added from there

    def edit_server(self):
        """Edit the selected MCP server."""
        selected_items = self.server_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Error", "Please select a server to edit.")
            return

        # Get the server name from the data of the first item in the selected row
        row = selected_items[0].row()
        server_name_item = self.server_table.item(row, 0)
        if not server_name_item:
             QMessageBox.warning(self, "Error", "Could not retrieve selected server name.")
             return

        server_name = server_name_item.data(Qt.ItemDataRole.UserRole)
        server = mcp_client.get_server(server_name)

        if server:
            dialog = MCPServerDialog(server, parent=self)
            if dialog.exec():
                self.refresh_server_list()
        else:
            QMessageBox.warning(self, "Error", f"Server '{server_name}' not found in configuration.")
            self.refresh_server_list() # Refresh list to remove potentially stale entry


    def remove_server(self):
        """Remove the selected MCP server."""
        selected_items = self.server_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Error", "Please select a server to remove.")
            return

        # Get the server name from the data of the first item in the selected row
        row = selected_items[0].row()
        server_name_item = self.server_table.item(row, 0)
        if not server_name_item:
             QMessageBox.warning(self, "Error", "Could not retrieve selected server name.")
             return

        server_name = server_name_item.data(Qt.ItemDataRole.UserRole)

        reply = QMessageBox.question(
            self,
            "Confirm Removal",
            f"Are you sure you want to remove the server '{server_name}'?\n\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if mcp_client.remove_server(server_name):
                QMessageBox.information(self, "Success", f"Server '{server_name}' removed.")
                self.refresh_server_list()
                self.refresh_available_list() # Refresh available list as it might now show up there
            else:
                 QMessageBox.warning(self, "Error", f"Failed to remove server '{server_name}'. It might not exist.")
                 self.refresh_server_list() # Refresh list anyway in case of discrepancy


    def add_available_server(self):
        """Add the selected available server."""
        selected_items = self.available_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Error", "Please select a server from the 'Available Servers' list to add.")
            return

        server_data = selected_items[0].data(Qt.ItemDataRole.UserRole)

        # Check if a server with the same name already exists in configured list
        if mcp_client.get_server(server_data.get("name", "")):
             QMessageBox.information(self, "Already Configured", f"A server with the name '{server_data.get('name', 'N/A')}' is already in your configured list. You can edit it there.")
             # Switch to the configured tab and select the existing server
             self.server_table.clearSelection()
             for row in range(self.server_table.rowCount()):
                 item = self.server_table.item(row, 0)
                 if item and item.data(Qt.ItemDataRole.UserRole) == server_data.get("name", ""):
                     self.server_table.selectRow(row)
                     self.server_table.scrollToItem(item)
                     break
             self.parent().findChild(QTabWidget).setCurrentIndex(0) # Assuming parent is the main window holding the tab widget
             return


        # Pre-fill dialog with server data
        server = MCPServer(
            name=server_data.get("name", ""),
            url=server_data.get("url", ""),
            description=server_data.get("description", ""),
            # Auth token and cx are typically empty for available servers, user needs to fill them
            auth_token="",
            cx="",
            enabled=True # Default to enabled when adding
        )

        dialog = MCPServerDialog(server, parent=self)
        if dialog.exec():
            self.refresh_server_list()
            self.refresh_available_list() # Refresh available list as the server is now configured

    def move_to_available(self):
        """Move selected configured server to available servers."""
        selected_items = self.server_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Error", "Please select a server to move.")
            return

        row = selected_items[0].row()
        server_name_item = self.server_table.item(row, 0)
        if not server_name_item:
            QMessageBox.warning(self, "Error", "Could not retrieve selected server name.")
            return

        server_name = server_name_item.data(Qt.ItemDataRole.UserRole)
        server = mcp_client.get_server(server_name)
        
        if not server:
            QMessageBox.warning(self, "Error", "Server not found.")
            return

        # Confirm the move
        reply = QMessageBox.question(
            self, "Move Server", 
            f"Move server '{server_name}' to available servers?\n\n"
            "The server configuration will be preserved and can be moved back later.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if mcp_client.move_server_to_available(server_name):
                self.refresh_server_list()
                self.refresh_available_list()
                QMessageBox.information(self, "Success", f"Server '{server_name}' moved to available servers.")
            else:
                QMessageBox.warning(self, "Error", f"Failed to move server '{server_name}'.")

    def move_to_configured(self):
        """Move selected available server to configured servers."""
        selected_items = self.available_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Error", "Please select a server to move.")
            return

        server_data = selected_items[0].data(Qt.ItemDataRole.UserRole)
        if not server_data:
            QMessageBox.warning(self, "Error", "Could not retrieve server data.")
            return

        server_name = server_data.get('name', 'Unknown')
        
        # Confirm the move
        reply = QMessageBox.question(
            self, "Move Server", 
            f"Move server '{server_name}' to configured servers?\n\n"
            "The server will be added to your configured list and enabled by default.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if mcp_client.move_server_to_configured(server_data):
                self.refresh_server_list()
                self.refresh_available_list()
                QMessageBox.information(self, "Success", f"Server '{server_name}' moved to configured servers.")
            else:
                QMessageBox.warning(self, "Error", f"Failed to move server '{server_name}'.")

    def create_folder_permissions_table(self):
        """Create the folder permissions table."""
        self.permissions_table = QTableWidget()
        
        # Define permission columns - 8 required operations plus folder path and browse button
        self.permission_operations = [
            'read_file', 'write_file', 'edit_file', 'create_directory',
            'list_directory', 'move_file', 'search_files', 'get_file_info'
        ]
        
        # Set up table structure
        column_count = len(self.permission_operations) + 2  # +2 for folder path and browse button
        self.permissions_table.setColumnCount(column_count)
        
        headers = ['Folder Path', 'Browse'] + [op.replace('_', ' ').title() for op in self.permission_operations]
        self.permissions_table.setHorizontalHeaderLabels(headers)
        
        # Configure column resize modes
        header = self.permissions_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Folder Path
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Browse button
        for i in range(2, column_count):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)  # Permission checkboxes
        
        self.permissions_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.permissions_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.permissions_table.verticalHeader().setVisible(False)
        
        # Set up checkbox delegates for permission columns
        for i in range(2, column_count):
            delegate = CheckBoxDelegate(self.permissions_table)
            self.permissions_table.setItemDelegateForColumn(i, delegate)
        
        # Load existing permissions
        self.refresh_folder_permissions()
        
        # Connect table changes to save permissions
        self.permissions_table.itemChanged.connect(self.on_folder_permission_changed)

    def refresh_folder_permissions(self):
        """Refresh the folder permissions table with current data."""
        self.permissions_table.setRowCount(0)
        
        for folder_path, permissions in self.file_ops.folder_permissions.items():
            self.add_folder_permission_row(folder_path, permissions)

    def add_folder_permission_row(self, folder_path: str, permissions: Dict[str, bool]):
        """Add a row to the folder permissions table."""
        row = self.permissions_table.rowCount()
        self.permissions_table.insertRow(row)
        
        # Folder path item
        path_item = QTableWidgetItem(folder_path)
        path_item.setData(Qt.ItemDataRole.UserRole, folder_path)  # Store original path
        self.permissions_table.setItem(row, 0, path_item)
        
        # Browse button
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(lambda checked, r=row: self.browse_folder_for_row(r))
        
        # Style the button for table use
        browse_button.setMinimumSize(80, 28)
        browse_button.setMaximumSize(120, 32)
        browse_button.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        browse_button.setStyleSheet("""
            QPushButton {
                padding: 4px 8px;
                margin: 2px;
                border: 1px solid #0078d7;
                border-radius: 3px;
                background-color: #0078d7;
                color: white;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #005a9e;
                border-color: #005a9e;
            }
            QPushButton:pressed {
                background-color: #003f6a;
            }
        """)
        
        self.permissions_table.setCellWidget(row, 1, browse_button)
        
        # Set row height to accommodate the button properly
        self.permissions_table.setRowHeight(row, 36)
        
        # Permission checkboxes
        for i, operation in enumerate(self.permission_operations):
            checkbox_item = QTableWidgetItem()
            checkbox_item.setData(Qt.ItemDataRole.EditRole, permissions.get(operation, False))
            checkbox_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.permissions_table.setItem(row, i + 2, checkbox_item)

    def browse_folder_for_row(self, row: int):
        """Browse for folder for the specified row."""
        current_path = self.permissions_table.item(row, 0).text()
        
        folder_path = QFileDialog.getExistingDirectory(
            self, "Select Folder", current_path if os.path.exists(current_path) else ""
        )
        
        if folder_path:
            # Update the folder path
            path_item = self.permissions_table.item(row, 0)
            old_path = path_item.data(Qt.ItemDataRole.UserRole)
            path_item.setText(folder_path)
            path_item.setData(Qt.ItemDataRole.UserRole, folder_path)
            
            # Update permissions data structure
            if old_path in self.file_ops.folder_permissions:
                permissions = self.file_ops.folder_permissions.pop(old_path)
                self.file_ops.folder_permissions[folder_path] = permissions
                self.save_folder_permissions()

    def add_folder_permission(self):
        """Add a new folder permission entry."""
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            if folder_path in self.file_ops.folder_permissions:
                QMessageBox.information(self, "Info", "This folder is already configured.")
                return
            
            # Create default permissions (all False)
            default_permissions = {op: False for op in self.permission_operations}
            self.file_ops.folder_permissions[folder_path] = default_permissions
            
            # Add to table
            self.add_folder_permission_row(folder_path, default_permissions)
            self.save_folder_permissions()

    def remove_folder_permission(self):
        """Remove selected folder permission."""
        current_row = self.permissions_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Selection Error", "Please select a folder to remove.")
            return
        
        path_item = self.permissions_table.item(current_row, 0)
        if not path_item:
            return
        
        folder_path = path_item.data(Qt.ItemDataRole.UserRole)
        
        reply = QMessageBox.question(
            self, "Remove Folder",
            f"Remove folder permission for:\n{folder_path}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Remove from data structure
            if folder_path in self.file_ops.folder_permissions:
                del self.file_ops.folder_permissions[folder_path]
            
            # Remove from table
            self.permissions_table.removeRow(current_row)
            self.save_folder_permissions()

    def on_folder_permission_changed(self, item):
        """Handle changes to folder permissions."""
        if item.column() >= 2:  # Only handle permission columns
            row = item.row()
            col = item.column()
            
            path_item = self.permissions_table.item(row, 0)
            if path_item:
                folder_path = path_item.data(Qt.ItemDataRole.UserRole)
                operation = self.permission_operations[col - 2]
                new_value = bool(item.data(Qt.ItemDataRole.EditRole))
                
                # Update permissions
                if folder_path in self.file_ops.folder_permissions:
                    self.file_ops.folder_permissions[folder_path][operation] = new_value
                    self.save_folder_permissions()

    def save_folder_permissions(self):
        """Save folder permissions to file."""
        try:
            # Ensure config directory exists
            os.makedirs(self.file_ops.config_dir, exist_ok=True)
            
            with open(self.file_ops.permissions_file, 'w', encoding='utf-8') as f:
                json.dump(self.file_ops.folder_permissions, f, indent=2)
            
            logger.info(f"Folder permissions saved to {self.file_ops.permissions_file}")
        except Exception as e:
            logger.error(f"Error saving folder permissions: {e}")
            QMessageBox.warning(self, "Save Error", f"Failed to save folder permissions: {e}")


class MCPExampleProfilesDialog(QDialog):
    """Dialog for loading example MCP profiles."""

    def __init__(self, parent=None):
        """Initialize the dialog.

        Args:
            parent: The parent widget
        """
        super().__init__(parent)
        self.initUI()
        self.apply_stylesheet()

    def apply_stylesheet(self):
        """Apply the defined stylesheet to the dialog."""
        self.setStyleSheet(STYLESHEET)

    def initUI(self):
        """Initialize the user interface."""
        self.setWindowTitle("Load Example MCP Profiles")
        self.setMinimumWidth(550) # Slightly wider
        self.setMinimumHeight(400) # Taller

        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Description
        description = QLabel(
            "Select an example profile to load a set of pre-configured MCP servers "
            "tailored for specific use cases. You will likely need to add API keys "
            "and configure URLs for these servers after loading."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        # Profile selection
        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.profile_combo = QComboBox()
        self.profiles_data = self._get_example_profiles_data() # Get profile data
        self.profile_combo.addItems([profile["name"] for profile in self.profiles_data])
        self.profile_combo.currentIndexChanged.connect(self.update_profile_description)
        form_layout.addRow("Profile:", self.profile_combo)

        layout.addLayout(form_layout)

        # Profile description and servers list
        description_group = QGroupBox("Profile Details")
        description_layout = QVBoxLayout(description_group)

        self.profile_description = QTextEdit()
        self.profile_description.setReadOnly(True)
        self.profile_description.setMaximumHeight(100)
        self.profile_description.setPlaceholderText("Select a profile to see its description.")
        self.profile_description.setStyleSheet("color: gray;")
        description_layout.addWidget(self.profile_description)

        servers_label = QLabel("Included Servers:")
        description_layout.addWidget(servers_label)

        self.profile_servers_list = QListWidget()
        self.profile_servers_list.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.profile_servers_list.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection) # Not selectable
        description_layout.addWidget(self.profile_servers_list)

        description_group.setLayout(description_layout)
        layout.addWidget(description_group)


        # Update the initial description and server list
        self.update_profile_description(0)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def _get_example_profiles_data(self) -> List[Dict[str, Any]]:
        """Define and return the data for example profiles."""
        # Define the servers for each profile. Use placeholder URLs/tokens.
        return [
            {
                "name": "Web Research Assistant",
                "description": "This profile includes MCP servers for web search, knowledge retrieval, and content extraction. Perfect for research tasks, fact-checking, and gathering information from the web.",
                "servers": [
                    MCPServer(
                        name="Brave Search",
                        url="https://api.search.brave.com/res/v1/web/search",
                        description="Search the web with Brave Search (Requires Subscription Token)",
                        capabilities=["web_search", "image_search", "news_search"],
                        auth_token=""
                    ),
                    MCPServer(
                        name="Google Search",
                        url="https://www.googleapis.com/customsearch/v1",
                        description="Search the web with Google Custom Search API (Requires API Key and CX)",
                        capabilities=["web_search", "image_search", "news_search"],
                        auth_token="",
                        cx=""
                    ),
                    MCPServer(
                        name="Context7",
                        url="https://api.context7.com/v1", # Placeholder URL
                        description="Access up-to-date documentation and code examples for popular libraries (Requires API Key)",
                        capabilities=["documentation", "code_examples", "api_reference"],
                        auth_token=""
                    )
                ]
            },
            {
                "name": "Software Development Helper",
                "description": "This profile includes MCP servers for code repositories, documentation, and development tools. Ideal for software development tasks, code review, and technical problem-solving.",
                "servers": [
                    MCPServer(
                        name="GitHub",
                        url="https://api.github.com", # Placeholder URL
                        description="Access GitHub repositories, issues, and pull requests (Requires Personal Access Token)",
                        capabilities=["repo_access", "issue_management", "pr_review"],
                        auth_token=""
                    ),
                    MCPServer(
                        name="Context7",
                        url="https://api.context7.com/v1", # Placeholder URL
                        description="Access up-to-date documentation and code examples for popular libraries (Requires API Key)",
                        capabilities=["documentation", "code_examples", "api_reference"],
                        auth_token=""
                    ),
                     MCPServer(
                        name="Serper Search",
                        url="https://api.serper.dev/search",
                        description="Fast and affordable Google Search API alternative for technical queries (Requires API Key)",
                        capabilities=["web_search", "news_search"],
                        auth_token=""
                    )
                ]
            },
            # Add more profiles here following the same structure
             {
                "name": "Data Analysis Toolkit",
                "description": "This profile includes MCP servers for data access and analysis tools. Great for data exploration, reporting, and insights.",
                "servers": [
                    MCPServer(
                        name="Google BigQuery",
                        url="http://localhost:8080/bigquery", # Placeholder URL - requires a custom MCP server implementation
                        description="Query Google BigQuery datasets (Requires Authentication)",
                        capabilities=["sql_execution", "schema_inspection"],
                        auth_token=""
                    ),
                    MCPServer(
                        name="Kaggle",
                        url="http://localhost:8080/kaggle", # Placeholder URL - requires a custom MCP server implementation
                        description="Access Kaggle datasets and notebooks (Requires Authentication)",
                        capabilities=["dataset_access", "notebook_execution"],
                        auth_token=""
                    ),
                    MCPServer(
                        name="Context7",
                        url="https://api.context7.com/v1", # Placeholder URL
                        description="Access up-to-date documentation and code examples for popular libraries (Requires API Key)",
                        capabilities=["documentation", "code_examples", "api_reference"],
                        auth_token=""
                    )
                ]
            },
            {
                "name": "Content Creation Suite",
                "description": "This profile includes MCP servers for content research, media access, and publishing platforms. Perfect for content creation, writing, and publishing.",
                "servers": [
                    MCPServer(
                        name="Google Drive",
                        url="http://localhost:8080/google-drive", # Placeholder URL - requires a custom MCP server implementation
                        description="Access files and folders in Google Drive (Requires Authentication)",
                        capabilities=["file_access", "file_creation", "file_update"],
                        auth_token=""
                    ),
                    MCPServer(
                        name="Unsplash",
                        url="https://api.unsplash.com",
                        description="Search for and download images from Unsplash (Requires API Key)",
                        capabilities=["image_search", "image_download"],
                        auth_token=""
                    ),
                    MCPServer(
                        name="Context7",
                        url="https://api.context7.com/v1", # Placeholder URL
                        description="Access up-to-date documentation and code examples for popular libraries (Requires API Key)",
                        capabilities=["documentation", "code_examples", "api_reference"],
                        auth_token=""
                    )
                ]
            },
             {
                "name": "Customer Support Agent",
                "description": "This profile includes MCP servers for customer communication, knowledge bases, and support tools. Ideal for customer support, troubleshooting, and service.",
                "servers": [
                    MCPServer(
                        name="Slack",
                        url="https://slack.com/api", # Placeholder URL - requires a custom MCP server implementation
                        description="Interact with Slack channels and messages (Requires API Token)",
                        capabilities=["message_sending", "channel_management", "user_lookup"],
                        auth_token=""
                    ),
                    MCPServer(
                        name="Zendesk",
                        url="http://localhost:8080/zendesk", # Placeholder URL - requires a custom MCP server implementation
                        description="Access and update Zendesk tickets (Requires Authentication)",
                        capabilities=["ticket_creation", "ticket_update", "ticket_search"],
                        auth_token=""
                    ),
                    MCPServer(
                        name="Context7",
                        url="https://api.context7.com/v1", # Placeholder URL
                        description="Access up-to-date documentation and code examples for popular libraries (Requires API Key)",
                        capabilities=["documentation", "code_examples", "api_reference"],
                        auth_token=""
                    )
                ]
            }
        ]


    def update_profile_description(self, index):
        """Update the profile description and server list based on the selected profile."""
        if 0 <= index < len(self.profiles_data):
            profile = self.profiles_data[index]
            self.profile_description.setText(profile["description"])
            self.profile_description.setStyleSheet("") # Clear placeholder style

            self.profile_servers_list.clear()
            for server in profile["servers"]:
                item = QListWidgetItem(f"{server.name} - {server.description}")
                self.profile_servers_list.addItem(item)
        else:
            self.profile_description.clear()
            self.profile_description.setPlaceholderText("Select a profile to see its description.")
            self.profile_description.setStyleSheet("color: gray;")
            self.profile_servers_list.clear()


    def accept(self):
        """Load the selected profile and close the dialog."""
        profile_index = self.profile_combo.currentIndex()
        if not (0 <= profile_index < len(self.profiles_data)):
             QMessageBox.warning(self, "Selection Error", "Please select a valid profile.")
             return

        profile = self.profiles_data[profile_index]
        servers_to_add = profile["servers"]

        # Add the servers for the selected profile
        added_count = 0
        for server in servers_to_add:
            # Check if a server with the same name already exists
            existing_server = mcp_client.get_server(server.name)
            if existing_server:
                 # Option: Ask user to overwrite or skip? For simplicity, we'll just update.
                 # The mcp_client.add_server handles updating by name.
                 logger.info(f"Server '{server.name}' already exists. Updating configuration.")
                 # Preserve existing capabilities if the example profile doesn't specify them
                 if not server.capabilities and existing_server.capabilities:
                      server.capabilities = existing_server.capabilities
                 # Preserve existing auth token if the example profile has an empty one
                 if not server.auth_token and existing_server.auth_token:
                      server.auth_token = existing_server.auth_token
                 # Preserve existing CX if the example profile has an empty one
                 if not server.cx and existing_server.cx:
                      server.cx = existing_server.cx


            mcp_client.add_server(server)
            added_count += 1

        QMessageBox.information(
            self,
            "Profile Loaded",
            f"Successfully loaded the '{profile['name']}' profile.\n\n"
            f"{added_count} server(s) were added or updated.\n\n"
            "IMPORTANT: You may need to open the 'Configure MCP Servers' dialog "
            "to add API keys, tokens, or correct URLs for the newly added servers."
        )

        super().accept()

# --- Example Usage (for testing the dialogs directly) ---
if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET) # Apply stylesheet globally

    # Example: Show the main config dialog
    main_dialog = MCPConfigDialog()
    main_dialog.exec()

    # Example: Show the example profiles dialog
    # profiles_dialog = MCPExampleProfilesDialog()
    # profiles_dialog.exec()

    sys.exit(app.exec())