"""
Unified Response Panel component.
This panel displays both agent discussions and final answers in a single window
with proper formatting and clear separation between different response types.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
                            QPushButton, QLabel, QSizePolicy, QScrollArea, QCheckBox,
                            QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QTextCursor, QIcon, QTextOption, QFont, QMouseEvent, QTextDocument
import os
from datetime import datetime
import re
from html import escape
from ui.text_formatter import TextFormatter
import time


class PreviewTextEdit(QTextEdit):
    """Custom QTextEdit that can handle preview button clicks."""
    
    preview_requested = pyqtSignal(int)  # block_index
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._open_external_links = True
        self._open_links = True
    
    def setOpenExternalLinks(self, enabled: bool):
        """Set whether external links should be opened."""
        self._open_external_links = enabled
        # Call parent method if it exists
        if hasattr(super(), 'setOpenExternalLinks'):
            super().setOpenExternalLinks(enabled)
    
    def setOpenLinks(self, enabled: bool):
        """Set whether links should be opened."""
        self._open_links = enabled
        # Call parent method if it exists
        if hasattr(super(), 'setOpenLinks'):
            super().setOpenLinks(enabled)
    
    def mousePressEvent(self, event: QMouseEvent):
        """Override mouse press event to detect preview button clicks."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Get the cursor at the click position
            cursor = self.cursorForPosition(event.pos())
            
            # Check if the cursor is over a link
            if cursor.charFormat().isAnchor():
                url = cursor.charFormat().anchorHref()
                if url.startswith("preview://"):
                    try:
                        block_index = int(url.split("://")[1])
                        self.preview_requested.emit(block_index)
                        return
                    except (ValueError, IndexError):
                        pass
        
        # Call the parent method for normal text editing behavior
        super().mousePressEvent(event)


class CodeBlockWidget(QFrame):
    """Widget for displaying code blocks with preview functionality."""
    
    preview_requested = pyqtSignal(str, str)  # content, language
    
    def __init__(self, code_content: str, language: str, parent=None):
        super().__init__(parent)
        self.code_content = code_content
        self.language = language
        self.initUI()
    
    def initUI(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Code display
        self.code_display = QTextEdit()
        self.code_display.setPlainText(self.code_content)
        self.code_display.setReadOnly(True)
        self.code_display.setMaximumHeight(200)
        self.code_display.setFont(QFont("Consolas", 10))
        self.code_display.setStyleSheet("""
            QTextEdit {
                background-color: #f6f8fa;
                border: 1px solid #e1e4e8;
                border-radius: 6px;
                padding: 8px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.code_display)
        
        # Preview button (for supported languages including Python)
        if self.language in ['html', 'css', 'javascript', 'js', 'python']:
            if self.language == 'python':
                preview_btn = QPushButton(f"🐍 Preview & Execute {self.language.upper()}")
                button_color = "#4CAF50"  # Green for Python
                hover_color = "#388E3C"
            else:
                preview_btn = QPushButton(f"👁️ Preview {self.language.upper()}")
                button_color = "#2196F3"  # Blue for web languages
                hover_color = "#1976D2"
                
            preview_btn.clicked.connect(self.request_preview)
            preview_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {button_color};
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-size: 12px;
                    font-weight: bold;
                    max-width: 200px;
                }}
                QPushButton:hover {{
                    background-color: {hover_color};
                }}
            """)
            layout.addWidget(preview_btn, alignment=Qt.AlignmentFlag.AlignCenter)
    
    def request_preview(self):
        """Emit signal to request preview."""
        self.preview_requested.emit(self.code_display.toPlainText(), self.language)


class UnifiedResponsePanel(QWidget):
    """Panel for displaying unified agent responses with proper formatting and separation."""

    # Define signals
    send_clicked = pyqtSignal()
    follow_up_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()
    clear_clicked = pyqtSignal()
    load_file_clicked = pyqtSignal()
    knowledge_base_clicked = pyqtSignal()
    save_pdf_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.text_formatter = TextFormatter()
        # Add a dictionary to manage streaming context for each agent
        self._streaming_contexts = {}
        # Store code blocks for preview functionality
        self._code_blocks = []
        self.initUI()

    def initUI(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)

        # Title label
        title_label = QLabel("Unified Response")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #212121;
                padding: 5px;
            }
        """)
        layout.addWidget(title_label)

        # Unified response area with modern styling (for backward compatibility)
        self.unified_response = PreviewTextEdit()
        self.unified_response.setReadOnly(True)
        self.unified_response.setPlaceholderText("Agent discussions will appear here...")
        self.unified_response.setAcceptRichText(True)
        self.unified_response.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.unified_response.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        self.unified_response.setOpenExternalLinks(True)
        self.unified_response.setOpenLinks(True)
        
        # Add a QTextDocument to manage content blocks
        self.unified_response.setDocument(QTextDocument())
        
        # Connect preview signal
        self.unified_response.preview_requested.connect(self.show_code_preview)
        
        # Import the font constants from main_window_ui
        from ui.main_window_ui import DEFAULT_FONT_FAMILY

        self.unified_response.setStyleSheet(f"""
            QTextEdit {{
                background-color: #FFFFFF;
                color: #000000;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                padding: 12px;
                font-family: '{DEFAULT_FONT_FAMILY}', 'Roboto', sans-serif;
                font-size: 13px;
                line-height: 1.5;
            }}
            QTextEdit QAbstractScrollArea {{
                word-wrap: break-word;
            }}
        """)

        # Add unified response to layout with stretch to push prompt to bottom
        layout.addWidget(self.unified_response, 1)

        # Add a spacer to push the prompt input and buttons to the bottom
        layout.addStretch()

        # Bottom section for prompt input and buttons
        bottom_section = QVBoxLayout()

        # Prompt input with modern styling
        self.input_prompt = QTextEdit()
        self.input_prompt.setPlaceholderText("Enter your prompt here...")
        self.input_prompt.setAcceptRichText(False)
        self.input_prompt.setMaximumHeight(100)  # Limit height
        # Use the same font as the unified response
        self.input_prompt.setStyleSheet(f"""
            QTextEdit {{
                background-color: white;
                color: #000000;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                padding: 12px;
                font-family: '{DEFAULT_FONT_FAMILY}', 'Roboto', sans-serif;
                font-size: 13px;
                line-height: 1.5;
            }}
            QTextEdit:focus {{
                border: 1px solid #2196F3;
            }}
        """)

        # Override paste behavior to ensure plain text
        try:
            from PyQt6.QtWidgets import QApplication
            self.input_prompt.paste = lambda: self.input_prompt.insertPlainText(
                QApplication.clipboard().text()
            )
        except ImportError:
            pass  # Handle case where QApplication is not available

        bottom_section.addWidget(self.input_prompt)

        # Button layout
        button_layout = QHBoxLayout()

        # Helper function to create buttons with icons
        def create_button(text, icon_name, tooltip):
            icon_path = os.path.join("icons", f"{icon_name}.svg")
            button = QPushButton(text)
            if os.path.exists(icon_path):
                button.setIcon(QIcon(icon_path))
            button.setToolTip(tooltip)
            button.setStyleSheet("""
                QPushButton {
                    background-color: #f0f0f0;
                    border: 1px solid #dcdcdc;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-size: 13px;
                    color: #333333;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
                QPushButton:pressed {
                    background-color: #d0d0d0;
                }
            """)
            return button

        # Create buttons with modern icons
        self.load_file_btn = create_button("Load File", "file", "Load a file for processing")
        self.knowledge_base_btn = create_button("RAG", "database", "Access knowledge base")
        self.send_btn = create_button("Send", "send", "Send prompt to agents")
        self.follow_up_btn = create_button("Follow Up", "chat", "Send a follow-up message")
        self.stop_btn = create_button("Stop", "stop", "Stop current process")
        self.clear_btn = create_button("Clear", "clear", "Clear all outputs")
        self.save_pdf_btn = create_button("Save PDF", "pdf", "Save as PDF")

        # Add buttons to layout with proper spacing
        button_layout.setSpacing(10)
        button_layout.addWidget(self.load_file_btn)
        button_layout.addWidget(self.knowledge_base_btn)
        button_layout.addWidget(self.send_btn)
        button_layout.addWidget(self.follow_up_btn)
        button_layout.addWidget(self.stop_btn)
        button_layout.addWidget(self.clear_btn)
        button_layout.addWidget(self.save_pdf_btn)

        # Connect button signals
        self.send_btn.clicked.connect(self.send_clicked)
        self.follow_up_btn.clicked.connect(self.follow_up_clicked)
        self.stop_btn.clicked.connect(self.stop_clicked)
        self.clear_btn.clicked.connect(self.clear_clicked)
        self.load_file_btn.clicked.connect(self.load_file_clicked)
        self.knowledge_base_btn.clicked.connect(self.knowledge_base_clicked)
        self.save_pdf_btn.clicked.connect(self.save_pdf_clicked)

        # Initially disable follow-up button
        self.follow_up_btn.setEnabled(False)

        # Add button layout to bottom section
        bottom_section.addLayout(button_layout)

        # Add bottom section to main layout
        layout.addLayout(bottom_section)

    def add_agent_discussion(self, text_chunk: str, agent_number: int, model_name: str, is_first_chunk: bool):
        """
        Adds agent discussion content to the response panel, handling streaming and code blocks.
        This method is now a dispatcher that uses helpers for clarity.
        """
        cursor = self.unified_response.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.unified_response.setTextCursor(cursor)

        # Initialize context on the first chunk
        if is_first_chunk or agent_number not in self._streaming_contexts:
            self._initialize_streaming_context(agent_number, model_name)

        context = self._streaming_contexts[agent_number]
        
        # Process the incoming chunk part by part, splitting by code fences
        # The regex includes the fence in the parts list for easier state management
        parts = re.split(r'(```[a-zA-Z]*\n?)', text_chunk)

        for part in parts:
            if not part:
                continue

            is_fence = part.strip().startswith('```')

            if is_fence:
                if context['in_code_block']:
                    self._handle_code_block_end(context)
                else:
                    language = part.strip().lstrip('```').strip() or 'plaintext'
                    self._handle_code_block_start(context, language)
            elif context['in_code_block']:
                self._handle_code_block_stream(context, part)
            else:
                self._handle_regular_text(part)
        
        # Ensure view scrolls to the latest content
        scrollbar = self.unified_response.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _initialize_streaming_context(self, agent_number: int, model_name: str):
        """Initializes or resets the streaming context for an agent and adds the header."""
        # Add a horizontal line before a new agent's response, unless it's the very first response
        if self.unified_response.document().toPlainText().strip():
            self.unified_response.insertHtml('<hr style="border: none; border-top: 1px solid #e0e0e0; margin: 20px 0;">')

        self._streaming_contexts[agent_number] = {
            'in_code_block': False,
            'language': None,
            'buffer': '',  # Buffer for raw code content
            'block_start_cursor_pos': -1,
        }
        self._insert_agent_header(agent_number, model_name)

    def _insert_agent_header(self, agent_number: int, model_name: str):
        """Inserts a styled header for the agent's response."""
        agent_colors = ["#1976D2", "#388E3C", "#D32F2F", "#7B1FA2", "#F57C00"]
        color = agent_colors[(agent_number - 1) % len(agent_colors)]
        header_html = (
            f'<div style="margin-top: 15px; margin-bottom: 8px;">'
            f'<span style="color: {color}; font-weight: bold; font-size: 14px;">'
            f'Agent {agent_number} ({model_name})'
            f'</span></div>'
        )
        self.unified_response.insertHtml(header_html)

    def _handle_code_block_start(self, context: dict, language: str):
        """Handles the start of a code block."""
        context['in_code_block'] = True
        context['language'] = language

        # Insert a styled header for the code block
        lang_header = f'```{language}'
        self.unified_response.insertHtml(
            f'<div style="background-color: #f0f0f0; padding: 4px 8px; border-top-left-radius: 4px; border-top-right-radius: 4px; font-family: monospace; color: #555;">{lang_header}</div>'
        )
        
        # The crucial <pre> tag that preserves whitespace for streamed content
        pre_wrapper_start = '<pre style="background-color: #f6f8fa; margin: 0; padding: 10px; border-bottom-left-radius: 4px; border-bottom-right-radius: 4px; white-space: pre-wrap; word-wrap: break-word; font-family: Consolas, monospace; font-size: 13px; border: 1px solid #e1e4e8; border-top: none;">'
        
        self.unified_response.insertHtml(pre_wrapper_start)
        
        # Mark the start position for later replacement
        cursor = self.unified_response.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        context['block_start_cursor_pos'] = cursor.position()

    def _handle_code_block_stream(self, context: dict, chunk: str):
        """Streams a piece of code content into the current code block."""
        context['buffer'] += chunk
        # Insert raw text. Qt will respect the whitespace because we are inside a <pre> block.
        cursor = self.unified_response.textCursor()
        cursor.insertText(chunk)

    def _handle_code_block_end(self, context: dict):
        """Finalizes a code block by replacing streamed content with highlighted HTML."""
        # Create a cursor to select the streamed raw text
        selection_cursor = QTextCursor(self.unified_response.document())
        selection_cursor.setPosition(context['block_start_cursor_pos'])
        
        # The end position is the current cursor position before we do anything else
        end_pos = self.unified_response.textCursor().position()
        selection_cursor.setPosition(end_pos, QTextCursor.MoveMode.KeepAnchor)
        
        # Replace the raw text with the beautifully formatted version
        final_code_html = self.text_formatter.format_code_block(context['buffer'], context['language'])
        selection_cursor.insertHtml(final_code_html)
        
        # Move cursor to the end of the newly inserted HTML
        cursor = self.unified_response.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.unified_response.setTextCursor(cursor)

        # Add a preview button if the language is supported
        if context['language'] in ['html', 'css', 'javascript', 'js', 'python']:
            block_index = len(self._code_blocks)
            self._code_blocks.append({'content': context['buffer'], 'language': context['language']})
            preview_button_html = self._create_preview_button_html(
                context['buffer'], context['language'], block_index
            )
            self.unified_response.insertHtml(preview_button_html)

        # Reset the context for the next block
        context['in_code_block'] = False
        context['buffer'] = ''
        context['block_start_cursor_pos'] = -1

    def _handle_regular_text(self, chunk: str):
        """Formats and inserts regular, non-code text."""
        if chunk.strip():
            formatted_text = self.text_formatter.format_text_content(chunk)
            self.unified_response.insertHtml(formatted_text)

    def _create_preview_button_html(self, code_content: str, language: str, block_index: int) -> str:
        """Create HTML for preview button."""
        # Customize button appearance and text based on language
        if language == 'python':
            button_text = f"🐍 Preview & Execute {language.upper()}"
            button_color = "#4CAF50"  # Green for Python
            hover_color = "#388E3C"
        else:
            button_text = f"👁️ Preview {language.upper()}"
            button_color = "#2196F3"  # Blue for web languages
            hover_color = "#1976D2"
        
        # Create a clickable link that we can detect
        button_html = f'''
        <div style="margin: 8px 0; text-align: center;">
            <a href="preview://{block_index}" 
               style="
                   background-color: {button_color};
                   color: white;
                   border: none;
                   border-radius: 4px;
                   padding: 6px 12px;
                   font-size: 12px;
                   cursor: pointer;
                   font-weight: bold;
                   text-decoration: none;
                   display: inline-block;
                   min-width: 120px;
               "
               onmouseover="this.style.backgroundColor='{hover_color}'"
               onmouseout="this.style.backgroundColor='{button_color}'"
            >
                {button_text}
            </a>
        </div>
        '''
        return button_html
    
    def _format_code_chunk_progressive(self, code_chunk: str) -> str:
        """Simplified progressive display for code chunks (now mainly for fallback)."""
        from html import escape
        # Just escape and return as a simple span - the real formatting happens on replacement
        escaped_chunk = escape(code_chunk).replace('\n', '<br>')
        return f'<span class="streamed-code-part">{escaped_chunk}</span>'

    def show_code_preview(self, block_index: int):
        """Show code preview dialog for the specified block."""
        if 0 <= block_index < len(self._code_blocks):
            block = self._code_blocks[block_index]
            try:
                from ui.code_preview_dialog import CodePreviewDialog
                dialog = CodePreviewDialog(block['content'], block['language'], self)
                dialog.exec()
            except ImportError:
                # Fallback if code preview dialog is not available
                import webbrowser
                import tempfile
                
                # Create temporary file and handle based on language
                content = block['content']
                language = block['language']
                
                if language == 'python':
                    # For Python, create a temporary .py file and show info
                    try:
                        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
                            f.write(content)
                            temp_path = f.name
                        
                        # Show dialog with file path and basic info
                        from PyQt6.QtWidgets import QMessageBox
                        msg = QMessageBox(self)
                        msg.setIcon(QMessageBox.Icon.Information)
                        msg.setWindowTitle("Python Code Preview")
                        msg.setText("Python code has been saved to a temporary file for preview.")
                        msg.setInformativeText(f"File location: {temp_path}\n\nFor full Python preview with execution, please install the code preview dialog.")
                        msg.setDetailedText(content)
                        msg.exec()
                        
                        # Clean up temporary file after user closes dialog
                        try:
                            os.unlink(temp_path)
                        except OSError:
                            pass
                    except Exception as e:
                        from PyQt6.QtWidgets import QMessageBox
                        QMessageBox.critical(self, "Error", f"Could not create temporary Python file: {e}")
                    return
                elif language == 'html':
                    html_content = content
                elif language == 'css':
                    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>CSS Preview</title>
    <style>
{content}
    </style>
</head>
<body>
    <div class="preview-content">
        <h1>CSS Preview</h1>
        <p>This is a preview of your CSS styles.</p>
        <div class="example-box">
            <h2>Example Box</h2>
                <p>This box demonstrates your CSS styling.</p>
        </div>
        <button class="example-button">Example Button</button>
    </div>
</body>
</html>
                    """
                elif language in ['javascript', 'js']:
                    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>JavaScript Preview</title>
</head>
<body>
    <h1>JavaScript Preview</h1>
    <div id="output"></div>
    <script>
{content}
    </script>
</body>
</html>
                    """
                else:
                    return
                
                with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                    f.write(html_content)
                    webbrowser.open(f'file://{f.name}')

    def clear(self):
        """Clear the response panel and prompt."""
        self.unified_response.clear()
        self._code_blocks.clear()

    def get_prompt(self):
        """Get the current prompt text."""
        return self.input_prompt.toPlainText()

    def clear_prompt(self):
        """Clear the prompt input."""
        self.input_prompt.clear()

    def enable_follow_up(self, enabled=True):
        """Enable or disable the follow-up button."""
        self.follow_up_btn.setEnabled(enabled)

    # Backward compatibility methods
    def append(self, text: str):
        """Append text to the unified response (backward compatibility)."""
        self.unified_response.append(text)

    def insertHtml(self, html: str):
        """Insert HTML into the unified response (backward compatibility)."""
        self.unified_response.insertHtml(html)
