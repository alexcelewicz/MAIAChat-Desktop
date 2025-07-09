#!/usr/bin/env python3
"""
Test script for the code preview functionality.
This script tests the new code preview feature to ensure it properly
displays preview buttons for HTML, CSS, and JavaScript code blocks.
"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from PyQt6.QtCore import Qt

# Import the unified response panel
from ui.unified_response_panel import UnifiedResponsePanel


class TestCodePreviewWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Code Preview Test - Unified Response Panel")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Add title
        title = QLabel("Testing Code Preview in Unified Response Panel")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Create unified response panel
        self.response_panel = UnifiedResponsePanel()
        layout.addWidget(self.response_panel)
        
        # Add test buttons
        button_layout = QVBoxLayout()
        
        test_html_btn = QPushButton("Test HTML Code with Preview")
        test_html_btn.clicked.connect(self.test_html_code)
        button_layout.addWidget(test_html_btn)
        
        test_css_btn = QPushButton("Test CSS Code with Preview")
        test_css_btn.clicked.connect(self.test_css_code)
        button_layout.addWidget(test_css_btn)
        
        test_js_btn = QPushButton("Test JavaScript Code with Preview")
        test_js_btn.clicked.connect(self.test_javascript_code)
        button_layout.addWidget(test_js_btn)
        
        test_python_btn = QPushButton("Test Python Code (No Preview)")
        test_python_btn.clicked.connect(self.test_python_code)
        button_layout.addWidget(test_python_btn)
        
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self.response_panel.clear)
        button_layout.addWidget(clear_btn)
        
        layout.addLayout(button_layout)
    
    def test_html_code(self):
        """Test HTML code with preview button."""
        html_content = """
# HTML Code Test

Here's a simple HTML page:

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
        .button {
            background-color: #2196F3;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        .button:hover {
            background-color: #1976D2;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Welcome to the Test Page</h1>
        <p>This is a test HTML page with embedded CSS and JavaScript.</p>
        <button class="button" onclick="showMessage()">Click Me!</button>
        <div id="message"></div>
    </div>
    
    <script>
        function showMessage() {
            document.getElementById('message').innerHTML = 
                '<p style="color: green; font-weight: bold;">Button clicked! JavaScript is working!</p>';
        }
    </script>
</body>
</html>
```

This HTML includes CSS styling and JavaScript functionality.
        """
        
        self.response_panel.add_agent_discussion(html_content, agent_number=1, model_name="Test Agent")
    
    def test_css_code(self):
        """Test CSS code with preview button."""
        css_content = """
# CSS Code Test

Here's some CSS styling:

```css
/* Modern CSS with gradients and animations */
body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    margin: 0;
    padding: 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
}

.container {
    max-width: 800px;
    margin: 0 auto;
    background: rgba(255, 255, 255, 0.95);
    border-radius: 15px;
    padding: 30px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
    backdrop-filter: blur(10px);
}

h1 {
    color: #2c3e50;
    text-align: center;
    margin-bottom: 30px;
    font-size: 2.5em;
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
}

.card {
    background: white;
    border-radius: 10px;
    padding: 20px;
    margin: 15px 0;
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.card:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
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
    box-shadow: 0 4px 15px rgba(33, 150, 243, 0.3);
}

.button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(33, 150, 243, 0.4);
}

.button:active {
    transform: translateY(0);
}

.alert {
    padding: 15px;
    border-radius: 8px;
    margin: 10px 0;
    border-left: 4px solid;
}

.alert-success {
    background-color: #d4edda;
    border-color: #28a745;
    color: #155724;
}

.alert-info {
    background-color: #d1ecf1;
    border-color: #17a2b8;
    color: #0c5460;
}

.alert-warning {
    background-color: #fff3cd;
    border-color: #ffc107;
    color: #856404;
}

.alert-danger {
    background-color: #f8d7da;
    border-color: #dc3545;
    color: #721c24;
}

/* Responsive design */
@media (max-width: 768px) {
    .container {
        margin: 10px;
        padding: 20px;
    }
    
    h1 {
        font-size: 2em;
    }
    
    .button {
        width: 100%;
        margin: 5px 0;
    }
}
```

This CSS includes modern styling with gradients, animations, and responsive design.
        """
        
        self.response_panel.add_agent_discussion(css_content, agent_number=2, model_name="CSS Expert")
    
    def test_javascript_code(self):
        """Test JavaScript code with preview button."""
        js_content = """
# JavaScript Code Test

Here's some JavaScript code:

```javascript
// Modern JavaScript with ES6+ features
class TodoApp {
    constructor() {
        this.todos = [];
        this.currentId = 0;
        this.init();
    }
    
    init() {
        this.createUI();
        this.bindEvents();
        this.loadFromStorage();
    }
    
    createUI() {
        const app = document.getElementById('app') || document.body;
        app.innerHTML = `
            <div class="todo-container">
                <h1>📝 Todo App</h1>
                <div class="input-section">
                    <input type="text" id="todoInput" placeholder="Add a new task..." />
                    <button id="addBtn" class="btn-primary">Add Task</button>
                </div>
                <div class="filters">
                    <button class="filter-btn active" data-filter="all">All</button>
                    <button class="filter-btn" data-filter="active">Active</button>
                    <button class="filter-btn" data-filter="completed">Completed</button>
                </div>
                <ul id="todoList" class="todo-list"></ul>
                <div class="stats">
                    <span id="taskCount">0 tasks</span>
                    <button id="clearCompleted" class="btn-secondary">Clear Completed</button>
                </div>
            </div>
        `;
    }
    
    bindEvents() {
        const addBtn = document.getElementById('addBtn');
        const todoInput = document.getElementById('todoInput');
        const todoList = document.getElementById('todoList');
        const clearCompleted = document.getElementById('clearCompleted');
        
        addBtn.addEventListener('click', () => this.addTodo());
        todoInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.addTodo();
        });
        
        todoList.addEventListener('click', (e) => {
            if (e.target.classList.contains('delete-btn')) {
                this.deleteTodo(parseInt(e.target.dataset.id));
            } else if (e.target.classList.contains('todo-checkbox')) {
                this.toggleTodo(parseInt(e.target.dataset.id));
            }
        });
        
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.setFilter(e.target.dataset.filter);
            });
        });
        
        clearCompleted.addEventListener('click', () => this.clearCompleted());
    }
    
    addTodo() {
        const input = document.getElementById('todoInput');
        const text = input.value.trim();
        
        if (text) {
            const todo = {
                id: ++this.currentId,
                text: text,
                completed: false,
                createdAt: new Date()
            };
            
            this.todos.push(todo);
            this.renderTodos();
            this.saveToStorage();
            input.value = '';
            
            console.log('✅ Task added:', todo);
        }
    }
    
    deleteTodo(id) {
        this.todos = this.todos.filter(todo => todo.id !== id);
        this.renderTodos();
        this.saveToStorage();
        console.log('🗑️ Task deleted:', id);
    }
    
    toggleTodo(id) {
        const todo = this.todos.find(t => t.id === id);
        if (todo) {
            todo.completed = !todo.completed;
            this.renderTodos();
            this.saveToStorage();
            console.log('🔄 Task toggled:', todo);
        }
    }
    
    renderTodos() {
        const todoList = document.getElementById('todoList');
        const filter = this.currentFilter || 'all';
        
        let filteredTodos = this.todos;
        if (filter === 'active') {
            filteredTodos = this.todos.filter(todo => !todo.completed);
        } else if (filter === 'completed') {
            filteredTodos = this.todos.filter(todo => todo.completed);
        }
        
        todoList.innerHTML = filteredTodos.map(todo => `
            <li class="todo-item ${todo.completed ? 'completed' : ''}">
                <input type="checkbox" class="todo-checkbox" data-id="${todo.id}" ${todo.completed ? 'checked' : ''}>
                <span class="todo-text">${todo.text}</span>
                <button class="delete-btn" data-id="${todo.id}">❌</button>
            </li>
        `).join('');
        
        this.updateStats();
    }
    
    updateStats() {
        const total = this.todos.length;
        const completed = this.todos.filter(todo => todo.completed).length;
        const active = total - completed;
        
        document.getElementById('taskCount').textContent = 
            `${active} active, ${completed} completed (${total} total)`;
    }
    
    setFilter(filter) {
        this.currentFilter = filter;
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.filter === filter);
        });
        this.renderTodos();
    }
    
    clearCompleted() {
        this.todos = this.todos.filter(todo => !todo.completed);
        this.renderTodos();
        this.saveToStorage();
        console.log('🧹 Completed tasks cleared');
    }
    
    saveToStorage() {
        localStorage.setItem('todos', JSON.stringify(this.todos));
    }
    
    loadFromStorage() {
        const stored = localStorage.getItem('todos');
        if (stored) {
            this.todos = JSON.parse(stored);
            this.currentId = Math.max(...this.todos.map(t => t.id), 0);
            this.renderTodos();
        }
    }
}

// Initialize the app when the page loads
document.addEventListener('DOMContentLoaded', () => {
    const app = new TodoApp();
    console.log('🚀 Todo App initialized!');
});
```

This JavaScript creates a fully functional todo application with modern ES6+ features.
        """
        
        self.response_panel.add_agent_discussion(js_content, agent_number=3, model_name="JavaScript Developer")
    
    def test_python_code(self):
        """Test Python code (should not show preview button)."""
        python_content = """
# Python Code Test

Here's some Python code:

```python
import asyncio
import aiohttp
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import json

@dataclass
class TodoItem:
    id: int
    title: str
    completed: bool
    created_at: datetime
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'title': self.title,
            'completed': self.completed,
            'created_at': self.created_at.isoformat()
        }

class TodoAPI:
    def __init__(self, base_url: str = "https://jsonplaceholder.typicode.com"):
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_todos(self) -> List[TodoItem]:
        """Fetch all todos from the API."""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")
        
        async with self.session.get(f"{self.base_url}/todos") as response:
            response.raise_for_status()
            data = await response.json()
            
            return [
                TodoItem(
                    id=item['id'],
                    title=item['title'],
                    completed=item['completed'],
                    created_at=datetime.now()  # API doesn't provide creation time
                )
                for item in data
            ]
    
    async def create_todo(self, title: str) -> TodoItem:
        """Create a new todo item."""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")
        
        payload = {
            'title': title,
            'completed': False,
            'userId': 1
        }
        
        async with self.session.post(f"{self.base_url}/todos", json=payload) as response:
            response.raise_for_status()
            data = await response.json()
            
            return TodoItem(
                id=data['id'],
                title=data['title'],
                completed=data['completed'],
                created_at=datetime.now()
            )
    
    async def update_todo(self, todo_id: int, **kwargs) -> TodoItem:
        """Update an existing todo item."""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")
        
        async with self.session.patch(f"{self.base_url}/todos/{todo_id}", json=kwargs) as response:
            response.raise_for_status()
            data = await response.json()
            
            return TodoItem(
                id=data['id'],
                title=data['title'],
                completed=data['completed'],
                created_at=datetime.now()
            )
    
    async def delete_todo(self, todo_id: int) -> bool:
        """Delete a todo item."""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")
        
        async with self.session.delete(f"{self.base_url}/todos/{todo_id}") as response:
            return response.status == 200

async def main():
    """Main function demonstrating the TodoAPI usage."""
    print("🚀 Starting Todo API Demo...")
    
    async with TodoAPI() as api:
        try:
            # Fetch all todos
            print("📥 Fetching todos...")
            todos = await api.get_todos()
            print(f"✅ Fetched {len(todos)} todos")
            
            # Show first 5 todos
            for todo in todos[:5]:
                status = "✅" if todo.completed else "⏳"
                print(f"{status} {todo.title}")
            
            # Create a new todo
            print("\n📝 Creating new todo...")
            new_todo = await api.create_todo("Learn async Python programming")
            print(f"✅ Created todo: {new_todo.title}")
            
            # Update the todo
            print("\n🔄 Updating todo...")
            updated_todo = await api.update_todo(new_todo.id, completed=True)
            print(f"✅ Updated todo: {updated_todo.title} (completed: {updated_todo.completed})")
            
            # Delete the todo
            print("\n🗑️ Deleting todo...")
            deleted = await api.delete_todo(new_todo.id)
            print(f"✅ Todo deleted: {deleted}")
            
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

This Python code demonstrates modern async programming with dataclasses and type hints.
        """
        
        self.response_panel.add_agent_discussion(python_content, agent_number=4, model_name="Python Developer")


def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show test window
    test_window = TestCodePreviewWindow()
    test_window.show()
    
    print("Code Preview Test Started")
    print("Use the buttons to test different code types:")
    print("1. HTML code should show a preview button")
    print("2. CSS code should show a preview button")
    print("3. JavaScript code should show a preview button")
    print("4. Python code should NOT show a preview button")
    print("5. Click the preview buttons to open the preview dialog")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 