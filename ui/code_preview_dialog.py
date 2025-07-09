"""
Code Preview Dialog component.
This dialog provides a preview of HTML, CSS, JavaScript, and Python code with live rendering and execution.
"""

import os
import tempfile
import webbrowser
import subprocess
import sys
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, 
                            QPushButton, QLabel, QSplitter, QTextBrowser,
                            QTabWidget, QWidget, QMessageBox, QFileDialog)
from PyQt6.QtCore import Qt, QUrl, QThread, pyqtSignal
from PyQt6.QtGui import QTextCursor, QFont, QTextOption
import re


class PythonExecutionThread(QThread):
    """Thread for executing Python code safely."""
    
    output_ready = pyqtSignal(str)
    error_ready = pyqtSignal(str)
    finished_execution = pyqtSignal()
    
    def __init__(self, code: str):
        super().__init__()
        self.code = code
        
    def run(self):
        """Execute Python code in a separate process."""
        try:
            # Create a temporary Python file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
                f.write(self.code)
                temp_file = f.name
            
            # Execute the Python file
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=30,  # 30 second timeout
                encoding='utf-8'
            )
            
            # Clean up temporary file
            try:
                os.unlink(temp_file)
            except OSError:
                pass
            
            if result.stdout:
                self.output_ready.emit(result.stdout)
            if result.stderr:
                self.error_ready.emit(result.stderr)
                
        except subprocess.TimeoutExpired:
            self.error_ready.emit("⚠️ Execution timed out after 30 seconds")
        except Exception as e:
            self.error_ready.emit(f"❌ Execution error: {str(e)}")
        finally:
            self.finished_execution.emit()


class CodePreviewDialog(QDialog):
    """Dialog for previewing HTML, CSS, JavaScript, and Python code."""
    
    def __init__(self, code_content: str, language: str, parent=None):
        super().__init__(parent)
        self.code_content = code_content
        self.language = language.lower()
        self.temp_file_path = None
        self.python_execution_thread = None
        self.initUI()
        
    def initUI(self):
        """Initialize the UI components."""
        self.setWindowTitle(f"Code Preview - {self.language.upper()}")
        self.setGeometry(100, 100, 1200, 800)
        
        layout = QVBoxLayout(self)
        
        # Create splitter for code and preview
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Code panel
        code_panel = QWidget()
        code_layout = QVBoxLayout(code_panel)
        code_layout.setContentsMargins(0, 0, 0, 0)
        
        self.code_editor = QTextEdit()
        self.code_editor.setPlainText(self.code_content)
        self.code_editor.setFont(QFont("Consolas", 11))
        self.code_editor.setWordWrapMode(QTextOption.WrapMode.NoWrap)
        self.code_editor.setStyleSheet("""
            QTextEdit {
                background-color: #f8f8f8;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Consolas', 'Monaco', monospace;
            }
        """)
        code_layout.addWidget(self.code_editor)
        
        # Preview panel
        preview_panel = QWidget()
        preview_layout = QVBoxLayout(preview_panel)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create tab widget for different preview modes
        self.preview_tabs = QTabWidget()
        
        if self.language == 'python':
            # Python execution output tab
            self.python_output = QTextEdit()
            self.python_output.setReadOnly(True)
            self.python_output.setFont(QFont("Consolas", 10))
            self.python_output.setPlaceholderText("Python output will appear here after execution...")
            self.python_output.setStyleSheet("""
                QTextEdit {
                    background-color: #1e1e1e;
                    color: #ffffff;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 8px;
                    font-family: 'Consolas', 'Monaco', monospace;
                }
            """)
            self.preview_tabs.addTab(self.python_output, "Python Output")
            
            # Code analysis tab
            self.code_analysis = QTextEdit()
            self.code_analysis.setReadOnly(True)
            self.code_analysis.setFont(QFont("Consolas", 10))
            self.code_analysis.setStyleSheet("""
                QTextEdit {
                    background-color: #f8f8f8;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 8px;
                    font-family: 'Consolas', 'Monaco', monospace;
                }
            """)
            self.preview_tabs.addTab(self.code_analysis, "Code Analysis")
            
        else:
            # HTML Preview tab for web languages
            self.html_preview = QTextBrowser()
            self.html_preview.setOpenExternalLinks(True)
            self.html_preview.setStyleSheet("""
                QTextBrowser {
                    background-color: white;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 8px;
                }
            """)
            self.preview_tabs.addTab(self.html_preview, "HTML Preview")
            
            # Raw HTML tab
            self.raw_html_view = QTextEdit()
            self.raw_html_view.setReadOnly(True)
            self.raw_html_view.setFont(QFont("Consolas", 10))
            self.raw_html_view.setWordWrapMode(QTextOption.WrapMode.NoWrap)
            self.raw_html_view.setStyleSheet("""
                QTextEdit {
                    background-color: #f8f8f8;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 8px;
                    font-family: 'Consolas', 'Monaco', monospace;
                }
            """)
            self.preview_tabs.addTab(self.raw_html_view, "Raw HTML")
        
        preview_layout.addWidget(self.preview_tabs)
        
        # Add panels to splitter
        splitter.addWidget(code_panel)
        splitter.addWidget(preview_panel)
        splitter.setSizes([600, 600])  # Equal split
        
        layout.addWidget(splitter)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        if self.language == 'python':
            # Execute button for Python
            self.execute_btn = QPushButton("▶️ Execute Python")
            self.execute_btn.clicked.connect(self.execute_python)
            self.execute_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #388E3C;
                }
                QPushButton:disabled {
                    background-color: #CCCCCC;
                    color: #666666;
                }
            """)
            
            # Clear output button
            self.clear_output_btn = QPushButton("🗑️ Clear Output")
            self.clear_output_btn.clicked.connect(self.clear_python_output)
            self.clear_output_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF5722;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #D84315;
                }
            """)
            
            button_layout.addWidget(self.execute_btn)
            button_layout.addWidget(self.clear_output_btn)
            
        else:
            # Preview button for web languages
            self.preview_btn = QPushButton("Update Preview")
            self.preview_btn.clicked.connect(self.update_preview)
            self.preview_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
            """)
            
            # Open in browser button
            self.browser_btn = QPushButton("Open in Browser")
            self.browser_btn.clicked.connect(self.open_in_browser)
            self.browser_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #388E3C;
                }
            """)
            
            button_layout.addWidget(self.preview_btn)
            button_layout.addWidget(self.browser_btn)
        
        # Save button (common for all languages)
        self.save_btn = QPushButton("💾 Save File")
        self.save_btn.clicked.connect(self.save_file)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        
        # Close button
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        
        button_layout.addWidget(self.save_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
        
        # Initial setup
        if self.language == 'python':
            self.analyze_python_code()
        else:
            self.update_preview()
    
    def analyze_python_code(self):
        """Analyze Python code and show basic information."""
        current_code = self.code_editor.toPlainText()
        
        # Basic code analysis
        lines = current_code.split('\n')
        total_lines = len(lines)
        non_empty_lines = len([line for line in lines if line.strip()])
        comment_lines = len([line for line in lines if line.strip().startswith('#')])
        
        # Count imports
        import_lines = [line for line in lines if line.strip().startswith(('import ', 'from '))]
        
        # Count function definitions
        function_lines = [line for line in lines if line.strip().startswith('def ')]
        
        # Count class definitions
        class_lines = [line for line in lines if line.strip().startswith('class ')]
        
        analysis = f"""📊 Python Code Analysis
{'='*50}

📈 Code Statistics:
• Total lines: {total_lines}
• Non-empty lines: {non_empty_lines}
• Comment lines: {comment_lines}
• Import statements: {len(import_lines)}
• Function definitions: {len(function_lines)}
• Class definitions: {len(class_lines)}

📦 Imports Found:
{chr(10).join(f'• {imp.strip()}' for imp in import_lines) if import_lines else '• No imports found'}

🔧 Functions Found:
{chr(10).join(f'• {func.strip()}' for func in function_lines) if function_lines else '• No functions found'}

🏗️ Classes Found:
{chr(10).join(f'• {cls.strip()}' for cls in class_lines) if class_lines else '• No classes found'}

⚠️ Execution Notes:
• Code will be executed in a separate process
• Execution timeout: 30 seconds
• Standard output and errors will be captured
• Some operations (file I/O, network) may be restricted

🚀 Ready to execute! Click "Execute Python" to run your code.
        """
        
        self.code_analysis.setPlainText(analysis)
    
    def execute_python(self):
        """Execute Python code in a separate thread."""
        if self.python_execution_thread and self.python_execution_thread.isRunning():
            QMessageBox.warning(self, "Execution in Progress", "Python code is already being executed. Please wait...")
            return
        
        current_code = self.code_editor.toPlainText().strip()
        if not current_code:
            QMessageBox.warning(self, "No Code", "Please enter some Python code to execute.")
            return
        
        # Clear previous output
        self.python_output.clear()
        self.python_output.append("🚀 Executing Python code...\n" + "="*50 + "\n")
        
        # Disable execute button during execution
        self.execute_btn.setEnabled(False)
        self.execute_btn.setText("⏳ Executing...")
        
        # Create and start execution thread
        self.python_execution_thread = PythonExecutionThread(current_code)
        self.python_execution_thread.output_ready.connect(self.on_python_output)
        self.python_execution_thread.error_ready.connect(self.on_python_error)
        self.python_execution_thread.finished_execution.connect(self.on_execution_finished)
        self.python_execution_thread.start()
    
    def on_python_output(self, output: str):
        """Handle Python execution output."""
        self.python_output.append(f"📤 Output:\n{output}\n")
    
    def on_python_error(self, error: str):
        """Handle Python execution errors."""
        self.python_output.append(f"❌ Error:\n{error}\n")
    
    def on_execution_finished(self):
        """Handle execution completion."""
        self.python_output.append("\n" + "="*50 + "\n✅ Execution completed.")
        self.execute_btn.setEnabled(True)
        self.execute_btn.setText("▶️ Execute Python")
    
    def clear_python_output(self):
        """Clear Python output."""
        self.python_output.clear()
        self.python_output.append("🗑️ Output cleared. Ready for new execution.\n")

    def get_full_html(self):
        """Returns the full HTML content for web languages."""
        current_code = self.code_editor.toPlainText()
        
        if self.language == 'html':
            return current_code
            
        elif self.language == 'css':
            return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>CSS Preview</title>
    <style>
{current_code}
    </style>
</head>
<body>
    <h1>CSS Preview</h1>
    <p>This is a preview of your CSS styles.</p>
    <div class="example-box">
        <h2>Example Box</h2>
        <p>This box demonstrates your CSS styling.</p>
    </div>
    <button class="example-button">Example Button</button>
</body>
</html>
            """
            
        elif self.language in ['javascript', 'js']:
            return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>JavaScript Preview</title>
</head>
<body>
    <h1>JavaScript Execution</h1>
    <p>Check the browser's developer console for script output.</p>
    <script>
{current_code}
    </script>
</body>
</html>
            """
        return ""
        
    def update_preview(self):
        """Update the preview based on the current code content."""
        if self.language != 'python':
            html_content = self.get_full_html()
            self.html_preview.setHtml(html_content)
            self.raw_html_view.setPlainText(html_content)
    
    def open_in_browser(self):
        """Save to a temporary file and open in the default web browser."""
        if self.language == 'python':
            QMessageBox.information(self, "Not Applicable", "Browser preview is not available for Python code. Use the Execute Python button instead.")
            return
            
        try:
            full_html = self.get_full_html()
            
            # Create a temporary file with UTF-8 encoding
            with tempfile.NamedTemporaryFile(
                mode='w', 
                encoding='utf-8', 
                delete=False, 
                suffix=".html",
                errors='replace'  # Handle potential encoding errors gracefully
            ) as f:
                self.temp_file_path = f.name
                f.write(full_html)
            
            # Use file:// URL scheme for local files
            url = QUrl.fromLocalFile(self.temp_file_path)
            webbrowser.open(url.toString())
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open in browser: {e}")
    
    def save_file(self):
        """Save the code to a file."""
        try:
            current_code = self.code_editor.toPlainText()
            
            # Determine file extension and default name
            if self.language == 'python':
                extension = 'Python Files (*.py);;All Files (*)'
                default_name = 'script.py'
                content_to_save = current_code
            elif self.language == 'html':
                extension = 'HTML Files (*.html);;All Files (*)'
                default_name = 'code.html'
                content_to_save = current_code
            elif self.language == 'css':
                extension = 'CSS Files (*.css);;All Files (*)'
                default_name = 'styles.css'
                content_to_save = current_code
            elif self.language in ['javascript', 'js']:
                extension = 'JavaScript Files (*.js);;All Files (*)'
                default_name = 'script.js'
                content_to_save = current_code
            else:
                extension = 'Text Files (*.txt);;All Files (*)'
                default_name = 'code.txt'
                content_to_save = current_code
            
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Code File", default_name, extension
            )
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content_to_save)
                QMessageBox.information(self, "Success", f"File saved successfully!\n\nPath: {file_path}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save file: {e}")
    
    def closeEvent(self, event):
        """Clean up resources when the dialog is closed."""
        # Stop Python execution thread if running
        if self.python_execution_thread and self.python_execution_thread.isRunning():
            self.python_execution_thread.terminate()
            self.python_execution_thread.wait(2000)  # Wait up to 2 seconds
        
        # Clean up temporary files
        if self.temp_file_path and os.path.exists(self.temp_file_path):
            try:
                os.remove(self.temp_file_path)
            except OSError as e:
                # Log this error if you have a logging system
                print(f"Error removing temporary file {self.temp_file_path}: {e}")
        super().closeEvent(event) 