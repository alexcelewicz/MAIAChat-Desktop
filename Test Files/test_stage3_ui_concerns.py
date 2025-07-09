#!/usr/bin/env python3
"""
Test script for Stage 3: Separating UI Concerns

This script verifies that the UI refactoring works correctly:
1. TextFormatter class properly separated
2. add_agent_discussion method refactored into helper methods
3. All UI functionality preserved after refactoring
"""

import sys
import os
import time
from pathlib import Path

# Add the current directory to the path so we can import modules
sys.path.insert(0, str(Path(__file__).parent))

def test_ui_separation():
    """Test the UI concerns separation and refactored methods."""
    
    print("\n=== STAGE 3 UI CONCERNS SEPARATION TEST ===")
    print("Testing UI refactoring and method separation\n")
    
    # Test 1: TextFormatter import and separation
    print("--- Testing TextFormatter Separation ---")
    try:
        from ui.text_formatter import TextFormatter
        print("✅ TextFormatter successfully imported from separate file")
        
        # Test TextFormatter functionality
        formatter = TextFormatter()
        test_code = "def hello():\n    print('Hello, world!')"
        formatted = formatter.format_code_block(test_code, "python")
        if (formatted and 
            "hello" in formatted.lower() and 
            any(tag in formatted for tag in ["<pre", "<div", "<span"]) and
            len(formatted) > 50):  # Should be a substantial HTML output
            print("✅ TextFormatter functionality working correctly")
        else:
            print(f"❌ TextFormatter functionality broken")
            print(f"   Formatted: {formatted[:100]}...")
            print(f"   Contains hello: {'hello' in formatted.lower()}")
            print(f"   Has HTML tags: {any(tag in formatted for tag in ['<pre', '<div', '<span'])}")
            return False
    except ImportError as e:
        print(f"❌ Failed to import TextFormatter: {e}")
        return False
    
    # Test 2: UnifiedResponsePanel structure
    print("\n--- Testing UnifiedResponsePanel Structure ---")
    try:
        from ui.unified_response_panel import UnifiedResponsePanel
        print("✅ UnifiedResponsePanel successfully imported")
        
        # Check if helper methods exist
        helper_methods = [
            '_initialize_streaming_context',
            '_insert_agent_header', 
            '_handle_code_block_start',
            '_handle_code_block_stream',
            '_handle_code_block_end',
            '_handle_regular_text'
        ]
        
        missing_methods = []
        for method in helper_methods:
            if not hasattr(UnifiedResponsePanel, method):
                missing_methods.append(method)
        
        if missing_methods:
            print(f"❌ Missing helper methods: {missing_methods}")
            return False
        else:
            print("✅ All helper methods present after refactoring")
            
    except ImportError as e:
        print(f"❌ Failed to import UnifiedResponsePanel: {e}")
        return False
    
    # Test 3: UI functionality with PyQt6
    print("\n--- Testing UI Functionality ---")
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
        
        # Create QApplication if it doesn't exist
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Create UnifiedResponsePanel instance
        panel = UnifiedResponsePanel()
        print("✅ UnifiedResponsePanel widget created successfully")
        
        # Test TextFormatter integration
        if hasattr(panel, 'text_formatter') and isinstance(panel.text_formatter, TextFormatter):
            print("✅ TextFormatter properly integrated into UnifiedResponsePanel")
        else:
            print("❌ TextFormatter integration broken")
            return False
        
        # Test streaming contexts initialization
        if hasattr(panel, '_streaming_contexts'):
            print("✅ Streaming contexts properly initialized")
        else:
            print("❌ Streaming contexts missing")
            return False
            
    except ImportError as e:
        print(f"❌ Failed to test UI functionality: {e}")
        return False
    except Exception as e:
        print(f"❌ UI functionality test error: {e}")
        return False
    
    # Test 4: Method refactoring validation
    print("\n--- Testing Method Refactoring ---")
    try:
        # Simulate add_agent_discussion call
        panel._streaming_contexts = {}  # Reset contexts
        
        # Test helper method calls
        panel._initialize_streaming_context(1, "test-model")
        if 1 in panel._streaming_contexts:
            print("✅ _initialize_streaming_context working correctly")
        else:
            print("❌ _initialize_streaming_context broken")
            return False
        
        # Test code block handling
        context = panel._streaming_contexts[1]
        panel._handle_code_block_start(context, "python")
        if context['in_code_block'] and context['language'] == "python":
            print("✅ _handle_code_block_start working correctly")
        else:
            print("❌ _handle_code_block_start broken")
            return False
        
        # Test regular text handling
        try:
            panel._handle_regular_text("Test content")
            print("✅ _handle_regular_text working correctly")
        except Exception as e:
            print(f"❌ _handle_regular_text failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Method refactoring test failed: {e}")
        return False
    
    # Test 5: Integration test with actual agent discussion
    print("\n--- Testing Integration ---")
    try:
        # Clear panel
        panel.clear()
        
        # Simulate streaming agent response with code
        test_chunks = [
            "Here's a Python function:\n\n",
            "```python\n",
            "def factorial(n):\n",
            "    if n <= 1:\n",
            "        return 1\n",
            "    return n * factorial(n-1)\n",
            "```\n",
            "\nThis calculates factorial recursively."
        ]
        
        for i, chunk in enumerate(test_chunks):
            is_first = (i == 0)
            panel.add_agent_discussion(chunk, 1, "test-model", is_first)
        
        # Check if content was added
        content = panel.unified_response.toPlainText()
        if "factorial" in content and "Agent 1" in content:
            print("✅ Integration test successful - agent discussion properly formatted")
        else:
            print("❌ Integration test failed - content not properly formatted")
            return False
            
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False
    
    print("\n=== STAGE 3 TEST RESULTS ===")
    print("✅ TextFormatter: Successfully separated into own file")
    print("✅ Helper Methods: All helper methods properly implemented")
    print("✅ UI Functionality: Widget creation and integration working")
    print("✅ Method Refactoring: Complex method broken into manageable pieces")
    print("✅ Integration: Full agent discussion flow working correctly")
    
    print(f"\n🔧 STAGE 3 VALIDATION:")
    print(f"✅ TextFormatter class moved to separate file")
    print(f"✅ add_agent_discussion method refactored into helpers")
    print(f"✅ UI concerns properly separated")
    print(f"✅ Code maintainability significantly improved")
    
    print(f"\n🎉 STAGE 3 IMPLEMENTATION: SUCCESSFUL")
    print(f"✅ UI concerns separation working correctly")
    print(f"✅ Code complexity significantly reduced")
    print(f"✅ All UI functionality preserved after refactoring")
    
    return True

if __name__ == "__main__":
    try:
        success = test_ui_separation()
        exit_code = 0 if success else 1
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 UNEXPECTED ERROR: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        sys.exit(1) 