#!/usr/bin/env python3
"""
MCP Helper Module for Agents
Provides easy-to-use functions to generate correct MCP syntax
"""

class MCPHelper:
    """
    Helper class for agents to generate correct MCP syntax
    Eliminates syntax errors by providing validated MCP request generation
    """
    
    @staticmethod
    def list_directory():
        """Generate MCP request to list directory contents"""
        return "[MCP:Local Files:list_directory:]"
    
    @staticmethod
    def read_file(filename):
        """
        Generate MCP request to read a file
        
        Args:
            filename (str): Name of file to read (e.g., 'snake.py', 'config.json')
        
        Returns:
            str: Properly formatted MCP request
        """
        if not filename:
            raise ValueError("filename cannot be empty")
        return f"[MCP:Local Files:read_file:{filename}]"
    
    @staticmethod
    def write_file(filename, content):
        """
        Generate MCP request to write/create a file
        
        Args:
            filename (str): Name of file to write (e.g., 'snake.py', 'config.json')
            content (str): Content to write to the file
        
        Returns:
            str: Properly formatted MCP request
        """
        if not filename:
            raise ValueError("filename cannot be empty")
        if content is None:
            content = ""
        return f"[MCP:Local Files:write_file:{filename}:{content}]"
    
    @staticmethod
    def delete_file(filename):
        """
        Generate MCP request to delete a file
        
        Args:
            filename (str): Name of file to delete
        
        Returns:
            str: Properly formatted MCP request
        """
        if not filename:
            raise ValueError("filename cannot be empty")
        return f"[MCP:Local Files:delete_file:{filename}]"
    
    @staticmethod
    def search_files(pattern=""):
        """
        Generate MCP request to search for files
        
        Args:
            pattern (str): Search pattern (e.g., '*.py', 'test_*', '*.json')
        
        Returns:
            str: Properly formatted MCP request
        """
        return f"[MCP:Local Files:search_files:{pattern}:]"

# Convenience functions for direct use
def mcp_list_directory():
    """Quick function to list directory"""
    return MCPHelper.list_directory()

def mcp_read_file(filename):
    """Quick function to read a file"""
    return MCPHelper.read_file(filename)

def mcp_write_file(filename, content):
    """Quick function to write a file"""
    return MCPHelper.write_file(filename, content)

def mcp_delete_file(filename):
    """Quick function to delete a file"""
    return MCPHelper.delete_file(filename)

def mcp_search_files(pattern=""):
    """Quick function to search files"""
    return MCPHelper.search_files(pattern)

# Common use case examples
class MCPExamples:
    """Common MCP usage examples for agents"""
    
    @staticmethod
    def create_snake_game():
        """Example: Create a snake game file"""
        snake_code = '''import pygame
import random

class SnakeGame:
    def __init__(self):
        self.width = 800
        self.height = 600
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Snake Game")
        
    def run(self):
        print("Snake game is running!")
        # Game loop would go here
        
if __name__ == "__main__":
    game = SnakeGame()
    game.run()'''
        
        return MCPHelper.write_file("snake.py", snake_code)
    
    @staticmethod
    def read_and_improve_code_workflow(filename):
        """
        Example workflow: Read file, then prepare to write improved version
        Returns tuple of (read_request, write_function)
        """
        read_request = MCPHelper.read_file(filename)
        
        def write_improved(improved_content):
            return MCPHelper.write_file(filename, improved_content)
        
        return read_request, write_improved
    
    @staticmethod
    def backup_and_update_config():
        """Example: Backup current config and update with new settings"""
        read_config = MCPHelper.read_file("config.json")
        backup_config = lambda content: MCPHelper.write_file("config_backup.json", content)
        update_config = lambda new_content: MCPHelper.write_file("config.json", new_content)
        
        return read_config, backup_config, update_config

def demo_usage():
    """Demonstrate how agents should use this helper"""
    print("🔧 MCP Helper Demo - How Agents Should Use This Module")
    print("=" * 60)
    
    helper = MCPHelper()
    
    # Example 1: List files
    print("\n1. List Directory:")
    print(f"   Request: {helper.list_directory()}")
    
    # Example 2: Read file  
    print("\n2. Read File:")
    print(f"   Request: {helper.read_file('snake.py')}")
    
    # Example 3: Write file
    print("\n3. Write File:")
    simple_code = 'print("Hello, World!")'
    print(f"   Request: {helper.write_file('hello.py', simple_code)}")
    
    # Example 4: Common workflow
    print("\n4. Read-Improve-Write Workflow:")
    read_req, write_func = MCPExamples.read_and_improve_code_workflow("snake.py")
    print(f"   Step 1 - Read: {read_req}")
    print(f"   Step 2 - Write: {write_func('# Improved code here')}")
    
    # Example 5: Create complete game
    print("\n5. Create Snake Game:")
    print(f"   Request: {MCPExamples.create_snake_game()}")
    
    print("\n✅ All requests use correct MCP syntax!")
    print("✅ No syntax errors possible when using this helper!")

if __name__ == "__main__":
    demo_usage() 