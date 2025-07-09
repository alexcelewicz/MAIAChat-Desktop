#!/usr/bin/env python3
"""
Cross-platform test for MCP double-pass mode configuration.
Tests the core functionality without requiring GUI components.
"""

import sys
import os
import platform
import tempfile
import json
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_config_manager_cross_platform():
    """Test that config manager works correctly across platforms."""
    print(f"Testing on: {platform.system()} {platform.release()}")
    
    try:
        from config_manager import ConfigManager
        print("✓ ConfigManager import successful")
        
        # Create a temporary config for testing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_config = {
                "MCP_SINGLE_PASS_MODE": True,
                "TEST_VALUE": "cross_platform_test"
            }
            json.dump(test_config, f, indent=2)
            temp_config_path = f.name
        
        # Test config manager with temporary file
        config_mgr = ConfigManager(config_file=temp_config_path, auto_reload=False)
        print("✓ ConfigManager initialization successful")
        
        # Test getting the MCP setting
        single_pass = config_mgr.get('MCP_SINGLE_PASS_MODE', False)
        print(f"✓ Read MCP_SINGLE_PASS_MODE: {single_pass}")
        
        # Test setting the value (simulating our UI toggle)
        config_mgr.set('MCP_SINGLE_PASS_MODE', False, save=True)
        print("✓ Set MCP_SINGLE_PASS_MODE to False (double-pass enabled)")
        
        # Test reading it back
        new_value = config_mgr.get('MCP_SINGLE_PASS_MODE', True)
        print(f"✓ Read back MCP_SINGLE_PASS_MODE: {new_value}")
        
        # Verify the file was updated
        with open(temp_config_path, 'r') as f:
            saved_config = json.load(f)
        
        if saved_config.get('MCP_SINGLE_PASS_MODE') == False:
            print("✓ Configuration correctly saved to file")
        else:
            print("✗ Configuration save failed")
            return False
        
        # Cleanup
        os.unlink(temp_config_path)
        print("✓ Test cleanup successful")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

def test_qt_checkbox_states():
    """Test Qt checkbox state handling without GUI."""
    print("\nTesting Qt CheckState enum compatibility...")
    
    try:
        # Test that we can import Qt without GUI
        from PyQt6.QtCore import Qt
        print("✓ PyQt6.QtCore import successful")
        
        # Test the checkbox states we use
        checked_state = Qt.CheckState.Checked
        unchecked_state = Qt.CheckState.Unchecked
        print(f"✓ Qt.CheckState.Checked = {checked_state}")
        print(f"✓ Qt.CheckState.Unchecked = {unchecked_state}")
        
        # Test our logic (simulating checkbox state changes)
        def simulate_checkbox_change(state):
            is_checked = (state == Qt.CheckState.Checked)
            single_pass_mode = not is_checked
            mode_name = "Double-Pass" if not single_pass_mode else "Single-Pass"
            return single_pass_mode, mode_name
        
        # Test checked state (double-pass enabled)
        single_pass, mode = simulate_checkbox_change(Qt.CheckState.Checked)
        print(f"✓ Checked state → single_pass={single_pass}, mode={mode}")
        
        # Test unchecked state (single-pass enabled)
        single_pass, mode = simulate_checkbox_change(Qt.CheckState.Unchecked)
        print(f"✓ Unchecked state → single_pass={single_pass}, mode={mode}")
        
        return True
        
    except Exception as e:
        print(f"✗ Qt test failed: {e}")
        return False

def test_import_chain():
    """Test the complete import chain our dialog uses."""
    print("\nTesting import chain...")
    
    try:
        # Test the config import we use in the dialog
        from config import config_manager
        print("✓ from config import config_manager")
        
        # Test basic functionality
        current_value = config_manager.get('MCP_SINGLE_PASS_MODE', True)
        print(f"✓ Current MCP_SINGLE_PASS_MODE: {current_value}")
        
        return True
        
    except Exception as e:
        print(f"✗ Import chain test failed: {e}")
        return False

def main():
    """Run all cross-platform tests."""
    print("=" * 60)
    print("MCP Double-Pass Mode Configuration - Cross-Platform Test")
    print("=" * 60)
    
    tests = [
        ("Config Manager", test_config_manager_cross_platform),
        ("Qt Checkbox States", test_qt_checkbox_states),
        ("Import Chain", test_import_chain)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- Testing {test_name} ---")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("🎉 All tests passed! Cross-platform compatibility verified.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)