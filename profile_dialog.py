"""
Dialog for selecting and loading agent profiles.
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                            QListWidget, QListWidgetItem, QPushButton,
                            QDialogButtonBox, QTextEdit, QSplitter, QWidget,
                            QMessageBox, QInputDialog, QLineEdit)
from mcp_config_dialog import MCPExampleProfilesDialog
from PyQt6.QtCore import Qt, pyqtSlot, pyqtSignal
from profile_manager import profile_manager, Profile
from typing import Optional


class ProfileDialog(QDialog):
    """Dialog for selecting and loading agent profiles."""

    profile_selected = pyqtSignal(Profile)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_profile = None
        self.selected_is_example = False
        self.initUI()

    def initUI(self):
        """Initialize the user interface."""
        self.setWindowTitle("Agent Profiles")
        self.setMinimumSize(800, 500)

        layout = QVBoxLayout()

        # Create splitter for list and details
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left side - profile list
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # Add label
        left_layout.addWidget(QLabel("Available Profiles:"))

        # Add search box for filtering profiles
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search profiles...")
        self.search_box.textChanged.connect(self.filter_profiles)
        left_layout.addWidget(self.search_box)

        # Add list widget with scrolling enabled
        self.profile_list = QListWidget()
        self.profile_list.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self.profile_list.setHorizontalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self.profile_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.profile_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.profile_list.setMinimumHeight(300)  # Ensure enough height to display multiple items
        self.profile_list.itemClicked.connect(self.on_profile_selected)
        left_layout.addWidget(self.profile_list)

        # Add buttons for managing profiles
        button_layout = QHBoxLayout()

        self.save_btn = QPushButton("Save Current")
        self.save_btn.clicked.connect(self.save_current_profile)
        button_layout.addWidget(self.save_btn)

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_profile)
        self.delete_btn.setEnabled(False)
        button_layout.addWidget(self.delete_btn)

        self.mcp_profiles_btn = QPushButton("MCP Profiles")
        self.mcp_profiles_btn.clicked.connect(self.show_mcp_profiles)
        button_layout.addWidget(self.mcp_profiles_btn)

        left_layout.addLayout(button_layout)

        # Right side - profile details
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # Add labels
        right_layout.addWidget(QLabel("Profile Details:"))

        # Add details text
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        right_layout.addWidget(self.details_text)

        # Add to splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([300, 500])

        layout.addWidget(splitter)

        # Add dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

        # Load profiles
        self.load_profiles()

    def load_profiles(self):
        """Load available profiles into the list."""
        self.profile_list.clear()

        # Get profiles
        self.profiles = profile_manager.get_profile_list()

        # Store profiles for filtering
        self.all_profiles = self.profiles

        # Display profiles
        self._display_profiles(self.profiles)

    def _display_profiles(self, profiles):
        """Display profiles in the list widget."""
        self.profile_list.clear()

        # Add user profiles first
        user_profiles = [p for p in profiles if not p[2]]
        for name, desc, _ in user_profiles:
            item = QListWidgetItem(f"{name}")
            item.setData(Qt.ItemDataRole.UserRole, (name, False))
            if desc:
                item.setToolTip(desc)  # Show description on hover
            self.profile_list.addItem(item)

        # Add separator if we have both user and example profiles
        if user_profiles and any(p[2] for p in profiles):
            separator = QListWidgetItem("--- Example Profiles ---")
            separator.setFlags(Qt.ItemFlag.NoItemFlags)
            separator.setBackground(Qt.GlobalColor.lightGray)
            self.profile_list.addItem(separator)

        # Add example profiles
        for name, desc, is_example in profiles:
            if is_example:
                item = QListWidgetItem(f"{name}")
                item.setData(Qt.ItemDataRole.UserRole, (name, True))
                if desc:
                    item.setToolTip(desc)  # Show description on hover
                self.profile_list.addItem(item)

    def filter_profiles(self, text):
        """Filter profiles based on search text."""
        if not text:
            # If search box is empty, show all profiles
            self._display_profiles(self.all_profiles)
            return

        # Filter profiles based on search text
        filtered_profiles = []
        search_text = text.lower()

        for name, desc, is_example in self.all_profiles:
            # Search in name and description
            if search_text in name.lower() or search_text in desc.lower():
                filtered_profiles.append((name, desc, is_example))

        # Display filtered profiles
        self._display_profiles(filtered_profiles)

    @pyqtSlot(QListWidgetItem)
    def on_profile_selected(self, item):
        """Handle profile selection."""
        if not item or not item.flags() & Qt.ItemFlag.ItemIsSelectable:
            return

        data = item.data(Qt.ItemDataRole.UserRole)
        if not data:
            return

        name, is_example = data

        # Load profile
        profile = profile_manager.load_profile(name, is_example)
        if not profile:
            self.details_text.setPlainText(f"Error loading profile '{name}'.\nThe profile may be corrupted or missing required fields.")
            self.selected_profile = None
            self.selected_is_example = False
            self.delete_btn.setEnabled(False)
            return

        # Store selected profile
        self.selected_profile = profile
        self.selected_is_example = is_example

        try:
            # Update details
            details = f"Name: {profile.name}\n\n"
            details += f"Description: {profile.description}\n\n"
            details += f"Internet Enabled: {'Yes' if profile.internet_enabled else 'No'}\n"
            details += f"MCP Enabled: {'Yes' if getattr(profile, 'mcp_enabled', False) else 'No'}\n\n"
            details += f"General Instructions:\n{profile.general_instructions}\n\n"
            details += f"Agents: {len(profile.agents)}\n\n"

            for i, agent in enumerate(profile.agents):
                agent_num = getattr(agent, 'agent_number', i+1)
                details += f"Agent {agent_num}:\n"
                details += f"  Provider: {agent.provider}\n"
                details += f"  Model: {agent.model}\n"

                # Safely get instructions and truncate if needed
                instructions = getattr(agent, 'instructions', '')
                if instructions:
                    if len(instructions) > 100:
                        details += f"  Instructions: {instructions[:100]}...\n\n"
                    else:
                        details += f"  Instructions: {instructions}\n\n"
                else:
                    details += "  Instructions: None\n\n"

            self.details_text.setPlainText(details)
        except Exception as e:
            import logging
            logging.error(f"Error displaying profile details: {e}")
            self.details_text.setPlainText(f"Error displaying profile details: {str(e)}")

        # Enable/disable delete button
        self.delete_btn.setEnabled(not is_example)

    def save_current_profile(self):
        """Save the current configuration as a profile."""
        # Get name and description from user
        name, ok = QInputDialog.getText(
            self, "Profile Name", "Enter a name for this profile:"
        )
        if not ok or not name:
            return

        description, ok = QInputDialog.getText(
            self, "Profile Description", "Enter a description for this profile:"
        )
        if not ok:
            return

        # Emit signal to request current configuration
        # This will be handled by the main window
        self.profile_name = name
        self.profile_description = description
        self.accept()

    def delete_profile(self):
        """Delete the selected profile."""
        if not self.selected_profile or self.selected_is_example:
            return

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the profile '{self.selected_profile.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Delete profile
            if profile_manager.delete_profile(self.selected_profile.name):
                # Reload profiles
                self.load_profiles()
                self.details_text.clear()
                self.selected_profile = None
                self.selected_is_example = False
                self.delete_btn.setEnabled(False)
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Failed to delete profile '{self.selected_profile.name}'."
                )

    def show_mcp_profiles(self):
        """Show the MCP example profiles dialog."""
        dialog = MCPExampleProfilesDialog(self)
        if dialog.exec():
            QMessageBox.information(
                self,
                "MCP Profiles",
                "MCP profile loaded successfully. You can now use MCP servers in your agents."
            )

    def accept(self):
        """Handle dialog acceptance."""
        if hasattr(self, 'profile_name'):
            # User wants to save current configuration
            super().accept()
            return

        if not self.selected_profile:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a profile to load."
            )
            return

        # Emit signal with selected profile
        self.profile_selected.emit(self.selected_profile)
        super().accept()
