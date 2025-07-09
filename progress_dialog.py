# progress_dialog.py
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QProgressBar, QLabel, QTextEdit, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont


class ProgressDialog(QDialog):
    def __init__(self, title, message, parent=None, show_details=False):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(400, 200 if not show_details else 350)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        layout = QVBoxLayout()

        # Main message label
        self.message_label = QLabel(message)
        self.message_label.setWordWrap(True)
        font = QFont()
        font.setPointSize(10)
        self.message_label.setFont(font)
        layout.addWidget(self.message_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)

        # Current operation label
        self.operation_label = QLabel("Initializing...")
        self.operation_label.setWordWrap(True)
        self.operation_label.setStyleSheet("color: #666; font-size: 9pt;")
        layout.addWidget(self.operation_label)

        # Details section (optional)
        if show_details:
            self.details_text = QTextEdit()
            self.details_text.setMaximumHeight(100)
            self.details_text.setReadOnly(True)
            self.details_text.setStyleSheet("background-color: #f5f5f5; border: 1px solid #ddd; font-size: 8pt;")
            layout.addWidget(self.details_text)
        else:
            self.details_text = None

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setMaximumWidth(80)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)

        # Timer to auto-close successful operations
        self.auto_close_timer = QTimer()
        self.auto_close_timer.setSingleShot(True)
        self.auto_close_timer.timeout.connect(self.accept)

    def update_progress(self, value, operation_text=None):
        """Update progress bar value and optional operation text"""
        self.progress_bar.setValue(value)
        
        if operation_text:
            self.operation_label.setText(operation_text)
            
        # Add to details if available
        if self.details_text and operation_text:
            self.details_text.append(f"{value}% : {operation_text}")
            # Auto-scroll to bottom
            scrollbar = self.details_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

        # Auto-close when complete
        if value >= 100:
            self.cancel_button.setText("Close")
            # Auto-close after 2 seconds if successful
            if "successfully" in operation_text.lower() or "completed" in operation_text.lower():
                self.auto_close_timer.start(2000)

    def update_message(self, message):
        """Update the main message"""
        self.message_label.setText(message)

    def add_detail(self, detail_text):
        """Add a detail line to the details text area"""
        if self.details_text:
            self.details_text.append(detail_text)
            # Auto-scroll to bottom
            scrollbar = self.details_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def set_complete(self, success=True, final_message=None):
        """Mark the operation as complete"""
        self.progress_bar.setValue(100)
        self.cancel_button.setText("Close")
        
        if final_message:
            self.operation_label.setText(final_message)
        
        if success:
            self.operation_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        else:
            self.operation_label.setStyleSheet("color: #f44336; font-weight: bold;")


class RAGProgressDialog(ProgressDialog):
    """Specialized progress dialog for RAG operations"""
    
    def __init__(self, parent=None, file_count=1):
        super().__init__(
            title="Processing Knowledge Base Files",
            message=f"Adding {file_count} file{'s' if file_count > 1 else ''} to knowledge base...",
            parent=parent,
            show_details=True
        )
        self.file_count = file_count
        self.processed_files = 0
        
        # Add file-specific progress elements as requested in TODO
        layout = self.layout()
        
        # Insert file status label after the main progress bar
        self.file_status_label = QLabel("Current File: None")
        self.file_status_label.setStyleSheet("color: #333; font-weight: bold; font-size: 9pt;")
        layout.insertWidget(3, self.file_status_label)  # Insert after progress bar
        
        # Add individual file progress bar
        self.file_progress_bar = QProgressBar()
        self.file_progress_bar.setRange(0, 100)
        self.file_progress_bar.setTextVisible(True)
        self.file_progress_bar.setMaximumHeight(20)
        layout.insertWidget(4, self.file_progress_bar)  # Insert after file status
        
    def update_file_progress(self, message, percentage):
        """Update progress for file processing"""
        self.update_progress(percentage, message)
        
    def file_completed(self, filename, success=True):
        """Mark a file as completed"""
        self.processed_files += 1
        status = "✓" if success else "✗"
        self.add_detail(f"{status} {filename}")
        
        # Update main progress
        overall_progress = (self.processed_files * 100) // self.file_count
        self.update_progress(overall_progress, f"Processed {self.processed_files}/{self.file_count} files")
        
        if self.processed_files >= self.file_count:
            success_count = self.processed_files if success else self.processed_files - 1
            self.set_complete(
                success=success_count > 0,
                final_message=f"Completed: {success_count}/{self.file_count} files processed successfully"
            )

    # New slot methods as specified in TODO Task 1.1
    def on_file_started(self, filename):
        """Handle file processing started signal"""
        self.file_status_label.setText(f"Current File: {filename}")
        self.file_progress_bar.setValue(0)
        self.add_detail(f"🔄 Starting: {filename}")

    def on_file_progress(self, filename, message, percentage):
        """Handle detailed file progress signal"""
        self.operation_label.setText(message)
        self.file_progress_bar.setValue(percentage)
        # Don't spam details with every progress update, only major milestones
        if percentage in [10, 25, 50, 75, 90, 100]:
            self.add_detail(f"   {percentage}% - {message}")

    def on_file_completed(self, filename, success):
        """Handle file processing completed signal"""
        self.processed_files += 1
        status = "✅" if success else "❌"
        self.add_detail(f"{status} {filename}")
        
        # Update overall progress
        overall_progress = int((self.processed_files * 100) / self.file_count)
        self.update_progress(overall_progress, f"Processed {self.processed_files}/{self.file_count} files")
        self.file_progress_bar.setValue(100)
        
        # Check if all files are complete
        if self.processed_files >= self.file_count:
            self.file_status_label.setText("All files processed")
            self.set_complete(
                success=True,
                final_message=f"Successfully processed {self.processed_files} file{'s' if self.processed_files > 1 else ''}"
            )
