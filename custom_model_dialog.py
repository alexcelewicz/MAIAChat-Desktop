"""
Dialog for managing models.
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                            QComboBox, QLineEdit, QPushButton, QListWidget,
                            QDialogButtonBox, QMessageBox, QWidget, QTabWidget,
                            QCheckBox, QListWidgetItem)
from PyQt6.QtCore import Qt, pyqtSlot
from custom_models_manager import custom_models_manager
from model_manager import model_manager
from typing import List, Dict, Optional, Tuple


class CustomModelDialog(QDialog):
    """Dialog for managing both standard and custom models."""

    def __init__(self, current_provider: str, parent=None):
        super().__init__(parent)
        self.current_provider = current_provider
        self.initUI()
        self.load_models()

    def initUI(self):
        """Initialize the user interface."""
        self.setWindowTitle("Manage Models")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        layout = QVBoxLayout()

        # Provider selection
        provider_layout = QHBoxLayout()
        provider_layout.addWidget(QLabel("Provider:"))

        self.provider_combo = QComboBox()
        from data_registry import PROVIDERS
        self.provider_combo.addItems(PROVIDERS)
        self.provider_combo.setCurrentText(self.current_provider)
        self.provider_combo.currentTextChanged.connect(self.load_models)
        provider_layout.addWidget(self.provider_combo)

        layout.addLayout(provider_layout)

        # Create tab widget for different model types
        self.tab_widget = QTabWidget()

        # Standard models tab
        self.standard_tab = QWidget()
        standard_layout = QVBoxLayout(self.standard_tab)

        standard_layout.addWidget(QLabel("Standard Models:"))
        self.standard_model_list = QListWidget()
        standard_layout.addWidget(self.standard_model_list)

        # Buttons for standard models
        standard_buttons_layout = QHBoxLayout()

        self.enable_button = QPushButton("Enable Selected")
        self.enable_button.clicked.connect(self.enable_standard_model)
        standard_buttons_layout.addWidget(self.enable_button)

        self.disable_button = QPushButton("Disable Selected")
        self.disable_button.clicked.connect(self.disable_standard_model)
        standard_buttons_layout.addWidget(self.disable_button)

        standard_layout.addLayout(standard_buttons_layout)

        # Custom models tab
        self.custom_tab = QWidget()
        custom_layout = QVBoxLayout(self.custom_tab)

        custom_layout.addWidget(QLabel("Custom Models:"))
        self.custom_model_list = QListWidget()
        custom_layout.addWidget(self.custom_model_list)

        # Add model controls
        add_layout = QHBoxLayout()
        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("Enter model name")
        add_layout.addWidget(self.model_input)

        add_button = QPushButton("Add")
        add_button.clicked.connect(self.add_custom_model)
        add_layout.addWidget(add_button)

        custom_layout.addLayout(add_layout)

        # Remove button for custom models
        remove_button = QPushButton("Remove Selected")
        remove_button.clicked.connect(self.remove_custom_model)
        custom_layout.addWidget(remove_button)

        # Add tabs to tab widget
        self.tab_widget.addTab(self.standard_tab, "Standard Models")
        self.tab_widget.addTab(self.custom_tab, "Custom Models")

        layout.addWidget(self.tab_widget)

        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def load_models(self):
        """Load models for the selected provider."""
        provider = self.provider_combo.currentText()

        # Get standard models
        from data_registry import MODEL_MAPPINGS, DEFAULT_OLLAMA_MODELS

        standard_models = []
        if provider == "LM Studio":
            # For LM Studio, we need to get models from the parent widget
            if self.parent() and hasattr(self.parent(), 'get_lmstudio_models'):
                standard_models = self.parent().get_lmstudio_models()
            else:
                standard_models = ["model_name"]
        elif provider == "OpenRouter":
            # For OpenRouter, we need to get models from the parent widget
            if self.parent() and hasattr(self.parent(), 'get_openrouter_models'):
                standard_models = self.parent().get_openrouter_models()
            else:
                standard_models = ["openrouter-model"]
        elif provider == "Ollama":
            # For Ollama, we need to get models from the parent widget
            if self.parent() and hasattr(self.parent(), 'get_ollama_models'):
                standard_models = self.parent().get_ollama_models()
            else:
                standard_models = DEFAULT_OLLAMA_MODELS
        else:
            standard_models = MODEL_MAPPINGS.get(provider, [])

        # Get model status from model manager
        model_status = model_manager.get_all_models(provider, standard_models)

        # Update standard models list
        self.standard_model_list.clear()

        # Add enabled standard models
        for model in model_status["enabled_standard"]:
            item = QListWidgetItem(f"✓ {model}")
            item.setData(Qt.ItemDataRole.UserRole, {"model": model, "enabled": True})
            self.standard_model_list.addItem(item)

        # Add disabled standard models
        for model in model_status["disabled_standard"]:
            item = QListWidgetItem(f"❌ {model}")
            item.setData(Qt.ItemDataRole.UserRole, {"model": model, "enabled": False})
            self.standard_model_list.addItem(item)

        # Update custom models list
        self.custom_model_list.clear()
        self.custom_model_list.addItems(model_status["custom"])

    @pyqtSlot()
    def add_custom_model(self):
        """Add a new custom model."""
        model_name = self.model_input.text().strip()
        if not model_name:
            QMessageBox.warning(self, "Warning", "Please enter a model name.")
            return

        provider = self.provider_combo.currentText()

        if custom_models_manager.add_model(provider, model_name):
            self.custom_model_list.addItem(model_name)
            self.model_input.clear()
        else:
            QMessageBox.warning(self, "Warning", f"Model '{model_name}' already exists for {provider}.")

    @pyqtSlot()
    def remove_custom_model(self):
        """Remove the selected custom model."""
        selected_items = self.custom_model_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select a model to remove.")
            return

        provider = self.provider_combo.currentText()

        for item in selected_items:
            model_name = item.text()
            if custom_models_manager.remove_model(provider, model_name):
                self.custom_model_list.takeItem(self.custom_model_list.row(item))

    @pyqtSlot()
    def disable_standard_model(self):
        """Disable the selected standard model."""
        selected_items = self.standard_model_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select a model to disable.")
            return

        provider = self.provider_combo.currentText()

        for item in selected_items:
            data = item.data(Qt.ItemDataRole.UserRole)
            if data and data["enabled"]:
                model_name = data["model"]
                if model_manager.disable_model(provider, model_name):
                    # Refresh the model list
                    self.load_models()

    @pyqtSlot()
    def enable_standard_model(self):
        """Enable the selected standard model."""
        selected_items = self.standard_model_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select a model to enable.")
            return

        provider = self.provider_combo.currentText()

        for item in selected_items:
            data = item.data(Qt.ItemDataRole.UserRole)
            if data and not data["enabled"]:
                model_name = data["model"]
                if model_manager.enable_model(provider, model_name):
                    # Refresh the model list
                    self.load_models()
