import threading
import logging
from PyQt6.QtCore import Qt, QThread
from worker import Worker
import os

class WorkerManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.worker = None
        self.worker_thread = None

    def _setup_worker_connections(self):
        """Set up worker signal connections"""
        if not self.worker:
            return

        # Ensure we're using Qt.QueuedConnection for thread safety
        self.worker.update_agents_discussion_signal.connect(
            self.main_window.update_agents_discussion,
            type=Qt.ConnectionType.QueuedConnection
        )
        self.worker.update_terminal_console_signal.connect(
            self.main_window.update_terminal_console,
            type=Qt.ConnectionType.QueuedConnection
        )
        self.worker.discussion_completed_signal.connect(
            self.main_window.on_discussion_completed,
            type=Qt.ConnectionType.QueuedConnection
        )
        self.worker.error_signal.connect(
            self.main_window.handle_error,
            type=Qt.ConnectionType.QueuedConnection
        )
        # Connect the conversation ID signal
        self.worker.update_conversation_id_signal.connect(
            lambda conversation_id: setattr(self.main_window, 'current_conversation_id', conversation_id),
            type=Qt.ConnectionType.QueuedConnection
        )

    def _setup_worker(self, prompt, knowledge_base_content=None, conversation_id=None):
        # Check if any agent has RAG enabled before accessing RAG handler
        agents = self.main_window._get_current_agents()
        any_agent_has_rag = any(agent.get('rag_enabled', False) for agent in agents)
        
        # Only get indexed files if at least one agent has RAG enabled
        knowledge_base_files = []
        if any_agent_has_rag:
            # Only access rag_handler when actually needed
            indexed_files = self.main_window.rag_handler.get_indexed_files_detailed()
            
            # Use file names instead of paths, since RAG system can work with file names
            # and paths might be outdated if files were moved
            for f in indexed_files:
                if f.get("file_name"):
                    # Try to use the path if it exists and file is accessible
                    file_path = f.get("path", "")
                    if file_path and os.path.exists(file_path):
                        knowledge_base_files.append(file_path)
                    else:
                        # Fall back to just the file name if path doesn't exist
                        knowledge_base_files.append(f["file_name"])
        
        self.worker = Worker(
            prompt=prompt,
            general_instructions=self.main_window.general_instructions.toPlainText(),
            agents=agents,
            knowledge_base_files=knowledge_base_files,
            knowledge_base_content=knowledge_base_content or "",
            json_instructions=getattr(self.main_window, 'json_instructions', None),
            config_manager=self.main_window.config_manager,
            conversation_history=self.main_window.conversation_history
        )

        # Set the conversation ID after creating the worker
        if conversation_id:
            self.worker.current_conversation_id = conversation_id
            # Also update the main window's conversation ID
            self.main_window.current_conversation_id = conversation_id
        return self.worker

    def start_worker_thread(self, prompt, knowledge_base_content=None, conversation_id=None):
        # Stop existing worker thread if running
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker.stop()
            self.worker_thread.join()

        # Setup the worker
        self._setup_worker(prompt, knowledge_base_content, conversation_id) # Pass conversation_id

        # Connect worker signals
        self._setup_worker_connections()

        # Connect worker to token manager for timing
        if hasattr(self.main_window, 'token_manager'):
            logging.debug("Connecting worker to token manager")
            self.main_window.token_manager.connect_to_worker(self.worker)

            # Make sure token counter is properly initialized for this run
            # We don't reset the session here (that's done in main_window.py)
            # but we ensure the timer variables are ready for a new run
            from token_counter import token_counter
            if token_counter:
                # Reset timer variables but keep the session data
                token_counter.generation_start_time = None
                token_counter.generation_end_time = None
                token_counter.total_output_tokens_generated = 0
                logging.debug("Reset token counter timer variables in worker_manager")
        else:
            logging.debug("main_window does not have token_manager attribute")

        # Create and start thread
        self.worker_thread = threading.Thread(target=self.worker.start_agent_discussion)
        self.worker_thread.start()

    def stop_worker(self):
        if self.worker:
            self.worker.stop()
            self.main_window.terminal_console.append("Agents processing stopped by user.")

    def cleanup_worker(self):
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker.stop()
            self.worker_thread.join()
        self.worker = None
        self.worker_thread = None