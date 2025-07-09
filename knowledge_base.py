# knowledge_base.py
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
                            QFileDialog, QMessageBox, QProgressBar, QListWidget)
from PyQt6.QtCore import QThread, pyqtSignal
from signal_manager import SignalManager
from progress_dialog import RAGProgressDialog
import os

# Worker thread for RAG processing
class RAGWorker(QThread):
    file_started = pyqtSignal(str) # filename
    file_progress = pyqtSignal(str, str, int) # filename, step_message, percentage
    file_completed = pyqtSignal(str, bool)   # filename, success
    finished = pyqtSignal(dict)              # results
    
    def __init__(self, rag_handler, file_paths):
        super().__init__()
        self.rag_handler = rag_handler
        self.file_paths = file_paths
        self.cancelled = False
    
    def run(self):
        def progress_callback(filename, message, percentage):
            if not self.cancelled:
                self.file_progress.emit(filename, message, percentage)
        
        results = {}
        try:
            for i, file_path in enumerate(self.file_paths):
                if self.cancelled:
                    break
                filename = os.path.basename(file_path)
                self.file_started.emit(filename)
                
                # The lambda captures the current filename and passes it to the progress_callback
                callback = lambda msg, pct: progress_callback(filename, msg, pct)
                
                success = self.rag_handler.add_file(file_path, progress_callback=callback)
                self.file_completed.emit(filename, success)
                results[file_path] = success

            if not self.cancelled:
                self.finished.emit(results)
        except Exception as e:
            if not self.cancelled:
                # Emit a generic error if the loop fails catastrophically
                self.file_progress.emit("System Error", f"An unexpected error occurred: {e}", 100)
                self.finished.emit(results)
    
    def cancel(self):
        self.cancelled = True

# Rename the class to match the import
class KnowledgeBaseDialog(QDialog):
    def __init__(self, rag_handler, parent=None):
        super().__init__(parent)
        self.rag_handler = rag_handler
        self.signals = SignalManager()
        self.parent = parent  # Store the parent reference
        self.rag_worker = None
        self.progress_dialog = None
        self.initUI()

    def show_success(self, message):
        if self.parent:
            self.parent.show_success_message(message)
        else:
            print(f"Success: {message}")

    def show_error(self, message):
        if self.parent:
            self.parent.show_error_message(message)
        else:
            print(f"Error: {message}")

    def add_files(self):
        try:
            # First check if the knowledge base directory is writable
            kb_path = self.rag_handler.get_knowledge_base_path()
            test_file = os.path.join(kb_path, f"write_test_temp.txt")
            try:
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
            except (IOError, PermissionError):
                # Show warning about read-only location
                reply = QMessageBox.warning(
                    self,
                    'Read-Only Knowledge Base',
                    f'The current knowledge base directory appears to be read-only: {kb_path}\n\nWould you like to select a different location before adding files?',
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.load_knowledge_base()
                    # Check if the new location is writable
                    kb_path = self.rag_handler.get_knowledge_base_path()
                    test_file = os.path.join(kb_path, f"write_test_temp.txt")
                    try:
                        with open(test_file, 'w') as f:
                            f.write('test')
                        os.remove(test_file)
                    except (IOError, PermissionError):
                        self.show_error(f"The selected knowledge base location is still not writable. Cannot add files.")
                        return

            files, _ = QFileDialog.getOpenFileNames(
                self, "Select Knowledge Base Files", "", "All Files (*)")

            if files:
                self.start_rag_processing(files)
        except Exception as e:
            self.show_error(f"Error adding files: {str(e)}")

    def start_rag_processing(self, file_paths):
        """Start RAG processing with progress dialog"""
        try:
            # Create and show progress dialog
            self.progress_dialog = RAGProgressDialog(self, len(file_paths))
            
            # Create worker thread
            self.rag_worker = RAGWorker(self.rag_handler, file_paths)
            
            # Connect signals
            self.rag_worker.file_started.connect(self.progress_dialog.on_file_started)
            self.rag_worker.file_progress.connect(self.progress_dialog.on_file_progress)
            self.rag_worker.file_completed.connect(self.progress_dialog.on_file_completed)
            self.rag_worker.finished.connect(self.on_rag_processing_finished)
            
            # Connect cancel button to worker
            self.progress_dialog.cancel_button.clicked.connect(self.cancel_rag_processing)
            
            # Start processing
            self.rag_worker.start()
            
            # Show dialog (blocks until completed or cancelled)
            result = self.progress_dialog.exec()
            
            if result == QDialog.DialogCode.Rejected:
                self.cancel_rag_processing()
                
        except Exception as e:
            self.show_error(f"Error starting RAG processing: {str(e)}")

    def cancel_rag_processing(self):
        """Cancel RAG processing"""
        if self.rag_worker and self.rag_worker.isRunning():
            self.rag_worker.cancel()
            self.rag_worker.terminate()
            self.rag_worker.wait(3000)  # Wait up to 3 seconds
            
    def on_rag_processing_finished(self, results):
        """Handle RAG processing completion"""
        try:
            # Count successful files
            success_count = sum(1 for result in results.values() if result)
            total_count = len(results)
            
            # Update file list
            self.update_file_list()
            
            # Show completion message
            if success_count == total_count:
                self.show_success(f"Successfully added {success_count} file(s) to knowledge base")
            elif success_count > 0:
                self.show_success(f"Added {success_count} of {total_count} files. Some files failed to process.")
            else:
                self.show_error("Failed to add any files to knowledge base")
                
            # Clean up
            self.rag_worker = None
            
        except Exception as e:
            self.show_error(f"Error completing RAG processing: {str(e)}")

    def initUI(self):
        self.setWindowTitle('Knowledge Base Manager')
        self.setGeometry(200, 200, 600, 400)

        layout = QVBoxLayout()

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # File list with search
        self.search_box = QTextEdit()
        self.search_box.setMaximumHeight(30)
        self.search_box.setPlaceholderText("Search files...")
        self.search_box.textChanged.connect(self.filter_files)
        layout.addWidget(self.search_box)

        self.file_list = QListWidget()
        self.update_file_list()
        layout.addWidget(self.file_list)

        # Buttons
        button_layout = QHBoxLayout()
        self.add_btn = QPushButton('Add Files')
        self.remove_btn = QPushButton('Remove Selected')
        self.clear_btn = QPushButton('Clear All')
        self.load_kb_btn = QPushButton('Load Knowledge Base')

        for btn in [self.add_btn, self.remove_btn, self.clear_btn, self.load_kb_btn]:
            button_layout.addWidget(btn)

        self.add_btn.clicked.connect(self.add_files)
        self.remove_btn.clicked.connect(self.remove_selected)
        self.clear_btn.clicked.connect(self.clear_knowledge_base)
        self.load_kb_btn.clicked.connect(self.load_knowledge_base)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def load_knowledge_base(self):
        """Handle loading a knowledge base directory"""
        options = QFileDialog.Option.DontUseNativeDialog
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Knowledge Base Directory",
            "",
            options=options
        )

        if directory:
            try:
                # Check if directory is writable
                test_file = os.path.join(directory, f"write_test_temp.txt")
                try:
                    with open(test_file, 'w') as f:
                        f.write('test')
                    os.remove(test_file)
                except (IOError, PermissionError):
                    # Show warning about read-only location
                    reply = QMessageBox.warning(
                        self,
                        'Read-Only Location',
                        f'The selected directory appears to be read-only. The application will use a fallback location in your home directory instead.\n\nDo you want to continue?',
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.Yes
                    )
                    if reply == QMessageBox.StandardButton.No:
                        return

                if self.rag_handler.set_knowledge_base_path(directory):
                    # Get the actual path that was used (might be fallback path)
                    actual_path = self.rag_handler.get_knowledge_base_path()

                    # Check if this is a new or existing knowledge base
                    if any(self.rag_handler.get_indexed_files()):
                        if actual_path != directory:
                            self.show_success(f"Loaded existing knowledge base from fallback location: {actual_path}")
                        else:
                            self.show_success(f"Loaded existing knowledge base from: {directory}")
                    else:
                        if actual_path != directory:
                            self.show_success(f"Created new knowledge base at fallback location: {actual_path}")
                        else:
                            self.show_success(f"Created new knowledge base at: {directory}")
                    self.update_file_list()
                else:
                    self.show_error("Failed to load knowledge base")
            except Exception as e:
                self.show_error(f"Error loading knowledge base: {str(e)}")

    def filter_files(self):
        search_text = self.search_box.toPlainText().lower()
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            item.setHidden(search_text not in item.text().lower())

    def update_file_list(self):
        self.file_list.clear()
        try:
            files = self.rag_handler.get_indexed_files()
            self.file_list.addItems(files)
        except Exception as e:
            self.parent().show_error(f"Error updating file list: {str(e)}")

    def remove_selected(self):
        try:
            selected_items = self.file_list.selectedItems()
            if not selected_items:
                self.show_error("No files selected")
                return

            for item in selected_items:
                file_name = item.text()
                if self.rag_handler.remove_file(file_name):
                    self.show_success(f"Removed {file_name}")
                else:
                    self.show_error(f"Failed to remove {file_name}")

            self.update_file_list()
        except Exception as e:
            self.show_error(f"Error removing files: {str(e)}")

    def clear_knowledge_base(self):
        try:
            reply = QMessageBox.question(
                self, 'Clear Knowledge Base',
                'Are you sure you want to clear the entire knowledge base?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                if self.rag_handler.clear_knowledge_base():
                    self.show_success("Knowledge base cleared")
                    self.update_file_list()
                else:
                    self.show_error("Failed to clear knowledge base")
        except Exception as e:
            self.show_error(f"Error clearing knowledge base: {str(e)}")