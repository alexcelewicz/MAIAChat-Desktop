#!/usr/bin/env python3
"""
Test script for the unified response panel functionality.
This script tests the new unified response panel to ensure it properly
formats and displays both agent discussions and final answers.
"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from PyQt6.QtCore import Qt

# Import the unified response panel
from ui.unified_response_panel import UnifiedResponsePanel


class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Unified Response Panel Test")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create unified response panel
        self.unified_panel = UnifiedResponsePanel()
        layout.addWidget(self.unified_panel)
        
        # Create test buttons
        button_layout = QVBoxLayout()
        
        # Test agent discussion button
        test_agent_btn = QPushButton("Test Agent Discussion")
        test_agent_btn.clicked.connect(self.test_agent_discussion)
        button_layout.addWidget(test_agent_btn)
        
        # Test final answer button
        test_final_btn = QPushButton("Test Final Answer")
        test_final_btn.clicked.connect(self.test_final_answer)
        button_layout.addWidget(test_final_btn)
        
        # Test code formatting button
        test_code_btn = QPushButton("Test Code Formatting")
        test_code_btn.clicked.connect(self.test_code_formatting)
        button_layout.addWidget(test_code_btn)
        
        # Test HTML formatting button
        test_html_btn = QPushButton("Test HTML Formatting")
        test_html_btn.clicked.connect(self.test_html_formatting)
        button_layout.addWidget(test_html_btn)
        
        # Clear button
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self.unified_panel.clear)
        button_layout.addWidget(clear_btn)
        
        layout.addLayout(button_layout)
    
    def test_agent_discussion(self):
        """Test agent discussion formatting."""
        agent_text = """
# Agent Discussion Test

This is a test of agent discussion formatting.

## Key Points:
- Point 1: Agent discussions should be clearly formatted
- Point 2: Code blocks should be properly highlighted
- Point 3: Lists and headers should work correctly

```python
def test_function():
    print("This is a test function")
    return "success"
```

> This is a blockquote to test formatting.

The discussion should be clearly separated from other content.
        """
        
        self.unified_panel.add_agent_discussion(agent_text, agent_number=1, model_name="GPT-4")
    
    def test_final_answer(self):
        """Test final answer formatting."""
        final_text = """
# Final Answer Test

This is the final answer with proper formatting.

## Summary:
1. **Bold text** should work
2. *Italic text* should work
3. `Inline code` should be highlighted

```javascript
function finalAnswer() {
    console.log("Final answer formatting test");
    return "success";
}
```

The final answer should be clearly distinguished from agent discussions.
        """
        
        self.unified_panel.add_final_answer(final_text)
    
    def test_code_formatting(self):
        """Test code formatting with different languages."""
        python_code = """
```python
import sys
from typing import List

def process_data(data: List[str]) -> str:
    \"\"\"Process the input data and return a result.\"\"\"
    result = ""
    for item in data:
        if item.startswith("#"):
            result += f"Comment: {item}\\n"
        else:
            result += f"Data: {item}\\n"
    return result

# Test the function
test_data = ["# This is a comment", "actual data", "# another comment"]
print(process_data(test_data))
```
        """
        
        self.unified_panel.add_agent_discussion(python_code, agent_number=2, model_name="Claude-3")
    
    def test_html_formatting(self):
        """Test HTML formatting."""
        html_content = """
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Page</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f0f0f0;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Test HTML Content</h1>
        <p>This is a test of HTML formatting in the unified response panel.</p>
        <ul>
            <li>Item 1</li>
            <li>Item 2</li>
            <li>Item 3</li>
        </ul>
    </div>
</body>
</html>
```
        """
        
        self.unified_panel.add_final_answer(html_content)


def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show test window
    test_window = TestWindow()
    test_window.show()
    
    print("Unified Response Panel Test Started")
    print("Use the buttons to test different formatting scenarios")
    print("Check that:")
    print("1. Agent discussions have blue headers with timestamps")
    print("2. Final answers have green headers with timestamps")
    print("3. Code blocks are properly formatted with syntax highlighting")
    print("4. Content is clearly separated with dividers")
    print("5. Text wraps properly and is readable")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 