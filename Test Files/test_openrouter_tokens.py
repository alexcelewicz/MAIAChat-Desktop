#!/usr/bin/env python3
"""
Test script to verify OpenRouter token limit coordination.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from model_settings import ModelSettings, settings_manager

def test_openrouter_token_limits():
    """Test OpenRouter token limit coordination specifically."""
    print("Testing OpenRouter token limit coordination...")
    
    # Test 1: OpenRouter with different token requests
    print("\nTest 1 - OpenRouter token limit validation:")
    settings = ModelSettings(provider="OpenRouter", model="anthropic/claude-3-5-sonnet")
    print(f"Default max_tokens: {settings.max_tokens}")
    
    # Test user requesting 50k tokens (should work with OpenRouter)
    validation_result = settings.validate_and_adjust_max_tokens(50000)
    print(f"User requested: {validation_result['user_requested']:,}")
    print(f"API limit: {validation_result['api_limit']:,}")
    print(f"Effective tokens: {validation_result['effective_tokens']:,}")
    print(f"Was adjusted: {validation_result['was_adjusted']}")
    print(f"Reason: {validation_result['adjustment_reason']}")
    
    # Test 2: OpenRouter with 100k tokens (should be capped at API limit)
    print("\nTest 2 - OpenRouter with 100k tokens:")
    validation_result = settings.validate_and_adjust_max_tokens(100000)
    print(f"User requested: {validation_result['user_requested']:,}")
    print(f"API limit: {validation_result['api_limit']:,}")
    print(f"Effective tokens: {validation_result['effective_tokens']:,}")
    print(f"Was adjusted: {validation_result['was_adjusted']}")
    print(f"Reason: {validation_result['adjustment_reason']}")
    
    # Test 3: OpenRouter with reasonable token limit
    print("\nTest 3 - OpenRouter with 20k tokens:")
    validation_result = settings.validate_and_adjust_max_tokens(20000)
    print(f"User requested: {validation_result['user_requested']:,}")
    print(f"Effective tokens: {validation_result['effective_tokens']:,}")
    print(f"Was adjusted: {validation_result['was_adjusted']}")
    
    # Test 4: Different OpenRouter models
    print("\nTest 4 - Different OpenRouter models:")
    models = [
        "anthropic/claude-3-5-sonnet",
        "openai/gpt-4o",
        "meta-llama/llama-3.1-70b-instruct",
        "google/gemini-1.5-flash"
    ]
    
    for model in models:
        settings = ModelSettings(provider="OpenRouter", model=model)
        api_limits = settings.get_api_token_limits()
        print(f"{model}: min={api_limits['min']:,}, max={api_limits['max']:,}, recommended={api_limits['recommended']:,}")
    
    # Test 5: Effective token calculation
    print("\nTest 5 - Effective token calculation:")
    settings = ModelSettings(provider="OpenRouter", model="anthropic/claude-3-5-sonnet")
    
    # Test with no user limit
    effective_tokens = settings.get_effective_max_tokens()
    print(f"Effective tokens (no user limit): {effective_tokens:,}")
    
    # Test with user limit within API limits
    effective_tokens = settings.get_effective_max_tokens(25000)
    print(f"Effective tokens (user limit 25k): {effective_tokens:,}")
    
    # Test with user limit exceeding API limits
    effective_tokens = settings.get_effective_max_tokens(50000)
    print(f"Effective tokens (user limit 50k): {effective_tokens:,}")
    
    print("\n✓ All OpenRouter token limit coordination tests completed!")

if __name__ == "__main__":
    test_openrouter_token_limits() 