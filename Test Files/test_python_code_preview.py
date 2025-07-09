#!/usr/bin/env python3
"""
Test script for the Python code preview functionality.
This script tests the new Python code preview feature to ensure it properly
displays preview buttons for Python code blocks and allows execution and download.
"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PyQt6.QtCore import Qt

# Import the unified response panel
from ui.unified_response_panel import UnifiedResponsePanel


class TestPythonPreviewWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python Code Preview Test - Unified Response Panel")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Add title
        title = QLabel("Testing Python Code Preview in Unified Response Panel")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Add description
        description = QLabel("This test demonstrates the new Python code preview functionality with execution and download capabilities.")
        description.setStyleSheet("margin: 10px; color: #666;")
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Create unified response panel
        self.response_panel = UnifiedResponsePanel()
        layout.addWidget(self.response_panel)
        
        # Add test buttons
        button_layout = QVBoxLayout()
        
        test_simple_btn = QPushButton("Test Simple Python Code")
        test_simple_btn.clicked.connect(self.test_simple_python)
        test_simple_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
        """)
        button_layout.addWidget(test_simple_btn)
        
        test_advanced_btn = QPushButton("Test Advanced Python Code")
        test_advanced_btn.clicked.connect(self.test_advanced_python)
        test_advanced_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        button_layout.addWidget(test_advanced_btn)
        
        test_data_analysis_btn = QPushButton("Test Data Analysis Python Code")
        test_data_analysis_btn.clicked.connect(self.test_data_analysis_python)
        test_data_analysis_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        button_layout.addWidget(test_data_analysis_btn)
        
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self.response_panel.clear)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        button_layout.addWidget(clear_btn)
        
        layout.addLayout(button_layout)
    
    def test_simple_python(self):
        """Test simple Python code with preview and execution."""
        python_content = '''
# Simple Python Code Test

Here's a simple Python script that demonstrates basic functionality:

```python
#!/usr/bin/env python3
# Simple Python script demonstration.
# This script shows basic Python features including:
# - Variables and data types
# - Functions
# - Control structures
# - String formatting

# Basic variables
name = "Python Code Preview"
version = "1.0"
features = ["Execution", "Analysis", "Download", "Syntax Highlighting"]

def greet_user(name):
    # Greet the user with a personalized message.
    return f"🐍 Hello from {name}! Welcome to the Python preview feature."

def demonstrate_features():
    # Demonstrate various Python features.
    print("="*50)
    print("🚀 Python Code Preview Demo")
    print("="*50)
    
    # String operations
    message = greet_user(name)
    print(message)
    
    # List operations
    print(f"\\n📋 Available features:")
    for i, feature in enumerate(features, 1):
        print(f"  {i}. {feature}")
    
    # Dictionary operations
    info = {
        "Language": "Python",
        "Version": version,
        "Features": len(features),
        "Status": "Active"
    }
    
    print(f"\\n📊 Script Information:")
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    # Mathematical operations
    numbers = [1, 2, 3, 4, 5]
    total = sum(numbers)
    average = total / len(numbers)
    
    print(f"\\n🔢 Math Demo:")
    print(f"  Numbers: {numbers}")
    print(f"  Sum: {total}")
    print(f"  Average: {average:.2f}")
    
    # Success message
    print("\\n✅ All features demonstrated successfully!")
    print("🎉 Python code preview is working perfectly!")

if __name__ == "__main__":
    demonstrate_features()
```

**Instructions:**
1. Look for the "🐍 Preview & Execute PYTHON" button below this code block
2. Click the preview button to open the Python preview dialog
3. In the preview dialog, you can:
   - See code analysis in the "Code Analysis" tab
   - Click "Execute Python" to run the code and see output
   - Click "Save File" to download the Python script
   - Edit the code and re-execute it

This demonstrates the full Python code preview functionality!
        '''
        
        self.response_panel.add_agent_discussion(python_content, agent_number=1, model_name="Python Demo Agent", is_first_chunk=True)
    
    def test_advanced_python(self):
        """Test advanced Python code with classes and modules."""
        python_content = '''
# Advanced Python Code Test

Here's a more advanced Python script demonstrating object-oriented programming:

```python
#!/usr/bin/env python3
# Advanced Python demonstration with classes, inheritance, and decorators.
# This script showcases more complex Python features.

import datetime
import json
from typing import List, Dict, Optional

class Task:
    # Represents a task in our todo application.
    
    def __init__(self, task_id, title, description):
        self.id = task_id
        self.title = title
        self.description = description
        self.completed = False
        self.created_at = datetime.datetime.now()
    
    def to_dict(self):
        # Convert task to dictionary.
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'completed': self.completed,
            'created_at': self.created_at.isoformat()
        }

class TodoManager:
    # Advanced todo manager with various operations.
    
    def __init__(self):
        self.tasks = []
        self.next_id = 1
    
    def add_task(self, title, description):
        # Add a new task.
        task = Task(self.next_id, title, description)
        self.tasks.append(task)
        self.next_id += 1
        print(f"✅ Task added: {title}")
        return task
    
    def complete_task(self, task_id):
        # Mark a task as completed.
        task = self.get_task(task_id)
        if task:
            task.completed = True
            print(f"🎉 Task completed: {task.title}")
            return True
        print(f"❌ Task {task_id} not found")
        return False
    
    def get_task(self, task_id):
        # Get a task by ID.
        return next((task for task in self.tasks if task.id == task_id), None)
    
    def list_tasks(self, completed=None):
        # List tasks with optional filter.
        filtered_tasks = self.tasks
        if completed is not None:
            filtered_tasks = [task for task in self.tasks if task.completed == completed]
        
        if not filtered_tasks:
            print("📝 No tasks found")
            return
        
        status_filter = "completed" if completed is True else "pending" if completed is False else "all"
        print(f"\\n📋 Tasks ({status_filter}):")
        print("-" * 60)
        
        for task in filtered_tasks:
            status = "✅" if task.completed else "⏳"
            age = (datetime.datetime.now() - task.created_at).days
            print(f"{status} [{task.id}] {task.title}")
            print(f"    {task.description}")
            print(f"    Created: {age} days ago")
            print()
    
    def get_statistics(self):
        # Get task statistics.
        total = len(self.tasks)
        completed = sum(1 for task in self.tasks if task.completed)
        pending = total - completed
        
        return {
            'total': total,
            'completed': completed,
            'pending': pending,
            'completion_rate': (completed / total * 100) if total > 0 else 0
        }

def main():
    # Main demonstration function.
    print("🚀 Advanced Python Todo Manager Demo")
    print("=" * 50)
    
    # Create todo manager
    todo_manager = TodoManager()
    
    # Add some tasks
    todo_manager.add_task("Learn Python", "Master Python programming fundamentals")
    todo_manager.add_task("Build GUI App", "Create a desktop application with PyQt6")
    todo_manager.add_task("Write Tests", "Add comprehensive unit tests")
    
    # Complete some tasks
    todo_manager.complete_task(1)
    todo_manager.complete_task(2)
    
    # Show all tasks
    todo_manager.list_tasks()
    
    # Show statistics
    stats = todo_manager.get_statistics()
    print("📊 Statistics:")
    print(f"  Total tasks: {stats['total']}")
    print(f"  Completed: {stats['completed']}")
    print(f"  Pending: {stats['pending']}")
    print(f"  Completion rate: {stats['completion_rate']:.1f}%")
    
    print("\\n✨ Advanced Python features demonstrated!")

if __name__ == "__main__":
    main()
```

This advanced example showcases object-oriented programming and more complex Python features.
        '''
        
        self.response_panel.add_agent_discussion(python_content, agent_number=2, model_name="Advanced Python Developer", is_first_chunk=True)
    
    def test_data_analysis_python(self):
        """Test data analysis Python code."""
        python_content = '''
# Data Analysis Python Code Test

Here's a data analysis script demonstrating scientific computing capabilities:

```python
#!/usr/bin/env python3
# Data Analysis and Visualization Script
# This script demonstrates data analysis capabilities using built-in Python libraries.

import random
import statistics
from collections import Counter

class DataAnalyzer:
    # Simple data analyzer using built-in Python libraries.
    
    def __init__(self):
        self.sales_data = []
    
    def generate_sample_data(self, size=50):
        # Generate sample data for analysis.
        print(f"📊 Generating {size} sample data points...")
        
        categories = ['Electronics', 'Clothing', 'Books', 'Home', 'Sports']
        
        for i in range(size):
            record = {
                'id': i + 1,
                'category': random.choice(categories),
                'sales': round(random.uniform(100, 1000), 2),
                'quantity': random.randint(1, 20),
                'month': random.randint(1, 12),
                'customer_rating': round(random.uniform(1, 5), 1)
            }
            self.sales_data.append(record)
        
        print(f"✅ Generated {len(self.sales_data)} records")
        return self.sales_data
    
    def basic_statistics(self):
        # Calculate basic statistics.
        if not self.sales_data:
            print("❌ No data available for analysis")
            return
        
        sales_values = [record['sales'] for record in self.sales_data]
        quantities = [record['quantity'] for record in self.sales_data]
        ratings = [record['customer_rating'] for record in self.sales_data]
        
        print("\\n📈 Basic Statistics:")
        print("-" * 40)
        
        # Sales statistics
        print("💰 Sales Analysis:")
        print(f"  Total Sales: ${sum(sales_values):,.2f}")
        print(f"  Average Sale: ${statistics.mean(sales_values):.2f}")
        print(f"  Median Sale: ${statistics.median(sales_values):.2f}")
        print(f"  Min Sale: ${min(sales_values):.2f}")
        print(f"  Max Sale: ${max(sales_values):.2f}")
        
        # Quantity statistics
        print("\\n📦 Quantity Analysis:")
        print(f"  Total Items Sold: {sum(quantities):,}")
        print(f"  Average Quantity: {statistics.mean(quantities):.1f}")
        
        # Rating statistics
        print("\\n⭐ Customer Rating Analysis:")
        print(f"  Average Rating: {statistics.mean(ratings):.2f}/5.0")
        print(f"  Highest Rating: {max(ratings)}")
        print(f"  Lowest Rating: {min(ratings)}")
    
    def category_analysis(self):
        # Analyze data by category.
        if not self.sales_data:
            return
        
        print("\\n🏷️ Category Analysis:")
        print("-" * 40)
        
        # Group data by category
        category_totals = {}
        for record in self.sales_data:
            category = record['category']
            if category not in category_totals:
                category_totals[category] = {'sales': 0, 'count': 0}
            category_totals[category]['sales'] += record['sales']
            category_totals[category]['count'] += 1
        
        for category, data in category_totals.items():
            avg_sale = data['sales'] / data['count']
            print(f"\\n📊 {category}:")
            print(f"  Total Sales: ${data['sales']:,.2f}")
            print(f"  Number of Sales: {data['count']}")
            print(f"  Average Sale: ${avg_sale:.2f}")

def main():
    # Main analysis function.
    print("🔬 Data Analysis Demo")
    print("=" * 50)
    
    # Create analyzer and generate data
    analyzer = DataAnalyzer()
    analyzer.generate_sample_data(30)
    
    # Perform various analyses
    analyzer.basic_statistics()
    analyzer.category_analysis()
    
    print("\\n✨ Analysis completed successfully!")
    print("\\n🎯 Features demonstrated:")
    print("  • Data generation and manipulation")
    print("  • Statistical calculations")
    print("  • Data grouping and aggregation")
    print("  • Object-oriented data analysis")

if __name__ == "__main__":
    main()
```

This example demonstrates data analysis capabilities using Python's built-in libraries.
        '''
        
        self.response_panel.add_agent_discussion(python_content, agent_number=3, model_name="Data Analysis Expert", is_first_chunk=True)


def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show test window
    test_window = TestPythonPreviewWindow()
    test_window.show()
    
    print("Python Code Preview Test Started")
    print("Use the buttons to test different Python code types:")
    print("1. Simple Python - Basic functionality demonstration")  
    print("2. Advanced Python - Classes, decorators, and OOP")
    print("3. Data Analysis - Statistical analysis and data manipulation")
    print("4. All Python code should show preview buttons")
    print("5. Click the preview buttons to open the Python preview dialog")
    print("6. Test the execution and download functionality")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 