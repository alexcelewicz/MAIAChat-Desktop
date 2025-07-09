#!/usr/bin/env python3
"""
Test script to reproduce and analyze code generation syntax issues.
This script tests the specific problem where LLM-generated code has consecutive
statements merged without proper line breaks or semicolons.
"""

import sys
import os
import re
from pathlib import Path

# Add the parent directory to the path to import modules
sys.path.append(str(Path(__file__).parent.parent))

from ui.text_formatter import TextFormatter
from ui.unified_response_panel import UnifiedResponsePanel
from PyQt6.QtWidgets import QApplication, QTextEdit
from PyQt6.QtCore import QObject

class MockConfigManager:
    """Mock config manager for testing"""
    def get(self, key, default=None):
        return default

def test_problematic_javascript_code():
    """Test the specific JavaScript code that causes syntax errors"""
    
    # This is the problematic code that gets generated with syntax errors
    problematic_js = """let player;let obstacles = [];
let score = 0;let highScore= 0;
let gameSpeed;let initialGameSpeed = 6;
const canvasWidth = 800;const canvasHeight = 400;"""
    
    # This is how it should look
    correct_js = """let player;
let obstacles = [];
let score = 0;
let highScore = 0;
let gameSpeed;
let initialGameSpeed = 6;
const canvasWidth = 800;
const canvasHeight = 400;"""
    
    print("=== PROBLEMATIC JAVASCRIPT CODE ===")
    print(problematic_js)
    print("\n=== CORRECT JAVASCRIPT CODE ===")
    print(correct_js)
    
    return problematic_js, correct_js

def test_text_formatter_processing():
    """Test how TextFormatter processes the problematic code"""
    
    print("\n=== TESTING TEXT FORMATTER ===")
    
    config_manager = MockConfigManager()
    formatter = TextFormatter(config_manager)
    
    problematic_js, correct_js = test_problematic_javascript_code()
    
    # Test formatting of problematic code
    print("\n--- Formatting Problematic Code ---")
    formatted_problematic = formatter.format_code_block(problematic_js, 'javascript')
    print("Formatted HTML:")
    print(formatted_problematic)
    
    # Test formatting of correct code
    print("\n--- Formatting Correct Code ---")
    formatted_correct = formatter.format_code_block(correct_js, 'javascript')
    print("Formatted HTML:")
    print(formatted_correct)
    
    return formatted_problematic, formatted_correct

def test_streaming_simulation():
    """Simulate how streaming might cause the issue"""
    
    print("\n=== TESTING STREAMING SIMULATION ===")
    
    # Simulate how the code might arrive in chunks during streaming
    streaming_chunks = [
        "let player;",
        "let obstacles = [];\n",
        "let score = 0;",
        "let highScore= 0;\n",
        "let gameSpeed;",
        "let initialGameSpeed = 6;\n",
        "const canvasWidth = 800;",
        "const canvasHeight = 400;"
    ]
    
    print("Streaming chunks:")
    for i, chunk in enumerate(streaming_chunks):
        print(f"Chunk {i+1}: {repr(chunk)}")
    
    # Simulate buffer accumulation with 50-character threshold
    buffer = ""
    flushed_chunks = []
    
    for chunk in streaming_chunks:
        buffer += chunk
        print(f"Buffer after adding chunk: {repr(buffer)}")
        
        # Simulate the flush conditions from worker.py
        flush_now = False
        if '\n\n' in buffer:
            flush_now = True
            print("  -> Flushing due to paragraph break")
        elif len(buffer) > 50:
            flush_now = True
            print(f"  -> Flushing due to length ({len(buffer)} > 50)")
        
        if flush_now:
            flushed_chunks.append(buffer)
            print(f"  -> Flushed: {repr(buffer)}")
            buffer = ""
    
    # Flush remaining buffer
    if buffer:
        flushed_chunks.append(buffer)
        print(f"  -> Final flush: {repr(buffer)}")
    
    print("\nFlushed chunks:")
    for i, chunk in enumerate(flushed_chunks):
        print(f"Flushed {i+1}: {repr(chunk)}")
    
    # Reconstruct the final result
    final_result = "".join(flushed_chunks)
    print(f"\nFinal reconstructed result: {repr(final_result)}")
    
    return flushed_chunks, final_result

def test_clean_agent_response():
    """Test the clean_agent_response method impact"""
    
    print("\n=== TESTING CLEAN_AGENT_RESPONSE IMPACT ===")
    
    # Import the Worker class to test its clean_agent_response method
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
        
        problematic_js, correct_js = test_problematic_javascript_code()
        
        print("--- Testing clean_agent_response on problematic code ---")
        cleaned_problematic = worker.clean_agent_response(problematic_js)
        print(f"Original: {repr(problematic_js)}")
        print(f"Cleaned:  {repr(cleaned_problematic)}")
        
        print("\n--- Testing clean_agent_response on correct code ---")
        cleaned_correct = worker.clean_agent_response(correct_js)
        print(f"Original: {repr(correct_js)}")
        print(f"Cleaned:  {repr(cleaned_correct)}")
        
        # Check if cleaning is causing the issue
        if cleaned_problematic != problematic_js:
            print("\n⚠️  clean_agent_response is modifying the problematic code!")
        else:
            print("\n✅ clean_agent_response is not modifying the problematic code")
            
        return cleaned_problematic, cleaned_correct
        
    except ImportError as e:
        print(f"Could not import Worker class: {e}")
        return None, None

def analyze_whitespace_normalization():
    """Analyze the specific whitespace normalization that might cause issues"""
    
    print("\n=== ANALYZING WHITESPACE NORMALIZATION ===")
    
    problematic_js, correct_js = test_problematic_javascript_code()
    
    # Test the specific regex patterns from clean_agent_response
    print("--- Testing regex patterns ---")
    
    # Pattern 1: Multiple newlines -> max two newlines
    pattern1 = r'\n{3,}'
    replacement1 = '\n\n'
    
    # Pattern 2: Multiple spaces/tabs -> single space  
    pattern2 = r'[ \t]{2,}'
    replacement2 = ' '
    
    test_text = problematic_js
    print(f"Original: {repr(test_text)}")
    
    # Apply pattern 1
    after_pattern1 = re.sub(pattern1, replacement1, test_text)
    print(f"After newline normalization: {repr(after_pattern1)}")
    
    # Apply pattern 2
    after_pattern2 = re.sub(pattern2, replacement2, after_pattern1)
    print(f"After space normalization: {repr(after_pattern2)}")
    
    # Check if this is causing the issue
    if after_pattern2 != test_text:
        print("\n⚠️  Whitespace normalization is modifying the code!")
        print("Changes detected:")
        if after_pattern1 != test_text:
            print("  - Newline normalization made changes")
        if after_pattern2 != after_pattern1:
            print("  - Space normalization made changes")
    else:
        print("\n✅ Whitespace normalization is not modifying this code")

def main():
    """Main test function"""
    print("🔍 INVESTIGATING CODE GENERATION SYNTAX ISSUES")
    print("=" * 60)
    
    # Test 1: Show the problematic code
    test_problematic_javascript_code()
    
    # Test 2: Test text formatter
    test_text_formatter_processing()
    
    # Test 3: Test streaming simulation
    test_streaming_simulation()
    
    # Test 4: Test clean_agent_response impact
    test_clean_agent_response()
    
    # Test 5: Analyze whitespace normalization
    analyze_whitespace_normalization()
    
    print("\n" + "=" * 60)
    print("🎯 ANALYSIS COMPLETE")
    print("Check the output above to identify where the syntax issues are introduced.")

if __name__ == "__main__":
    main()
