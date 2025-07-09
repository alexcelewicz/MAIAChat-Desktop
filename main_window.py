# main_window.py - Streaming

import sys
from typing import List
from PyQt6.QtWidgets import (QApplication, QMainWindow, QMessageBox, QFileDialog,
                             QDialog, QMenu, QLabel)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QTextCursor

from agent_config import AgentConfig
from rag_handler import RAGHandler
from threading import Lock
from progress_dialog import ProgressDialog
from config_manager import ConfigManager
from pathlib import Path
from signal_manager import SignalManager
from knowledge_base import KnowledgeBaseDialog
from profile_dialog import ProfileDialog
from profile_manager import profile_manager, Profile, AgentProfile
from mcp_client import add_default_servers_if_empty
from api_key_manager import api_key_manager
from mcp_config_dialog import MCPConfigDialog, MCPExampleProfilesDialog
from py_to_pdf_converter import py_to_pdf
from conversation_manager import ConversationManager

# Import UI components
from ui.main_window_ui import MainWindowUI
from ui.text_formatter import TextFormatter

# Import handlers and managers
from handlers.conversation_handler import ConversationHandler
from handlers.file_handler import FileHandler
from handlers.format_response import FormatResponse
from managers.token_manager import TokenManager
from managers.worker_manager import WorkerManager

# Import token counter
try:
    from token_counter import token_counter
except ImportError:
    token_counter = None

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Basic initializations
        self.worker = None
        self.thread = None
        self.worker_lock = Lock()
        self.agent_configs: List[AgentConfig] = []
        self.knowledge_base_files: List[str] = []
        self.signals = SignalManager()
        self.knowledge_base_content = ""
        self.current_conversation_id = None
        self.conversation_history = []

        # Initialize token count label for status bar
        self.token_count_label = QLabel("Token Usage: Input+System: 0 | Output: 0 | Total: 0 | Cost: $0.0000 | Tokens/s: 0.0")

        # Create directories
        Path("conversation_history").mkdir(exist_ok=True)
        Path("mcp_config").mkdir(exist_ok=True)

        # Initialize managers and handlers
        self.config_manager = ConfigManager()

        # Initialize API key manager with config
        api_key_manager.load_api_keys(self.config_manager.config)

        # Check for missing required API keys
        self.missing_keys_info = self.config_manager.missing_required_api_keys

        # Initialize RAG handler lazily (only when needed)
        self._rag_handler = None

        # Add default MCP servers
        add_default_servers_if_empty()

        # Initialize specialized managers and handlers
        self.worker_manager = WorkerManager(self)
        self.text_formatter = TextFormatter()
        self.conversation_manager = ConversationManager()  # Initialize conversation manager

        # Set the maximum response context size from config
        max_context = self.config_manager.get_max_response_context()
        self.conversation_manager.set_max_response_context(max_context)

        self.conversation_handler = ConversationHandler(self)
        self.file_handler = FileHandler(self)
        self.format_response = FormatResponse(self)
        self.token_manager = TokenManager(self)

        # Initialize UI
        self.ui = MainWindowUI(self)

        # Set up agent configurations
        self.setup_agent_configs()

        # Set up signals
        self.setup_signals()

        # Update RAG status display
        self.update_rag_status()

        # Log missing API keys to console instead of showing popup
        if self.missing_keys_info:
            missing_keys_str = ", ".join(self.missing_keys_info)
            self.terminal_console.append(f"Warning: The following required API keys are missing: {missing_keys_str}. Some features may be limited.")

        # Auto-load last used profile if available
        self.auto_load_last_profile()

    def auto_load_last_profile(self):
        """Automatically load the last used profile on startup."""
        try:
            last_profile_name = self.config_manager.get('LAST_PROFILE_NAME')
            last_profile_is_example = self.config_manager.get('LAST_PROFILE_IS_EXAMPLE', False)
            
            if last_profile_name:
                # Try to load the last used profile
                profile = profile_manager.load_profile(last_profile_name, last_profile_is_example)
                if profile:
                    self.load_profile(profile, save_as_last=False)  # Don't save as last to avoid recursion
                    profile_type = "example" if last_profile_is_example else "user"
                    self.terminal_console.append(f"Auto-loaded last used profile: {last_profile_name} ({profile_type})")
                else:
                    # Profile not found, clear the saved reference
                    self.config_manager.remove('LAST_PROFILE_NAME', save=False)
                    self.config_manager.remove('LAST_PROFILE_IS_EXAMPLE', save=False)
                    self.config_manager.save_config()
                    self.terminal_console.append(f"Last used profile '{last_profile_name}' not found. Cleared from settings.")
        except Exception as e:
            self.terminal_console.append(f"Error auto-loading last profile: {str(e)}")

    @property
    def rag_handler(self):
        """Lazy initialization of RAG handler - only creates it when first accessed."""
        if self._rag_handler is None:
            try:
                self.terminal_console.append("Initializing RAG handler on first use...")
                self._rag_handler = RAGHandler(
                    persist_directory="./knowledge_base",
                    use_openai=False,  # Set to False to use Sentence Transformers
                    embedding_model="all-mpnet-base-v2",
                    dimension=768,  # Updated dimension for all-mpnet-base-v2
                    chunk_size=500,
                    chunk_overlap=50
                )
                self.terminal_console.append("RAG handler initialized successfully!")
            except Exception as e:
                error_msg = f"Failed to initialize RAG handler: {str(e)}"
                self.terminal_console.append(f"Error: {error_msg}")
                QMessageBox.critical(self, "RAG Error", error_msg)
                # Return a mock RAG handler that doesn't crash the app
                self._rag_handler = None
                raise
        return self._rag_handler

    def is_rag_needed(self) -> bool:
        """Check if any agents have RAG enabled."""
        try:
            for agent_config in self.agent_configs:
                if hasattr(agent_config, 'get_rag_enabled') and agent_config.get_rag_enabled():
                    return True
            return False
        except Exception as e:
            self.terminal_console.append(f"Error checking if RAG is needed: {str(e)}")
            return False

    def show_progress_dialog(self, title: str, message: str) -> ProgressDialog:
        progress_dialog = ProgressDialog(title, message, self)
        progress_dialog.show()
        return progress_dialog

    def setup_agent_configs(self):
        for agent_config in self.agent_configs:
            agent_config.configuration_changed.connect(self.update_worker_configuration)

    def update_worker_configuration(self):
        if getattr(self, 'worker', None) is not None:
            current_agents = []
            for agent_config in self.agent_configs:
                current_agents.append({
                    'agent_number': agent_config.agent_number,
                    'provider': agent_config.provider_combo.currentText(),
                    'model': agent_config.model_combo.currentText(),
                    'instructions': agent_config.instructions.toPlainText(),
                    'token_mode': agent_config.get_token_mode(),
                    'manual_max_tokens': agent_config.get_manual_max_tokens()
                })
            self.worker.agents = current_agents

    def select_knowledge_base(self):
        options = QFileDialog.Option.DontUseNativeDialog
        directory = QFileDialog.getExistingDirectory(self, "Select Knowledge Base Directory", "", options=options)
        if directory:
            try:
                if self.rag_handler.set_knowledge_base_path(directory):
                    self.terminal_console.append(f"Knowledge base path set to: {directory}")
                else:
                    self.terminal_console.append("Failed to set knowledge base path")
            except Exception as e:
                self.terminal_console.append(f"Error setting knowledge base path: {str(e)}")

    def handle_error(self, error_message):
        self.terminal_console.append(f"Error: {error_message}")
        QMessageBox.critical(self, "Error", error_message)

    def show_mcp_dialog(self):
        """Show the MCP configuration dialog."""
        dialog = MCPConfigDialog(self)
        dialog.exec()

    def show_mcp_example_profiles_dialog(self):
        """Show the MCP example profiles dialog."""
        dialog = MCPExampleProfilesDialog(self)
        dialog.exec()

    def setup_signals(self):
        """Setup signal connections."""
        self.signals.update_agents_discussion.connect(self.update_agents_discussion)
        self.signals.update_terminal_console.connect(self.update_terminal_console)
        self.signals.update_conversation_history.connect(self.update_conversation_history)
        self.signals.update_conversation_id.connect(self.update_conversation_id)
        self.signals.discussion_completed.connect(self.on_discussion_completed)
        self.signals.error.connect(self.handle_error)
        self.signals.token_generation_started.connect(self.on_token_generation_started)
        self.signals.token_generation_ended.connect(self.on_token_generation_ended)

    def update_token_display(self):
        """Update the token count display in the status bar, chat tab, and history tab"""
        self.token_manager.update_token_display()


    def clear_chat(self):
        self.unified_response.clear()
        self.conversation_history = []
        self.input_prompt.clear()



    @pyqtSlot(str)
    def show_error_message(self, message: str):
        self.terminal_console.append(f"Error: {message}")
        QMessageBox.critical(self, "Error", message)

    @pyqtSlot(str)
    def show_success_message(self, message: str):
        self.terminal_console.append(f"Success: {message}")

    @pyqtSlot(int)
    def update_progress(self, value: int):
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setValue(value)



    def refresh_conversation_list(self):
        """Refresh the conversation list"""
        self.conversation_handler.refresh_conversation_list()

    def show_conversation_context_menu(self, position):
        """Show context menu for conversation list"""
        item = self.conversation_list.itemAt(position)
        if not item:
            return

        menu = QMenu()
        load_action = menu.addAction("Load Conversation")
        delete_action = menu.addAction("Delete Conversation")

        action = menu.exec(self.conversation_list.mapToGlobal(position))

        if action == load_action:
            self.load_selected_conversation()
        elif action == delete_action:
            self.delete_selected_conversation()

    def load_selected_conversation(self):
        """Load the selected conversation"""
        self.conversation_handler.load_selected_conversation()

    def delete_selected_conversation(self):
        """Delete the selected conversation"""
        self.conversation_handler.delete_selected_conversation()

    def delete_all_conversations(self):
        """Delete all conversations"""
        self.conversation_handler.delete_all_conversations()


    def save_api_keys(self):
        """Save API keys to configuration"""
        for key_name, input_field in self.api_inputs.items():
            # Check if the input field is QLineEdit (new implementation) or QTextEdit (old implementation)
            from PyQt6.QtWidgets import QLineEdit
            if isinstance(input_field, QLineEdit):
                value = input_field.text().strip()
            else:
                value = input_field.toPlainText().strip()

            if value:
                self.config_manager.set_api_key(key_name, value)
                # Also update the API key manager
                api_key_manager.set_api_key(key_name, value)
            else:
                self.config_manager.remove_api_key(key_name)

        # Save maximum response context size
        if hasattr(self, 'max_context_input'):
            max_context = self.max_context_input.value()
            self.config_manager.set_max_response_context(max_context)
            # Update the conversation manager with the new value
            self.conversation_manager.set_max_response_context(max_context)

        # Save configuration
        self.config_manager.save_config()

        # Load API keys into the API key manager
        api_key_manager.load_api_keys(self.config_manager.config)

        QMessageBox.information(self, "Success", "Settings have been saved successfully!")


    def save_code_to_pdf(self):
        """Generate PDF of the current codebase"""
        self.file_handler.save_code_to_pdf()

    def show_profiles_dialog(self):
        """Show the profiles dialog to load example profiles"""
        dialog = ProfileDialog(self)
        dialog.profile_selected.connect(self.load_profile)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Check if user wants to save current configuration
            if hasattr(dialog, 'profile_name'):
                self.save_current_profile(dialog.profile_name, dialog.profile_description)

    def load_profile(self, profile, save_as_last=True):
        """Load a profile into the UI"""
        try:
            # Update agent count
            self.agent_count.setValue(len(profile.agents))

            # Set general instructions
            self.general_instructions.setPlainText(profile.general_instructions)

            # Configure each agent
            for i, agent_profile in enumerate(profile.agents):
                if i < len(self.agent_configs):
                    agent_config = self.agent_configs[i]

                    # Set provider
                    agent_config.provider_combo.setCurrentText(agent_profile.provider)

                    # Set model (after provider to ensure model list is updated)
                    agent_config.update_models(agent_profile.provider)
                    agent_config.model_combo.setCurrentText(agent_profile.model)

                    # Set instructions
                    agent_config.instructions.setPlainText(agent_profile.instructions)
                    
                    # Set thinking enabled if available
                    if hasattr(agent_profile, 'thinking_enabled'):
                        if hasattr(agent_config, 'set_thinking_enabled'):
                            agent_config.set_thinking_enabled(agent_profile.thinking_enabled)
                    # Set per-agent toggles
                    if hasattr(agent_profile, 'internet_enabled'):
                        agent_config.set_internet_enabled(agent_profile.internet_enabled)
                    if hasattr(agent_profile, 'rag_enabled'):
                        agent_config.set_rag_enabled(agent_profile.rag_enabled)
                    if hasattr(agent_profile, 'mcp_enabled'):
                        agent_config.set_mcp_enabled(agent_profile.mcp_enabled)

            # Save as last used profile if requested
            if save_as_last:
                self.save_last_used_profile(profile)

            self.terminal_console.append(f"Loaded profile: {profile.name}")

        except Exception as e:
            self.terminal_console.append(f"Error loading profile: {str(e)}")
            QMessageBox.warning(self, "Error", f"Failed to load profile: {str(e)}")

    def save_last_used_profile(self, profile):
        """Save the profile as the last used profile for auto-loading."""
        try:
            # Determine if this is an example profile by checking if it exists in example_profiles
            is_example = False
            example_profiles = profile_manager.get_profile_list()
            for name, desc, is_ex in example_profiles:
                if name == profile.name and is_ex:
                    is_example = True
                    break
            
            # Save to configuration
            self.config_manager.set('LAST_PROFILE_NAME', profile.name, save=False)
            self.config_manager.set('LAST_PROFILE_IS_EXAMPLE', is_example, save=False)
            self.config_manager.save_config()
            
        except Exception as e:
            self.terminal_console.append(f"Error saving last used profile: {str(e)}")

    def save_current_profile(self, name, description):
        """Save the current configuration as a profile"""
        try:
            # Create agent profiles
            agents = []
            for agent_config in self.agent_configs:
                agent_profile = AgentProfile(
                    provider=agent_config.provider_combo.currentText(),
                    model=agent_config.model_combo.currentText(),
                    instructions=agent_config.instructions.toPlainText(),
                    agent_number=agent_config.agent_number,
                    thinking_enabled=agent_config.get_thinking_enabled(),
                    internet_enabled=agent_config.get_internet_enabled(),
                    rag_enabled=agent_config.get_rag_enabled(),
                    mcp_enabled=agent_config.get_mcp_enabled()
                )
                agents.append(agent_profile)

            # Create profile
            profile = Profile(
                name=name,
                description=description,
                general_instructions=self.general_instructions.toPlainText(),
                agents=agents
            )

            # Save profile
            if profile_manager.save_profile(profile):
                self.terminal_console.append(f"Saved profile: {name}")
            else:
                self.terminal_console.append(f"Failed to save profile: {name}")
                QMessageBox.warning(self, "Error", f"Failed to save profile: {name}")

        except Exception as e:
            self.terminal_console.append(f"Error saving profile: {str(e)}")
            QMessageBox.warning(self, "Error", f"Failed to save profile: {str(e)}")

    @pyqtSlot(int)
    def update_agent_config(self, count):
        # Clear existing agent configs
        for i in reversed(range(self.agent_config_layout.count())):
            widget = self.agent_config_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        self.agent_configs = []

        # Add new agent configs
        for i in range(count):
            agent_config = AgentConfig(i + 1)  # Only pass agent_number
            self.agent_configs.append(agent_config)
            self.agent_config_layout.addWidget(agent_config)

        # Update instructions for all agents to reflect new total
        for agent_config in self.agent_configs:
            agent_config.update_total_agents(count)

    def send_prompt(self):
        """Start a new conversation."""
        # Clear history for new conversation
        self.conversation_history = []
        prompt = self.input_prompt.toPlainText()
        if not prompt.strip():
            QMessageBox.warning(self, "Input Error", "Please enter a prompt.")
            return

        # Reset token counter for new conversation if available
        if token_counter:
            token_counter.reset_session()
            self.update_token_display()

        # Clear previous conversation display
        self.unified_response.clear()

        # Start the worker thread via WorkerManager
        self.toggle_input_buttons(False)
        # Reset current conversation ID for new conversation
        self.current_conversation_id = None
        self.worker_manager.start_worker_thread(prompt)

    def send_follow_up(self):
        """Continue existing conversation."""
        follow_up_prompt = self.input_prompt.toPlainText()
        if not follow_up_prompt.strip():
            QMessageBox.warning(self, "Input Error", "Please enter a follow-up question.")
            return

        # Reset token counter for follow-up if available
        # This ensures the tokens/s counter is reset for each new message
        if token_counter:
            token_counter.reset_session()
            self.update_token_display()

        # Use the current conversation ID if available, otherwise find the most recent one
        current_conversation_id = self.current_conversation_id

        if not current_conversation_id:
            # Find the most recent conversation file
            history_dir = Path("conversation_history")

            if history_dir.exists():
                conversation_files = sorted(
                    history_dir.glob("conversation_*.json"),
                    key=lambda x: x.stat().st_mtime,
                    reverse=True
                )
                if conversation_files:
                    current_conversation_id = conversation_files[0].stem.replace('conversation_', '')

        if not current_conversation_id:
            QMessageBox.warning(
                self,
                "No Active Conversation",
                "No previous conversation found. Starting a new conversation instead."
            )
            self.send_prompt()
            return

        # Load the existing conversation
        if not self.conversation_manager.load_conversation(current_conversation_id):
            # Try creating a new conversation manager and loading the conversation
            conversation_manager = ConversationManager()
            if conversation_manager.load_conversation(current_conversation_id):
                # Copy the loaded conversation to our main conversation manager
                self.conversation_manager.current_conversation = conversation_manager.current_conversation
            else:
                QMessageBox.warning(self, "Error", f"Failed to load conversation {current_conversation_id}")
                return

        # Update conversation history from the loaded conversation
        self.conversation_history = [
            f"{msg['role']}: {msg['content']}"
            for msg in self.conversation_manager.current_conversation["messages"]
        ]

        # Start the worker thread via WorkerManager with the current conversation ID
        self.toggle_input_buttons(False)
        self.worker_manager.start_worker_thread(follow_up_prompt, conversation_id=current_conversation_id)

        # Also store it in the main window for future follow-ups
        self.current_conversation_id = current_conversation_id

    def toggle_input_buttons(self, enabled):
        self.send_btn.setEnabled(enabled)
        self.follow_up_btn.setEnabled(enabled)
        self.load_file_btn.setEnabled(enabled)
        self.knowledge_base_btn.setEnabled(enabled)

    def stop_agents(self):
        self.worker_manager.stop_worker()

    def clear_outputs(self):
        self.unified_response.clear()
        self.terminal_console.append("Cleared unified response.")


    def update_conversation_history(self, history):
        """Update the conversation history and display."""
        self.conversation_history = history
        # Optionally, update a UI element that displays conversation history
        self.terminal_console.append("Conversation history updated.")

    @pyqtSlot(str, int, str, bool)
    def update_agents_discussion(self, text: str, agent_number: int, model_name: str, is_first_chunk: bool):
        """Update the unified response window with agent discussion text."""
        # Get the unified response panel from the main layout
        unified_panel = self.ui.main_layout.get_unified_response_panel()
        
        # Add the agent discussion content with proper formatting
        unified_panel.add_agent_discussion(text, agent_number, model_name, is_first_chunk)



    # Formatting methods have been moved to ui/text_formatter.py

    @pyqtSlot(str)
    def update_terminal_console(self, message):
        self.terminal_console.append(message)

    @pyqtSlot(str)
    def update_conversation_id(self, conversation_id: str):
        """Update the conversation ID display."""
        self.terminal_console.append(f"Conversation ID: {conversation_id}")

    @pyqtSlot(list)
    def update_conversation_history(self, history):
        """Update the conversation history display."""
        # This method can be used to update conversation history in the UI
        pass

    @pyqtSlot(float)
    def on_token_generation_started(self, timestamp: float):
        """Handle token generation started signal."""
        self.terminal_console.append(f"Token generation started at {timestamp}")

    @pyqtSlot(float, int)
    def on_token_generation_ended(self, timestamp: float, total_tokens: int):
        """Handle token generation ended signal."""
        self.terminal_console.append(f"Token generation ended at {timestamp}, total tokens: {total_tokens}")

    @pyqtSlot()
    def on_discussion_completed(self):
        """Handle discussion completed signal."""
        # Enable all input buttons
        self.toggle_input_buttons(True)
    def load_file(self):
        """Load a file into the input prompt"""
        self.file_handler.load_file()

    def access_knowledge_base(self):
        dialog = KnowledgeBaseDialog(self.rag_handler, self)
        dialog.exec()

        # Update the knowledge base path in the main window after dialog closes
        current_kb_path = self.rag_handler.get_knowledge_base_path()
        if current_kb_path:
            self.terminal_console.append(f"Current knowledge base path: {current_kb_path}")

    def open_rag_settings(self):
        """Open the RAG settings dialog."""
        try:
            from rag_settings_dialog import RAGSettingsDialog
            dialog = RAGSettingsDialog(self)
            dialog.settings_changed.connect(self.on_rag_settings_changed)
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.terminal_console.append("RAG settings updated successfully")
                self.update_rag_status()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open RAG settings: {str(e)}")
            self.terminal_console.append(f"Error opening RAG settings: {str(e)}")

    def open_general_settings(self):
        """Open the general settings dialog."""
        try:
            from general_settings_dialog import GeneralSettingsDialog
            dialog = GeneralSettingsDialog(self)
            dialog.settings_changed.connect(self.on_general_settings_changed)
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.terminal_console.append("General settings updated successfully")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open general settings: {str(e)}")
            self.terminal_console.append(f"Error opening general settings: {str(e)}")

    def on_rag_settings_changed(self, settings):
        """Handle RAG settings changes."""
        try:
            # Update the RAG handler with new settings
            if hasattr(self, 'rag_handler') and self.rag_handler:
                # Update the RAG handler's configuration
                self.rag_handler.ultra_safe_mode = settings['ultra_safe_mode']
                self.rag_handler.safe_retrieval_mode = settings['safe_retrieval_mode']
                self.rag_handler.embedding_device_setting = settings['embedding_device']
                
                # Log the changes
                self.terminal_console.append("RAG settings applied:")
                self.terminal_console.append(f"  - Ultra Safe Mode: {settings['ultra_safe_mode']}")
                self.terminal_console.append(f"  - Safe Retrieval Mode: {settings['safe_retrieval_mode']}")
                self.terminal_console.append(f"  - Embedding Device: {settings['embedding_device']}")
                self.terminal_console.append(f"  - Number of Results: {settings['n_results']}")
                self.terminal_console.append(f"  - Alpha: {settings['alpha']}")
                self.terminal_console.append(f"  - Importance Score: {settings['importance_score']}")
                self.terminal_console.append(f"  - Token Limit: {settings['token_limit']}")
            
            # Update the status display
            self.update_rag_status()
            
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Some RAG settings may not have been applied: {str(e)}")

    def on_general_settings_changed(self, settings):
        """Handle general settings changes."""
        try:
            # Log the changes
            self.terminal_console.append("General settings applied:")
            for key, value in settings.items():
                self.terminal_console.append(f"  - {key.replace('_', ' ').title()}: {value}")
            
            # Reload settings manager to pick up changes
            from model_settings import settings_manager
            settings_manager.load_general_settings()
            
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Some general settings may not have been applied: {str(e)}")

    def update_rag_status(self):
        """Update the RAG status display in the settings tab."""
        try:
            if hasattr(self, 'rag_status_label'):
                # Get current settings from config
                ultra_safe = self.config_manager.get('RAG_ULTRA_SAFE_MODE', False)
                safe_retrieval = self.config_manager.get('RAG_SAFE_RETRIEVAL_MODE', False)
                device = self.config_manager.get('EMBEDDING_DEVICE', 'cpu')
                
                # Determine status
                if ultra_safe and safe_retrieval:
                    status = "Ultra Safe Mode (Conservative)"
                    color = "#e74c3c"  # Red
                elif safe_retrieval:
                    status = "Safe Mode (Balanced)"
                    color = "#f39c12"  # Orange
                else:
                    status = "Performance Mode (Optimized)"
                    color = "#27ae60"  # Green
                
                # Update the label
                self.rag_status_label.setText(f"RAG Status: {status}")
                self.rag_status_label.setStyleSheet(f"""
                    color: {color};
                    font-size: 12px;
                    font-weight: bold;
                """)
                
        except Exception as e:
            if hasattr(self, 'rag_status_label'):
                self.rag_status_label.setText("RAG Status: Error")
                self.rag_status_label.setStyleSheet("color: #e74c3c; font-size: 12px;")

    def save_to_json(self):
        """Save the current configuration to a JSON file"""
        self.file_handler.save_to_json()


    def load_from_json(self):
        """Load configuration from a JSON file"""
        self.file_handler.load_from_json()

    def _update_model_selection(self, agent_config, model):
        """Helper method to update model selection after provider update"""
        available_models = [agent_config.model_combo.itemText(i)
                        for i in range(agent_config.model_combo.count())]
        if model in available_models:
            agent_config.model_combo.setCurrentText(model)

    def _get_current_agents(self):
        return [{
            'agent_number': agent_config.agent_number,
            'provider': agent_config.provider_combo.currentText(),
            'model': agent_config.model_combo.currentText(),
            'instructions': agent_config.instructions.toPlainText(),
            'thinking_enabled': agent_config.get_thinking_enabled(),
            'internet_enabled': agent_config.get_internet_enabled(),
            'rag_enabled': agent_config.get_rag_enabled(),
            'mcp_enabled': agent_config.get_mcp_enabled(),
            'token_mode': agent_config.get_token_mode(),
            'manual_max_tokens': agent_config.get_manual_max_tokens()
        } for agent_config in self.agent_configs]

    def closeEvent(self, event):
        # Cleanup the worker thread on application exit
        self.worker_manager.cleanup_worker()
        event.accept()

    def load_knowledge_base(self):
        options = QFileDialog.Option()
        files, _ = QFileDialog.getOpenFileNames(self, "Select Knowledge Base Files", "",
                                                "Text Files (*.txt);;All Files (*)", options=options)
        if files:
            try:
                # Add files to RAG system
                results = self.rag_handler.batch_add_files(files)

                # Update UI
                self.knowledge_base_label.setText(f"{len(files)} file(s) selected")

                # Show success/error messages
                success_count = sum(1 for result in results.values() if result)
                if success_count > 0:
                    QMessageBox.information(self, "Success", f"Successfully added {success_count} file(s) to knowledge base")
                if success_count < len(files):
                    QMessageBox.warning(self, "Warning", f"Failed to add {len(files) - success_count} file(s)")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load knowledge base: {str(e)}")

    def on_discussion_completed(self):
        # Enable all input buttons
        self.toggle_input_buttons(True)
        # Make sure the follow-up button is enabled
        self.follow_up_btn.setEnabled(True)
        # Clear worker thread reference
        self.worker_thread = None
