#!/usr/bin/env python3
"""
Test script for MCP Folder Awareness functionality
Tests that agents receive proper folder permission context
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp_client import mcp_client
from mcp_file_operations import get_file_operations
import json

def test_folder_permissions_context():
    """Test that MCP client provides folder permissions context."""
    
    print("🧪 Testing MCP Folder Awareness Functionality...")
    
    # Test 1: Check folder permissions are loaded
    print("\n1. Testing folder permissions loading...")
    file_ops = get_file_operations()
    permissions = file_ops.folder_permissions
    print(f"✅ Loaded {len(permissions)} folder permission(s)")
    
    for folder_path, folder_perms in permissions.items():
        enabled_ops = [op for op, enabled in folder_perms.items() if enabled]
        print(f"   - {folder_path}: {len(enabled_ops)} operations enabled")
    
    # Test 2: Check MCP context includes folder permissions
    print("\n2. Testing MCP context preparation...")
    mcp_context = mcp_client.prepare_mcp_context("list files in folder")
    
    if "folder_permissions" in mcp_context:
        folder_context = mcp_context["folder_permissions"]
        print(f"✅ MCP context includes {len(folder_context)} folder(s)")
        
        for folder_path, folder_info in folder_context.items():
            allowed_ops = folder_info.get("allowed_operations", [])
            print(f"   - {folder_path}:")
            print(f"     Readable: {folder_info.get('readable', False)}")
            print(f"     Writable: {folder_info.get('writable', False)}")
            print(f"     Can List: {folder_info.get('can_list', False)}")
            print(f"     Operations: {', '.join(allowed_ops)}")
    else:
        print("❌ MCP context missing folder_permissions")
        return False
    
    # Test 3: Simulate agent context formatting (like worker.py does)
    print("\n3. Testing agent context formatting...")
    
    if "folder_permissions" in mcp_context and mcp_context["folder_permissions"]:
        formatted_context = "=== MCP CONTEXT ===\n"
        formatted_context += "Configured Folder Access:\n"
        folders = mcp_context["folder_permissions"]
        
        if len(folders) == 1:
            # Single folder scenario
            folder_path, folder_info = next(iter(folders.items()))
            formatted_context += f"You have access to: {folder_path}\n"
            if folder_info.get("can_list", False):
                formatted_context += f"To list files in this folder, use: [MCP:Local Files:list_directory:{folder_path}]\n"
            allowed_ops = folder_info.get("allowed_operations", [])
            if allowed_ops:
                formatted_context += f"Allowed operations: {', '.join(allowed_ops)}\n"
        else:
            # Multiple folders scenario
            formatted_context += "Available folders:\n"
            for folder_path, folder_info in folders.items():
                formatted_context += f"- {folder_path}\n"
                allowed_ops = folder_info.get("allowed_operations", [])
                if allowed_ops:
                    formatted_context += f"  Operations: {', '.join(allowed_ops)}\n"
            formatted_context += "When working with files, specify the full path or use one of these configured folders.\n"
        
        print("✅ Agent context formatting:")
        print(formatted_context)
    else:
        print("❌ No folder permissions to format")
        return False
    
    # Test 4: Verify intelligent folder selection logic
    print("\n4. Testing intelligent folder selection...")
    
    folders = mcp_context["folder_permissions"]
    
    if len(folders) == 1:
        folder_path = next(iter(folders.keys()))
        print(f"✅ Single folder detected: {folder_path}")
        print("   Agent should automatically use this folder for file operations")
    elif len(folders) > 1:
        print(f"✅ Multiple folders detected ({len(folders)})")
        print("   Agent should ask user to specify which folder to use")
    else:
        print("❌ No folders configured")
        return False
    
    print("\n🎉 All MCP folder awareness tests passed!")
    
    # Show expected agent behavior
    print("\n📋 Expected Agent Behavior:")
    if len(folders) == 1:
        folder_path = next(iter(folders.keys()))
        print(f"When user asks to 'list files in folder', agent should:")
        print(f"   Use: [MCP:Local Files:list_directory:{folder_path}]")
        print(f"   Instead of asking for folder path")
    else:
        print("When user asks to 'list files in folder', agent should:")
        print("   Ask which folder to use from the configured list")
        print("   Or suggest using one of the available folders")
    
    return True

if __name__ == "__main__":
    success = test_folder_permissions_context()
    sys.exit(0 if success else 1)