"""
File Handler - Manages file operations for the application
"""
import os
import json
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from py_to_pdf_converter import py_to_pdf

class FileHandler:
    def __init__(self, main_window):
        self.main_window = main_window
        self.loaded_file_content = ""
    
    def load_file(self):
        """Load a file into the input prompt"""
        options = QFileDialog.Option.ReadOnly
        file_name, _ = QFileDialog.getOpenFileName(
            self.main_window, 
            "Select File", 
            "", 
            "All Files (*)", 
            options=options
        )
        
        if file_name:
            try:
                with open(file_name, 'r', encoding='utf-8') as file:
                    self.loaded_file_content = file.read()
                self.main_window.input_prompt.setPlainText(self.loaded_file_content)
                self.main_window.terminal_console.append(f"File '{os.path.basename(file_name)}' loaded successfully.")
            except Exception as e:
                self.main_window.terminal_console.append(f"Error loading file: {str(e)}")
    
    def save_to_json(self):
        """Save the current configuration to a JSON file"""
        config = {
            'agent_count': self.main_window.agent_count.value(),
            'general_instructions': self.main_window.general_instructions.toPlainText(),
            'knowledge_base_path': self.main_window.rag_handler.get_knowledge_base_path(),
            'agents': []
        }

        for agent_config in self.main_window.agent_configs:
            config['agents'].append({
                'provider': agent_config.provider_combo.currentText(),
                'model': agent_config.model_combo.currentText(),
                'instructions': agent_config.instructions.toPlainText(),
                'thinking_enabled': agent_config.get_thinking_enabled()
            })

        options = QFileDialog.Option.DontUseNativeDialog
        file_name, _ = QFileDialog.getSaveFileName(
            self.main_window, 
            "Save Configuration", 
            "", 
            "JSON Files (*.json)", 
            options=options
        )
        
        if file_name:
            try:
                with open(file_name, 'w', encoding='utf-8') as file:
                    json.dump(config, file, indent=4)
                self.main_window.terminal_console.append(f"Configuration saved to '{os.path.basename(file_name)}'.")
            except Exception as e:
                self.main_window.terminal_console.append(f"Error saving configuration: {str(e)}")
    
    def load_from_json(self):
        """Load configuration from a JSON file"""
        options = QFileDialog.Option.ReadOnly
        file_name, _ = QFileDialog.getOpenFileName(
            self.main_window, 
            "Load Configuration", 
            "", 
            "JSON Files (*.json)", 
            options=options
        )

        if not file_name:
            return

        try:
            with open(file_name, 'r', encoding='utf-8') as file:
                config = json.load(file)

            # Validate required fields
            required_fields = ['agent_count', 'general_instructions', 'agents']
            if not all(field in config for field in required_fields):
                raise ValueError("Invalid configuration file: missing required fields")

            # Update agent count first
            agent_count = config.get('agent_count', 1)
            if not isinstance(agent_count, int) or agent_count < 1:
                raise ValueError("Invalid agent count")

            self.main_window.agent_count.setValue(agent_count)  # This triggers update_agent_config

            # Set general instructions
            general_instructions = config.get('general_instructions', '')
            self.main_window.general_instructions.setPlainText(general_instructions)

            # Handle knowledge base path if present
            kb_path = config.get('knowledge_base_path')
            if kb_path:
                reply = QMessageBox.question(
                    self.main_window,
                    'Knowledge Base Path',
                    f'Use saved knowledge base path:\n{kb_path}\n\nWould you like to use this path or select a new one?',
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )

                if reply == QMessageBox.StandardButton.No:
                    new_path = QFileDialog.getExistingDirectory(
                        self.main_window,
                        "Select Knowledge Base Directory",
                        "",
                        QFileDialog.Option.ShowDirsOnly
                    )
                    if new_path:
                        kb_path = new_path
                    else:
                        kb_path = None

                if kb_path:
                    try:
                        self.main_window.rag_handler.set_knowledge_base_path(kb_path)
                        self.main_window.terminal_console.append(f"Knowledge base path set to: {kb_path}")
                    except Exception as e:
                        self.main_window.terminal_console.append(f"Error setting knowledge base path: {str(e)}")

            # Update agent configurations
            agents_data = config.get('agents', [])
            for idx, agent_data in enumerate(agents_data):
                if idx < len(self.main_window.agent_configs):
                    try:
                        agent_config = self.main_window.agent_configs[idx]

                        # Get values with defaults
                        provider = agent_data.get('provider', 'OpenAI')
                        model = agent_data.get('model', 'gpt-4')
                        instructions = agent_data.get('instructions', '')
                        thinking_enabled = agent_data.get('thinking_enabled', False)

                        # Get available providers from combo box
                        available_providers = [agent_config.provider_combo.itemText(i)
                                            for i in range(agent_config.provider_combo.count())]

                        # Update provider if it's available
                        if provider in available_providers:
                            agent_config.provider_combo.setCurrentText(provider)

                            # Wait for the model list to update
                            from PyQt6.QtCore import QTimer
                            QTimer.singleShot(100, lambda ac=agent_config, m=model, t=thinking_enabled:
                                self._update_model_and_thinking_selection(ac, m, t))

                        # Set instructions
                        agent_config.instructions.setPlainText(instructions)

                    except Exception as e:
                        self.main_window.terminal_console.append(f"Error configuring agent {idx + 1}: {str(e)}")

            self.main_window.terminal_console.append(
                f"Configuration loaded successfully from '{os.path.basename(file_name)}'")

        except json.JSONDecodeError as e:
            self.main_window.terminal_console.append(f"Error: Invalid JSON file format - {str(e)}")
            QMessageBox.critical(self.main_window, "Error", "Invalid JSON file format")
        except ValueError as e:
            self.main_window.terminal_console.append(f"Error: {str(e)}")
            QMessageBox.critical(self.main_window, "Error", str(e))
        except Exception as e:
            self.main_window.terminal_console.append(f"Error loading configuration: {str(e)}")
            QMessageBox.critical(self.main_window, "Error", f"Failed to load configuration: {str(e)}")
    
    def _update_model_and_thinking_selection(self, agent_config, model, thinking_enabled):
        """Helper method to update model and thinking selection after provider update"""
        available_models = [agent_config.model_combo.itemText(i)
                        for i in range(agent_config.model_combo.count())]
        if model in available_models:
            agent_config.model_combo.setCurrentText(model)
            agent_config.set_thinking_enabled(thinking_enabled)
    
    def save_code_to_pdf(self):
        """Generate PDF of the current codebase"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # Go up one directory to get the main directory
            main_dir = os.path.dirname(current_dir)
            pdf_path = py_to_pdf(
                directory=main_dir,
                archive_dir='code_archives',
                force=True
            )
            if pdf_path:
                self.main_window.terminal_console.append(f"Code archived to PDF: {pdf_path}")
            else:
                self.main_window.terminal_console.append("No PDF was created")
        except Exception as e:
            self.main_window.terminal_console.append(f"Error creating PDF: {str(e)}")
