#!/usr/bin/env python3
"""
Test script to verify token limit coordination for large agent responses.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from model_settings import ModelSettings, settings_manager

def test_token_limit_coordination():
    """Test the token limit coordination features."""
    print("Testing token limit coordination...")
    
    # Test 1: Basic token limit validation
    print("\nTest 1 - Basic token limit validation:")
    settings = ModelSettings(provider="OpenAI", model="gpt-4")
    print(f"Default max_tokens: {settings.max_tokens}")
    
    # Test user requesting 100k tokens
    validation_result = settings.validate_and_adjust_max_tokens(100000)
    print(f"User requested: {validation_result['user_requested']:,}")
    print(f"API limit: {validation_result['api_limit']:,}")
    print(f"Effective tokens: {validation_result['effective_tokens']:,}")
    print(f"Was adjusted: {validation_result['was_adjusted']}")
    print(f"Reason: {validation_result['adjustment_reason']}")
    
    # Test 2: Different providers
    print("\nTest 2 - Different providers:")
    providers = ["OpenAI", "Anthropic", "Groq", "Ollama"]
    for provider in providers:
        settings = ModelSettings(provider=provider, model="test-model")
        api_limits = settings.get_api_token_limits()
        print(f"{provider}: min={api_limits['min']:,}, max={api_limits['max']:,}, recommended={api_limits['recommended']:,}")
    
    # Test 3: User limits within API limits
    print("\nTest 3 - User limits within API limits:")
    settings = ModelSettings(provider="Anthropic", model="claude-3-5-sonnet")
    validation_result = settings.validate_and_adjust_max_tokens(20000)
    print(f"User requested: {validation_result['user_requested']:,}")
    print(f"Effective tokens: {validation_result['effective_tokens']:,}")
    print(f"Was adjusted: {validation_result['was_adjusted']}")
    
    # Test 4: User limits exceeding API limits
    print("\nTest 4 - User limits exceeding API limits:")
    settings = ModelSettings(provider="Groq", model="llama3-70b-8192")
    validation_result = settings.validate_and_adjust_max_tokens(50000)
    print(f"User requested: {validation_result['user_requested']:,}")
    print(f"API limit: {validation_result['api_limit']:,}")
    print(f"Effective tokens: {validation_result['effective_tokens']:,}")
    print(f"Was adjusted: {validation_result['was_adjusted']}")
    print(f"Reason: {validation_result['adjustment_reason']}")
    
    # Test 5: No user limit specified
    print("\nTest 5 - No user limit specified:")
    settings = ModelSettings(provider="OpenAI", model="gpt-4")
    effective_tokens = settings.get_effective_max_tokens()
    print(f"Effective tokens (no user limit): {effective_tokens:,}")
    
    print("\n✓ All token limit coordination tests completed!")

if __name__ == "__main__":
    test_token_limit_coordination() 