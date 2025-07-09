#!/usr/bin/env python3
"""
Test script to verify dynamic token calculation for OpenRouter.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from archive.worker_old import Worker

def test_dynamic_token_calculation():
    """Test the dynamic token calculation for OpenRouter."""
    print("Testing dynamic token calculation for OpenRouter...")
    
    # Create a mock worker instance
    worker = Worker(
        prompt="Test prompt",
        general_instructions="Test instructions",
        agents=[],
        knowledge_base_files=[],
        internet_enabled=False,
        config_manager=None
    )
    
    # Test 1: Small input (should allow high max_tokens)
    print("\nTest 1 - Small input:")
    small_input = "This is a small input prompt."
    result = worker._calculate_dynamic_max_tokens(small_input, "OpenRouter", 50000)
    estimated_input = len(small_input) // 4
    print(f"Input: ~{estimated_input} tokens")
    print(f"User requested: 50,000 tokens")
    print(f"Calculated max_tokens: {result:,} tokens")
    print(f"Available for output: {result:,} tokens")
    
    # Test 2: Medium input (should reduce max_tokens)
    print("\nTest 2 - Medium input:")
    medium_input = "This is a medium input prompt. " * 1000  # ~25k tokens
    result = worker._calculate_dynamic_max_tokens(medium_input, "OpenRouter", 50000)
    estimated_input = len(medium_input) // 4
    print(f"Input: ~{estimated_input:,} tokens")
    print(f"User requested: 50,000 tokens")
    print(f"Calculated max_tokens: {result:,} tokens")
    print(f"Available for output: {result:,} tokens")
    
    # Test 3: Large input (should significantly reduce max_tokens)
    print("\nTest 3 - Large input:")
    large_input = "This is a large input prompt. " * 3000  # ~75k tokens
    result = worker._calculate_dynamic_max_tokens(large_input, "OpenRouter", 50000)
    estimated_input = len(large_input) // 4
    safe_limit = int(40960 * 0.95)
    print(f"Input: ~{estimated_input:,} tokens")
    print(f"Safe context limit: {safe_limit:,} tokens")
    print(f"User requested: 50,000 tokens")
    print(f"Calculated max_tokens: {result:,} tokens")
    print(f"Available for output: {result:,} tokens")
    print(f"Total estimated: {estimated_input + result:,} tokens (should be <= {safe_limit:,})")
    
    # Test 4: Very large input (should hit minimum)
    print("\nTest 4 - Very large input:")
    very_large_input = "This is a very large input prompt. " * 4000  # ~100k tokens
    result = worker._calculate_dynamic_max_tokens(very_large_input, "OpenRouter", 50000)
    estimated_input = len(very_large_input) // 4
    safe_limit = int(40960 * 0.95)
    print(f"Input: ~{estimated_input:,} tokens")
    print(f"Safe context limit: {safe_limit:,} tokens")
    print(f"User requested: 50,000 tokens")
    print(f"Calculated max_tokens: {result:,} tokens")
    print(f"Available for output: {result:,} tokens")
    print(f"Total estimated: {estimated_input + result:,} tokens (should be <= {safe_limit:,})")
    
    # Test 5: Edge case - input that would exceed safe limit
    print("\nTest 5 - Edge case (input near safe limit):")
    edge_input = "This is an edge case input. " * 3500  # ~87.5k tokens
    result = worker._calculate_dynamic_max_tokens(edge_input, "OpenRouter", 50000)
    estimated_input = len(edge_input) // 4
    safe_limit = int(40960 * 0.95)
    print(f"Input: ~{estimated_input:,} tokens")
    print(f"Safe context limit: {safe_limit:,} tokens")
    print(f"User requested: 50,000 tokens")
    print(f"Calculated max_tokens: {result:,} tokens")
    print(f"Available for output: {result:,} tokens")
    print(f"Total estimated: {estimated_input + result:,} tokens (should be <= {safe_limit:,})")
    
    # Test 6: Other providers (should not be affected by input size)
    print("\nTest 6 - Other providers:")
    for provider in ["OpenAI", "Anthropic", "Groq"]:
        result = worker._calculate_dynamic_max_tokens(large_input, provider, 50000)
        print(f"{provider}: {result:,} tokens (not affected by input size)")
    
    print("\n✓ Dynamic token calculation test completed!")

if __name__ == "__main__":
    test_dynamic_token_calculation() 