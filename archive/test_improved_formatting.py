"""
Test script for the improved text formatting functionality.
"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QTextEdit, QPushButton
from ui.text_formatter import TextFormatter

class TestFormattingWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Improved Formatting Test")
        self.setGeometry(100, 100, 1000, 800)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create text edit for input
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Enter text with code blocks...")
        layout.addWidget(self.input_text)
        
        # Create button to format
        format_button = QPushButton("Format Text")
        format_button.clicked.connect(self.format_text)
        layout.addWidget(format_button)
        
        # Create text edit for output
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        layout.addWidget(self.output_text)
        
        # Initialize text formatter
        self.text_formatter = TextFormatter()
        
        # Set sample text
        self.input_text.setPlainText("""# Test Formatting

This is a test of the improved formatting functionality.

## Code Block Example

```python
def hello_world():
    # This is a comment
    print("Hello, world!")
    
    # Triple quotes example
    doc_string = '''This is a triple
    quoted string that spans
    multiple lines'''
    
    another_doc = """Another triple
    quoted string example"""
    
    # Number formatting
    decimal = 12345
    hex_number = 0x1A3F
    binary = 0b1010
    
    for i in range(10):
        if i % 2 == 0:
            print(f"Even number: {i}")
        else:
            print(f"Odd number: {i}")
            
    return True
```

## Another Example

```javascript
function calculateSum(a, b) {
    // Add two numbers
    return a + b;
}
```

That's all for now!
""")
    
    def format_text(self):
        input_text = self.input_text.toPlainText()
        formatted_text = self.text_formatter.format_text_content(input_text)
        self.output_text.setHtml(formatted_text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestFormattingWindow()
    window.show()
    sys.exit(app.exec())
