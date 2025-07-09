#!/usr/bin/env python3
"""
Direct file operations that bypass MCP syntax entirely
These methods work regardless of MCP configuration
"""

import os
import json
from pathlib import Path

class DirectFileOperations:
    """Direct file operations without MCP dependency"""
    
    @staticmethod
    def write_file_direct(filename: str, content: str) -> bool:
        """Write file directly using Python's built-in file operations"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Direct write successful: {filename}")
            return True
        except Exception as e:
            print(f"❌ Direct write failed: {e}")
            return False
    
    @staticmethod
    def read_file_direct(filename: str) -> str:
        """Read file directly using Python's built-in file operations"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"✅ Direct read successful: {filename}")
            return content
        except Exception as e:
            print(f"❌ Direct read failed: {e}")
            return ""
    
    @staticmethod
    def list_files_direct(directory: str = ".") -> list:
        """List files directly using pathlib"""
        try:
            path = Path(directory)
            files = [f.name for f in path.iterdir() if f.is_file()]
            print(f"✅ Direct listing successful: {len(files)} files found")
            return files
        except Exception as e:
            print(f"❌ Direct listing failed: {e}")
            return []
    
    @staticmethod
    def delete_file_direct(filename: str) -> bool:
        """Delete file directly using os.remove"""
        try:
            os.remove(filename)
            print(f"✅ Direct deletion successful: {filename}")
            return True
        except Exception as e:
            print(f"❌ Direct deletion failed: {e}")
            return False

def demo_direct_operations():
    """Demonstrate direct file operations without MCP"""
    print("🔧 Direct File Operations Demo (No MCP Required)")
    
    ops = DirectFileOperations()
    
    # Create a test file
    test_content = '''def hello_world():
    print("Hello from direct file operations!")
    return "No MCP syntax required!"

if __name__ == "__main__":
    hello_world()
'''
    
    # Write file directly
    print("\n1. Writing file directly...")
    success = ops.write_file_direct("direct_test.py", test_content)
    
    if success:
        # Read it back
        print("\n2. Reading file directly...")
        content = ops.read_file_direct("direct_test.py")
        print(f"Content length: {len(content)} characters")
        
        # List files
        print("\n3. Listing files directly...")
        files = ops.list_files_direct(".")
        python_files = [f for f in files if f.endswith('.py')]
        print(f"Python files found: {python_files[:5]}...")  # Show first 5
        
        # Clean up
        print("\n4. Cleaning up...")
        ops.delete_file_direct("direct_test.py")

if __name__ == "__main__":
    demo_direct_operations() 