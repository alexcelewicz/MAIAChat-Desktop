#!/usr/bin/env python3
"""
Simple demonstration of the code preview feature.
This script shows how the code preview functionality works.
"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PyQt6.QtCore import Qt

# Import the unified response panel
from ui.unified_response_panel import UnifiedResponsePanel


class CodePreviewDemo(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Code Preview Demo")
        self.setGeometry(100, 100, 1000, 700)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Add title
        title = QLabel("Code Preview Feature Demonstration")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Add description
        description = QLabel("This demo shows the new code preview functionality. Click the buttons below to add different types of code blocks.")
        description.setStyleSheet("margin: 10px; color: #666;")
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Create unified response panel
        self.response_panel = UnifiedResponsePanel()
        layout.addWidget(self.response_panel)
        
        # Add demo button
        demo_btn = QPushButton("Add HTML Code Block with Preview")
        demo_btn.clicked.connect(self.add_html_demo)
        demo_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                margin: 10px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        layout.addWidget(demo_btn)
    
    def add_html_demo(self):
        """Add a simple HTML demo with preview button."""
        html_content = """
# HTML Code Preview Demo

Here's a simple HTML page that you can preview:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Code Preview Demo</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 20px;
        }
        .button {
            background: linear-gradient(45deg, #2196F3, #21CBF3);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            transition: all 0.3s ease;
            margin: 10px;
        }
        .button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(33, 150, 243, 0.4);
        }
        .message {
            margin: 20px 0;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            font-weight: bold;
        }
        .success {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎉 Code Preview Demo</h1>
        <p>This is a demonstration of the code preview feature in the MAIAChat application.</p>
        <p>Click the button below to see JavaScript in action:</p>
        
        <div style="text-align: center;">
            <button class="button" onclick="showMessage()">Click Me!</button>
            <button class="button" onclick="changeColor()">Change Color</button>
        </div>
        
        <div id="message" class="message" style="display: none;"></div>
        
        <div style="margin-top: 30px; padding: 20px; background-color: #f8f9fa; border-radius: 8px;">
            <h3>Features Demonstrated:</h3>
            <ul>
                <li>✅ HTML structure and styling</li>
                <li>✅ CSS gradients and animations</li>
                <li>✅ JavaScript interactivity</li>
                <li>✅ Responsive design</li>
                <li>✅ Modern UI components</li>
            </ul>
        </div>
    </div>
    
    <script>
        function showMessage() {
            const messageDiv = document.getElementById('message');
            messageDiv.innerHTML = '🎉 JavaScript is working! Code preview feature is functional!';
            messageDiv.className = 'message success';
            messageDiv.style.display = 'block';
            
            // Add some animation
            messageDiv.style.animation = 'fadeIn 0.5s ease-in';
        }
        
        function changeColor() {
            const container = document.querySelector('.container');
            const colors = ['#e3f2fd', '#f3e5f5', '#e8f5e8', '#fff3e0', '#fce4ec'];
            const randomColor = colors[Math.floor(Math.random() * colors.length)];
            container.style.backgroundColor = randomColor;
        }
        
        // Add CSS animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(-10px); }
                to { opacity: 1; transform: translateY(0); }
            }
        `;
        document.head.appendChild(style);
    </script>
</body>
</html>
```

**Instructions:**
1. Look for the "👁️ Preview HTML" button below this code block
2. Click the preview button to open the preview dialog
3. In the preview dialog, you can:
   - See the rendered HTML in the "HTML Preview" tab
   - View the raw HTML in the "Raw HTML" tab
   - Click "Update Preview" to refresh after editing
   - Click "Open in Browser" to view in your default browser
   - Click "Save File" to save the code to a file

This demonstrates the full code preview functionality!
        """
        
        self.response_panel.add_agent_discussion(html_content, agent_number=1, model_name="Demo Agent")


def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show demo window
    demo_window = CodePreviewDemo()
    demo_window.show()
    
    print("Code Preview Demo Started")
    print("Click the 'Add HTML Code Block with Preview' button to see the feature in action")
    print("Then look for the preview button below the code block and click it!")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 