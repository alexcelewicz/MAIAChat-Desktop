# agent_config.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QTextEdit, QPushButton, QCheckBox, QSpinBox, QFrame, QLineEdit
from PyQt6.QtCore import pyqtSlot, pyqtSignal
import logging
import requests
import os
from typing import List, Optional
from instruction_templates import InstructionTemplates, MiscInstructions
from dataclasses import dataclass
from model_settings_dialog import ModelSettingsDialog
from model_settings import settings_manager
from custom_models_manager import custom_models_manager
from custom_model_dialog import CustomModelDialog
from model_manager import model_manager

# Import constants from centralized data registry
from data_registry import PROVIDERS, MODEL_MAPPINGS, DEFAULT_OLLAMA_MODELS, THINKING_CAPABLE_MODELS

@dataclass
class AgentConfiguration:
    agent_number: int
    provider: str
    model: str
    instructions: str
    thinking_enabled: bool = False
    internet_enabled: bool = False
    rag_enabled: bool = False
    mcp_enabled: bool = False
    token_mode: str = "dynamic"  # "dynamic" or "manual"
    manual_max_tokens: int = 4096  # Only used when token_mode is "manual"

class AgentConfig(QWidget):
    configuration_changed = pyqtSignal()

    def __init__(self, agent_number: int):
        super().__init__()
        self.agent_number: int = agent_number
        self.total_agents: int = 1  # Fixed: default to 1, will be set by update_total_agents
        self.agent_internet_enabled: bool = False
        self.agent_rag_enabled: bool = False
        self.agent_mcp_enabled: bool = False
        self.all_models_for_provider = [] # To store the complete list of models for the current provider
        self.initUI()

    def is_thinking_capable_model(self, provider: str, model: str) -> bool:
        """Check if the current provider/model combination supports thinking."""
        if provider in THINKING_CAPABLE_MODELS:
            return model in THINKING_CAPABLE_MODELS[provider]
        return False

    def update_thinking_visibility(self):
        """Update the visibility of the thinking checkbox based on current model."""
        provider = self.provider_combo.currentText()
        model = self.model_combo.currentText()
        
        if self.is_thinking_capable_model(provider, model):
            self.thinking_checkbox.setVisible(True)
            self.thinking_checkbox.setEnabled(True)
        else:
            self.thinking_checkbox.setVisible(False)
            self.thinking_checkbox.setChecked(False)
            self.thinking_enabled = False

    @pyqtSlot(str)
    def provider_changed(self, new_provider: str) -> None:
        self.update_models(new_provider)
        self.update_thinking_visibility()
        self.configuration_changed.emit()

    def model_changed(self):
        """Handle model selection change."""
        self.update_thinking_visibility()
        self.configuration_changed.emit()
        self.update_manual_tokens_from_model_settings()

    def thinking_toggled(self, checked: bool):
        """Handle thinking checkbox toggle."""
        self.thinking_enabled = checked
        self.configuration_changed.emit()

    def get_ollama_models(self) -> List[str]:
        """Fetch available models from Ollama server"""
        try:
            # Get base URL from settings manager
            ollama_base_url = settings_manager.get_ollama_url()
            ollama_api_tags_url = f"{ollama_base_url.rstrip('/')}/api/tags"
            
            response = requests.get(ollama_api_tags_url, timeout=5)
            if response.status_code == 200:
                models = [model['name'] for model in response.json().get('models', [])]
                return models if models else DEFAULT_OLLAMA_MODELS
            logging.warning(f"Failed to fetch Ollama models. Status code: {response.status_code}")
            return DEFAULT_OLLAMA_MODELS
        except requests.RequestException as e:
            logging.error(f"Error fetching Ollama models: {e}")
            return DEFAULT_OLLAMA_MODELS
        except Exception as e:
            logging.error(f"Unexpected error fetching Ollama models: {e}")
            return DEFAULT_OLLAMA_MODELS

    def get_lmstudio_models(self) -> List[str]:
        """Fetch available models from LM Studio server"""
        try:
            # Get base URL from settings manager
            lmstudio_base_url = settings_manager.get_lmstudio_url()
            lmstudio_models_url = f"{lmstudio_base_url.rstrip('/')}/models"
            
            response = requests.get(lmstudio_models_url, timeout=5)
            if response.status_code == 200:
                models_data = response.json()
                if models_data.get("data"):
                    return [model["id"] for model in models_data["data"]]
            logging.warning(f"Failed to fetch LM Studio models. Status code: {response.status_code}")
            return ["model_name"]  # Return default if no models found
        except requests.RequestException as e:
            logging.error(f"Error fetching LM Studio models: {e}")
            return ["model_name"]
        except Exception as e:
            logging.error(f"Unexpected error fetching LM Studio models: {e}")
            return ["model_name"]

    def get_requesty_models(self) -> List[str]:
        """Fetch available models from Requesty API"""
        try:
            from utils import get_requesty_models
            from config import config_manager
            # Use global config manager instead of load_config
            api_key = config_manager.get('REQUESTY_API_KEY', None)
            models = get_requesty_models(api_key)
            if models:
                return models
            else:
                logging.warning(f"No models returned from Requesty API.")
                return ["requesty-model"] # Fallback
        except Exception as e:
            logging.error(f"Error fetching Requesty models: {e}")
            return ["requesty-model"] # Fallback

    def get_groq_models(self) -> List[str]:
        """Get available models from Groq API"""
        try:
            from utils import get_groq_models
            from config import config_manager
            
            # Get API key from global config manager
            api_key = config_manager.get('GROQ_API_KEY', None)
            models = get_groq_models(api_key)
            
            if models:
                logging.info(f"Successfully fetched {len(models)} Groq models")
                return models
            else:
                logging.warning("No Groq models found or API error")
                return []
        except Exception as e:
            logging.error(f"Error fetching Groq models: {e}")
            return []

    def get_openrouter_models(self) -> List[str]:
        """Fetch available models from OpenRouter API"""
        try:
            from utils import get_openrouter_models
            from config import config_manager
            # Use global config manager instead of load_config
            api_key = config_manager.get('OPENROUTER_API_KEY', None)
            models = get_openrouter_models(api_key)
            if models:
                return models
            else:
                logging.warning(f"No models returned from OpenRouter API.")
                return ["openrouter-model"]
        except Exception as e:
            logging.error(f"Error fetching OpenRouter models: {e}")
            return ["openrouter-model"]

    def update_models(self, provider: str) -> None:
        """Update model list based on selected provider"""
        self.model_combo.clear()
        self.all_models_for_provider = [] # Clear the master list
        self.model_search.clear()  # Clear the search field

        try:
            # Get standard models
            standard_models = []
            if provider == "LM Studio":
                standard_models = self.get_lmstudio_models()
            elif provider == "OpenRouter":
                standard_models = self.get_openrouter_models()
            elif provider == "Requesty":
                standard_models = self.get_requesty_models()
            elif provider == "Groq":
                standard_models = self.get_groq_models()
            elif provider == "Ollama":
                standard_models = self.get_ollama_models()
            else:
                standard_models = MODEL_MAPPINGS.get(provider, [])
                if not standard_models:
                    logging.warning(f"No models found for provider: {provider}")

            # Get custom models and combine with standard models
            custom_models = custom_models_manager.get_models(provider)
            
            # The full list of models for the provider
            self.all_models_for_provider = [model for model in standard_models if not model_manager.is_model_disabled(provider, model)] + custom_models

            # Initially populate the combo box with the full list
            self.model_combo.clear()
            self.model_combo.addItems(self.all_models_for_provider)

            # If there are models, set the first one as default
            if self.all_models_for_provider:
                self.model_combo.setCurrentIndex(0)

            # After updating the model combo, set manual max tokens to the model's default
            self.update_manual_tokens_from_model_settings()
            
        except Exception as e:
            logging.error(f"Error updating models for provider {provider}: {e}")
            self.model_combo.clear()
        
        # Manually trigger a model change to update dependent UI elements
        self.model_changed()

    def filter_models(self, search_text: str):
        """Filter the models in the dropdown based on search input."""
        # When clearing the filter (text is empty), restore the full list
        if not search_text.strip():
            self.model_combo.clear()
            self.model_combo.addItems(self.all_models_for_provider)
            return

        # Find matching models from the master list (case-insensitive)
        search_lower = search_text.lower()
        matching_models = [model for model in self.all_models_for_provider if search_lower in model.lower()]

        # Update the dropdown with the filtered list
        current_selection = self.model_combo.currentText()
        self.model_combo.clear()
        self.model_combo.addItems(matching_models)
        
        # Try to maintain the current selection if it's still in the filtered list
        if current_selection in matching_models:
            self.model_combo.setCurrentText(current_selection)
        elif matching_models:
            self.model_combo.setCurrentIndex(0)

    def initUI(self) -> None:
        """Initialize the UI components for the agent configuration."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Agent color for styling
        agent_colors = ["#4A90E2", "#7ED321", "#F5A623", "#D0021B", "#9013FE", "#50E3C2", "#B8E986", "#4BD5EE"]
        agent_color = agent_colors[(self.agent_number - 1) % len(agent_colors)]
        
        # Create pastel background color
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        def rgb_to_hex(rgb):
            return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))
        
        # Convert to RGB, blend with white for pastel effect
        rgb = hex_to_rgb(agent_color)
        pastel_rgb = tuple(int(c * 0.3 + 255 * 0.7) for c in rgb)  # 30% original color, 70% white
        pastel_bg = rgb_to_hex(pastel_rgb)

        # Create a frame to wrap the entire agent config with colored border and subtle pastel background
        agent_frame = QFrame()
        agent_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        # Store the frame reference for dynamic styling
        self.agent_frame = agent_frame
        self.agent_color = agent_color
        self.pastel_bg = pastel_bg
        self.update_frame_styling()
        
        agent_frame_layout = QVBoxLayout(agent_frame)
        agent_frame_layout.setContentsMargins(6, 6, 6, 6)
        agent_frame_layout.setSpacing(6)  # Reduced spacing between elements

        self.provider_combo = QComboBox()
        self.provider_combo.addItems(PROVIDERS)
        self.provider_combo.currentTextChanged.connect(self.update_models)
        agent_frame_layout.addWidget(self.provider_combo)

        # Model search field
        search_layout = QHBoxLayout()
        search_layout.setSpacing(6)  # Compact spacing
        search_label = QLabel("Search Models:")
        search_label.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                color: {agent_color};
                font-weight: 500;
            }}
        """)
        search_layout.addWidget(search_label)
        
        self.model_search = QLineEdit()
        self.model_search.setPlaceholderText("Type to filter models...")
        self.model_search.setStyleSheet(f"""
            QLineEdit {{
                font-size: 12px;
                padding: 4px 8px;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                background-color: white;
            }}
            QLineEdit:focus {{
                border-color: {agent_color};
            }}
        """)
        self.model_search.textChanged.connect(self.filter_models)
        search_layout.addWidget(self.model_search)
        
        # Clear search button
        clear_search_btn = QPushButton("Clear")
        clear_search_btn.setStyleSheet(f"""
            QPushButton {{
                font-size: 11px;
                padding: 4px 8px;
                border: 1px solid {agent_color};
                border-radius: 4px;
                background-color: white;
                color: {agent_color};
            }}
            QPushButton:hover {{
                background-color: {agent_color};
                color: white;
            }}
        """)
        clear_search_btn.clicked.connect(lambda: self.model_search.clear())
        search_layout.addWidget(clear_search_btn)
        
        agent_frame_layout.addLayout(search_layout)

        # Model selection with settings and custom model buttons
        model_layout = QHBoxLayout()
        model_layout.setSpacing(6)  # Compact spacing

        self.model_combo = QComboBox()
        self.model_combo.currentIndexChanged.connect(self.model_changed)
        model_layout.addWidget(self.model_combo, 3)  # Give more space to the combo box

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(4)  # Compact spacing for buttons

        self.custom_models_btn = QPushButton("Manage Models")
        self.custom_models_btn.clicked.connect(self.show_custom_models_dialog)
        buttons_layout.addWidget(self.custom_models_btn)

        self.settings_btn = QPushButton("Settings")
        self.settings_btn.clicked.connect(self.show_model_settings)
        buttons_layout.addWidget(self.settings_btn)

        model_layout.addLayout(buttons_layout, 2)

        agent_frame_layout.addLayout(model_layout)

        # Thinking checkbox (initially hidden)
        self.thinking_checkbox = QCheckBox("Enable Thinking (for supported models)")
        self.thinking_checkbox.setVisible(False)
        self.thinking_checkbox.setToolTip("Enable thinking mode for models that support it (DeepSeek R1, Qwen 3)")
        self.thinking_checkbox.setStyleSheet(f"""
            QCheckBox {{
                font-size: 12px;
                color: {agent_color};
                font-weight: 500;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
            }}
            QCheckBox::indicator:unchecked {{
                border: 2px solid #ddd;
                background-color: white;
                border-radius: 3px;
            }}
            QCheckBox::indicator:checked {{
                border: 2px solid {agent_color};
                background-color: {agent_color};
                border-radius: 3px;
            }}
        """)
        self.thinking_checkbox.stateChanged.connect(self.thinking_toggled)
        agent_frame_layout.addWidget(self.thinking_checkbox)

        # New: Per-agent Internet, RAG, MCP checkboxes
        feature_h_layout = QHBoxLayout()
        feature_h_layout.setSpacing(8)  # Compact spacing for features

        self.internet_checkbox = QCheckBox("Enable Internet")
        self.internet_checkbox.setToolTip("Allow this agent to perform internet searches.")
        self.internet_checkbox.setStyleSheet(f"""
            QCheckBox {{
                font-size: 12px;
                color: {agent_color};
                font-weight: 500;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
            }}
            QCheckBox::indicator:unchecked {{
                border: 2px solid #ddd;
                background-color: white;
                border-radius: 3px;
            }}
            QCheckBox::indicator:checked {{
                border: 2px solid {agent_color};
                background-color: {agent_color};
                border-radius: 3px;
            }}
        """)
        self.internet_checkbox.stateChanged.connect(lambda state: self._update_feature_state('internet', state))
        feature_h_layout.addWidget(self.internet_checkbox)

        self.rag_checkbox = QCheckBox("Enable RAG")
        self.rag_checkbox.setToolTip("Allow this agent to access the knowledge base.")
        self.rag_checkbox.setStyleSheet(self.internet_checkbox.styleSheet()) # Reuse style
        self.rag_checkbox.stateChanged.connect(lambda state: self._update_feature_state('rag', state))
        feature_h_layout.addWidget(self.rag_checkbox)

        self.mcp_checkbox = QCheckBox("Enable MCP")
        self.mcp_checkbox.setToolTip("Allow this agent to use MCP (Model Context Protocol) servers.")
        self.mcp_checkbox.setStyleSheet(self.internet_checkbox.styleSheet()) # Reuse style
        self.mcp_checkbox.stateChanged.connect(lambda state: self._update_feature_state('mcp', state))
        feature_h_layout.addWidget(self.mcp_checkbox)

        agent_frame_layout.addLayout(feature_h_layout)

        # Token Settings Section
        token_settings_layout = QHBoxLayout()
        token_settings_layout.setSpacing(8)  # Compact spacing for token settings
        
        # Token Mode Selection
        token_mode_label = QLabel("Token Mode:")
        token_mode_label.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                color: {agent_color};
                font-weight: 500;
            }}
        """)
        token_settings_layout.addWidget(token_mode_label)
        
        self.token_mode_combo = QComboBox()
        self.token_mode_combo.addItems(["Dynamic", "Manual"])
        self.token_mode_combo.setCurrentText("Dynamic")
        self.token_mode_combo.setToolTip("Dynamic: Automatically calculate tokens based on input length\nManual: Use fixed token limit set below")
        self.token_mode_combo.setStyleSheet(f"""
            QComboBox {{
                font-size: 12px;
                padding: 4px 8px;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                background-color: white;
            }}
            QComboBox:focus {{
                border-color: {agent_color};
            }}
        """)
        self.token_mode_combo.currentTextChanged.connect(self.token_mode_changed)
        token_settings_layout.addWidget(self.token_mode_combo)
        
        # Manual Token Input
        manual_tokens_label = QLabel("Manual Max Tokens:")
        manual_tokens_label.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                color: {agent_color};
                font-weight: 500;
            }}
        """)
        token_settings_layout.addWidget(manual_tokens_label)
        
        self.manual_tokens_spin = QSpinBox()
        self.manual_tokens_spin.setRange(100, 100000)
        self.manual_tokens_spin.setValue(4096)
        self.manual_tokens_spin.setSingleStep(1024)
        self.manual_tokens_spin.setToolTip("Maximum tokens for output when using manual mode")
        self.manual_tokens_spin.setStyleSheet(f"""
            QSpinBox {{
                font-size: 12px;
                padding: 4px 8px;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                background-color: white;
            }}
            QSpinBox:focus {{
                border-color: {agent_color};
            }}
        """)
        self.manual_tokens_spin.valueChanged.connect(self.manual_tokens_changed)
        token_settings_layout.addWidget(self.manual_tokens_spin)
        
        # Initially disable manual tokens input since dynamic is default
        self.manual_tokens_spin.setEnabled(False)
        
        agent_frame_layout.addLayout(token_settings_layout)

        # Instructions section with collapsible header
        instructions_header_layout = QHBoxLayout()
        instructions_header_layout.setSpacing(8)  # Compact spacing
        
        instructions_label = QLabel(f"Agent {self.agent_number} Instructions:")
        instructions_label.setStyleSheet(f"""
            QLabel {{
                font-size: 13px;
                color: {agent_color};
                font-weight: bold;
                padding: 4px 0;
            }}
        """)
        instructions_header_layout.addWidget(instructions_label)
        
        # Collapse button for instructions
        self.instructions_collapse_btn = QPushButton()
        self.instructions_collapse_btn.setFixedSize(24, 24)
        self.instructions_collapse_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {agent_color};
                border: 1px solid {agent_color};
                border-radius: 12px;
                font-size: 14px;
                font-weight: bold;
                color: white;
            }}
            QPushButton:hover {{
                background-color: white;
                color: {agent_color};
                border: 2px solid {agent_color};
            }}
            QPushButton:pressed {{
                background-color: {pastel_bg};
            }}
        """)
        # Start collapsed by default, but will be updated based on total agents
        self.instructions_collapsed = True
        self.instructions_collapse_btn.setText("▶")  # Right arrow for collapsed
        self.instructions_collapse_btn.setToolTip("Click to expand/collapse instructions")
        self.instructions_collapse_btn.clicked.connect(self.toggle_instructions_collapse)
        instructions_header_layout.addWidget(self.instructions_collapse_btn)
        
        instructions_header_layout.addStretch()
        agent_frame_layout.addLayout(instructions_header_layout)

        self.instructions = QTextEdit()
        self.instructions.setPlaceholderText(f"Agent {self.agent_number} instructions and role")
        self.instructions.setStyleSheet(f"""
            QTextEdit {{
                background-color: white;
                color: #000000;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                padding: 12px;
                font-family: 'Segoe UI', 'Roboto', sans-serif;
                font-size: 13px;
                line-height: 1.5;
            }}
            QTextEdit:focus {{
                border: 1px solid {agent_color};
            }}
        """)
        # Start with instructions collapsed by default, will be updated based on total agents
        self.instructions.hide()
        agent_frame_layout.addWidget(self.instructions)

        # Add the agent frame to the main layout
        main_layout.addWidget(agent_frame)

        # Set default provider and model
        self.provider_combo.setCurrentText("Google GenAI")
        self.update_models("Google GenAI")
        self.model_combo.setCurrentText('gemini-2.0-pro-exp-02-05')

        # Set default role-based instructions
        self.set_default_instructions()

        # Connect signals
        self.provider_combo.currentTextChanged.connect(self.provider_changed)
        self.model_combo.currentTextChanged.connect(self.model_changed)

        # Update thinking visibility for initial model
        self.update_thinking_visibility()

        # In initUI, after setting default provider/model, also set manual tokens
        self.update_manual_tokens_from_model_settings()
        
        # Initialize instructions visibility based on total agents
        # Since total_agents starts as 1, show instructions for single agent
        if self.total_agents == 1:
            self.instructions.show()
            self.instructions_collapse_btn.setText("▼")  # Down arrow for expanded
            self.instructions_collapsed = False
        
        # Update frame styling based on initial state
        self.update_frame_styling_for_state()

    def set_default_instructions(self) -> None:
        """Set default instructions for the agent"""
        try:
            instructions = InstructionTemplates.get_agent_instructions(
                self.agent_number,
                self.total_agents,
                False  # Default to False, will be handled by global setting
            )
            self.instructions.setPlainText(instructions + "\n\n" + MiscInstructions.IMAGE_HANDLING)
        except Exception as e:
            logging.error(f"Error setting default instructions: {e}")
            self.instructions.setPlainText("Error loading instructions. Please check the logs.")

    def update_total_agents(self, total_agents: int) -> None:
        """Update the total number of agents and refresh instructions"""
        self.total_agents = total_agents
        self.set_default_instructions()
        
        # Update instructions visibility based on total agents
        # Show instructions for single agent, collapse for multiple agents
        if total_agents == 1:
            # Single agent: show instructions
            if self.instructions_collapsed:
                self.instructions.show()
                self.instructions_collapse_btn.setText("▼")  # Down arrow for expanded
                self.instructions_collapsed = False
                self.update_frame_styling_for_state()
        else:
            # Multiple agents: collapse instructions to save space
            if not self.instructions_collapsed:
                self.instructions.hide()
                self.instructions_collapse_btn.setText("▶")  # Right arrow for collapsed
                self.instructions_collapsed = True
                self.update_frame_styling_for_state()

    def update_frame_styling_for_state(self):
        """Update frame styling based on current collapse state."""
        if self.instructions_collapsed:
            # Collapsed state
            self.agent_frame.setMaximumHeight(16777215)  # Remove height constraint completely
            self.agent_frame.setStyleSheet(f"""
                QFrame {{
                    border: 2px solid {self.agent_color};
                    border-radius: 8px;
                    background-color: {self.pastel_bg};
                    padding: 6px;
                    margin: 2px 0 6px 0;
                }}
            """)
        else:
            # Expanded state
            self.agent_frame.setMaximumHeight(16777215)  # Remove height constraint
            self.agent_frame.setStyleSheet(f"""
                QFrame {{
                    border: 2px solid {self.agent_color};
                    border-radius: 8px;
                    background-color: {self.pastel_bg};
                    padding: 6px;
                    margin: 2px 0 8px 0;
                }}
            """)

    def show_model_settings(self) -> None:
        """Show the model settings dialog"""
        provider = self.provider_combo.currentText()
        model = self.model_combo.currentText()

        dialog = ModelSettingsDialog(provider, model, self)
        dialog.exec()

    def show_custom_models_dialog(self) -> None:
        """Show the custom models dialog"""
        provider = self.provider_combo.currentText()

        dialog = CustomModelDialog(provider, self)
        dialog.exec()

        # Always refresh the model list, even if the dialog was cancelled
        # This ensures any changes made to custom models are reflected
        self.update_models(self.provider_combo.currentText())

    def get_thinking_enabled(self) -> bool:
        """Get the current thinking enabled state."""
        return self.thinking_checkbox.isChecked() and self.thinking_checkbox.isVisible()

    def set_thinking_enabled(self, enabled: bool):
        """Set the thinking enabled state."""
        self.thinking_checkbox.setChecked(enabled)
        self.update_thinking_visibility() # Ensure visibility is updated

    def get_internet_enabled(self) -> bool:
        return self.internet_checkbox.isChecked()

    def set_internet_enabled(self, enabled: bool):
        self.internet_checkbox.setChecked(enabled)

    def get_rag_enabled(self) -> bool:
        return self.rag_checkbox.isChecked()

    def set_rag_enabled(self, enabled: bool):
        self.rag_checkbox.setChecked(enabled)

    def get_mcp_enabled(self) -> bool:
        return self.mcp_checkbox.isChecked()

    def set_mcp_enabled(self, enabled: bool):
        self.mcp_checkbox.setChecked(enabled)

    def get_token_mode(self) -> str:
        """Get the current token mode (dynamic or manual)."""
        return self.token_mode_combo.currentText().lower()

    def set_token_mode(self, mode: str):
        """Set the token mode (dynamic or manual)."""
        mode = mode.lower()
        if mode in ["dynamic", "manual"]:
            self.token_mode_combo.setCurrentText(mode.title())
            self.token_mode_changed(mode.title())

    def get_manual_max_tokens(self) -> int:
        """Get the manual max tokens value."""
        return self.manual_tokens_spin.value()

    def set_manual_max_tokens(self, tokens: int):
        """Set the manual max tokens value."""
        self.manual_tokens_spin.setValue(tokens)

    def token_mode_changed(self, mode: str):
        """Handle token mode change."""
        if mode.lower() == "manual":
            self.manual_tokens_spin.setEnabled(True)
        else:
            self.manual_tokens_spin.setEnabled(False)
        self.configuration_changed.emit()

    def manual_tokens_changed(self, value: int):
        """Handle manual tokens value change."""
        self.configuration_changed.emit()

    def _update_feature_state(self, feature: str, state: bool):
        """Update the state of a feature (Internet, RAG, MCP)"""
        if feature == 'internet':
            self.agent_internet_enabled = state
        elif feature == 'rag':
            self.agent_rag_enabled = state
        elif feature == 'mcp':
            self.agent_mcp_enabled = state
        self.configuration_changed.emit()

    def update_manual_tokens_from_model_settings(self):
        """Set manual max tokens to the current model's max_tokens from model settings."""
        provider = self.provider_combo.currentText()
        model = self.model_combo.currentText()
        from model_settings import settings_manager
        settings = settings_manager.get_settings(provider, model)
        if settings and hasattr(self, 'manual_tokens_spin'):
            self.manual_tokens_spin.setValue(settings.max_tokens)

    def toggle_instructions_collapse(self):
        """Toggle the collapse state of the instructions section."""
        if self.instructions_collapsed:
            self.instructions.show()
            self.instructions_collapse_btn.setText("▼")  # Down arrow for expanded
        else:
            self.instructions.hide()
            self.instructions_collapse_btn.setText("▶")  # Right arrow for collapsed
        
        self.instructions_collapsed = not self.instructions_collapsed
        self.update_frame_styling_for_state()
        self.configuration_changed.emit()

    def update_frame_styling(self):
        """Update the frame styling based on the current agent color and pastel background."""
        agent_frame = self.agent_frame
        agent_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        # Start with collapsed styling since instructions start collapsed, but no height constraint
        agent_frame.setMaximumHeight(16777215)  # Remove height constraint completely
        agent_frame.setStyleSheet(f"""
            QFrame {{
                border: 2px solid {self.agent_color};
                border-radius: 8px;
                background-color: {self.pastel_bg};
                padding: 6px;
                margin: 2px 0 6px 0;
            }}
        """)