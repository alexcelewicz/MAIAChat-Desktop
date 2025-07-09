"""
Test script to demonstrate the improved code formatting functionality.
This script shows how code blocks are now properly formatted with indentation and syntax highlighting.
"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTextEdit, QPushButton, QLabel
from PyQt6.QtCore import Qt
from ui.unified_response_panel import UnifiedResponsePanel

class TestCodeFormattingWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Code Formatting Test - Unified Response Panel")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Add title
        title = QLabel("Testing Code Formatting in Unified Response Panel")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Create unified response panel
        self.response_panel = UnifiedResponsePanel()
        layout.addWidget(self.response_panel)
        
        # Add test buttons
        button_layout = QVBoxLayout()
        
        test_python_btn = QPushButton("Test Python Code")
        test_python_btn.clicked.connect(self.test_python_code)
        button_layout.addWidget(test_python_btn)
        
        test_javascript_btn = QPushButton("Test JavaScript Code")
        test_javascript_btn.clicked.connect(self.test_javascript_code)
        button_layout.addWidget(test_javascript_btn)
        
        test_html_btn = QPushButton("Test HTML Code")
        test_html_btn.clicked.connect(self.test_html_code)
        button_layout.addWidget(test_html_btn)
        
        test_css_btn = QPushButton("Test CSS Code")
        test_css_btn.clicked.connect(self.test_css_code)
        button_layout.addWidget(test_css_btn)
        
        test_json_btn = QPushButton("Test JSON Code")
        test_json_btn.clicked.connect(self.test_json_code)
        button_layout.addWidget(test_json_btn)
        
        test_mixed_btn = QPushButton("Test Mixed Content")
        test_mixed_btn.clicked.connect(self.test_mixed_content)
        button_layout.addWidget(test_mixed_btn)
        
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self.response_panel.clear)
        button_layout.addWidget(clear_btn)
        
        layout.addLayout(button_layout)
    
    def test_python_code(self):
        """Test Python code formatting"""
        python_code = """# Python Code Example
def fibonacci(n):
    \"\"\"
    Calculate the nth Fibonacci number using recursion.
    This is a docstring example.
    \"\"\"
    if n <= 1:
        return n
    else:
        return fibonacci(n-1) + fibonacci(n-2)

# Example usage
for i in range(10):
    if i % 2 == 0:
        print(f"Even Fibonacci number {i}: {fibonacci(i)}")
    else:
        print(f"Odd Fibonacci number {i}: {fibonacci(i)}")

# Class example
class Calculator:
    def __init__(self):
        self.result = 0
    
    def add(self, x, y):
        return x + y
    
    def multiply(self, x, y):
        return x * y"""
        
        self.response_panel.add_agent_discussion(
            f"Here's an example of Python code with proper formatting:\n\n```python\n{python_code}\n```\n\nThis code demonstrates functions, classes, loops, and comments.",
            agent_number=1,
            model_name="GPT-4",
            is_first_chunk=True
        )
    
    def test_javascript_code(self):
        """Test JavaScript code formatting"""
        javascript_code = """// JavaScript Code Example
function calculateFactorial(n) {
    // Base case
    if (n <= 1) {
        return 1;
    }
    
    // Recursive case
    return n * calculateFactorial(n - 1);
}

// Arrow function example
const multiply = (a, b) => a * b;

// Class example
class Person {
    constructor(name, age) {
        this.name = name;
        this.age = age;
    }
    
    greet() {
        return `Hello, my name is ${this.name} and I'm ${this.age} years old.`;
    }
}

// Async function example
async function fetchData(url) {
    try {
        const response = await fetch(url);
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching data:', error);
        throw error;
    }
}"""
        
        self.response_panel.add_agent_discussion(
            f"Here's an example of JavaScript code with proper formatting:\n\n```javascript\n{javascript_code}\n```\n\nThis code demonstrates functions, classes, async/await, and modern JavaScript features.",
            agent_number=2,
            model_name="Claude-3",
            is_first_chunk=True
        )
    
    def test_html_code(self):
        """Test HTML code formatting"""
        html_code = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Example HTML Page</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <header>
        <h1>Welcome to My Website</h1>
        <nav>
            <ul>
                <li><a href="#home">Home</a></li>
                <li><a href="#about">About</a></li>
                <li><a href="#contact">Contact</a></li>
            </ul>
        </nav>
    </header>
    
    <main>
        <section id="content">
            <h2>Main Content</h2>
            <p>This is a paragraph with <strong>bold text</strong> and <em>italic text</em>.</p>
            
            <!-- This is an HTML comment -->
            <div class="container">
                <button onclick="handleClick()">Click Me</button>
            </div>
        </section>
    </main>
    
    <footer>
        <p>&copy; 2024 My Website. All rights reserved.</p>
    </footer>
</body>
</html>"""
        
        self.response_panel.add_agent_discussion(
            f"Here's an example of HTML code with proper formatting:\n\n```html\n{html_code}\n```\n\nThis HTML demonstrates proper structure, semantic elements, and comments.",
            agent_number=3,
            model_name="Gemini",
            is_first_chunk=True
        )
    
    def test_css_code(self):
        """Test CSS code formatting"""
        css_code = """/* CSS Code Example */
.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
    background-color: #f5f5f5;
}

/* Header styles */
header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1rem;
    border-radius: 8px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

/* Navigation styles */
nav ul {
    list-style: none;
    display: flex;
    gap: 20px;
    margin: 0;
    padding: 0;
}

nav a {
    color: white;
    text-decoration: none;
    transition: color 0.3s ease;
}

nav a:hover {
    color: #ffd700;
}

/* Button styles */
.btn {
    background-color: #007bff;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.3s ease;
}

.btn:hover {
    background-color: #0056b3;
}

/* Responsive design */
@media (max-width: 768px) {
    .container {
        padding: 10px;
    }
    
    nav ul {
        flex-direction: column;
        gap: 10px;
    }
}"""
        
        self.response_panel.add_agent_discussion(
            f"Here's an example of CSS code with proper formatting:\n\n```css\n{css_code}\n```\n\nThis CSS demonstrates selectors, properties, media queries, and comments.",
            agent_number=4,
            model_name="CodeLlama",
            is_first_chunk=True
        )
    
    def test_json_code(self):
        """Test JSON code formatting"""
        json_code = """{
    "name": "John Doe",
    "age": 30,
    "email": "john.doe@example.com",
    "isActive": true,
    "address": {
        "street": "123 Main St",
        "city": "Anytown",
        "state": "CA",
        "zipCode": "12345"
    },
    "phoneNumbers": [
        {
            "type": "home",
            "number": "555-123-4567"
        },
        {
            "type": "work",
            "number": "555-987-6543"
        }
    ],
    "skills": [
        "Python",
        "JavaScript",
        "HTML",
        "CSS",
        "SQL"
    ],
    "metadata": {
        "createdAt": "2024-01-15T10:30:00Z",
        "lastModified": "2024-01-20T14:45:00Z",
        "version": "1.0.0"
    }
}"""
        
        self.response_panel.add_agent_discussion(
            f"Here's an example of JSON code with proper formatting:\n\n```json\n{json_code}\n```\n\nThis JSON demonstrates nested objects, arrays, and various data types.",
            agent_number=5,
            model_name="Mistral",
            is_first_chunk=True
        )
    
    def test_mixed_content(self):
        """Test mixed content with headers, paragraphs, and code blocks"""
        mixed_content = """# Code Formatting Test

This is a comprehensive test of the improved code formatting functionality in the Unified Response Panel.

## Python Example

Here's a simple Python function:

```python
def greet_user(name):
    # This is a comment
    message = f"Hello, {name}!"
    return message

# Usage
result = greet_user("World")
print(result)
```

## JavaScript Example

And here's a JavaScript equivalent:

```javascript
function greetUser(name) {
    // This is a comment
    const message = `Hello, ${name}!`;
    return message;
}

// Usage
const result = greetUser("World");
console.log(result);
```

## HTML Structure

Here's a simple HTML structure:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Example</title>
</head>
<body>
    <h1>Hello World</h1>
    <p>This is a paragraph.</p>
</body>
</html>
```

## Final Answer

The code formatting now properly handles:
- **Indentation preservation** using `<pre>` tags
- **Syntax highlighting** for multiple languages
- **Proper spacing** and typography
- **Language-specific background colors**
- **Comment highlighting** in various languages

This makes the code much more readable and professional-looking!"""
        
        self.response_panel.add_agent_discussion(
            mixed_content,
            agent_number=6,
            model_name="Mixed-Test",
            is_first_chunk=True
        )

def main():
    app = QApplication(sys.argv)
    window = TestCodeFormattingWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 