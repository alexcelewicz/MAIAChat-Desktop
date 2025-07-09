#!/usr/bin/env python3
"""
Test script to verify the code-aware streaming fix works correctly.
This tests the new _should_flush_for_code_integrity method.
"""

import sys
import os
import re
from pathlib import Path

# Add the parent directory to the path to import modules
sys.path.append(str(Path(__file__).parent.parent))

class MockConfigManager:
    """Mock config manager for testing"""
    def get(self, key, default=None):
        return default

def test_code_integrity_detection():
    """Test the _should_flush_for_code_integrity method"""
    
    print("🧪 TESTING CODE INTEGRITY DETECTION")
    print("=" * 50)
    
    # Import the Worker class to test the new method
    try:
        from worker import Worker
        
        # Create a mock worker instance
        config_manager = MockConfigManager()
        worker = Worker(
            prompt="test",
            general_instructions="test", 
            agents=[],
            knowledge_base_files=[],
            config_manager=config_manager
        )
        
        # Test cases for code detection
        test_cases = [
            # JavaScript variable declarations
            ("let player;", True, "JavaScript let declaration"),
            ("const width = 800;", True, "JavaScript const declaration"),
            ("var score = 0;", True, "JavaScript var declaration"),
            ("let player;\nlet obstacles", True, "JavaScript with newline"),
            
            # Python code
            ("def function_name():", True, "Python function definition"),
            ("class MyClass:", True, "Python class definition"),
            ("import os", True, "Python import"),
            ("from math import pi", True, "Python from import"),
            
            # HTML/CSS
            ("<div class='container'>", True, "HTML tag"),
            ("body { margin: 0; }", True, "CSS rule"),
            
            # Control structures
            ("if (condition) {", True, "If statement"),
            ("for (let i = 0;", True, "For loop"),
            ("while (true) {", True, "While loop"),
            
            # Non-code content
            ("This is regular text", False, "Regular text"),
            ("Hello world!", False, "Simple text"),
            ("Some text with numbers 123", False, "Text with numbers"),
            ("", False, "Empty string"),
        ]
        
        print("Testing code pattern detection:")
        for buffer, expected, description in test_cases:
            result = worker._should_flush_for_code_integrity(buffer)
            status = "✅" if result == expected else "❌"
            print(f"  {status} {description}: {repr(buffer)} -> {result}")
            if result != expected:
                print(f"      Expected: {expected}, Got: {result}")
        
        return worker
        
    except ImportError as e:
        print(f"Could not import Worker class: {e}")
        return None

def test_streaming_with_fix():
    """Test streaming with the new code-aware fix"""
    
    print("\n" + "=" * 50)
    print("🔧 TESTING STREAMING WITH CODE-AWARE FIX")
    print("=" * 50)
    
    worker = test_code_integrity_detection()
    if not worker:
        print("Cannot test streaming - Worker import failed")
        return
    
    # Simulate the problematic JavaScript code streaming
    incoming_chunks = [
        "let", " ", "player", ";", "\n",
        "let", " ", "obstacles", " ", "=", " ", "[", "]", ";", "\n", 
        "let", " ", "score", " ", "=", " ", "0", ";", "\n",
        "let", " ", "highScore", "=", " ", "0", ";", "\n"
    ]
    
    stream_buffer = ""
    flushed_chunks = []
    
    print("Simulating streaming with code-aware logic:")
    
    for i, chunk in enumerate(incoming_chunks):
        stream_buffer += chunk
        
        # Apply the new flush logic
        flush_now = False
        
        if i == 0:  # first_chunk
            flush_now = True
            reason = "first chunk"
        elif worker._should_flush_for_code_integrity(stream_buffer):  # NEW: Code-aware flushing
            flush_now = True
            reason = "code integrity"
        elif '\n\n' in stream_buffer:  # paragraph break
            flush_now = True
            reason = "paragraph break"
        elif len(stream_buffer) > 50:  # length threshold
            flush_now = True
            reason = f"length threshold ({len(stream_buffer)} > 50)"
        
        print(f"  Chunk {i+1:2d}: {repr(chunk)} -> Buffer: {repr(stream_buffer)}")
        
        if flush_now:
            flushed_chunks.append(stream_buffer)
            print(f"    ✅ FLUSHED ({reason}): {repr(stream_buffer)}")
            stream_buffer = ""
        else:
            print(f"    ⏳ Buffering... (length: {len(stream_buffer)})")
    
    # Flush remaining buffer
    if stream_buffer:
        flushed_chunks.append(stream_buffer)
        print(f"    ✅ FINAL FLUSH: {repr(stream_buffer)}")
    
    final_result = "".join(flushed_chunks)
    print(f"\nFixed result:")
    print(repr(final_result))
    print("\nFormatted view:")
    print(final_result)
    
    # Analyze the result
    print("\n🎯 SYNTAX ANALYSIS:")
    lines = final_result.split('\n')
    syntax_errors = 0
    
    for i, line in enumerate(lines, 1):
        if line.strip():
            # Check for merged statements (multiple semicolons)
            if line.count(';') > 1:
                print(f"  Line {i}: ❌ Multiple statements merged: {repr(line)}")
                syntax_errors += 1
            # Check for incomplete statements
            elif 'let ' in line and '=' in line and not line.strip().endswith(';'):
                print(f"  Line {i}: ❌ Incomplete statement: {repr(line)}")
                syntax_errors += 1
            else:
                print(f"  Line {i}: ✅ Valid statement: {repr(line)}")
    
    if syntax_errors == 0:
        print(f"\n🎉 SUCCESS: No syntax errors detected!")
    else:
        print(f"\n⚠️  Found {syntax_errors} syntax error(s)")
    
    return final_result

def test_comparison():
    """Compare old vs new streaming behavior"""
    
    print("\n" + "=" * 50)
    print("📊 COMPARISON: OLD VS NEW BEHAVIOR")
    print("=" * 50)
    
    # Simulate old behavior (from our earlier analysis)
    old_result = "let player;\nlet obstacles = [];\nlet score = 0;\nlet highScore= 0;\nlet gameSpeed;\nlet initialGameSpeed = 6;\nconst canvasWidth = 800;\nconst canvasHeight = 400;"
    
    # Get new behavior result
    new_result = test_streaming_with_fix()
    
    print(f"\nOLD BEHAVIOR:")
    print(repr(old_result))
    print("\nNEW BEHAVIOR:")
    print(repr(new_result))
    
    # Check for improvements
    print(f"\n🔍 IMPROVEMENTS:")
    
    # Check for proper spacing
    old_has_spacing_issues = "highScore=" in old_result
    new_has_spacing_issues = "highScore=" in new_result if new_result else True
    
    if old_has_spacing_issues and not new_has_spacing_issues:
        print("  ✅ Fixed spacing issues (highScore= -> highScore =)")
    elif old_has_spacing_issues and new_has_spacing_issues:
        print("  ⚠️  Spacing issues still present")
    else:
        print("  ✅ No spacing issues detected")
    
    # Check for merged statements
    old_merged = any(line.count(';') > 1 for line in old_result.split('\n'))
    new_merged = any(line.count(';') > 1 for line in new_result.split('\n')) if new_result else True
    
    if old_merged and not new_merged:
        print("  ✅ Fixed merged statements")
    elif old_merged and new_merged:
        print("  ⚠️  Merged statements still present")
    else:
        print("  ✅ No merged statements detected")

if __name__ == "__main__":
    test_comparison()
