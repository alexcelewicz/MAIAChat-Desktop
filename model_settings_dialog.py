"""
Dialog for editing model-specific settings.
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                            QDoubleSpinBox, QSpinBox, QDialogButtonBox,
                            QFormLayout, QLineEdit, QPushButton, QListWidget,
                            QWidget, QScrollArea, QFrame, QCheckBox)
from PyQt6.QtCore import Qt, pyqtSlot
from model_settings import ModelSettings, settings_manager, PROVIDER_PARAMETERS
from typing import Dict, Any, List, Optional


class ModelSettingsDialog(QDialog):
    """Dialog for editing model-specific settings."""
    
    def __init__(self, provider: str, model: str, parent=None):
        super().__init__(parent)
        self.provider = provider
        self.model = model
        self.settings = settings_manager.get_settings(provider, model)
        self.parameter_widgets = {}
        self.stop_sequences = self.settings.stop_sequences.copy()
        
        self.initUI()
    
    def initUI(self):
        """Initialize the user interface."""
        self.setWindowTitle(f"Settings for {self.provider} - {self.model}")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # Create a scroll area for the form
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        # Create a widget to hold the form
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        form_layout.setContentsMargins(0, 0, 0, 0)
        
        # Get available parameters for this provider
        available_params = PROVIDER_PARAMETERS.get(self.provider, [])
        
        # Add widgets for each parameter
        for param in available_params:
            if param == "stop_sequences":
                # Special handling for stop sequences
                self.add_stop_sequences_widget(form_layout)
            else:
                self.add_parameter_widget(form_layout, param)
        
        scroll_area.setWidget(form_widget)
        layout.addWidget(scroll_area)
        
        # Add buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def add_parameter_widget(self, layout, param_name: str):
        """Add a widget for a specific parameter."""
        current_value = getattr(self.settings, param_name)
        param_range = self.settings.get_parameter_range(param_name)
        
        if param_name in ["temperature", "top_p", "frequency_penalty", "presence_penalty", "repetition_penalty"]:
            # Float parameters
            widget = QDoubleSpinBox()
            if param_range:
                widget.setRange(param_range[0], param_range[1])
            else:
                widget.setRange(0.0, 2.0)
            widget.setSingleStep(0.05)
            widget.setValue(current_value)
            
        elif param_name in ["top_k", "max_tokens", "thinking_budget"]:
            # Integer parameters
            widget = QSpinBox()
            if param_range:
                widget.setRange(param_range[0], param_range[1])
            else:
                if param_name == "thinking_budget":
                    widget.setRange(-1, 10000)
                    widget.setSpecialValueText("Unlimited")
                else:
                    widget.setRange(1, 32000)
            widget.setSingleStep(1)
            widget.setValue(current_value)

        elif param_name == "thinking_enabled":
            # Boolean parameter
            widget = QCheckBox()
            widget.setChecked(current_value)
            widget.setText("Enable thinking mode for supported models")
        
        else:
            # Default to text input
            widget = QLineEdit(str(current_value))
        
        # Format the parameter name for display
        display_name = param_name.replace('_', ' ').title()
        
        layout.addRow(display_name, widget)
        self.parameter_widgets[param_name] = widget
    
    def add_stop_sequences_widget(self, layout):
        """Add widget for managing stop sequences."""
        stop_widget = QWidget()
        stop_layout = QVBoxLayout(stop_widget)
        stop_layout.setContentsMargins(0, 0, 0, 0)
        
        # List widget for stop sequences
        self.stop_list = QListWidget()
        self.stop_list.addItems(self.stop_sequences)
        stop_layout.addWidget(self.stop_list)
        
        # Add/remove buttons
        buttons_layout = QHBoxLayout()
        
        add_button = QPushButton("Add")
        add_button.clicked.connect(self.add_stop_sequence)
        buttons_layout.addWidget(add_button)
        
        remove_button = QPushButton("Remove")
        remove_button.clicked.connect(self.remove_stop_sequence)
        buttons_layout.addWidget(remove_button)
        
        stop_layout.addLayout(buttons_layout)
        
        # Add to form
        layout.addRow("Stop Sequences", stop_widget)
    
    @pyqtSlot()
    def add_stop_sequence(self):
        """Add a new stop sequence."""
        # Create a simple dialog to get the stop sequence
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Stop Sequence")
        
        dialog_layout = QVBoxLayout(dialog)
        
        # Add input field
        input_field = QLineEdit()
        dialog_layout.addWidget(QLabel("Enter stop sequence:"))
        dialog_layout.addWidget(input_field)
        
        # Add buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        dialog_layout.addWidget(button_box)
        
        # Show dialog
        if dialog.exec() == QDialog.DialogCode.Accepted:
            sequence = input_field.text().strip()
            if sequence and sequence not in self.stop_sequences:
                self.stop_sequences.append(sequence)
                self.stop_list.addItem(sequence)
    
    @pyqtSlot()
    def remove_stop_sequence(self):
        """Remove the selected stop sequence."""
        selected_items = self.stop_list.selectedItems()
        if not selected_items:
            return
        
        for item in selected_items:
            sequence = item.text()
            if sequence in self.stop_sequences:
                self.stop_sequences.remove(sequence)
            
            # Remove from list widget
            self.stop_list.takeItem(self.stop_list.row(item))
    
    def accept(self):
        """Save settings and close dialog."""
        # Update settings from widgets
        for param, widget in self.parameter_widgets.items():
            if isinstance(widget, (QDoubleSpinBox, QSpinBox)):
                value = widget.value()
            elif isinstance(widget, QCheckBox):
                value = widget.isChecked()
            else:
                # Handle other widget types
                value = widget.text()

                # Convert to appropriate type if needed
                try:
                    if param in ["top_k", "max_tokens", "thinking_budget"]:
                        value = int(value)
                    elif param in ["temperature", "top_p", "frequency_penalty", "presence_penalty", "repetition_penalty"]:
                        value = float(value)
                except ValueError:
                    # Keep as string if conversion fails
                    pass

            setattr(self.settings, param, value)
        
        # Update stop sequences
        self.settings.stop_sequences = self.stop_sequences
        
        # Save settings
        settings_manager.save_settings(self.settings)
        
        super().accept()
