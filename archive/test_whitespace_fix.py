"""
Test script for the improved agent discussion formatting with whitespace fixes.
"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout
from ui.text_formatter import TextFormatter

class TestWhitespaceFixWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Whitespace Fix Test")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)
        
        # Left panel for input
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Create text edit for input
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Enter agent response with code blocks...")
        left_layout.addWidget(self.input_text)
        
        # Create buttons
        button_layout = QHBoxLayout()
        
        format_button = QPushButton("Format as Agent 1")
        format_button.clicked.connect(lambda: self.format_agent_response(1, "GPT-4"))
        button_layout.addWidget(format_button)
        
        left_layout.addLayout(button_layout)
        
        # Right panel for output
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Create text edit for output
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setAcceptRichText(True)
        right_layout.addWidget(self.output_text)
        
        # Add panels to main layout
        layout.addWidget(left_panel)
        layout.addWidget(right_panel)
        
        # Initialize text formatter
        self.text_formatter = TextFormatter()
        
        # Set sample text
        self.input_text.setPlainText("""# Agent Response Example

I've analyzed the code and found several issues that need to be addressed:

## Issues Found

1. The function is missing proper error handling
2. There's a potential memory leak in the resource allocation
3. The algorithm complexity is O(n²) which can be improved

## Suggested Solution

Here's my implementation that fixes these issues:

```python
def optimize_resource_allocation(resources, tasks):
    """
    Optimize resource allocation with improved efficiency.
    
    Args:
        resources (list): Available resources
        tasks (list): Tasks to be completed
        
    Returns:
        dict: Optimal allocation mapping
    """
    # Input validation
    if not resources or not tasks:
        return {}
    
    # Initialize allocation map
    allocation = {}
    
    # Use a more efficient O(n log n) algorithm
    sorted_tasks = sorted(tasks, key=lambda t: t.priority, reverse=True)
    
    for task in sorted_tasks:
        # Find best resource match
        best_resource = None
        best_score = float('-inf')
        
        for resource in resources:
            if resource.available:
                score = calculate_compatibility(resource, task)
                if score > best_score:
                    best_score = score
                    best_resource = resource
        
        if best_resource:
            allocation[task.id] = best_resource.id
            best_resource.available = False
    
    return allocation
```

This implementation has several advantages:
- O(n log n) complexity instead of O(n²)
- Proper input validation
- No memory leaks
- Better resource utilization

## Performance Comparison

| Input Size | Original | Optimized |
|------------|----------|-----------|
| 100        | 250ms    | 15ms      |
| 1000       | 25s      | 200ms     |
| 10000      | Timeout  | 2.5s      |

Let me know if you'd like me to explain any part of this implementation in more detail.""")
        
    def format_agent_response(self, agent_number, model_name):
        """Format the input text as an agent response and display it in the output panel."""
        input_text = self.input_text.toPlainText()
        
        # Define colors for different agents
        agent_colors = [
            "#1976D2",  # Blue
            "#388E3C",  # Green
            "#D32F2F",  # Red
            "#7B1FA2",  # Purple
            "#F57C00",  # Orange
        ]
        
        # Get color for this agent
        color = agent_colors[(agent_number - 1) % len(agent_colors)]
        
        # Create header - single line to avoid extra whitespace
        header = f"<div style='background-color: {color}; color: white; padding: 8px 12px; border-radius: 8px 8px 0 0; margin-top: 16px; font-weight: bold; font-family: Arial, sans-serif; font-size: 14px;'>Agent {agent_number} ({model_name})</div>"
        
        # Format the content with proper code block handling
        formatted_content = self.text_formatter.format_text_content(input_text)
        
        # Wrap in a styled div - single line to avoid extra whitespace
        formatted_response = f"{header}<div style='background-color: #F5F5F5; border: 1px solid {color}; border-radius: 0 0 8px 8px; padding: 12px; margin-bottom: 16px; font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6; color: #212121;'>{formatted_content}</div>"
        
        # Display the formatted response
        self.output_text.setHtml(formatted_response)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWhitespaceFixWindow()
    window.show()
    sys.exit(app.exec())
