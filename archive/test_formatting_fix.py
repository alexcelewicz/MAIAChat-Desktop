#!/usr/bin/env python3
"""
Test script to verify the formatting fixes for agent discussion and final answer windows.
"""
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QTextEdit
from PyQt6.QtCore import Qt

class TestFormattingWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Formatting Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create text edit for agent discussion
        self.agent_discussion = QTextEdit()
        self.agent_discussion.setReadOnly(True)
        layout.addWidget(self.agent_discussion)
        
        # Create text edit for final answer
        self.final_answer = QTextEdit()
        self.final_answer.setReadOnly(True)
        layout.addWidget(self.final_answer)
        
        # Create test buttons
        test_agent_btn = QPushButton("Test Agent Discussion")
        test_agent_btn.clicked.connect(self.test_agent_discussion)
        layout.addWidget(test_agent_btn)
        
        test_final_btn = QPushButton("Test Final Answer")
        test_final_btn.clicked.connect(self.test_final_answer)
        layout.addWidget(test_final_btn)
        
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_all)
        layout.addWidget(clear_btn)
    
    def test_agent_discussion(self):
        """Test agent discussion formatting"""
        # Test with a simple agent response
        agent_header = "<b style='color: #1976D2;'>Agent 1 (gpt-4):</b> "
        agent_content = "Here's a simple response with some code:\n\n```python\ndef hello_world():\n    print('Hello, world!')\n```\n\nAnd here's a list:\n- Item 1\n- Item 2\n- Item 3"
        
        # Insert the HTML directly
        self.agent_discussion.insertHtml(agent_header + agent_content)
    
    def test_final_answer(self):
        """Test final answer formatting"""
        # Test with a simple final answer
        final_content = "<div style='background-color: #FFFFFF; border: 1px solid #2196F3; border-radius: 8px; padding: 16px; margin: 16px 0; font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6; color: #212121;'>Here's a final answer with some code:\n\n```python\ndef hello_world():\n    print('Hello, world!')\n```\n\nAnd here's a list:\n- Item 1\n- Item 2\n- Item 3</div>"
        
        # Set the HTML directly
        self.final_answer.setHtml(final_content)
    
    def clear_all(self):
        """Clear all text edits"""
        self.agent_discussion.clear()
        self.final_answer.clear()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestFormattingWindow()
    window.show()
    sys.exit(app.exec())
