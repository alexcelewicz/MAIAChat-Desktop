#!/usr/bin/env python3
"""
Test script for the JSON-based MCP implementation fix.
This verifies that the new format resolves the path parsing issues.
"""

import sys
import os
import json
import traceback
from pathlib import Path

# Add the parent directory to the path to import project modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_client import MCPClient
from mcp_filesystem_server import create_filesystem_server

def test_json_mcp_format():
    """Test the new JSON-based MCP format implementation."""
    print("=== Testing JSON-based MCP Format Implementation ===\n")
    
    # Test 1: Direct filesystem server with JSON format
    print("1. Testing Direct Filesystem Server with JSON Format")
    print("-" * 50)
    
    try:
        # Create a filesystem server
        test_dir = os.path.abspath(".")
        filesystem_server = create_filesystem_server(
            allowed_directory=test_dir,
            max_file_size=10 * 1024 * 1024,
            enable_logging=True
        )
        
        # Test read_file operation with JSON format
        test_file_path = os.path.join(test_dir, "requirements.txt")
        if os.path.exists(test_file_path):
            print(f"✓ Testing read_file operation on: {test_file_path}")
            result = filesystem_server.read_file(test_file_path)
            if "error" not in result:
                print(f"✓ Successfully read file: {len(result.get('content', ''))} characters")
            else:
                print(f"✗ Error reading file: {result.get('error')}")
        else:
            print(f"✗ Test file not found: {test_file_path}")
            
        # Test list_directory operation
        print(f"✓ Testing list_directory operation on: {test_dir}")
        result = filesystem_server.list_directory(test_dir)
        if "error" not in result:
            files = result.get('files', [])
            print(f"✓ Successfully listed directory: {len(files)} items found")
        else:
            print(f"✗ Error listing directory: {result.get('error')}")
            
    except Exception as e:
        print(f"✗ Direct filesystem server test failed: {str(e)}")
        traceback.print_exc()
    
    print()
    
    # Test 2: MCP Client with JSON format
    print("2. Testing MCP Client with JSON Format")
    print("-" * 50)
    
    try:
        # Initialize MCP client
        mcp_client = MCPClient()
        
        # Check if we have a Local Files server configured
        local_files_server = mcp_client.get_server("Local Files")
        if not local_files_server:
            print("⚠ No 'Local Files' server configured, setting up test server...")
            
            # Create a temporary filesystem server configuration
            from mcp_client import MCPServer
            test_server = MCPServer(
                name="Test Local Files",
                url="filesystem://local",
                description="Test filesystem server",
                enabled=True,
                server_type="filesystem",
                config_data={
                    "allowed_directory": os.path.abspath("."),
                    "max_file_size": 10,
                    "read_only": False,
                    "enable_logging": True
                }
            )
            
            # Add the test server
            mcp_client.add_server(test_server)
            local_files_server = test_server
        
        # Test JSON-formatted queries
        test_queries = [
            {
                "description": "Read requirements.txt file",
                "query": json.dumps({
                    "operation": "read_file",
                    "params": {
                        "file_path": os.path.join(os.path.abspath("."), "requirements.txt")
                    }
                })
            },
            {
                "description": "List current directory",
                "query": json.dumps({
                    "operation": "list_directory", 
                    "params": {
                        "directory_path": os.path.abspath(".")
                    }
                })
            },
            {
                "description": "Search for Python files",
                "query": json.dumps({
                    "operation": "search_files",
                    "params": {
                        "pattern": "*.py",
                        "directory": os.path.abspath("."),
                        "recursive": True
                    }
                })
            }
        ]
        
        for i, test_case in enumerate(test_queries, 1):
            print(f"Test {i}: {test_case['description']}")
            print(f"Query: {test_case['query']}")
            
            try:
                result = mcp_client.query_mcp_server(local_files_server, test_case['query'])
                
                if "error" in result:
                    print(f"✗ Error: {result['error']}")
                    if "example" in result:
                        print(f"  Example: {result['example']}")
                else:
                    print(f"✓ Success: Operation completed")
                    if "files" in result:
                        print(f"  Found {len(result['files'])} items")
                    elif "content" in result:
                        print(f"  Content length: {len(result['content'])} characters")
                    elif "matches" in result:
                        print(f"  Found {len(result['matches'])} matches")
                        
            except Exception as e:
                print(f"✗ Exception: {str(e)}")
                
            print()
            
    except Exception as e:
        print(f"✗ MCP Client test failed: {str(e)}")
        traceback.print_exc()
    
    print()
    
    # Test 3: Test error handling with malformed queries
    print("3. Testing Error Handling with Malformed Queries")
    print("-" * 50)
    
    try:
        mcp_client = MCPClient()
        local_files_server = mcp_client.get_server("Test Local Files") or mcp_client.get_server("Local Files")
        
        if local_files_server:
            # Test malformed JSON
            malformed_queries = [
                {
                    "description": "Invalid JSON syntax",
                    "query": '{"operation": "read_file", "params": {"file_path": "test.txt"'  # Missing closing brace
                },
                {
                    "description": "Missing required parameter",
                    "query": json.dumps({
                        "operation": "read_file",
                        "params": {}  # Missing file_path
                    })
                },
                {
                    "description": "Unknown operation",
                    "query": json.dumps({
                        "operation": "invalid_operation",
                        "params": {"file_path": "test.txt"}
                    })
                },
                {
                    "description": "Old colon-separated format (should fail gracefully)",
                    "query": "read_file:E:/Vibe_Coding/Python_Agents/requirements.txt"
                }
            ]
            
            for i, test_case in enumerate(malformed_queries, 1):
                print(f"Error Test {i}: {test_case['description']}")
                print(f"Query: {test_case['query']}")
                
                try:
                    result = mcp_client.query_mcp_server(local_files_server, test_case['query'])
                    
                    if "error" in result:
                        print(f"✓ Correctly handled error: {result['error']}")
                        if "example" in result:
                            print(f"  Helpful example provided: {result['example']}")
                        if "available_operations" in result:
                            print(f"  Available operations: {result['available_operations']}")
                    else:
                        print(f"✗ Unexpected success for malformed query")
                        
                except Exception as e:
                    print(f"✓ Exception properly handled: {str(e)}")
                    
                print()
        else:
            print("⚠ No filesystem server available for error testing")
            
    except Exception as e:
        print(f"✗ Error handling test failed: {str(e)}")
        traceback.print_exc()
    
    print()
    
    # Test 4: Test path format robustness
    print("4. Testing Path Format Robustness")
    print("-" * 50)
    
    try:
        # Test various path formats that should work
        test_paths = [
            os.path.join(os.path.abspath("."), "requirements.txt"),  # Standard path
            os.path.abspath(".") + "/requirements.txt",  # Mixed separators
            "./requirements.txt",  # Relative path
            "requirements.txt"  # Just filename
        ]
        
        filesystem_server = create_filesystem_server(
            allowed_directory=os.path.abspath("."),
            max_file_size=10 * 1024 * 1024,
            enable_logging=True
        )
        
        for i, test_path in enumerate(test_paths, 1):
            print(f"Path Test {i}: {test_path}")
            
            try:
                result = filesystem_server.read_file(test_path)
                
                if "error" not in result:
                    print(f"✓ Successfully handled path format")
                else:
                    print(f"✗ Path format failed: {result['error']}")
                    
            except Exception as e:
                print(f"✗ Exception with path format: {str(e)}")
                
            print()
            
    except Exception as e:
        print(f"✗ Path format test failed: {str(e)}")
        traceback.print_exc()
    
    print("=== JSON-based MCP Format Testing Complete ===")

if __name__ == "__main__":
    test_json_mcp_format() 