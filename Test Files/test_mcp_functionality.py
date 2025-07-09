#!/usr/bin/env python3
"""
MCP Functionality Test Script
Tests all MCP operations with the "Local Files" server to ensure proper functionality.
"""

import sys
import os
import time
import json
import traceback
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_client import MCPClient, MCPServer

class MCPTester:
    """Comprehensive MCP functionality tester."""
    
    def __init__(self):
        self.client = MCPClient()
        self.test_results = []
        self.server_name = "Local Files"
        
    def log_test(self, test_name, success, details="", error=None):
        """Log test results."""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "error": str(error) if error else None,
            "timestamp": time.strftime("%H:%M:%S")
        }
        self.test_results.append(result)
        print(f"{status} | {test_name}")
        if details:
            print(f"    Details: {details}")
        if error:
            print(f"    Error: {error}")
        print()
    
    def test_server_configuration(self):
        """Test 1: Server Configuration"""
        try:
            server = self.client.get_server(self.server_name)
            if not server:
                self.log_test("Server Configuration", False, "Server not found")
                return False
            
            if not server.enabled:
                self.log_test("Server Configuration", False, "Server is disabled")
                return False
            
            if not hasattr(server, 'server_type') or server.server_type != 'filesystem':
                self.log_test("Server Configuration", False, "Missing or incorrect server_type")
                return False
            
            expected_capabilities = ['list_directory', 'read_file', 'write_file', 'delete_file', 'search_files', 'get_file_info']
            missing_caps = [cap for cap in expected_capabilities if cap not in server.capabilities]
            
            if missing_caps:
                self.log_test("Server Configuration", False, f"Missing capabilities: {missing_caps}")
                return False
            
            self.log_test("Server Configuration", True, f"Server properly configured with {len(server.capabilities)} capabilities")
            return True
            
        except Exception as e:
            self.log_test("Server Configuration", False, error=e)
            return False
    
    def test_list_directory(self):
        """Test 2: List Directory Operation"""
        try:
            server = self.client.get_server(self.server_name)
            result = self.client.query_mcp_server(server, "list_directory:./")
            
            if 'error' in result:
                self.log_test("List Directory", False, f"MCP Error: {result['error']}")
                return False
            
            if 'items' not in result:
                self.log_test("List Directory", False, "No 'items' in result")
                return False
            
            items_count = len(result['items'])
            total_items = result.get('total_items', items_count)
            
            # Check if snake.py is in the results
            snake_found = any(item['name'] == 'snake.py' for item in result['items'])
            
            details = f"Found {items_count} items (total: {total_items})"
            if snake_found:
                details += ", snake.py found"
            
            self.log_test("List Directory", True, details)
            return True
            
        except Exception as e:
            self.log_test("List Directory", False, error=e)
            return False
    
    def test_read_file(self):
        """Test 3: Read File Operation"""
        try:
            server = self.client.get_server(self.server_name)
            result = self.client.query_mcp_server(server, "read_file:snake.py")
            
            if 'error' in result:
                self.log_test("Read File", False, f"MCP Error: {result['error']}")
                return False
            
            if 'content' not in result:
                self.log_test("Read File", False, "No 'content' in result")
                return False
            
            content = result['content']
            content_length = len(content)
            
            # Check if it looks like Python code
            is_python = 'import' in content or 'def ' in content or 'class ' in content
            
            details = f"Read {content_length} characters"
            if is_python:
                details += ", valid Python code detected"
            
            self.log_test("Read File", True, details)
            return True
            
        except Exception as e:
            self.log_test("Read File", False, error=e)
            return False
    
    def test_write_file(self):
        """Test 4: Write File Operation"""
        test_filename = "mcp_test_file.txt"
        test_content = f"MCP Test File\nCreated at: {time.strftime('%Y-%m-%d %H:%M:%S')}\nThis is a test of MCP write functionality."
        
        try:
            server = self.client.get_server(self.server_name)
            result = self.client.query_mcp_server(server, f"write_file:{test_filename}:{test_content}")
            
            if 'error' in result:
                self.log_test("Write File", False, f"MCP Error: {result['error']}")
                return False
            
            # Verify the file was actually created
            if not os.path.exists(test_filename):
                self.log_test("Write File", False, "File was not created on disk")
                return False
            
            # Read back the content to verify
            with open(test_filename, 'r') as f:
                written_content = f.read()
            
            if written_content != test_content:
                self.log_test("Write File", False, "Written content doesn't match expected")
                return False
            
            file_size = os.path.getsize(test_filename)
            self.log_test("Write File", True, f"Created {test_filename} ({file_size} bytes)")
            return True
            
        except Exception as e:
            self.log_test("Write File", False, error=e)
            return False
    
    def test_get_file_info(self):
        """Test 5: Get File Info Operation"""
        try:
            server = self.client.get_server(self.server_name)
            result = self.client.query_mcp_server(server, "get_file_info:snake.py")
            
            if 'error' in result:
                self.log_test("Get File Info", False, f"MCP Error: {result['error']}")
                return False
            
            expected_fields = ['type', 'size']
            missing_fields = [field for field in expected_fields if field not in result]
            
            if missing_fields:
                self.log_test("Get File Info", False, f"Missing fields: {missing_fields}")
                return False
            
            file_type = result.get('type', 'unknown')
            file_size = result.get('size', 0)
            
            details = f"Type: {file_type}, Size: {file_size} bytes"
            self.log_test("Get File Info", True, details)
            return True
            
        except Exception as e:
            self.log_test("Get File Info", False, error=e)
            return False
    
    def test_search_files(self):
        """Test 6: Search Files Operation"""
        try:
            server = self.client.get_server(self.server_name)
            result = self.client.query_mcp_server(server, "search_files:*.py")
            
            if 'error' in result:
                self.log_test("Search Files", False, f"MCP Error: {result['error']}")
                return False
            
            if 'matches' not in result:
                self.log_test("Search Files", False, "No 'matches' in result")
                return False
            
            matches = result['matches']
            match_count = len(matches)
            
            # Check if snake.py is in the matches
            snake_found = any(match['name'] == 'snake.py' for match in matches)
            
            details = f"Found {match_count} Python files"
            if snake_found:
                details += ", snake.py included"
            
            self.log_test("Search Files", True, details)
            return True
            
        except Exception as e:
            self.log_test("Search Files", False, error=e)
            return False
    
    def test_delete_file(self):
        """Test 7: Delete File Operation"""
        test_filename = "mcp_test_file.txt"
        
        # Only run if the test file exists from previous test
        if not os.path.exists(test_filename):
            self.log_test("Delete File", False, "Test file doesn't exist (write test may have failed)")
            return False
        
        try:
            server = self.client.get_server(self.server_name)
            result = self.client.query_mcp_server(server, f"delete_file:{test_filename}")
            
            if 'error' in result:
                self.log_test("Delete File", False, f"MCP Error: {result['error']}")
                return False
            
            # Verify the file was actually deleted
            if os.path.exists(test_filename):
                self.log_test("Delete File", False, "File still exists on disk")
                return False
            
            self.log_test("Delete File", True, f"Successfully deleted {test_filename}")
            return True
            
        except Exception as e:
            self.log_test("Delete File", False, error=e)
            return False
    
    def test_error_handling(self):
        """Test 8: Error Handling"""
        try:
            server = self.client.get_server(self.server_name)
            
            # Test reading non-existent file
            result = self.client.query_mcp_server(server, "read_file:nonexistent_file_12345.txt")
            
            if 'error' not in result:
                self.log_test("Error Handling", False, "Should return error for non-existent file")
                return False
            
            error_msg = result['error']
            self.log_test("Error Handling", True, f"Properly returned error: {error_msg}")
            return True
            
        except Exception as e:
            self.log_test("Error Handling", False, error=e)
            return False
    
    def test_result_formatting(self):
        """Test 9: Result Formatting"""
        try:
            from worker import Worker
            
            # Create a mock worker to test formatting
            worker = Worker("test", "", [], [], config_manager=None)
            
            # Test filesystem result formatting
            mock_result = {
                'items': [
                    {'name': 'test.py', 'type': 'file', 'size': 1234},
                    {'name': 'folder', 'type': 'directory', 'size': None}
                ],
                'total_items': 2,
                'path': './'
            }
            
            formatted = worker.format_mcp_filesystem_results(mock_result, "list_directory:./", "Local Files")
            
            # Check if formatting includes expected elements
            expected_elements = ['Directory:', 'Total Items:', 'Contents:', '📁', '📄']
            missing_elements = [elem for elem in expected_elements if elem not in formatted]
            
            if missing_elements:
                self.log_test("Result Formatting", False, f"Missing formatting elements: {missing_elements}")
                return False
            
            self.log_test("Result Formatting", True, "Proper formatting with icons and structure")
            return True
            
        except Exception as e:
            self.log_test("Result Formatting", False, error=e)
            return False
    
    def run_all_tests(self):
        """Run all MCP tests."""
        print("=" * 60)
        print("🧪 MCP FUNCTIONALITY TEST SUITE")
        print("=" * 60)
        print(f"Testing server: {self.server_name}")
        print(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print()
        
        tests = [
            self.test_server_configuration,
            self.test_list_directory,
            self.test_read_file,
            self.test_write_file,
            self.test_get_file_info,
            self.test_search_files,
            self.test_delete_file,
            self.test_error_handling,
            self.test_result_formatting
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
            except Exception as e:
                print(f"❌ FAIL | {test.__name__} - Unexpected error: {e}")
                print()
        
        print("=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        print()
        
        if passed == total:
            print("🎉 ALL TESTS PASSED! MCP functionality is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the details above.")
        
        print("=" * 60)
        
        # Save detailed results to file
        results_file = "mcp_test_results.json"
        with open(results_file, 'w') as f:
            json.dump({
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'server_tested': self.server_name,
                'total_tests': total,
                'passed_tests': passed,
                'success_rate': f"{(passed/total)*100:.1f}%",
                'detailed_results': self.test_results
            }, f, indent=2)
        
        print(f"📄 Detailed results saved to: {results_file}")
        
        return passed == total

def main():
    """Main test execution."""
    tester = MCPTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 