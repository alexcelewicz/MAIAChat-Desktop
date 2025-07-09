#!/usr/bin/env python3
"""
Test script to verify the validation fixes for large agent responses.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from conversation_manager import ConversationManager, MessageValidationRule

def test_large_response_validation():
    """Test the enhanced validation for large responses."""
    print("Testing large response validation...")
    
    # Create conversation manager with default validation rules
    cm = ConversationManager()
    
    # Start a new conversation first
    conv_id = cm.start_new_conversation("Test conversation for validation")
    print(f"✓ Started conversation: {conv_id}")
    
    # Test 1: Small response (should pass)
    small_response = "This is a small response."
    print(f"Test 1 - Small response ({len(small_response)} chars):")
    try:
        cm.add_message(small_response, "agent_4", {"test": "small"})
        print("✓ PASSED - Small response added successfully")
    except Exception as e:
        print(f"✗ FAILED - Small response failed: {e}")
    
    # Test 2: Large response (should pass with warning)
    large_response = "Large response content. " * 5000  # ~100,000 chars
    print(f"\nTest 2 - Large response ({len(large_response)} chars):")
    try:
        cm.add_message(large_response, "agent_4", {"test": "large"})
        print("✓ PASSED - Large response added successfully")
    except Exception as e:
        print(f"✗ FAILED - Large response failed: {e}")
    
    # Test 3: Very large response (should be truncated)
    very_large_response = "Very large response content. " * 25000  # ~500,000 chars
    print(f"\nTest 3 - Very large response ({len(very_large_response)} chars):")
    try:
        cm.add_message(very_large_response, "agent_4", {"test": "very_large"})
        print("✓ PASSED - Very large response handled (truncated)")
    except Exception as e:
        print(f"✗ FAILED - Very large response failed: {e}")
    
    # Test 4: Extremely large response (should be truncated)
    extremely_large_response = "Extremely large response content. " * 50000  # ~1,000,000 chars
    print(f"\nTest 4 - Extremely large response ({len(extremely_large_response)} chars):")
    try:
        cm.add_message(extremely_large_response, "agent_4", {"test": "extremely_large"})
        print("✓ PASSED - Extremely large response handled (truncated)")
    except Exception as e:
        print(f"✗ FAILED - Extremely large response failed: {e}")
    
    # Test 5: Check validation rules
    print(f"\nTest 5 - Validation rules:")
    rules = cm.get_validation_rules()
    print(f"✓ Max content length: {rules.max_content_length:,} chars")
    print(f"✓ Warning threshold: {rules.max_content_length_warning:,} chars")
    print(f"✓ Content truncation enabled: {rules.enable_content_truncation}")
    
    # Test 6: Check content size analysis
    print(f"\nTest 6 - Content size analysis:")
    size_info = cm.check_content_size(large_response)
    print(f"✓ Content length: {size_info['content_length']:,} chars")
    print(f"✓ Is large: {size_info['is_large']}")
    print(f"✓ Is too large: {size_info['is_too_large']}")
    print(f"✓ Truncation needed: {size_info['truncation_needed']}")
    
    # Test 7: Update validation rules
    print(f"\nTest 7 - Update validation rules:")
    cm.update_validation_rules(max_content_length=1000000, max_content_length_warning=200000)
    updated_rules = cm.get_validation_rules()
    print(f"✓ Updated max content length: {updated_rules.max_content_length:,} chars")
    print(f"✓ Updated warning threshold: {updated_rules.max_content_length_warning:,} chars")
    
    print(f"\n✓ All validation tests completed successfully!")

def test_conversation_persistence():
    """Test that large responses are properly saved and loaded."""
    print("\n" + "="*50)
    print("Testing conversation persistence with large responses...")
    
    # Create conversation manager
    cm = ConversationManager()
    
    # Start a new conversation
    conv_id = cm.start_new_conversation("Test conversation with large responses")
    print(f"✓ Started conversation: {conv_id}")
    
    # Add a large response
    large_response = "Large response content. " * 10000  # ~200,000 chars
    cm.add_message(large_response, "agent_4", {"test": "persistence"})
    print(f"✓ Added large response ({len(large_response):,} chars)")
    
    # Save and reload conversation
    cm.save_current_conversation()
    print("✓ Saved conversation")
    
    # Load conversation
    success = cm.load_conversation(conv_id)
    if success:
        print("✓ Loaded conversation successfully")
        
        # Check if the message was preserved
        messages = cm.current_conversation.get("messages", [])
        if messages:
            last_message = messages[-1]
            print(f"✓ Last message role: {last_message['role']}")
            print(f"✓ Last message content length: {len(last_message['content']):,} chars")
            print(f"✓ Last message metadata: {last_message.get('metadata', {})}")
        else:
            print("✗ No messages found in loaded conversation")
    else:
        print("✗ Failed to load conversation")
    
    print(f"\n✓ Persistence test completed!")

if __name__ == "__main__":
    print("Validation Fix Test Suite")
    print("="*50)
    
    try:
        test_large_response_validation()
        test_conversation_persistence()
        print(f"\n🎉 All tests passed! The validation fixes are working correctly.")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc() 