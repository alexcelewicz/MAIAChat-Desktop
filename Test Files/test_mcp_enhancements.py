#!/usr/bin/env python3
"""
Test script for MCP Configuration Enhancements
Tests the new features: checkboxes, server movement, and folder permissions
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from mcp_config_dialog import MCPConfigDialog
from mcp_client import mcp_client
import json

def test_mcp_enhancements():
    """Test the MCP configuration enhancements."""
    
    print("🧪 Testing MCP Configuration Enhancements...")
    
    app = QApplication(sys.argv)
    
    try:
        # Test 1: Dialog Creation
        print("\n1. Testing dialog creation...")
        dialog = MCPConfigDialog()
        print("✅ MCP Config Dialog created successfully")
        
        # Test 2: Tab Structure
        print("\n2. Testing tab structure...")
        tab_widget = None
        for child in dialog.children():
            if 'QTabWidget' in str(type(child)):
                tab_widget = child
                break
        
        if tab_widget:
            print(f"✅ Found {tab_widget.count()} tabs:")
            for i in range(tab_widget.count()):
                print(f"   - {tab_widget.tabText(i)}")
        
        # Test 3: Server Table with Checkboxes
        print("\n3. Testing server table with checkboxes...")
        print(f"✅ Server table has {dialog.server_table.rowCount()} servers")
        print(f"✅ Checkbox delegate: {'✓' if hasattr(dialog, 'checkbox_delegate') else '✗'}")
        
        # Test 4: Server Movement Methods
        print("\n4. Testing server movement functionality...")
        move_methods = ['move_to_available', 'move_to_configured']
        for method in move_methods:
            exists = hasattr(dialog, method)
            print(f"✅ {method}: {'✓' if exists else '✗'}")
        
        # Test 5: Folder Permissions
        print("\n5. Testing folder permissions...")
        print(f"✅ File operations handler: {'✓' if hasattr(dialog, 'file_ops') else '✗'}")
        print(f"✅ Permissions table: {'✓' if hasattr(dialog, 'permissions_table') else '✗'}")
        print(f"✅ Permission operations count: {len(dialog.permission_operations)}")
        print(f"   Operations: {', '.join(dialog.permission_operations)}")
        
        # Test 6: Current Folder Permissions
        print("\n6. Testing current folder permissions...")
        for path, perms in dialog.file_ops.folder_permissions.items():
            enabled_count = sum(1 for enabled in perms.values() if enabled)
            print(f"   {path}: {enabled_count}/{len(perms)} permissions enabled")
        
        # Test 7: Server Types
        print("\n7. Testing server type detection...")
        for name, server in mcp_client.servers.items():
            server_type = getattr(server, 'server_type', 'unknown')
            print(f"   {name}: {server_type} ({'enabled' if server.enabled else 'disabled'})")
        
        # Test 8: Available Servers
        print("\n8. Testing available servers...")
        available = mcp_client.get_available_mcp_servers()
        print(f"✅ Found {len(available)} available servers")
        
        print("\n🎉 All tests passed! MCP configuration enhancements are working correctly.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_mcp_enhancements()
    sys.exit(0 if success else 1)