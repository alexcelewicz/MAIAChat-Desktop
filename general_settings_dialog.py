#!/usr/bin/env python3
"""
General Settings Dialog for Python Agents
This dialog allows users to configure API endpoint URLs and other general settings through the UI.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QLineEdit, QPushButton, QDialogButtonBox, QGroupBox,
    QScrollArea, QWidget, QFrame, QTextEdit, QMessageBox,
    QCheckBox, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
import json
import logging
import requests
from pathlib import Path
from model_settings import settings_manager
from config import config_manager

logger = logging.getLogger(__name__)

class GeneralSettingsDialog(QDialog):
    """Dialog for configuring general settings including API endpoint URLs."""
    
    settings_changed = pyqtSignal(dict)  # Signal emitted when settings are changed
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        self.load_current_settings()
        
    def initUI(self):
        """Initialize the user interface."""
        self.setWindowTitle("General Settings")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        # Main layout
        main_layout = QVBoxLayout()
        
        # Create scroll area for better UX
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        # Create content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        # Add description
        description = QLabel(
            "Configure API endpoint URLs and other general settings. "
            "These settings control where the application connects to various AI services."
        )
        description.setWordWrap(True)
        description.setStyleSheet("""
            QLabel {
                background-color: #f0f8ff;
                border: 1px solid #b0d4f1;
                border-radius: 8px;
                padding: 12px;
                margin-bottom: 10px;
                font-size: 13px;
                color: #2c3e50;
            }
        """)
        content_layout.addWidget(description)
        
        # API Endpoints Group
        endpoints_group = QGroupBox("API Endpoint Configuration")
        endpoints_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #2c3e50;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        endpoints_layout = QFormLayout(endpoints_group)
        
        # Ollama Base URL
        self.ollama_url_edit = QLineEdit()
        self.ollama_url_edit.setPlaceholderText("http://localhost:11434")
        self.ollama_url_edit.setToolTip("Base URL for Ollama local inference server")
        endpoints_layout.addRow("Ollama Base URL:", self.ollama_url_edit)
        
        # LM Studio Base URL
        self.lmstudio_url_edit = QLineEdit()
        self.lmstudio_url_edit.setPlaceholderText("http://localhost:1234/v1")
        self.lmstudio_url_edit.setToolTip("Base URL for LM Studio local inference server")
        endpoints_layout.addRow("LM Studio Base URL:", self.lmstudio_url_edit)
        
        # DeepSeek Base URL
        self.deepseek_url_edit = QLineEdit()
        self.deepseek_url_edit.setPlaceholderText("https://api.deepseek.com")
        self.deepseek_url_edit.setToolTip("Base URL for DeepSeek API")
        endpoints_layout.addRow("DeepSeek Base URL:", self.deepseek_url_edit)
        
        # OpenRouter Base URL
        self.openrouter_url_edit = QLineEdit()
        self.openrouter_url_edit.setPlaceholderText("https://openrouter.ai/api/v1")
        self.openrouter_url_edit.setToolTip("Base URL for OpenRouter API")
        endpoints_layout.addRow("OpenRouter Base URL:", self.openrouter_url_edit)
        
        # Groq Base URL
        self.groq_url_edit = QLineEdit()
        self.groq_url_edit.setPlaceholderText("https://api.groq.com/openai/v1")
        self.groq_url_edit.setToolTip("Base URL for Groq API")
        endpoints_layout.addRow("Groq Base URL:", self.groq_url_edit)
        
        # Grok Base URL
        self.grok_url_edit = QLineEdit()
        self.grok_url_edit.setPlaceholderText("https://api.x.ai/v1")
        self.grok_url_edit.setToolTip("Base URL for Grok API")
        endpoints_layout.addRow("Grok Base URL:", self.grok_url_edit)
        
        content_layout.addWidget(endpoints_group)

        # Context Management Group
        context_group = QGroupBox("Agent Context Management")
        context_group.setStyleSheet(endpoints_group.styleSheet())
        context_layout = QFormLayout(context_group)

        # Context Management Enable/Disable
        self.context_management_checkbox = QCheckBox("Enable Context Management")
        self.context_management_checkbox.setToolTip(
            "Enable intelligent context window management for multi-agent workflows.\n"
            "This prevents context overflow by intelligently truncating older agent responses\n"
            "while preserving key information from all agents."
        )
        context_layout.addRow("", self.context_management_checkbox)

        # Context Strategy Selection
        self.context_strategy_combo = QComboBox()
        self.context_strategy_combo.addItems([
            "intelligent_truncation",
            "simple_truncation",
            "summarization_only"
        ])
        self.context_strategy_combo.setToolTip(
            "Select the context management strategy:\n"
            "• Intelligent Truncation: Smart paragraph-aware truncation with summarization\n"
            "• Simple Truncation: Basic character-based truncation\n"
            "• Summarization Only: Summarize older responses without truncation"
        )
        context_layout.addRow("Context Strategy:", self.context_strategy_combo)

        # Context Management Description
        context_description = QLabel(
            "Context management prevents token overflow in multi-agent workflows by:\n"
            "• Giving priority to recent agent responses (full content)\n"
            "• Intelligently summarizing older agent responses\n"
            "• Preserving collaborative intelligence across all agents\n"
            "• Ensuring all agents can process without hitting token limits"
        )
        context_description.setStyleSheet("""
            QLabel {
                background-color: #e8f4fd;
                border: 1px solid #b0d4f1;
                border-radius: 6px;
                padding: 10px;
                margin: 5px 0px;
                font-size: 12px;
                color: #2c3e50;
                line-height: 1.4;
            }
        """)
        context_layout.addRow("", context_description)

        content_layout.addWidget(context_group)

        # Test Connection Group
        test_group = QGroupBox("Test Connections")
        test_group.setStyleSheet(endpoints_group.styleSheet())
        test_layout = QVBoxLayout(test_group)
        
        # Test buttons layout
        test_buttons_layout = QHBoxLayout()
        
        self.test_ollama_btn = QPushButton("Test Ollama")
        self.test_ollama_btn.setToolTip("Test connection to Ollama server")
        self.test_ollama_btn.clicked.connect(lambda: self.test_connection("ollama"))
        
        self.test_lmstudio_btn = QPushButton("Test LM Studio")
        self.test_lmstudio_btn.setToolTip("Test connection to LM Studio server")
        self.test_lmstudio_btn.clicked.connect(lambda: self.test_connection("lmstudio"))
        
        self.test_deepseek_btn = QPushButton("Test DeepSeek")
        self.test_deepseek_btn.setToolTip("Test connection to DeepSeek API")
        self.test_deepseek_btn.clicked.connect(lambda: self.test_connection("deepseek"))
        
        test_buttons_layout.addWidget(self.test_ollama_btn)
        test_buttons_layout.addWidget(self.test_lmstudio_btn)
        test_buttons_layout.addWidget(self.test_deepseek_btn)
        test_buttons_layout.addStretch()
        
        test_layout.addLayout(test_buttons_layout)
        
        # Test results display
        self.test_results_text = QTextEdit()
        self.test_results_text.setMaximumHeight(100)
        self.test_results_text.setReadOnly(True)
        self.test_results_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Courier New', monospace;
                font-size: 11px;
            }
        """)
        self.test_results_text.setPlaceholderText("Click test buttons to check connections...")
        test_layout.addWidget(self.test_results_text)
        
        content_layout.addWidget(test_group)
        
        # Current Settings Display
        current_group = QGroupBox("Current Settings")
        current_group.setStyleSheet(endpoints_group.styleSheet())
        current_layout = QVBoxLayout(current_group)
        
        self.current_settings_text = QTextEdit()
        self.current_settings_text.setMaximumHeight(120)
        self.current_settings_text.setReadOnly(True)
        self.current_settings_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Courier New', monospace;
                font-size: 11px;
            }
        """)
        current_layout.addWidget(self.current_settings_text)
        
        content_layout.addWidget(current_group)
        
        # Add content widget to scroll area
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Reset
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.StandardButton.Reset).clicked.connect(self.reset_to_defaults)
        
        main_layout.addWidget(button_box)
        
        self.setLayout(main_layout)
        
        # Connect signals for real-time updates
        self.connect_signals()
        
    def connect_signals(self):
        """Connect signals for real-time updates."""
        # Connect all URL edit fields to update display
        url_edits = [
            self.ollama_url_edit, self.lmstudio_url_edit, self.deepseek_url_edit,
            self.openrouter_url_edit, self.groq_url_edit, self.grok_url_edit
        ]

        for edit in url_edits:
            edit.textChanged.connect(self.update_current_settings_display)

        # Connect context management controls
        self.context_management_checkbox.stateChanged.connect(self.update_current_settings_display)
        self.context_strategy_combo.currentTextChanged.connect(self.update_current_settings_display)
        
    def load_current_settings(self):
        """Load current settings from general_settings.json."""
        try:
            # Load current settings from settings manager
            self.ollama_url_edit.setText(settings_manager.get_ollama_url())
            self.lmstudio_url_edit.setText(settings_manager.get_lmstudio_url())
            self.deepseek_url_edit.setText(settings_manager.get_deepseek_url())
            self.openrouter_url_edit.setText(settings_manager.get_openrouter_url())
            self.groq_url_edit.setText(settings_manager.get_groq_url())
            self.grok_url_edit.setText(settings_manager.get_grok_url())

            # Load context management settings from config_manager
            context_management_enabled = config_manager.get('AGENT_CONTEXT_MANAGEMENT', True)
            context_strategy = config_manager.get('AGENT_CONTEXT_STRATEGY', 'intelligent_truncation')

            self.context_management_checkbox.setChecked(context_management_enabled)

            # Set the combo box to the current strategy
            strategy_index = self.context_strategy_combo.findText(context_strategy)
            if strategy_index >= 0:
                self.context_strategy_combo.setCurrentIndex(strategy_index)

            self.update_current_settings_display()
        except Exception as e:
            logger.error(f"Error loading current settings: {e}")
    
    def update_current_settings_display(self):
        """Update the current settings display."""
        settings = self.get_current_settings()
        display_text = f"""Current Configuration:

API Endpoints:
• Ollama Base URL: {settings['ollama_base_url']}
• LM Studio Base URL: {settings['lmstudio_base_url']}
• DeepSeek Base URL: {settings['deepseek_base_url']}
• OpenRouter Base URL: {settings['openrouter_base_url']}
• Groq Base URL: {settings['groq_base_url']}
• Grok Base URL: {settings['grok_base_url']}

Context Management:
• Enabled: {settings['context_management_enabled']}
• Strategy: {settings['context_strategy']}"""

        self.current_settings_text.setPlainText(display_text)
    
    def get_current_settings(self):
        """Get current settings from UI."""
        return {
            'ollama_base_url': self.ollama_url_edit.text().strip(),
            'lmstudio_base_url': self.lmstudio_url_edit.text().strip(),
            'deepseek_base_url': self.deepseek_url_edit.text().strip(),
            'openrouter_base_url': self.openrouter_url_edit.text().strip(),
            'groq_base_url': self.groq_url_edit.text().strip(),
            'grok_base_url': self.grok_url_edit.text().strip(),
            'context_management_enabled': self.context_management_checkbox.isChecked(),
            'context_strategy': self.context_strategy_combo.currentText()
        }
    
    def test_connection(self, service):
        """Test connection to a specific service."""
        try:
            if service == "ollama":
                url = self.ollama_url_edit.text().strip()
                if not url:
                    url = "http://localhost:11434"
                test_url = f"{url.rstrip('/')}/api/tags"
                service_name = "Ollama"
                
            elif service == "lmstudio":
                url = self.lmstudio_url_edit.text().strip()
                if not url:
                    url = "http://localhost:1234/v1"
                test_url = f"{url.rstrip('/')}/models"
                service_name = "LM Studio"
                
            elif service == "deepseek":
                url = self.deepseek_url_edit.text().strip()
                if not url:
                    url = "https://api.deepseek.com"
                test_url = f"{url.rstrip('/')}/models"
                service_name = "DeepSeek"
                
            else:
                self.test_results_text.append(f"❌ Unknown service: {service}")
                return
            
            # Test the connection
            response = requests.get(test_url, timeout=5)
            
            if response.status_code == 200:
                result = f"✅ {service_name} connection successful"
                if service in ["ollama", "lmstudio"]:
                    try:
                        data = response.json()
                        if service == "ollama" and "models" in data:
                            model_count = len(data["models"])
                            result += f" ({model_count} models available)"
                        elif service == "lmstudio" and "data" in data:
                            model_count = len(data["data"])
                            result += f" ({model_count} models available)"
                    except:
                        pass
            else:
                result = f"❌ {service_name} connection failed (HTTP {response.status_code})"
            
            self.test_results_text.append(result)
            
        except requests.exceptions.ConnectionError:
            self.test_results_text.append(f"❌ {service_name} connection failed (Connection Error)")
        except requests.exceptions.Timeout:
            self.test_results_text.append(f"❌ {service_name} connection failed (Timeout)")
        except Exception as e:
            self.test_results_text.append(f"❌ {service_name} connection failed: {str(e)}")
    
    def reset_to_defaults(self):
        """Reset to default settings."""
        self.ollama_url_edit.setText("http://localhost:11434")
        self.lmstudio_url_edit.setText("http://localhost:1234/v1")
        self.deepseek_url_edit.setText("https://api.deepseek.com")
        self.openrouter_url_edit.setText("https://openrouter.ai/api/v1")
        self.groq_url_edit.setText("https://api.groq.com/openai/v1")
        self.grok_url_edit.setText("https://api.x.ai/v1")

        # Reset context management to defaults
        self.context_management_checkbox.setChecked(True)
        self.context_strategy_combo.setCurrentText("intelligent_truncation")

        self.test_results_text.clear()
        self.test_results_text.setPlaceholderText("Click test buttons to check connections...")
    
    def accept(self):
        """Save settings when OK is clicked."""
        try:
            settings = self.get_current_settings()

            # Validate URLs (basic validation) - skip context management settings
            url_settings = {k: v for k, v in settings.items()
                          if k.endswith('_url') and v}
            for key, url in url_settings.items():
                if not (url.startswith('http://') or url.startswith('https://')):
                    QMessageBox.warning(
                        self,
                        "Invalid URL",
                        f"Please enter a valid URL for {key.replace('_', ' ').title()}. "
                        "URLs should start with http:// or https://"
                    )
                    return

            # Update settings manager with URL settings
            url_only_settings = {k: v for k, v in settings.items() if k.endswith('_url')}
            settings_manager.general_settings.update(url_only_settings)
            settings_manager.save_general_settings()

            # Save context management settings to config_manager
            config_manager.set('AGENT_CONTEXT_MANAGEMENT', settings['context_management_enabled'])
            config_manager.set('AGENT_CONTEXT_STRATEGY', settings['context_strategy'])
            config_manager.save_config()

            # Emit signal with all settings
            self.settings_changed.emit(settings)
            
            QMessageBox.information(
                self,
                "Settings Saved",
                "General settings have been saved successfully. "
                "You may need to restart the application for some changes to take effect."
            )
            
            super().accept()
            
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}") 