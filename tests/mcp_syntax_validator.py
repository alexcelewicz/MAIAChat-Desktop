#!/usr/bin/env python3
"""
MCP Syntax Validator - Prevents MCP syntax errors before sending requests
"""

import re

class MCPSyntaxValidator:
    """Validates MCP syntax before sending requests"""
    
    # Valid MCP patterns
    VALID_PATTERNS = {
        'list_directory': r'^\[MCP:Local Files:list_directory:\]$',
        'read_file': r'^\[MCP:Local Files:read_file:[^:]+\]$',
        'write_file': r'^\[MCP:Local Files:write_file:[^:]+:.+\]$',
        'delete_file': r'^\[MCP:Local Files:delete_file:[^:]+\]$',
        'search_files': r'^\[MCP:Local Files:search_files:[^:]*:\]$'
    }
    
    @staticmethod
    def validate_mcp_syntax(mcp_request: str) -> dict:
        """
        Validates MCP request syntax
        Returns: {'valid': bool, 'error': str, 'suggestion': str}
        """
        if not mcp_request.startswith('[MCP:') or not mcp_request.endswith(']'):
            return {
                'valid': False,
                'error': 'MCP request must start with [MCP: and end with ]',
                'suggestion': 'Use format: [MCP:Server:operation:params]'
            }
        
        # Check for common patterns
        for operation, pattern in MCPSyntaxValidator.VALID_PATTERNS.items():
            if re.match(pattern, mcp_request):
                return {'valid': True, 'error': None, 'suggestion': None}
        
        # Specific error detection
        if ':Local Files:' not in mcp_request:
            return {
                'valid': False,
                'error': 'Missing server name or incorrect format',
                'suggestion': 'Use: [MCP:Local Files:operation:params]'
            }
        
        parts = mcp_request[1:-1].split(':')  # Remove [ ] and split
        if len(parts) < 3:
            return {
                'valid': False,
                'error': 'Insufficient parameters',
                'suggestion': 'Need at least: [MCP:Server:Operation:]'
            }
        
        return {
            'valid': False,
            'error': 'Unknown MCP operation or malformed syntax',
            'suggestion': 'Valid operations: list_directory, read_file, write_file, delete_file, search_files'
        }
    
    @staticmethod
    def create_safe_mcp_request(operation: str, **kwargs) -> str:
        """
        Creates a properly formatted MCP request
        """
        if operation == 'list_directory':
            return '[MCP:Local Files:list_directory:]'
        
        elif operation == 'read_file':
            filename = kwargs.get('filename', '')
            if not filename:
                raise ValueError("filename required for read_file operation")
            return f'[MCP:Local Files:read_file:{filename}]'
        
        elif operation == 'write_file':
            filename = kwargs.get('filename', '')
            content = kwargs.get('content', '')
            if not filename:
                raise ValueError("filename required for write_file operation")
            if not content:
                raise ValueError("content required for write_file operation")
            return f'[MCP:Local Files:write_file:{filename}:{content}]'
        
        elif operation == 'delete_file':
            filename = kwargs.get('filename', '')
            if not filename:
                raise ValueError("filename required for delete_file operation")
            return f'[MCP:Local Files:delete_file:{filename}]'
        
        elif operation == 'search_files':
            pattern = kwargs.get('pattern', '')
            return f'[MCP:Local Files:search_files:{pattern}:]'
        
        else:
            raise ValueError(f"Unknown operation: {operation}")

def test_mcp_validator():
    """Test the MCP syntax validator"""
    print("🧪 Testing MCP Syntax Validator")
    
    validator = MCPSyntaxValidator()
    
    # Test cases
    test_cases = [
        # Valid cases
        "[MCP:Local Files:list_directory:]",
        "[MCP:Local Files:read_file:test.py]",
        "[MCP:Local Files:write_file:test.py:print('hello')]",
        "[MCP:Local Files:delete_file:test.py]",
        
        # Invalid cases
        "[MCP:Local Files:list_directory]",  # Missing final colon
        "[MCP Local Files:read_file:test.py]",  # Missing colon after MCP
        "[MCP:Local Files read_file:test.py]",  # Missing colon after Files
        "[MCP:Local Files:write_file:test.py]",  # Missing content
        "MCP:Local Files:list_directory:",  # Missing brackets
    ]
    
    print("\n📝 Validation Results:")
    for i, test in enumerate(test_cases, 1):
        result = validator.validate_mcp_syntax(test)
        status = "✅" if result['valid'] else "❌"
        print(f"{status} {i:2d}. {test}")
        if not result['valid']:
            print(f"      Error: {result['error']}")
            print(f"      Suggestion: {result['suggestion']}")
    
    print("\n🔧 Safe MCP Request Creation:")
    try:
        safe_requests = [
            validator.create_safe_mcp_request('list_directory'),
            validator.create_safe_mcp_request('read_file', filename='snake.py'),
            validator.create_safe_mcp_request('write_file', filename='test.py', content='print("safe!")'),
            validator.create_safe_mcp_request('delete_file', filename='test.py'),
        ]
        
        for req in safe_requests:
            print(f"✅ {req}")
            
    except Exception as e:
        print(f"❌ Error creating safe request: {e}")

if __name__ == "__main__":
    test_mcp_validator() 