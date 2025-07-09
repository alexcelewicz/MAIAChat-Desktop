#!/usr/bin/env python3
"""
Simple test for the code-aware streaming fix without heavy dependencies.
"""

import re

def _should_flush_for_code_integrity(buffer: str) -> bool:
    """
    Test version of the code integrity detection method.
    """
    if not buffer:
        return False
    
    # Check if we're likely inside a code block by looking for code patterns
    code_indicators = [
        # JavaScript/TypeScript patterns
        r'let\s+\w+',
        r'const\s+\w+', 
        r'var\s+\w+',
        r'function\s+\w+\s*\(',
        r'class\s+\w+\s*{',
        # Python patterns
        r'def\s+\w+\s*\(',
        r'class\s+\w+\s*:',
        r'import\s+\w+',
        r'from\s+\w+\s+import',
        # General programming patterns
        r'if\s*\(',
        r'for\s*\(',
        r'while\s*\(',
        r'}\s*else\s*{',
        # HTML/CSS patterns
        r'<\w+[^>]*>',
        r'}\s*$',  # CSS rule ending
    ]
    
    # Check if buffer contains code patterns
    has_code_pattern = any(re.search(pattern, buffer, re.IGNORECASE) for pattern in code_indicators)
    
    if has_code_pattern:
        # For code content, flush on single newlines to preserve line structure
        if '\n' in buffer:
            return True
        # Flush after assignment operators to prevent variable name/value separation
        if '=' in buffer and any(keyword in buffer.lower() for keyword in ['let ', 'const ', 'var ']):
            return True
        # Also flush after semicolons in JavaScript-like code to preserve statement boundaries
        if ';' in buffer and any(keyword in buffer.lower() for keyword in ['let ', 'const ', 'var ', 'function']):
            return True
    
    return False

def test_streaming_fix():
    """Test the streaming fix with the problematic JavaScript code"""
    
    print("🧪 TESTING CODE-AWARE STREAMING FIX")
    print("=" * 50)
    
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
        elif _should_flush_for_code_integrity(stream_buffer):  # NEW: Code-aware flushing
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
            # Check for spacing issues around equals
            elif '=' in line and ('=' in line.replace(' =', '').replace('= ', '')):
                # Check if there are missing spaces around =
                if re.search(r'\w=\w', line) or re.search(r'\w=\s', line) or re.search(r'\s=\w', line):
                    print(f"  Line {i}: ⚠️  Spacing issue around =: {repr(line)}")
                else:
                    print(f"  Line {i}: ✅ Valid statement: {repr(line)}")
            else:
                print(f"  Line {i}: ✅ Valid statement: {repr(line)}")
    
    if syntax_errors == 0:
        print(f"\n🎉 SUCCESS: No syntax errors detected!")
    else:
        print(f"\n⚠️  Found {syntax_errors} syntax error(s)")
    
    return final_result

def test_comparison():
    """Compare old vs new behavior"""
    
    print("\n" + "=" * 50)
    print("📊 COMPARISON: OLD VS NEW BEHAVIOR")
    print("=" * 50)
    
    # Old problematic result
    old_result = "let player;let obstacles = [];\nlet score = 0;let highScore= 0;\nlet gameSpeed;let initialGameSpeed = 6;\nconst canvasWidth = 800;const canvasHeight = 400;"
    
    # New fixed result
    new_result = test_streaming_fix()
    
    print(f"\nOLD BEHAVIOR (problematic):")
    print(repr(old_result))
    print("Formatted:")
    print(old_result)
    
    print(f"\nNEW BEHAVIOR (fixed):")
    print(repr(new_result))
    
    # Check for improvements
    print(f"\n🔍 IMPROVEMENTS:")
    
    # Check for merged statements on same line
    old_has_merged = any(line.count(';') > 1 for line in old_result.split('\n'))
    new_has_merged = any(line.count(';') > 1 for line in new_result.split('\n')) if new_result else True
    
    if old_has_merged and not new_has_merged:
        print("  ✅ Fixed merged statements on same line")
    elif old_has_merged and new_has_merged:
        print("  ⚠️  Merged statements still present")
    else:
        print("  ✅ No merged statements detected")
    
    # Check for proper line separation
    old_lines = [line.strip() for line in old_result.split('\n') if line.strip()]
    new_lines = [line.strip() for line in new_result.split('\n') if line.strip()]
    
    print(f"  📊 Statement count: Old={len(old_lines)}, New={len(new_lines)}")
    
    # Check each line for syntax validity
    print(f"\n📝 LINE-BY-LINE ANALYSIS:")
    print("OLD BEHAVIOR:")
    for i, line in enumerate(old_lines, 1):
        if ';' in line and line.count(';') > 1:
            print(f"  Line {i}: ❌ {repr(line)} (multiple statements)")
        else:
            print(f"  Line {i}: ✅ {repr(line)}")
    
    print("NEW BEHAVIOR:")
    for i, line in enumerate(new_lines, 1):
        if ';' in line and line.count(';') > 1:
            print(f"  Line {i}: ❌ {repr(line)} (multiple statements)")
        else:
            print(f"  Line {i}: ✅ {repr(line)}")

if __name__ == "__main__":
    test_comparison()
