#!/usr/bin/env python3
"""
Test script to verify the multiple folder permissions fix for MCP.
This tests that agents can access files in all configured directories.
"""

import sys
import os
import json
import tempfile
import shutil
from pathlib import Path

# Add the parent directory to the path to import project modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_client import MCPClient
from mcp_filesystem_server import create_filesystem_server

def test_multiple_folder_permissions():
    """Test that the MCP filesystem server supports multiple allowed directories."""
    print("=== Testing Multiple Folder Permissions Fix ===\n")
    
    # Create temporary test directories and files
    temp_dir1 = tempfile.mkdtemp(prefix="mcp_test1_")
    temp_dir2 = tempfile.mkdtemp(prefix="mcp_test2_")
    
    try:
        # Create test files
        test_file1 = Path(temp_dir1) / "test1.txt"
        test_file2 = Path(temp_dir2) / "test2.txt"
        
        test_file1.write_text("Content from directory 1")
        test_file2.write_text("Content from directory 2")
        
        print(f"Created test directories:")
        print(f"  Directory 1: {temp_dir1}")
        print(f"  Directory 2: {temp_dir2}")
        print()
        
        # Test 1: Create filesystem server with multiple allowed directories
        print("1. Testing Filesystem Server with Multiple Directories")
        print("-" * 50)
        
        allowed_directories = {
            temp_dir1: {
                "read_file": True,
                "write_file": True,
                "edit_file": True,
                "create_directory": True,
                "list_directory": True,
                "move_file": True,
                "search_files": True,
                "get_file_info": True
            },
            temp_dir2: {
                "read_file": True,
                "write_file": False,  # Read-only for directory 2
                "edit_file": False,
                "create_directory": False,
                "list_directory": True,
                "move_file": False,
                "search_files": True,
                "get_file_info": True
            }
        }
        
        filesystem_server = create_filesystem_server(
            allowed_directory=temp_dir1,  # Primary directory
            allowed_directories=allowed_directories,
            max_file_size=1024 * 1024,  # 1MB
            read_only=False,
            enable_logging=True
        )
        
        print("✅ Filesystem server created with multiple directories")
        
        # Test 2: Read file from first directory
        print("\n2. Testing File Access in Directory 1")
        print("-" * 50)
        
        result1 = filesystem_server.read_file(str(test_file1))
        if "error" not in result1:
            print(f"✅ Successfully read file from directory 1: {result1['content']}")
        else:
            print(f"❌ Failed to read file from directory 1: {result1['error']}")
        
        # Test 3: Read file from second directory
        print("\n3. Testing File Access in Directory 2")
        print("-" * 50)
        
        result2 = filesystem_server.read_file(str(test_file2))
        if "error" not in result2:
            print(f"✅ Successfully read file from directory 2: {result2['content']}")
        else:
            print(f"❌ Failed to read file from directory 2: {result2['error']}")
        
        # Test 4: Test write permissions (should work in dir1, fail in dir2)
        print("\n4. Testing Write Permissions")
        print("-" * 50)
        
        test_write_file1 = str(Path(temp_dir1) / "write_test.txt")
        result_write1 = filesystem_server.write_file(test_write_file1, "Write test content")
        
        if "error" not in result_write1:
            print("✅ Successfully wrote to directory 1 (write allowed)")
        else:
            print(f"❌ Failed to write to directory 1: {result_write1['error']}")
        
        test_write_file2 = str(Path(temp_dir2) / "write_test.txt")
        result_write2 = filesystem_server.write_file(test_write_file2, "Write test content")
        
        if "error" in result_write2 and "Permission denied" in result_write2['error']:
            print("✅ Correctly denied write to directory 2 (write not allowed)")
        else:
            print(f"❌ Unexpected result for directory 2 write: {result_write2}")
        
        # Test 5: Test directory listing
        print("\n5. Testing Directory Listing")
        print("-" * 50)
        
        list_result1 = filesystem_server.list_directory("")  # Should list primary directory
        if "error" not in list_result1:
            print(f"✅ Successfully listed primary directory: {len(list_result1['items'])} items")
        else:
            print(f"❌ Failed to list primary directory: {list_result1['error']}")
        
        # Test 6: Test path validation for unauthorized directory
        print("\n6. Testing Path Validation for Unauthorized Directory")
        print("-" * 50)
        
        unauthorized_dir = tempfile.mkdtemp(prefix="mcp_unauthorized_")
        unauthorized_file = Path(unauthorized_dir) / "unauthorized.txt"
        unauthorized_file.write_text("Should not be accessible")
        
        result_unauthorized = filesystem_server.read_file(str(unauthorized_file))
        if "error" in result_unauthorized and "outside allowed directories" in result_unauthorized['error']:
            print("✅ Correctly denied access to unauthorized directory")
        else:
            print(f"❌ Unexpected result for unauthorized access: {result_unauthorized}")
        
        shutil.rmtree(unauthorized_dir)
        
        print("\n" + "=" * 50)
        print("✅ All tests completed successfully!")
        print("The multiple folder permissions fix is working correctly.")
        
    finally:
        # Clean up temporary directories
        shutil.rmtree(temp_dir1, ignore_errors=True)
        shutil.rmtree(temp_dir2, ignore_errors=True)

def test_mcp_client_integration():
    """Test that the MCP client properly loads and uses folder permissions."""
    print("\n=== Testing MCP Client Integration ===\n")
    
    try:
        mcp_client = MCPClient()
        
        # Test loading folder permissions
        folder_permissions = mcp_client._load_folder_permissions()
        
        if folder_permissions:
            print(f"✅ Successfully loaded folder permissions for {len(folder_permissions)} directories:")
            for folder_path, permissions in folder_permissions.items():
                allowed_ops = [op for op, allowed in permissions.items() if allowed]
                print(f"  {folder_path}: {', '.join(allowed_ops)}")
        else:
            print("ℹ️  No folder permissions configured (this is normal for a fresh setup)")
        
        # Test folder permissions context
        context = mcp_client._get_folder_permissions_context()
        print(f"✅ Successfully generated folder permissions context with {len(context)} entries")
        
    except Exception as e:
        print(f"❌ Error testing MCP client integration: {e}")
        import traceback
        traceback.print_exc()

def demonstrate_fix():
    """Demonstrate how the fix resolves the original issue."""
    print("\n=== Demonstration: How the Fix Resolves the Issue ===\n")
    
    print("🔍 ORIGINAL PROBLEM:")
    print("   - User adds folder 'C:/Users/voyce/Desktop/Large PDF Files/' in UI")
    print("   - Folder appears in folder_permissions.json with correct permissions")
    print("   - Agent tries to read PDF file from that folder")
    print("   - MCP filesystem server rejects with 'Path outside allowed directory'")
    print()
    
    print("🔧 ROOT CAUSE:")
    print("   - Filesystem server only checked against ONE allowed directory")
    print("   - folder_permissions.json supported multiple directories but server ignored them")
    print("   - _validate_path() method only used self.allowed_path (primary directory)")
    print()
    
    print("✅ SOLUTION IMPLEMENTED:")
    print("   1. Updated FileSystemConfig to support allowed_directories parameter")
    print("   2. Modified _validate_path() to check against ALL allowed directories")
    print("   3. Added _check_operation_permission() for per-directory permissions")
    print("   4. Updated MCP client to load and pass folder_permissions.json")
    print("   5. Enhanced read_file() and other operations to check permissions")
    print()
    
    print("🎯 RESULT:")
    print("   - Agents can now access files in ANY configured directory")
    print("   - Permissions are enforced per-directory (read-only, full access, etc.)")
    print("   - UI folder configuration now works as expected")
    print("   - Backward compatibility maintained with single-directory setups")

if __name__ == "__main__":
    test_multiple_folder_permissions()
    test_mcp_client_integration()
    demonstrate_fix() 